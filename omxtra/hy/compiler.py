# ruff: noqa: A001, A002, S307
"""Compiling Hy models into Python ASTs."""
import ast
import contextlib
import copy
import traceback
import types
import typing as ta
import warnings

from omcore import check

from .errors import HyCompileError
from .errors import HyLanguageError
from .errors import HySyntaxError
from .macros import macroexpand
from .models import Bytes
from .models import Complex
from .models import Dict
from .models import Expression
from .models import FComponent
from .models import Float
from .models import FString
from .models import Integer
from .models import Keyword
from .models import Lazy
from .models import List
from .models import Object
from .models import Sequence
from .models import Set
from .models import String
from .models import Symbol
from .models import Tuple
from .models import as_model
from .models import is_unpack
from .reader import HyReader
from .reader import mangle
from .results import Result
from .results import ResultStatement
from .results import asty
from .scoping import ResolveOuterVars
from .scoping import ScopeBase
from .scoping import ScopeGlobal


if ta.TYPE_CHECKING:
    from .runtime import HyRuntime


CompilerOutput: ta.TypeAlias = Result | ast.AST
ModelCompilerT = ta.TypeVar('ModelCompilerT', bound=ta.Callable[..., CompilerOutput])
SequenceT = ta.TypeVar('SequenceT', bound=Sequence)


##


_MODEL_COMPILERS: dict[type[Object], ta.Callable[..., CompilerOutput]] = {}


def builds_model(*model_types: type[Object]) -> ta.Callable[[ModelCompilerT], ModelCompilerT]:
    """Decorator registering the decorated `HyASTCompiler` method as the compiler of models of the given types."""

    def _dec(fn: ModelCompilerT) -> ModelCompilerT:
        for t in model_types:
            _MODEL_COMPILERS[t] = fn
        return fn

    return _dec


def _make_hy_model_item(a: ta.Any) -> ta.Any:
    if type(a) is str:
        return Symbol(a)
    elif type(a) is list:
        return a[0]
    else:
        return a


def make_hy_model(outer: type[SequenceT], x: ta.Iterable[ta.Any], rest: list[ta.Any] | None) -> SequenceT:
    """
    Make a model of type ``outer`` from the items ``x``, followed by ``rest``. Strings in ``x`` are made symbols, and
    single-item lists are unwrapped - allowing a string to be passed as-is.
    """

    return outer([_make_hy_model_item(a) for a in x] + (rest or []))


def mkexpr(*items: ta.Any, rest: list[ta.Any] | None = None) -> Expression:
    return make_hy_model(Expression, items, rest)


def is_annotate_expression(model: Object) -> bool:
    return isinstance(model, Expression) and bool(model) and model[0] == Symbol('annotate')


def _is_method_call_head(model: Object) -> ta.TypeGuard[Expression]:
    """Whether ``model`` is the head of a method call like ``(.a1.a2 obj v1 v2)``, read as ``(. None a1 a2)``."""

    return (
        isinstance(model, Expression) and
        len(model) >= 2 and
        isinstance(model[0], Symbol) and
        not str(model[0]).strip('.') and
        model[1] == Symbol('None')
    )


class HyASTCompiler:
    """
    A Hy-to-Python AST compiler.

    The compiler compiles into the context of a given ``module``, in which macros are looked up and compile-time code is
    evaluated, and on behalf of a given ``runtime``, which provides the core macros, the names visible to all Hy code
    (such as ``hy``), and module importing. ``filename`` and ``source`` are optional information used for error messages
    and debugging. ``extra_macros`` take precedence over macros in ``module``.

    Much of the compiler - including underscore-prefixed members like ``_syntax_error`` and ``_compile_branch`` - is
    used by the core macros, both those implemented in Python and those implemented in Hy.
    """

    def __init__(
            self,
            module: types.ModuleType | str,
            filename: str | None = None,
            source: str | None = None,
            extra_macros: ta.Mapping[str, ta.Callable[..., ta.Any]] | None = None,
            *,
            runtime: HyRuntime,
    ) -> None:
        super().__init__()

        self._runtime = runtime
        self._extra_macros: ta.Mapping[str, ta.Callable[..., ta.Any]] = extra_macros or {}

        self._anon_var_count = 0

        # A stack of dicts of local compiler settings, such as the definitions of local macros, the last being the top.
        self._local_state_stack: list[dict[str, ta.Any]] = []
        self.new_local_state()

        if isinstance(module, str):
            module = runtime.import_module(module)
        self._module = module

        # This makes the runtime's `hy` namespace and prelude available to - and the macro tables expected by - the code
        # being compiled.
        runtime.prepare_module(module)

        self._module_name = module.__name__

        # These may be reassigned between compilations, as by the REPL.
        self.filename = filename
        self.source = source

        # Set by `macroexpand` to the expression currently being macro-expanded, accessible to macros as
        # `_hy_compiler.this`.
        self.this: Expression | None = None

        # Swapped by scopes as they're entered and exited.
        self.scope: ScopeBase = ScopeGlobal(self)

    @property
    def runtime(self) -> HyRuntime:
        return self._runtime

    @property
    def module(self) -> types.ModuleType:
        return self._module

    @property
    def module_name(self) -> str:
        return self._module_name

    @property
    def extra_macros(self) -> ta.Mapping[str, ta.Callable[..., ta.Any]]:
        return self._extra_macros

    @property
    def anon_var_count(self) -> int:
        return self._anon_var_count

    @property
    def local_state_stack(self) -> ta.Sequence[dict[str, ta.Any]]:
        return self._local_state_stack

    ##
    # Local state

    def new_local_state(self) -> None:
        """Add a new local state to the top of the stack."""

        self._local_state_stack.append(dict(macros={}))

    @contextlib.contextmanager
    def local_state(self) -> ta.Iterator[None]:
        self.new_local_state()
        try:
            yield
        finally:
            self._local_state_stack.pop()

    def is_in_local_state(self) -> bool:
        return len(self._local_state_stack) > 1

    def get_local_option(self, key: str, default: ta.Any) -> ta.Any:
        """Get the topmost available value of a local-state setting."""

        return next((s[key] for s in reversed(self._local_state_stack) if key in s), default)

    def warn_on_core_shadow(self, name: str) -> None:
        if (
                mangle(name) in self._runtime.core_macros and
                self.get_local_option('warn_on_core_shadow', True)
        ):
            warnings.warn(
                f'New macro `{name}` will shadow the core macro of the same name',
                RuntimeWarning,
            )

    ##
    # Helpers

    def get_anon_var(self, base: str = 'anon', name: str = '') -> str:
        self._anon_var_count += 1
        name = name and '_' + name
        return f'_hy_{base}{name}_{self._anon_var_count}'

    def _syntax_error(self, expr: Object, message: str) -> ta.NoReturn:
        raise HySyntaxError(message, expr, self.filename, self.source)

    def _nonconst(self, name: Symbol) -> Symbol:
        if str(name) in ('None', 'True', 'False'):
            self._syntax_error(name, "Can't assign to constant")
        return name

    def eval(self, model: Object) -> ta.Any:
        """Evaluate ``model`` at compile-time, in the module being compiled."""

        return hy_eval(
            model,
            locals=self._module.__dict__,
            module=self._module,
            filename=self.filename,
            source=self.source,
            runtime=self._runtime,
        )

    ##
    # Compilation

    def compile_atom(self, atom: Object) -> Result:
        # Compilation methods may mutate the atom, so copy it first.
        atom = copy.copy(atom)
        return Result() + _MODEL_COMPILERS[type(atom)](self, atom)

    def compile(self, tree: Object | None) -> Result:
        if tree is None:
            return Result()

        try:
            return self.compile_atom(tree)

        except (HyCompileError, HyLanguageError):
            # `HyCompileError`s come from nested calls of `compile`, and mustn't be wrapped again. `HyLanguageError`s
            # are expected errors that should be passed to the user.
            raise

        except Exception as e:
            # These are unexpected errors that will - hopefully - never be seen by the user.
            raise HyCompileError(f'Internal Compiler Bug\n {traceback.format_exc()}') from e

    def _compile_collect(
            self,
            exprs: ta.Iterable[Object],
            with_kwargs: bool = False,
            dict_display: bool = False,
    ) -> tuple[list[ast.expr | None], Result, list[ast.keyword]]:
        """
        Compile the given models, returning a list of their expression contexts, the sum of their Results, and - if
        ``with_kwargs`` is set - the keyword arguments among them. With ``dict_display``, a mapping unpacking
        contributes a None key followed by its value, as in an `ast.Dict`.
        """

        compiled_exprs: list[ast.expr | None] = []
        ret = Result()
        keywords: list[ast.keyword] = []

        exprs_iter = iter(exprs)
        for expr in exprs_iter:
            if is_unpack('mapping', expr):
                ret += self.compile(ta.cast(Expression, expr)[1])
                if dict_display:
                    compiled_exprs.append(None)
                    compiled_exprs.append(ret.force_expr)
                elif with_kwargs:
                    keywords.append(asty.keyword(expr, arg=None, value=ret.force_expr))

            elif with_kwargs and isinstance(expr, Keyword):
                try:
                    value = next(exprs_iter)
                except StopIteration:
                    self._syntax_error(expr, f'Keyword argument {expr} needs a value.')

                if not expr:
                    self._syntax_error(expr, "Can't call a function with the empty keyword")

                compiled_value = self.compile(value)
                ret += compiled_value

                arg = str(expr)[1:]
                keywords.append(asty.keyword(expr, arg=mangle(arg), value=compiled_value.force_expr))

            else:
                ret += self.compile(expr)
                compiled_exprs.append(ret.force_expr)

        return compiled_exprs, ret, keywords

    @builds_model(Lazy)
    def _compile_branch(self, exprs: ta.Iterable[Object]) -> Result:
        """
        Make a branch out of an iterable of models, compiling each and forcing its expression context as a statement
        before the next is compiled. The expression context of the last is kept for the returned Result.
        """

        result = Result()
        last: Result | None = None
        for node in exprs:
            if last is not None:
                result += last.expr_as_stmt()
            last = self.compile(node)
            result += last

        return result

    def _storeize(
            self,
            expr: Object,
            name: Result | ast.expr,
            func: type[ast.expr_context] | None = None,
    ) -> ast.expr:
        """Return a copy of the assignment target ``name`` with an expression context of ``func``, by default Store."""

        if not func:
            func = ast.Store

        if isinstance(name, Result):
            if not name.is_expr():
                self._syntax_error(expr, "Can't assign or delete a non-expression")
            name = name.force_expr

        new_name: ast.expr
        if isinstance(name, (ast.Tuple, ast.List)):
            new_name = type(name)(elts=[self._storeize(expr, x, func) for x in name.elts])

        elif isinstance(name, ast.Name):
            new_name = ast.Name(id=name.id)
            if func == ast.Store:
                self.scope.assign(new_name)

        elif isinstance(name, ast.Subscript):
            new_name = ast.Subscript(value=name.value, slice=name.slice)

        elif isinstance(name, ast.Attribute):
            new_name = ast.Attribute(value=name.value, attr=name.attr)

        elif isinstance(name, ast.Starred):
            new_name = ast.Starred(value=self._storeize(expr, name.value, func))

        else:
            what = 'constant' if isinstance(name, ast.Constant) else type(expr).__name__
            self._syntax_error(expr, f"Can't assign or delete a {what}")

        new_name.ctx = func()
        ast.copy_location(new_name, name)
        return new_name

    def _find_method_call_object(self, expr: Expression, args: ta.Sequence[Object]) -> int:
        """
        Return the index in ``args`` - the arguments of the method call ``expr`` - of the object the method is called
        on, skipping keyword arguments and mapping unpackings.
        """

        i = 0
        while i < len(args):
            if isinstance(args[i], Keyword):
                if i == 0 and len(args) == 1:
                    break
                i += 2
            elif is_unpack('iterable', args[i]):
                self._syntax_error(args[i], "can't call a method on an `unpack-iterable` form")
            elif is_unpack('mapping', args[i]):
                i += 1
            else:
                break
        else:
            self._syntax_error(expr, 'attribute access requires object')

        return i

    ##
    # Model compilers

    @builds_model(Expression)
    def compile_expression(self, expr: Expression) -> CompilerOutput:
        expanded = macroexpand(expr, self._module, self)
        if isinstance(expanded, (Result, ast.AST)):
            return expanded
        elif not isinstance(expanded, Expression):
            # Go through compile again if we have a different type of model.
            return self.compile(expanded)
        expr = expanded

        if not expr:
            self._syntax_error(expr, 'empty expressions are not allowed at top level')

        args = list(expr)
        root = args.pop(0)

        func: Result | None = None
        if _is_method_call_head(root):
            # ((. None a1 a2) obj v1 v2) -> ((. obj a1 a2) v1 v2)
            obj = args.pop(self._find_method_call_object(expr, args))
            func = self.compile(Expression([Symbol('.'), obj, *root[2:]]).replace(root))

        if is_annotate_expression(root):
            # Flatten and compile the annotation expression.
            return self.compile_expression(Expression(root + args).replace(root))

        if func is None:
            func = self.compile(root)

        call_args, ret, keywords = self._compile_collect(args, with_kwargs=True)

        return (
            func +
            ret +
            asty.Call(
                expr,
                func=func.expr or asty.Constant(root, value=None),
                args=call_args,
                keywords=keywords,
            )
        )

    @builds_model(Integer, Float, Complex)
    def compile_numeric_literal(self, x: Integer | Float | Complex) -> ast.Constant:
        return asty.Constant(x, value={Integer: int, Float: float, Complex: complex}[type(x)](x))

    @builds_model(Symbol)
    def compile_symbol(self, symbol: Symbol) -> ast.AST:
        if symbol == Symbol('...'):
            return asty.Constant(symbol, value=Ellipsis)

        # By this point, `symbol` should be either all dots or dot-free.
        check.state(not symbol.strip('.') or '.' not in symbol)

        if mangle(symbol) in ('None', 'False', 'True'):
            return asty.Constant(symbol, value=ast.literal_eval(mangle(symbol)))

        return self.scope.access(asty.Name(symbol, id=mangle(symbol), ctx=ast.Load()))

    @builds_model(Keyword)
    def compile_keyword(self, obj: Keyword) -> Result:
        # hy.models.Keyword(name)
        return Result() + asty.Call(
            obj,
            func=asty.Attribute(
                obj,
                value=asty.Attribute(
                    obj,
                    value=asty.Name(obj, id='hy', ctx=ast.Load()),
                    attr='models',
                    ctx=ast.Load(),
                ),
                attr='Keyword',
                ctx=ast.Load(),
            ),
            args=[asty.Constant(obj, value=obj.name)],
            keywords=[],
        )

    @builds_model(String, Bytes)
    def compile_string(self, string: String | Bytes) -> ast.Constant:
        return asty.Constant(string, value=bytes(string) if isinstance(string, Bytes) else str(string))

    @builds_model(FComponent)
    def compile_fcomponent(self, fcomponent: FComponent) -> Result:
        if fcomponent.conversion not in (None, 's', 'r', 'a'):
            self._syntax_error(fcomponent, f'Invalid conversion character {fcomponent.conversion!r}')
        conversion = ord(fcomponent.conversion) if fcomponent.conversion else -1

        root, *rest = fcomponent
        value = self.compile(root)
        elts, ret, _ = self._compile_collect(rest)
        spec = asty.JoinedStr(fcomponent, values=elts) if elts else None

        node_type = asty.Interpolation if fcomponent.is_tstring else asty.FormattedValue
        extra_kwargs = dict(str=fcomponent.expression) if fcomponent.is_tstring else {}

        return (
            value +
            ret +
            node_type(
                fcomponent,
                value=value.expr,
                conversion=conversion,
                format_spec=spec,
                **extra_kwargs,
            )
        )

    @builds_model(FString)
    def compile_fstring(self, fstring: FString) -> Result:
        elts, ret, _ = self._compile_collect(fstring)
        return ret + (asty.TemplateStr if fstring.is_tstring else asty.JoinedStr)(fstring, values=elts)

    @builds_model(List, Set)
    def compile_list(self, expression: List | Set) -> Result:
        elts, ret, _ = self._compile_collect(expression)
        node = {List: asty.List, Set: asty.Set}[type(expression)]
        return ret + node(
            expression,
            elts=elts,
            **({} if node is asty.Set else dict(ctx=ast.Load())),
        )

    @builds_model(Dict)
    def compile_dict(self, m: Dict) -> Result:
        keyvalues, ret, _ = self._compile_collect(m, dict_display=True)
        return ret + asty.Dict(m, keys=keyvalues[::2], values=keyvalues[1::2])

    @builds_model(Tuple)
    def compile_tuple(self, expression: Tuple) -> Result:
        elts, ret, _ = self._compile_collect(expression)
        return ret + asty.Tuple(expression, elts=elts, ctx=ast.Load())


##


def hy_eval(
        hytree: ta.Any,
        locals: ta.MutableMapping[str, ta.Any] | None,
        module: types.ModuleType | str,
        compiler: HyASTCompiler | None = None,
        filename: str | None = None,
        source: str | None = None,
        globals: dict[str, ta.Any] | None = None,
        extra_macros: ta.Mapping[str, ta.Callable[..., ta.Any]] | None = None,
        *,
        runtime: HyRuntime | None = None,
) -> ta.Any:
    """
    Compile and evaluate a Hy tree in the context of ``module``, returning the value of its final form. The low-level
    workhorse of evaluation: no stack introspection is done, and nothing beyond ``module`` (and ``globals``) is touched.
    """

    # The tree's own filename and source, if it has them, take precedence.
    filename = getattr(hytree, 'filename', filename) or '<string>'
    source = getattr(hytree, 'source', source)

    module_ast, expr_ast = hy_compile(
        hytree,
        module,
        get_expr=True,
        compiler=compiler,
        filename=filename,
        source=source,
        extra_macros=extra_macros,
        runtime=runtime,
    )

    if globals is None:
        if compiler is not None:
            globals = compiler.module.__dict__
        elif isinstance(module, types.ModuleType):
            globals = module.__dict__
        else:
            globals = check.not_none(runtime).import_module(module).__dict__

    # Run the statements, then evaluate the final expression.
    eval(compile(module_ast, filename, 'exec'), globals, locals)
    return eval(compile(expr_ast, filename, 'eval'), globals, locals)


def _pop_module_head(stmts: list[ResultStatement]) -> list[ResultStatement]:
    """
    Remove and return the statements at the start of ``stmts`` which must begin a module body: a docstring, then any
    `__future__` imports.
    """

    head: list[ResultStatement] = []

    if (
            stmts and
            isinstance(stmts[0], ast.Expr) and
            isinstance(stmts[0].value, ast.Constant) and
            isinstance(stmts[0].value.value, str)
    ):
        head.append(stmts.pop(0))

    while (
            stmts and
            isinstance(stmts[0], ast.ImportFrom) and
            stmts[0].module == '__future__'
    ):
        head.append(stmts.pop(0))

    return head


@ta.overload
def hy_compile(
        tree: ta.Any,
        module: types.ModuleType | str,
        root: type[ast.Module | ast.Interactive] = ast.Module,
        get_expr: ta.Literal[False] = False,
        compiler: HyASTCompiler | None = None,
        filename: str | None = None,
        source: str | None = None,
        preamble: bool = False,
        extra_macros: ta.Mapping[str, ta.Callable[..., ta.Any]] | None = None,
        *,
        runtime: HyRuntime | None = None,
) -> ast.Module | ast.Interactive:
    ...


@ta.overload
def hy_compile(
        tree: ta.Any,
        module: types.ModuleType | str,
        root: type[ast.Module | ast.Interactive] = ast.Module,
        *,
        get_expr: ta.Literal[True],
        compiler: HyASTCompiler | None = None,
        filename: str | None = None,
        source: str | None = None,
        preamble: bool = False,
        extra_macros: ta.Mapping[str, ta.Callable[..., ta.Any]] | None = None,
        runtime: HyRuntime | None = None,
) -> tuple[ast.Module | ast.Interactive, ast.Expression]:
    ...


def hy_compile(
        tree: ta.Any,
        module: types.ModuleType | str,
        root: type[ast.Module | ast.Interactive] = ast.Module,
        get_expr: bool = False,
        compiler: HyASTCompiler | None = None,
        filename: str | None = None,
        source: str | None = None,
        preamble: bool = False,
        extra_macros: ta.Mapping[str, ta.Callable[..., ta.Any]] | None = None,
        *,
        runtime: HyRuntime | None = None,
) -> ast.Module | ast.Interactive | tuple[ast.Module | ast.Interactive, ast.Expression]:
    """
    Compile a Hy model tree (or anything which can be promoted to one) into a Python AST of type ``root``. If
    ``get_expr`` is set, the value of the tree's final form is kept rather than discarded, and a tuple of the AST and an
    `ast.Expression` of that value is returned.

    The tree is compiled in the context of ``module`` (or the module of that name) on behalf of ``runtime``, unless an
    existing ``compiler`` is given, in which case its module, runtime, filename, and source take priority.
    ``extra_macros`` are passed to a newly created compiler. The ``filename`` and ``source`` attributes of ``tree``, if
    any, take priority over those given.

    If ``preamble`` is set, a module body is prefixed with statements binding ``hy`` and the runtime's prelude (such as
    ``ta``), for code which will be executed somewhere the runtime can't inject them itself (such as in bytecode loaded
    by Python's import system).
    """

    if compiler is not None:
        runtime = compiler.runtime
    runtime = check.not_none(runtime)

    filename = getattr(tree, 'filename', filename)
    source = getattr(tree, 'source', source)
    reader = getattr(tree, 'reader', None)

    tree = as_model(tree)
    if not isinstance(tree, Object):
        raise TypeError('`tree` must be a hy.models.Object or capable of being promoted to one')

    if compiler is None:
        compiler = HyASTCompiler(
            module,
            filename=filename,
            source=source,
            extra_macros=extra_macros,
            runtime=runtime,
        )

    with HyReader.using_reader(reader, create=False), compiler.scope:
        result = compiler.compile(tree)
    expr = result.force_expr

    if not get_expr:
        result += result.expr_as_stmt()

    result.stmts = list(map(ResolveOuterVars().visit, result.stmts))

    body: list[ResultStatement] = []
    if issubclass(root, ast.Module):
        body.extend(_pop_module_head(result.stmts))
        if preamble:
            body.extend(runtime.preamble_statements())
    body.extend(result.stmts)

    ret = root(
        # Exception handlers are consumed by `try` before they could reach a module body.
        body=ta.cast('list[ast.stmt]', body),
        **({} if root is ast.Interactive else dict(type_ignores=[])),
    )

    if get_expr:
        return ret, ast.Expression(body=expr)

    return ret
