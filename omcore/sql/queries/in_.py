import operator
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ... import marshal as msh
from .exprs import CanExpr
from .exprs import Expr
from .exprs import ExprBuilder


##


class In(Expr, lang.Final):
    v: Expr
    vs: ta.Sequence[Expr] = dc.xfield(coerce=lambda v: tuple(check.not_isinstance(v, str)))

    _: dc.KW_ONLY

    not_: bool = dc.xfield(False, repr_fn=lang.truthy_repr) | msh.dc_field_options(omit_if=operator.not_)


class InBuilder(ExprBuilder):
    def in_(self, v: CanExpr, vs: ta.Iterable[CanExpr]) -> In:
        return In(
            self.expr(v),
            tuple(self.expr(e) for e in vs),
        )

    def not_in(self, v: CanExpr, vs: ta.Iterable[CanExpr]) -> In:
        return In(
            self.expr(v),
            tuple(self.expr(e) for e in vs),
            not_=True,
        )
