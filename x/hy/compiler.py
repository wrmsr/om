# ruff: noqa: A001, A002, S307
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
from .results import ResultStatement  # noqa: F401
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


_model_compilers: dict[type[Object], ta.Callable[..., Result | ast.AST]] = {}


def builds_model(*model_types: type[Object]) -> ta.Callable[[ModelCompilerT], ModelCompilerT]:
    "Assign the decorated method to _model_compilers for the given types."

    def _dec(fn: ModelCompilerT) -> ModelCompilerT:
        for t in model_types:
            _model_compilers[t] = fn
        return fn

    return _dec


def make_hy_model(outer: type[SequenceT], x: ta.Iterable[ta.Any], rest: list[ta.Any] | None) -> SequenceT:
    return outer(
        [Symbol(a) if type(a) is str else a[0] if type(a) is list else a for a in x] +
        (rest or []),
    )


def mkexpr(*items: ta.Any, **kwargs: ta.Any) -> Expression:
    return make_hy_model(Expression, items, kwargs.get('rest'))


def is_annotate_expression(model: Object) -> bool:
    return isinstance(model, Expression) and bool(model) and model[0] == Symbol('annotate')


class HyASTCompiler:
    """
    A Hy-to-Python AST compiler.

    The compiler compiles into the context of a given ``module``, in which macros are looked up and compile-time code is
    evaluated, and on behalf of a given ``runtime``, which provides the core macros, the names visible to all Hy code
    (such as ``hy``), and module importing. ``filename`` and ``source`` are optional information used for error messages
    and debugging. ``extra_macros`` take precedence over macros in ``module``.
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

        self.runtime = runtime

        self.anon_var_count = 0
        self.temp_if: str | None = None
        self.extra_macros = extra_macros or {}

        # Make a list of dictionaries with local compiler settings, such as the definitions of local macros. The last
        # element is considered the top of the stack.
        self.local_state_stack: list[dict[str, ta.Any]] = []
        self.new_local_state()

        if isinstance(module, str):
            self.module = runtime.import_module(module)
        else:
            self.module = module

        # This makes the runtime's `hy` namespace and prelude available to - and the macro tables expected by - the code
        # being compiled.
        runtime.prepare_module(self.module)

        self.module_name = self.module.__name__

        self.filename = filename
        self.source = source

        self.this: Expression | None = None
        # Set in `macroexpand` to the current expression being macro-expanded, so it can be accessed as
        # `&compiler.this`.

        self.scope: ScopeBase = ScopeGlobal(self)

    def new_local_state(self) -> None:
        """Add a new local state to the top of the stack."""

        self.local_state_stack.append(dict(macros={}))

    def is_in_local_state(self) -> bool:
        return len(self.local_state_stack) > 1

    def get_local_option(self, key: str, default: ta.Any) -> ta.Any:
        """Get the topmost available value of a local-state setting."""

        return next(
            (s[key]
                for s in reversed(self.local_state_stack)
                if key in s),
            default)

    def warn_on_core_shadow(self, name: str) -> None:
        if (
                mangle(name) in self.runtime.core_macros and
                self.get_local_option('warn_on_core_shadow', True)
        ):
            warnings.warn(
                f'New macro `{name}` will shadow the core macro of the same name',
                RuntimeWarning,
            )

    def get_anon_var(self, base: str = 'anon', name: str = '') -> str:
        self.anon_var_count += 1
        name = name and '_' + name
        return f'_hy_{base}{name}_{self.anon_var_count}'

    def compile_atom(self, atom: Object) -> Result:
        # Compilation methods may mutate the atom, so copy it first.
        atom = copy.copy(atom)
        return Result() + _model_compilers[type(atom)](self, atom)

    def compile(self, tree: Object | None) -> Result:
        if tree is None:
            return Result()
        try:
            ret = self.compile_atom(tree)
            return ret
        except HyCompileError:
            # compile calls compile, so we're going to have multiple raise nested; so let's re-raise this exception,
            # let's not wrap it in another HyCompileError!
            raise
        except HyLanguageError:
            # These are expected errors that should be passed to the user.
            raise
        except Exception as e:  # noqa: BLE001
            # These are unexpected errors that will--hopefully--never be seen by the user.
            f_exc = traceback.format_exc()
            exc_msg = f'Internal Compiler Bug\n {f_exc}'
            raise HyCompileError(exc_msg) from e

    def _syntax_error(self, expr: Object, message: str) -> ta.NoReturn:
        raise HySyntaxError(message, expr, self.filename, self.source)

    def _compile_collect(
            self,
            exprs: ta.Iterable[Object],
            with_kwargs: bool = False,
            dict_display: bool = False,
    ) -> tuple[list[ast.expr | None], Result, list[ast.keyword]]:
        """
        Collect the expression contexts from a list of compiled expression.

        This returns a list of the expression contexts, and the sum of the Result objects passed as arguments.
        """

        compiled_exprs: list[ast.expr | None] = []
        ret = Result()
        keywords = []

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
        Make a branch out of an iterable of Result objects

        This generates a Result from the given sequence of Results, forcing each expression context as a statement
        before the next result is used.

        We keep the expression context of the last argument for the returned Result
        """

        result = Result()
        last = None
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
        """Return a new `name` object with an ast.Store() context"""

        if not func:
            func = ast.Store

        if isinstance(name, Result):
            if not name.is_expr():
                self._syntax_error(expr, "Can't assign or delete a non-expression")
            name = name.force_expr

        new_name: ast.expr
        if isinstance(name, (ast.Tuple, ast.List)):
            typ = type(name)
            new_elts = []
            for x in name.elts:
                new_elts.append(self._storeize(expr, x, func))
            new_name = typ(elts=new_elts)
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
            self._syntax_error(
                expr,
                "Can't assign or delete a "
                + (
                    'constant'
                    if isinstance(name, ast.Constant)
                    else type(expr).__name__
                ),
            )

        new_name.ctx = func()
        ast.copy_location(new_name, name)
        return new_name

    def _nonconst(self, name: Symbol) -> Symbol:
        if str(name) in ('None', 'True', 'False'):
            self._syntax_error(name, "Can't assign to constant")
        return name

    def eval(self, model: Object) -> ta.Any:
        return hy_eval(
            model,
            locals=self.module.__dict__,
            module=self.module,
            filename=self.filename,
            source=self.source,
            runtime=self.runtime,
        )

    @contextlib.contextmanager
    def local_state(self) -> ta.Iterator[None]:
        self.new_local_state()
        try:
            yield
        finally:
            self.local_state_stack.pop()

    @builds_model(Expression)
    def compile_expression(self, expr: Expression) -> Result | ast.AST:
        # Perform macro expansions
        expanded = macroexpand(expr, self.module, self)
        if isinstance(expanded, (Result, ast.AST)):
            # Use this as-is.
            return expanded
        elif not isinstance(expanded, Expression):
            # Go through compile again if we have a different type of model.
            return self.compile(expanded)
        expr = expanded

        if not expr:
            self._syntax_error(
                expr, 'empty expressions are not allowed at top level',
            )

        args = list(expr)
        root = args.pop(0)
        func = None

        if (
            isinstance(root, Expression) and
            len(root) >= 2 and
            isinstance(root[0], Symbol) and
            not str(root[0]).strip('.') and
            root[1] == Symbol('None')
        ):
            # ((. None a1 a2) obj v1 v2) -> ((. obj a1 a2) v1 v2)
            # (The reader already parsed `.a1.a2` as `(. None a1 a2)`.)

            # Find the object we're calling the method on.
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

            func = self.compile(
                Expression([Symbol('.'), args.pop(i), *root[2:]]).replace(root),
            )

        if is_annotate_expression(root):
            # Flatten and compile the annotation expression.
            ann_expr = Expression(root + args).replace(root)
            return self.compile_expression(ann_expr)

        if not func:
            func = self.compile(root)

        args, ret, keywords = self._compile_collect(args, with_kwargs=True)

        return (
            func +
            ret +
            asty.Call(
                expr,
                func=func.expr or asty.Constant(root, value=None),
                args=args,
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
        ret = Result()
        ret += asty.Call(
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
        return ret

    @builds_model(String, Bytes)
    def compile_string(self, string: String | Bytes) -> ast.Constant:
        return asty.Constant(string, value=bytes(string) if isinstance(string, Bytes) else str(string))

    @builds_model(FComponent)
    def compile_fcomponent(self, fcomponent: FComponent) -> Result:
        if fcomponent.conversion not in (None, 's', 'r', 'a'):
            self._syntax_error(
                fcomponent, f'Invalid conversion character {fcomponent.conversion!r}',
            )
        conversion = ord(fcomponent.conversion) if fcomponent.conversion else -1
        root, *rest = fcomponent
        value = self.compile(root)
        elts, ret, _ = self._compile_collect(rest)
        if elts:
            spec = asty.JoinedStr(fcomponent, values=elts)
        else:
            spec = None
        return (
            value +
            ret +
            (asty.Interpolation if fcomponent.is_tstring else asty.FormattedValue)(
                fcomponent,
                value=value.expr,
                conversion=conversion,
                format_spec=spec,
                **(dict(str=fcomponent.expression) if fcomponent.is_tstring else {}),
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

    # Does the Hy AST object come with its own information?
    filename = getattr(hytree, 'filename', filename) or '<string>'
    source = getattr(hytree, 'source', source)

    _ast, expr = hy_compile(
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

    # Two-step eval: eval() the body of the exec call
    eval(compile(_ast, filename, 'exec'), globals, locals)

    # Then eval the expression context and return that
    return eval(compile(expr, filename, 'eval'), globals, locals)


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
    Compile a hy.models.Object tree into a Python AST Module.

    Args:
        tree (Object): The Hy AST object to compile.
        module (Union[str, types.ModuleType]): Module, or name of the module, in which the Hy tree is evaluated.
            The module associated with `compiler` takes priority over this value.
        root (Type[ast.AST]): Root object for the Python AST tree.
        get_expr (bool): If true, return a tuple with `(root_obj, last_expression)`.
        compiler (Optional[HyASTCompiler]): An existing Hy compiler to use for compilation.  Also serves as
            the `module` and `runtime` values when given.
        filename (Optional[str]): The filename corresponding to the source for `tree`.  This will be
            overridden by the `filename` field of `tree`, if any; otherwise, it defaults to "<string>".  When `compiler`
            is given, its `filename` field value is always used.
        source (Optional[str]): A string containing the source code for `tree`.  This will be
            overridden by the `source` field of `tree`, if any; otherwise, if `None`, an attempt will be made to obtain
            it from the module given by `module`.  When `compiler` is given, its `source` field value is always used.
        preamble (bool): If true, prefix the module body with statements binding `hy` and the runtime's prelude (such as
            `ta`), for code which will be executed somewhere the runtime can't inject them itself (such as in bytecode
            loaded by Python's import system).
        extra_macros (Optional[dict]): Passed through to `HyASTCompiler`, if it's called.
        runtime (Optional[HyRuntime]): The runtime on whose behalf to compile. Required unless `compiler` is given.

    Returns:
        ast.AST: A Python AST tree
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

    compiler = compiler or HyASTCompiler(
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

    body = []

    if issubclass(root, ast.Module):
        # Pull out a single docstring and prepend to the resulting body.
        if (
            result.stmts and
            isinstance(result.stmts[0], ast.Expr) and
            isinstance(result.stmts[0].value, ast.Constant) and
            isinstance(result.stmts[0].value.value, str)
        ):

            body += [result.stmts.pop(0)]

        # Pull out any __future__ imports, since they are required to be at the beginning.
        while (
            result.stmts and
            isinstance(result.stmts[0], ast.ImportFrom) and
            result.stmts[0].module == '__future__'
        ):

            body += [result.stmts.pop(0)]

        if preamble:
            body.extend(runtime.preamble_statements())

    body += result.stmts
    ret = root(
        # Try macros consume exception handlers before producing module bodies.
        body=ta.cast('list[ast.stmt]', body),
        **({} if root is ast.Interactive else dict(type_ignores=[])))

    if get_expr:
        return ret, ast.Expression(body=expr)

    return ret
