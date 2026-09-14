# ruff: noqa: UP007
import enum
import typing as ta

from ... import dataclasses as dc
from ... import lang
from ... import marshal as msh
from .base import Node
from .exprs import CanExpr
from .exprs import Expr
from .exprs import ExprBuilder


##


class OrderByDirection(enum.Enum):
    ASC = enum.auto()
    DESC = enum.auto()

    @property
    def literal(self) -> OrderByDirectionLiteral:
        return ORDER_BY_LITERALS_BY_DIRECTION[self]

    @classmethod
    def of_literal(cls, l: OrderByDirectionLiteral) -> OrderByDirection:
        return ORDER_BY_DIRECTIONS_BY_LITERAL[l]


OrderByDirectionLiteral: ta.TypeAlias = ta.Literal[
    'asc',
    'desc',
]


ORDER_BY_DIRECTIONS_BY_LITERAL: ta.Mapping[OrderByDirectionLiteral, OrderByDirection] = {
    'asc': OrderByDirection.ASC,
    'desc': OrderByDirection.DESC,
}


ORDER_BY_LITERALS_BY_DIRECTION: ta.Mapping[OrderByDirection, OrderByDirectionLiteral] = {
    OrderByDirection.ASC: 'asc',
    OrderByDirection.DESC: 'desc',
}


#


class OrderByNulls(enum.Enum):
    FIRST = enum.auto()
    LAST = enum.auto()

    @property
    def literal(self) -> OrderByNullsLiteral:
        return ORDER_BY_LITERALS_BY_NULLS[self]

    @classmethod
    def of_literal(cls, l: OrderByNullsLiteral) -> OrderByNulls:
        return ORDER_BY_NULLS_BY_LITERAL[l]


OrderByNullsLiteral: ta.TypeAlias = ta.Literal[
    'nulls_first',
    'nulls_last',
]


ORDER_BY_NULLS_BY_LITERAL: ta.Mapping[OrderByNullsLiteral, OrderByNulls] = {
    'nulls_first': OrderByNulls.FIRST,
    'nulls_last': OrderByNulls.LAST,
}


ORDER_BY_LITERALS_BY_NULLS: ta.Mapping[OrderByNulls, OrderByNullsLiteral] = {
    OrderByNulls.FIRST: 'nulls_first',
    OrderByNulls.LAST: 'nulls_last',
}


#


class OrderByItem(Node, lang.Final):
    v: Expr

    _: dc.KW_ONLY

    direction: OrderByDirection | None = dc.xfield(None, repr_fn=lang.opt_repr) | msh.dc_field_options(omit_if=lang.is_none)  # noqa
    nulls: OrderByNulls | None = dc.xfield(None, repr_fn=lang.opt_repr) | msh.dc_field_options(omit_if=lang.is_none)  # noqa


##


CanOrderByDirection: ta.TypeAlias = OrderByDirection | OrderByDirectionLiteral

CanOrderByNulls: ta.TypeAlias = OrderByNulls | OrderByNullsLiteral

CanOrderByItem: ta.TypeAlias = ta.Union[
    OrderByItem,
    tuple[CanExpr, CanOrderByDirection],
    tuple[CanExpr, CanOrderByDirection, CanOrderByNulls],
    CanExpr,
]

# Note: `list` specifically to prevent clashing with tuple form of `CanOrderByItem`
CanOrderBy: ta.TypeAlias = list[CanOrderByItem] | CanOrderByItem


class OrderByBuilder(ExprBuilder):
    def order_by_direction(self, o: CanOrderByDirection) -> OrderByDirection:
        if isinstance(o, OrderByDirection):
            return o
        elif isinstance(o, str):
            try:
                return ORDER_BY_DIRECTIONS_BY_LITERAL[o]
            except KeyError:
                raise ValueError(o) from None
        else:
            raise TypeError(o)

    def order_by_nulls(self, o: CanOrderByNulls) -> OrderByNulls:
        if isinstance(o, OrderByNulls):
            return o
        elif isinstance(o, str):
            try:
                return ORDER_BY_NULLS_BY_LITERAL[o]
            except KeyError:
                raise ValueError(o) from None
        else:
            raise TypeError(o)

    def order_by_item(self, o: CanOrderByItem) -> OrderByItem:
        if isinstance(o, OrderByItem):
            return o
        elif isinstance(o, tuple):
            d: CanOrderByDirection
            n: CanOrderByNulls | None = None
            if len(o) == 2:
                e, d = o  # type: ignore[assignment]
            else:
                e, d, n = o
            return OrderByItem(
                self.expr(e),
                direction=self.order_by_direction(d) if d is not None else None,
                nulls=self.order_by_nulls(n) if n is not None else None,
            )
        else:
            return OrderByItem(
                self.expr(o),
            )

    def order_by(self, o: CanOrderBy) -> ta.Sequence[OrderByItem]:
        if isinstance(o, str):
            raise TypeError(o)
        elif isinstance(o, list):
            return tuple(self.order_by_item(e) for e in o)
        else:
            return (self.order_by_item(o),)
