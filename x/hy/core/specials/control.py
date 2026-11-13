# ruff: noqa: SLF001
"""Control flow: `if`, `while`, `break`, `continue`, and `with`."""
import ast
import typing as ta

from ...compiler import HyASTCompiler
from ...funcparserlib.parser import many
from ...funcparserlib.parser import maybe
from ...funcparserlib.parser import oneplus
from ...macros import pattern_macro
from ...models import Expression
from ...models import Keyword
from ...models import Object
from ...models import Symbol
from ...patterns import FORM
from ...patterns import brackets
from ...patterns import dolike
from ...patterns import keepsym
from ...patterns import notpexpr
from ...reader import mangle
from ...results import Result
from ...results import asty


# A context manager of a `with`: whether it's `:async`, the variable it's bound to (`_` for none), and the context
# manager itself, either as a form or already compiled.
_WithItem: ta.TypeAlias = tuple[Keyword | None, Object, Object | Result]


##


@pattern_macro('if', [FORM, FORM, FORM])
def compile_if(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        cond: Object,
        body: Object,
        orel_expr: Object,
) -> Result | ast.AST:
    cond_ret = compiler.compile(cond)
    body_ret = compiler.compile(body)
    orel_ret = compiler.compile(orel_expr)

    # The statements of the condition are hoisted before the `if`.
    ret = cond_ret

    if body_ret.stmts or orel_ret.stmts:
        # The branches have statements, so this must be an `if` statement storing its result in a temporary variable.
        var = compiler.get_anon_var()
        name = asty.Name(expr, id=mangle(var), ctx=ast.Store())

        body_ret += asty.Assign(expr, targets=[name], value=body_ret.force_expr)
        orel_ret += asty.Assign(expr, targets=[name], value=orel_ret.force_expr)

        ret += asty.If(expr, test=ret.force_expr, body=body_ret.stmts, orelse=orel_ret.stmts)

        expr_name = asty.Name(expr, id=mangle(var), ctx=ast.Load())
        ret += Result(expr=expr_name, temp_variables=[expr_name, name])

    else:
        ret += asty.IfExp(expr, test=ret.force_expr, body=body_ret.force_expr, orelse=orel_ret.force_expr)

    return ret


@pattern_macro(['while'], [FORM, many(notpexpr('else')), maybe(dolike('else'))])
def compile_while_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        cond: Object,
        body: list[Object],
        else_expr: list[Object] | None,
) -> Result:
    cond_compiled = compiler.compile(cond)

    body_ret = compiler._compile_branch(body)
    body_ret += body_ret.expr_as_stmt()
    body_stmts = body_ret.stmts or [asty.Pass(expr)]

    if cond_compiled.stmts:
        # The statements for the condition must be executed on every iteration, so the loop is rewritten to use a single
        # anonymous variable as the condition:
        #
        #   anon_var = True
        #   while anon_var:
        #     condition stmts...
        #     anon_var = condition expr
        #     if anon_var:
        #       while loop body
        #
        cond_var = asty.Name(cond, id=compiler.get_anon_var(), ctx=ast.Load())

        def make_not(operand: ast.expr) -> ast.UnaryOp:
            return asty.UnaryOp(cond, op=ast.Not(), operand=operand)

        body_stmts = [
            *cond_compiled.stmts,
            asty.Assign(
                cond,
                targets=[compiler._storeize(cond, cond_var)],
                # Cast the condition to a bool in case it's mutable and changes its truth value, but use (not (not ...))
                # instead of `bool` in case `bool` has been redefined.
                value=make_not(make_not(cond_compiled.force_expr)),
            ),
            asty.If(cond, test=cond_var, body=body_stmts, orelse=[]),
        ]

        cond_compiled = (
            Result() +
            asty.Assign(
                cond,
                targets=[compiler._storeize(cond, cond_var)],
                value=asty.Constant(cond, value=True),
            ) +
            cond_var
        )

    orel = Result()
    if else_expr is not None:
        orel = compiler._compile_branch(else_expr)
        orel += orel.expr_as_stmt()

    return cond_compiled + asty.While(expr, test=cond_compiled.force_expr, body=body_stmts, orelse=orel.stmts)


@pattern_macro(['break', 'continue'], [])
def compile_break_or_continue_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
) -> ast.AST:
    return (asty.Break if root == 'break' else asty.Continue)(expr)


##


def _compile_with(
        compiler: HyASTCompiler,
        expr: Expression,
        items: ta.Sequence[_WithItem],
        body: list[Object],
) -> Result:
    # The result of the body is stored in a temporary variable, initialized to `None` in case the `with` exits early
    # with an exception.
    temp_var = compiler.get_anon_var()
    name = asty.Name(expr, id=mangle(temp_var), ctx=ast.Store())
    initial_assign = asty.Assign(expr, targets=[name], value=asty.Constant(expr, value=None))

    ret = Result(stmts=[initial_assign])
    with_items: list[ast.withitem] = []
    was_async: bool | None = None
    cbody: Result | None = None
    for i, (async_kw, variable, ctx) in enumerate(items):
        is_async = bool(async_kw)
        if was_async is None:
            was_async = is_async
        elif is_async != was_async:
            # This `with` mixes synchronous and asynchronous context managers. Python doesn't support this directly, so
            # start a new `with` inside the body.
            cbody = _compile_with(compiler, expr, items[i:], body)
            break

        if not isinstance(ctx, Result):
            # Context managers are compiled here, except the first of a nested `with` started below, which already is.
            ctx = compiler.compile(ctx)
            if i == 0:
                ret += ctx
            elif ctx.stmts:
                # This context manager needs some statements, but this `with` already has at least one prior context
                # manager. So, put the statements in the body and then start a new `with`.
                cbody = ctx + _compile_with(compiler, expr, [(async_kw, variable, ctx), *items[i + 1:]], body)
                break

        optional_vars = None if variable == Symbol('_') else compiler._storeize(variable, compiler.compile(variable))
        with_items.append(ast.withitem(context_expr=ctx.force_expr, optional_vars=optional_vars))

    if cbody is None:
        cbody = compiler._compile_branch(body)
        cbody += asty.Assign(expr, targets=[name], value=cbody.force_expr)

    ret += (asty.AsyncWith if was_async else asty.With)(expr, body=cbody.stmts, items=with_items)

    # The result isn't given any temporary variables, as `Result.rename` mustn't touch `name` - otherwise,
    # `initial_assign` would clobber any preexisting value of the renamed-to variable.
    expr_name = asty.Name(expr, id=mangle(temp_var), ctx=ast.Load())
    return ret + Result(expr=expr_name)


@pattern_macro('with', [
    (
        brackets(oneplus(maybe(keepsym(':async')) + FORM + FORM)) |
        brackets((maybe(keepsym(':async')) + FORM) >> (lambda x: [(x[0], Symbol('_'), x[1])]))
    ),
    many(FORM),
])
def compile_with_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        args: ta.Any,
        body: list[Object],
) -> Result:
    [items] = args
    return _compile_with(compiler, expr, items, body)
