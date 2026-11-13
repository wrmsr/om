# ruff: noqa: SLF001
"""Subsetting: `get`, attribute access, `cut`, and unpacking."""
import ast

from ...compiler import HyASTCompiler
from ...funcparserlib.parser import many
from ...funcparserlib.parser import maybe
from ...funcparserlib.parser import oneplus
from ...macros import pattern_macro
from ...models import Expression
from ...models import List
from ...models import Object
from ...models import Symbol
from ...patterns import FORM
from ...patterns import SYM
from ...patterns import brackets
from ...patterns import pexpr
from ...reader import mangle
from ...results import Result
from ...results import asty
from .helpers import notsym


##


@pattern_macro('get', [FORM, oneplus(FORM)], shadow=True)
def compile_index_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        obj: Object,
        indices: list[Object],
) -> Result:
    index_exprs, ret, _ = compiler._compile_collect(indices)
    ret += compiler.compile(obj)

    for ix in index_exprs:
        ret += asty.Subscript(expr, value=ret.force_expr, slice=ix, ctx=ast.Load())

    return ret


@pattern_macro(
    '.',
    [
        FORM,
        many(
            SYM |
            brackets(FORM) |
            pexpr(notsym('unpack-iterable', 'unpack-mapping'), many(FORM)),
        ),
    ],
)
def compile_attribute_access(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        invocant: Object,
        keys: list[Symbol | List | Expression],
) -> Result:
    ret = compiler.compile(invocant)

    for attr in keys:
        if isinstance(attr, Symbol):
            ret += asty.Attribute(attr, value=ret.force_expr, attr=mangle(attr), ctx=ast.Load())

        elif isinstance(attr, Expression):
            # A method call.
            method, method_args = attr
            func = asty.Attribute(method, value=ret.force_expr, attr=mangle(method), ctx=ast.Load())
            args, func_ret, keywords = compiler._compile_collect(method_args, with_kwargs=True)
            ret += func_ret + func + asty.Call(expr, func=func, args=args, keywords=keywords)

        else:
            # A subscript, as by `[index]`.
            compiled_attr = compiler.compile(attr[0])
            ret = compiled_attr + ret + asty.Subscript(
                attr,
                value=ret.force_expr,
                slice=compiled_attr.force_expr,
                ctx=ast.Load(),
            )

    return ret


@pattern_macro('cut', [FORM, maybe(FORM), maybe(FORM), maybe(FORM)])
def compile_cut_expression(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        obj: Object,
        lower: Object | None,
        upper: Object | None,
        step: Object | None,
) -> Result:
    if upper is None:
        # A single index is an upper bound, consistent with `slice` and `itertools.islice`.
        upper = lower
        lower = Symbol('None')

    ret = Result()
    exprs: list[ast.expr] = []
    for form in (obj, lower, upper, step):
        ret += compiler.compile(form)
        exprs.append(ret.force_expr)

    obj_expr, lower_expr, upper_expr, step_expr = exprs
    return ret + asty.Subscript(
        expr,
        value=obj_expr,
        slice=asty.Slice(expr, lower=lower_expr, upper=upper_expr, step=step_expr),
        ctx=ast.Load(),
    )


@pattern_macro('unpack-iterable', [FORM])
def compile_unpack_iterable(
        compiler: HyASTCompiler,
        expr: Expression,
        root: str,
        arg: Object,
) -> Result:
    ret = compiler.compile(arg)
    return ret + asty.Starred(expr, value=ret.force_expr, ctx=ast.Load())
