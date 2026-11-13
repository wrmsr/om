# ruff: noqa: SLF001
"""`raise`, `try`, and `assert`."""
import ast
import typing as ta

from ...compiler import HyASTCompiler
from ...funcparserlib.parser import many
from ...funcparserlib.parser import maybe
from ...macros import pattern_macro
from ...models import Expression
from ...models import List
from ...models import Object
from ...patterns import FORM
from ...patterns import SYM
from ...patterns import brackets
from ...patterns import dolike
from ...patterns import keepsym
from ...patterns import notpexpr
from ...patterns import pexpr
from ...patterns import sym
from ...reader import mangle
from ...results import Result
from ...results import ResultStatement
from ...results import asty
from ...scoping import ScopeLet


##


@pattern_macro('raise', [maybe(FORM), maybe(sym(':from') + FORM)])
def compile_raise_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        exc: Object | None,
        cause: Object | None,
) -> Result:
    ret = Result()

    exc_expr = None
    if exc is not None:
        exc_ret = compiler.compile(exc)
        ret += exc_ret
        exc_expr = exc_ret.force_expr

    cause_expr = None
    if cause is not None:
        cause_ret = compiler.compile(cause)
        ret += cause_ret
        cause_expr = cause_ret.force_expr

    return ret + asty.Raise(expr, exc=exc_expr, cause=cause_expr)


##


def _compile_try_branch(
        compiler: HyASTCompiler,
        forms: ta.Iterable[Object],
        *,
        return_var: ast.Name | None,
        pos: Object,
) -> list[ResultStatement]:
    """Compile a branch of a `try`, assigning its value to `return_var`, if given."""

    ret = compiler._compile_branch(forms)
    if return_var is not None:
        ret += asty.Assign(pos, targets=[return_var], value=ret.force_expr)
    else:
        ret += ret.expr_as_stmt()
    return ret.stmts


def _compile_except_handler(
        compiler: HyASTCompiler,
        catcher: Expression,
        return_var: ast.Name,
) -> tuple[list[ResultStatement], ast.ExceptHandler]:
    """
    Compile an `except` (or `except*`) clause, returning the statements computing its exception types, which must
    precede the `try`, and its handler. The clause's exception spec is either `[]`, catching all exceptions, or the
    exception type (or a list of them) to catch, optionally preceded by the name to bind the exception to.
    """

    _, exceptions, ebody = catcher

    name = None
    if len(exceptions) == 0:
        exceptions = 'ALL'
    elif len(exceptions) == 1:
        [exceptions] = exceptions
    else:
        [name, exceptions] = exceptions
        name = mangle(compiler._nonconst(name))

    if exceptions == 'ALL':
        # Catch all exceptions - as does `[ALL]`, since symbols compare equal to strings.
        types = Result()
    elif isinstance(exceptions, List):
        elts, types, _ = compiler._compile_collect(exceptions)
        types += asty.Tuple(exceptions, elts=elts, ctx=ast.Load())
    else:
        types = compiler.compile(exceptions)

    # Create a 'fake' scope for the exception variable. See:
    # https://docs.python.org/3/reference/compound_stmts.html#the-try-statement
    with compiler.scope.create(ScopeLet) as scope:
        if name:
            name = scope.add(name, compiler.get_anon_var('exc', name))
        body_stmts = _compile_try_branch(compiler, ebody, return_var=return_var, pos=catcher)

    handler = asty.ExceptHandler(
        catcher,
        type=types.expr,
        name=name,
        body=body_stmts or [asty.Pass(catcher)],
    )

    return types.stmts, handler


@pattern_macro(
    'try',
    [
        many(notpexpr('except', 'except*', 'else', 'finally')),
        many(
            pexpr(
                keepsym('except') | keepsym('except*'),
                brackets() | brackets(FORM) | brackets(SYM, FORM),
                many(FORM),
            ),
        ),
        maybe(dolike('else')),
        maybe(dolike('finally')),
    ],
)
def compile_try_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        body: list[Object],
        catchers: list[Expression],
        orelse: list[Object] | None,
        finalbody: list[Object] | None,
) -> Result:
    if orelse is not None and not catchers:
        # Python forbids `else` when there are no `except` clauses. But we can get the same effect by appending the
        # `else` forms to the body.
        body += list(orelse)
        orelse = None

    body_ret = compiler._compile_branch(body)
    if not (catchers or finalbody):
        # Python forbids this, so just return the body, per `do`.
        return body_ret

    return_var = asty.Name(expr, id=mangle(compiler.get_anon_var()), ctx=ast.Store())

    types_stmts: list[ResultStatement] = []
    handlers: list[ast.ExceptHandler] = []
    except_syms_seen: set[str] = set()
    for catcher in catchers:
        except_sym = catcher[0]
        except_syms_seen.add(str(except_sym))
        if len(except_syms_seen) > 1:
            compiler._syntax_error(except_sym, 'cannot have both `except` and `except*` on the same `try`')

        catcher_types_stmts, handler = _compile_except_handler(compiler, catcher, return_var)
        types_stmts.extend(catcher_types_stmts)
        handlers.append(handler)

    orelse_stmts: list[ResultStatement] = []
    if orelse is not None:
        orelse_stmts = _compile_try_branch(compiler, orelse, return_var=return_var, pos=expr)

    finalbody_stmts: list[ResultStatement] = []
    if finalbody is not None:
        finalbody_stmts = _compile_try_branch(compiler, finalbody, return_var=None, pos=expr)

    returnable = Result(
        expr=asty.Name(expr, id=return_var.id, ctx=ast.Load()),
        temp_variables=[return_var],
    )

    if orelse_stmts:
        # The `else` branch provides the value.
        body_ret += body_ret.expr_as_stmt()
    else:
        body_ret += asty.Assign(expr, targets=[return_var], value=body_ret.force_expr)

    try_node = (asty.TryStar if 'except*' in except_syms_seen else asty.Try)(
        expr,
        body=body_ret.stmts or [asty.Pass(expr)],
        handlers=handlers,
        orelse=orelse_stmts,
        finalbody=finalbody_stmts,
    )

    return Result(stmts=types_stmts) + try_node + returnable


##


@pattern_macro('assert', [FORM, maybe(FORM)])
def compile_assert_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        test: Object,
        msg: ta.Any,
) -> ast.AST:
    test_ret = compiler.compile(test)
    if msg:
        msg = compiler.compile(msg)

    if not (test_ret.stmts or (msg and msg.stmts)):
        return asty.Assert(expr, test=test_ret.force_expr, msg=msg and msg.force_expr)

    return asty.If(
        expr,
        test=asty.Name(expr, id='__debug__', ctx=ast.Load()),
        orelse=[],
        body=[
            *test_ret.stmts,
            asty.If(
                test_ret,
                test=asty.UnaryOp(test_ret, op=ast.Not(), operand=test_ret.force_expr),
                orelse=[],
                body=[
                    *(msg.stmts if msg else []),
                    asty.Assert(
                        expr,
                        test=asty.Constant(test_ret, value=False),
                        msg=msg and msg.force_expr,
                    ),
                ],
            ),
        ],
    )
