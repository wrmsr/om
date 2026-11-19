# ruff: noqa: SLF001
"""Functions and macros."""
import ast
import itertools
import typing as ta

from omcore import check

from ...compiler import HyASTCompiler
from ...funcparserlib.parser import many
from ...funcparserlib.parser import maybe
from ...funcparserlib.parser import some
from ...macros import local_macro_name
from ...macros import pattern_macro
from ...models import Expression
from ...models import Keyword
from ...models import List
from ...models import Object
from ...models import Symbol
from ...patterns import FORM
from ...patterns import SYM
from ...patterns import ModelParser
from ...patterns import brackets
from ...patterns import keepsym
from ...patterns import sym
from ...patterns import times
from ...reader import mangle
from ...results import Result
from ...results import asty
from ...scoping import ScopeFn
from ...scoping import is_inside_function_scope
from ...scoping import nearest_python_scope
from .helpers import TYPE_PARAMS
from .helpers import digest_type_params
from .helpers import dotted
from .helpers import maybe_annotated
from .helpers import pvalue


##


# A parameter name: any symbol but the `/` and `*` delimiters.
_PARAM_NAME: ModelParser = some(lambda x: isinstance(x, Symbol) and x not in (Symbol('/'), Symbol('*')))

# A parameter, with an optional default, as `[name default]`.
_PARAM = maybe_annotated(_PARAM_NAME | brackets(_PARAM_NAME, FORM))

_KWONLY_DELIM: ModelParser = some(lambda x: x == Symbol('*'))


def _varargs(unpack_type: str, wanted: ModelParser) -> ModelParser:
    """Match a variadic parameter, as `#* args` or `#** kwargs`."""

    return maybe_annotated(pvalue(unpack_type, wanted))


_LAMBDA_LIST = brackets(
    maybe(many(_PARAM) + sym('/')),
    many(_PARAM),
    maybe(_KWONLY_DELIM | _varargs('unpack-iterable', _PARAM_NAME)),
    many(_PARAM),
    maybe(_varargs('unpack-mapping', _PARAM_NAME)),
)


class _LambdaListCompiler:
    """Compiles a parsed lambda list to an `ast.arguments`, accumulating the compilation of annotations and defaults."""

    def __init__(self, compiler: HyASTCompiler) -> None:
        super().__init__()

        self._compiler = compiler

        self._ret = Result()

    def _compile_params(
            self,
            params: ta.Sequence[ta.Any],
            *,
            is_kwonly: bool = False,
    ) -> tuple[list[ast.arg], list[ast.expr | None]]:
        compiler = self._compiler

        args: list[ast.arg] = []
        defaults: list[ast.expr | None] = []

        for param, ann in params:
            # The parser ensures that a `List` here is a parameter with a default value.
            default = None
            if isinstance(param, List):
                name, default = param
            else:
                name = param

            ann_expr = None
            if ann is not None:
                self._ret += compiler.compile(ann)
                ann_expr = self._ret.force_expr

            if default is not None:
                self._ret += compiler.compile(default)
                defaults.append(self._ret.force_expr)
            elif is_kwonly:
                # Keyword-only parameters without defaults are required, which Python represents by a `None` default.
                defaults.append(None)

            args.append(asty.arg(name, arg=mangle(compiler._nonconst(name)), annotation=ann_expr))

        return args, defaults

    def compile(self, params: ta.Any) -> tuple[ast.arguments, Result]:
        compiler = self._compiler

        posonly_params, args_params, rest_param, kwonly_params, kwargs_param = params

        if not (posonly_params or posonly_params is None):
            compiler._syntax_error(params, 'at least one argument must precede /')

        posonly_params = posonly_params or []

        def is_positional(param: ta.Any) -> bool:
            return isinstance(param[0], Symbol)

        invalid_non_default = next(
            (
                param
                for param in itertools.dropwhile(is_positional, posonly_params + args_params)
                if is_positional(param)
            ),
            None,
        )
        if invalid_non_default:
            compiler._syntax_error(invalid_non_default[0], 'non-default argument follows default argument')

        posonly_ast, posonly_defaults = self._compile_params(posonly_params)
        args_ast, args_defaults = self._compile_params(args_params)
        kwonly_ast, kwonly_defaults = self._compile_params(kwonly_params, is_kwonly=True)

        rest_ast = kwargs_ast = None
        if rest_param == Symbol('*'):
            # A bare `*`, delimiting keyword-only parameters.
            if not kwonly_params:
                compiler._syntax_error(rest_param, 'named arguments must follow bare *')
        elif rest_param:
            [rest_ast], _ = self._compile_params([rest_param])

        if kwargs_param:
            [kwargs_ast], _ = self._compile_params([kwargs_param])

        arguments = ast.arguments(
            args=args_ast,
            defaults=ta.cast('list[ast.expr]', [*posonly_defaults, *args_defaults]),
            vararg=rest_ast,
            posonlyargs=posonly_ast,
            kwonlyargs=kwonly_ast,
            kw_defaults=kwonly_defaults,
            kwarg=kwargs_ast,
        )

        return arguments, self._ret


def _compile_function_node(
        compiler: HyASTCompiler,
        expr: Expression,
        *,
        node: ta.Callable[..., ast.FunctionDef | ast.AsyncFunctionDef],
        decorators: list[ast.expr | None],
        tp: ta.Any,
        name: str,
        args: ast.arguments,
        returns: Object | None,
        body: Result,
        scope: ScopeFn,
) -> Result:
    """
    Build a function definition, whose name and node are given as the temporary variables of the result, so that
    `setv` may rename it.
    """

    if body.expr:
        # Implicitly return the final expression, except for async generators.
        enode = asty.Expr if scope.is_async and scope.has_yield else asty.Return
        body += enode(body.expr, value=body.expr)

    fn_node = node(
        expr,
        name=name,
        args=args,
        body=body.stmts or [asty.Pass(expr)],
        decorator_list=decorators,
        returns=compiler.compile(returns).force_expr if returns is not None else None,
        **digest_type_params(compiler, tp),
    )

    ast_name = asty.Name(expr, id=name, ctx=ast.Load())
    return Result() + fn_node + Result(temp_variables=[ast_name, fn_node])


@pattern_macro('fn', [
    maybe(keepsym(':async')),
    maybe(TYPE_PARAMS),
    maybe_annotated(_LAMBDA_LIST),
    many(FORM),
])
def compile_function_lambda(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        is_async: Keyword | None,
        tp: ta.Any,
        annotated_params: ta.Any,
        body: list[Object],
) -> Result | ast.AST:
    params, returns = annotated_params
    posonly, args, rest, kwonly, kwargs = params
    has_annotations = returns is not None or any(
        isinstance(param, tuple) and param[1] is not None
        for param in (posonly or []) + args + kwonly + [rest, kwargs]
    )

    arguments, ret = _LambdaListCompiler(compiler).compile(params)
    with compiler.local_state(), compiler.scope.create(ScopeFn, arguments, is_async) as scope:
        body_ret = compiler._compile_branch(body)

    # Compile to a lambda if possible.
    if not (has_annotations or tp or body_ret.stmts or is_async):
        return ret + asty.Lambda(expr, args=arguments, body=body_ret.force_expr)

    # Otherwise create a standard function, and return its name as the final expression.
    ret += _compile_function_node(
        compiler,
        expr,
        node=asty.AsyncFunctionDef if is_async else asty.FunctionDef,
        decorators=[],
        tp=tp,
        name=compiler.get_anon_var(),
        args=arguments,
        returns=returns,
        body=body_ret,
        scope=scope,
    )
    return ret + Result(expr=check.isinstance(ret.temp_variables[0], ast.Name))


@pattern_macro('defn', [
    maybe(keepsym(':async')),
    maybe(brackets(many(FORM))),
    maybe(TYPE_PARAMS),
    maybe_annotated(SYM),
    _LAMBDA_LIST,
    many(FORM),
])
def compile_function_def(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        is_async: Keyword | None,
        decorators: ta.Any,
        tp: ta.Any,
        annotated_name: tuple[Symbol, Object | None],
        params: ta.Any,
        body: list[Object],
) -> Result:
    name, returns = annotated_name
    node = asty.AsyncFunctionDef if is_async else asty.FunctionDef

    decorator_exprs, ret, _ = compiler._compile_collect(decorators[0] if decorators else [])
    arguments, args_ret = _LambdaListCompiler(compiler).compile(params)
    ret += args_ret

    mangled_name = mangle(compiler._nonconst(name))
    compiler.scope.define(mangled_name)
    with compiler.local_state(), compiler.scope.create(ScopeFn, arguments, is_async) as scope:
        body_ret = compiler._compile_branch(body)

    return ret + _compile_function_node(
        compiler,
        expr,
        node=node,
        decorators=decorator_exprs,
        tp=tp,
        name=mangled_name,
        args=arguments,
        returns=returns,
        body=body_ret,
        scope=scope,
    )


@pattern_macro('defmacro', [
    SYM,
    brackets(
        maybe(many(_PARAM) + sym('/')),
        many(_PARAM),
        maybe(_varargs('unpack-iterable', _PARAM_NAME)),
    ),
    many(FORM),
])
def compile_macro_def(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        name: Symbol,
        params: ta.Any,
        body: list[Object],
) -> Result:
    compiler.warn_on_core_shadow(name)

    fn_def = Expression([Symbol('fn'), List(expr[2]), *body]).replace(expr)

    if compiler.is_in_local_state():
        # We're in a local scope, so define the new macro locally: produce code that will set the macro to a local
        # variable, and also evaluate the definition now, putting it in the local state's macros.
        state = compiler.local_state_stack[-1]
        ret = compiler.compile(Expression([Symbol('setv'), Symbol(local_macro_name(name)), fn_def]).replace(expr))
        state['macros'][mangle(name)] = compiler.eval(fn_def)
        return ret + ret.expr_as_stmt()

    # Otherwise, define the macro module-wide.
    ret = compiler.compile(Expression([
        Symbol('eval-and-compile'),
        Expression([Expression([dotted('hy.macros.macro'), str(name)]), fn_def]),
    ]).replace(expr))
    return ret + ret.expr_as_stmt()


##


@pattern_macro('return', [maybe(FORM)])
def compile_return(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        arg: Object | None,
) -> Result | ast.AST:
    if arg is None:
        return asty.Return(expr, value=None)

    ret = compiler.compile(arg)
    return ret + asty.Return(expr, value=ret.force_expr)


@pattern_macro('yield', [times(0, 2, FORM)])
def compile_yield_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        args: list[Object],
) -> Result:
    if is_inside_function_scope(compiler.scope):
        check.isinstance(nearest_python_scope(compiler.scope), ScopeFn).has_yield = True

    yield_from = False
    if len(args) == 2:
        from_kw, x = args
        if from_kw != Keyword('from'):
            compiler._syntax_error(from_kw, 'two-argument `yield` requires `:from`')
        yield_from = True
        args = [x]

    ret = Result()
    if args:
        ret += compiler.compile(args[0])
    return ret + (asty.YieldFrom if yield_from else asty.Yield)(expr, value=ret.force_expr)


@pattern_macro('await', [FORM])
def compile_await_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        arg: Object,
) -> Result:
    ret = compiler.compile(arg)
    return ret + asty.Await(expr, value=ret.force_expr)
