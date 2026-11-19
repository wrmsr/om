"""Helpers shared by the special forms: common sub-patterns, and models naming parts of the `hy` namespace."""
import ast
import typing as ta

from ...compiler import HyASTCompiler
from ...funcparserlib.parser import many
from ...funcparserlib.parser import some
from ...models import Expression
from ...models import Symbol
from ...models import is_unpack
from ...patterns import FORM
from ...patterns import SYM
from ...patterns import ModelParser
from ...patterns import brackets
from ...patterns import pexpr
from ...patterns import sym
from ...patterns import unpack
from ...reader import mangle
from ...results import asty


##


def pvalue(root: str, wanted: ModelParser) -> ModelParser:
    """Match an expression `(root ...)` whose remaining forms match `wanted`, producing the result of `wanted`."""

    return pexpr(sym(root) + wanted) >> (lambda x: x[0])


def notsym(*disallowed: str) -> ModelParser:
    """Match any symbol other than those named by `disallowed`."""

    return some(lambda x: isinstance(x, Symbol) and str(x) not in disallowed)


def maybe_annotated(target: ModelParser) -> ModelParser:
    """
    Match either `target`, or an `annotate` form of `target` and an annotation, producing a pair of the result of
    `target` and the annotation (or `None`).
    """

    return (
        pexpr(sym('annotate'), target, FORM).named('`annotate` form') |
        (target >> (lambda x: (x, None)))
    )


def dotted(name: str) -> Expression:
    """Build the model of the dotted name `name`, as by reading `a.b.c` as `(. a b c)`."""

    return Expression(map(Symbol, ['.', *name.split('.')]))


##


TYPE_PARAMS: ModelParser = sym(':tp') + brackets(many(maybe_annotated(SYM) | unpack('either', Symbol)))


def digest_type_params(compiler: HyASTCompiler, tp: ta.Any) -> dict[str, ta.Any]:
    """Return the `type_params` keyword argument, if any, for a `FunctionDef`, `ClassDef`, or `TypeAlias` node."""

    if not tp:
        return {}

    type_params: list[ast.type_param] = []
    for x in tp[0]:
        if is_unpack('iterable', x):
            type_params.append(asty.TypeVarTuple(x[1], name=mangle(x[1])))

        elif is_unpack('mapping', x):
            type_params.append(asty.ParamSpec(x[1], name=mangle(x[1])))

        else:
            name, bound = x
            type_params.append(asty.TypeVar(
                name,
                name=mangle(name),
                bound=bound and compiler.compile(bound).force_expr,
            ))

    return dict(type_params=type_params)
