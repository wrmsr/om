# ruff: noqa: SLF001
"""`match`."""
import ast
import typing as ta

from omcore import check

from ...compiler import HyASTCompiler
from ...compiler import mkexpr
from ...funcparserlib.parser import forward_decl
from ...funcparserlib.parser import many
from ...funcparserlib.parser import maybe
from ...funcparserlib.parser import oneplus
from ...macros import pattern_macro
from ...models import Bytes
from ...models import Complex
from ...models import Dict
from ...models import Expression
from ...models import Float
from ...models import Integer
from ...models import Keyword
from ...models import List
from ...models import Object
from ...models import String
from ...models import Symbol
from ...models import Tuple
from ...models import is_unpack
from ...patterns import FORM
from ...patterns import KEYWORD
from ...patterns import LITERAL
from ...patterns import SYM
from ...patterns import ModelParser
from ...patterns import braces
from ...patterns import brackets
from ...patterns import in_tuple
from ...patterns import keepsym
from ...patterns import parse_if
from ...patterns import pexpr
from ...patterns import sym
from ...patterns import unpack
from ...reader import mangle
from ...results import Result
from ...results import asty
from .helpers import dotted
from .helpers import notsym
from .helpers import pvalue


##


def _build_match_clause_parser() -> ModelParser:
    """Build the parser of a `match` clause's pattern, `:as` name, and `:if` guard (but not its body)."""

    pattern = forward_decl()
    pattern.define(
        (
            SYM |
            KEYWORD |
            LITERAL |
            brackets(many(pattern | unpack('iterable'))) |
            in_tuple(many(pattern | unpack('iterable'))) |
            pexpr(keepsym('.'), many(SYM)) |
            pexpr(keepsym('|'), many(pattern)) |
            braces(many(LITERAL + pattern), maybe(pvalue('unpack-mapping', SYM))) |
            pexpr(
                pexpr(keepsym('.'), oneplus(SYM)) | notsym('.', '|', 'unpack-mapping', 'unpack-iterable'),
                many(parse_if(lambda x: not isinstance(x, Keyword), pattern)),
                many(KEYWORD + pattern),
            )
        ) +
        maybe(sym(':as') + SYM),
    )

    return pattern + maybe(sym(':if') + FORM)


_MATCH_CLAUSE = _build_match_clause_parser()


def _compile_pattern(compiler: HyASTCompiler, pattern: ta.Any) -> ast.pattern:
    """Compile a parsed pattern - a pair of the pattern itself and its `:as` name, if any - to a Python pattern."""

    value, assignment = pattern
    if assignment is not None:
        return ta.cast(ast.pattern, compiler.scope.assign(asty.MatchAs(
            value,
            pattern=_compile_pattern(compiler, (value, None)),
            name=mangle(compiler._nonconst(assignment)),
        )))

    if str(value) in ('None', 'True', 'False'):
        return asty.MatchSingleton(
            value,
            value=check.isinstance(compiler.compile(value).force_expr, ast.Constant).value,
        )

    elif isinstance(value, (String, Integer, Float, Complex, Bytes)):
        return asty.MatchValue(value, value=compiler.compile(value).expr)

    elif value == Symbol('_'):
        return asty.MatchAs(value)

    elif isinstance(value, Symbol):
        return ta.cast(ast.pattern, compiler.scope.assign(asty.MatchAs(value, name=mangle(value))))

    elif isinstance(value, Expression) and value[0] == Symbol('|'):
        return asty.MatchOr(value, patterns=[_compile_pattern(compiler, v) for v in value[1]])

    elif isinstance(value, Expression) and value[0] == Symbol('.'):
        root, syms = value
        dotform = mkexpr(root, *syms).replace(value)
        return asty.MatchValue(value, value=compiler.compile(dotform).expr)

    elif isinstance(value, (Tuple, List)):
        return asty.MatchSequence(
            value,
            patterns=[
                _compile_pattern(compiler, (v, None) if is_unpack('iterable', v) else v)
                for v in value[0]
            ],
        )

    elif is_unpack('iterable', value):
        return ta.cast(ast.pattern, compiler.scope.assign(asty.MatchStar(value, name=mangle(value[1]))))

    elif isinstance(value, Dict):
        kvs, rest = value
        keys, values = zip(*kvs) if kvs else ([], [])
        # This calls `scope.assign` for the assignment to `rest`.
        return ta.cast(ast.pattern, compiler.scope.assign(asty.MatchMapping(
            value,
            keys=[compiler.compile(key).expr for key in keys],
            patterns=[_compile_pattern(compiler, v) for v in values],
            rest=mangle(rest) if rest else None,
        )))

    elif isinstance(value, Expression):
        head, args, kwargs = value
        keywords, values = zip(*kwargs) if kwargs else ([], [])
        return asty.MatchClass(
            value,
            cls=compiler.compile(
                # `head` could be a symbol or a dotted form.
                (head[:1] + head[1]).replace(head) if type(head) is Expression else head,
            ).expr,
            patterns=[_compile_pattern(compiler, v) for v in args],
            kwd_attrs=[kwd.name for kwd in keywords],
            kwd_patterns=[_compile_pattern(compiler, v) for v in values],
        )

    elif isinstance(value, Keyword):
        return asty.MatchClass(
            value,
            cls=compiler.compile(dotted('hy.models.Keyword')).expr,
            patterns=[asty.MatchValue(value, value=asty.Constant(value, value=value.name))],
            kwd_attrs=[],
            kwd_patterns=[],
        )

    else:
        raise compiler._syntax_error(value, 'unsupported')  # noqa: RET503


def _lift_guard(compiler: HyASTCompiler, guard: Result) -> tuple[Result, Result]:
    """
    Lift a guard which needs statements into a function, as a pattern's guard must be an expression. Returns the
    function definition and the guard calling it.
    """

    fname = compiler.get_anon_var()

    guard_def = Result() + asty.FunctionDef(
        guard,
        name=fname,
        args=ast.arguments(
            args=[],
            kwarg=None,
            posonlyargs=[],
            kwonlyargs=[],
            kw_defaults=[],
            defaults=[],
        ),
        body=[*guard.stmts, asty.Return(guard.expr, value=guard.expr)],
        decorator_list=[],
        type_params=[],
    )

    return guard_def, Result(expr=asty.parse(guard, f'{fname}()').body[0].value)


@pattern_macro('match', [FORM, many(_MATCH_CLAUSE + FORM)])
def compile_match_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        subject: Object,
        clauses: ta.Any,
) -> Result:
    subject_ret = compiler.compile(subject)
    return_var = asty.Name(expr, id=mangle(compiler.get_anon_var()), ctx=ast.Store())

    lifted_guard_defs: list[Result] = []
    match_cases: list[ast.match_case] = []
    for *pattern, guard, body in clauses:
        # The guard is a model, which may itself be falsey (as with `:if 0`).
        if guard is not None and body == Keyword('as'):
            compiler._syntax_error(body, ':as clause cannot come after :if guard')

        body_ret = compiler._compile_branch([body])
        body_ret += asty.Assign(pattern[0], targets=[return_var], value=body_ret.force_expr)

        pattern_ast = _compile_pattern(compiler, pattern)

        guard_ret: Result | None = None
        if guard is not None:
            guard_ret = compiler.compile(guard)
            if guard_ret.stmts:
                guard_def, guard_ret = _lift_guard(compiler, guard_ret)
                lifted_guard_defs.append(guard_def)

        match_cases.append(ast.match_case(
            pattern=pattern_ast,
            guard=guard_ret.force_expr if guard_ret is not None else None,
            body=body_ret.stmts,
        ))

    returnable = Result(
        expr=asty.Name(expr, id=return_var.id, ctx=ast.Load()),
        temp_variables=[return_var],
    )

    ret = Result() + subject_ret
    ret += asty.Assign(expr, targets=[return_var], value=asty.Constant(expr, value=None))
    if not match_cases:
        return ret + returnable

    for guard_def in lifted_guard_defs:
        ret += guard_def
    ret += asty.Match(expr, subject=subject_ret.force_expr, cases=match_cases)
    return ret + returnable
