# ruff: noqa: SLF001
"""`defclass`."""
import typing as ta

from ...compiler import HyASTCompiler
from ...funcparserlib.parser import many
from ...funcparserlib.parser import maybe
from ...macros import pattern_macro
from ...models import Expression
from ...models import Symbol
from ...patterns import FORM
from ...patterns import STR
from ...patterns import SYM
from ...patterns import brackets
from ...reader import mangle
from ...results import Result
from ...results import asty
from ...scoping import ScopeFn
from .helpers import TYPE_PARAMS
from .helpers import digest_type_params


##


@pattern_macro(
    'defclass',
    [
        maybe(brackets(many(FORM))),
        maybe(TYPE_PARAMS),
        SYM,
        maybe(brackets(many(FORM)) + maybe(STR) + many(FORM)),
    ],
)
def compile_class_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        decorators: ta.Any,
        tp: ta.Any,
        name: Symbol,
        rest: ta.Any,
) -> Result:
    base_list, docstring, body = rest or ([[]], None, [])

    decorator_exprs, ret, _ = compiler._compile_collect(decorators[0] if decorators else [])
    bases_exprs, bases_ret, keywords = compiler._compile_collect(base_list[0], with_kwargs=True)
    ret += bases_ret

    body_ret = Result()
    if docstring is not None:
        body_ret += compiler.compile(docstring).expr_as_stmt()

    mangled_name = mangle(compiler._nonconst(name))
    compiler.scope.define(mangled_name)

    with compiler.local_state(), compiler.scope.create(ScopeFn):
        e = compiler._compile_branch(body)
        body_ret += e + e.expr_as_stmt()

    return ret + asty.ClassDef(
        expr,
        decorator_list=decorator_exprs,
        name=mangled_name,
        keywords=keywords,
        bases=bases_exprs,
        body=body_ret.stmts or [asty.Pass(expr)],
        **digest_type_params(compiler, tp),
    )
