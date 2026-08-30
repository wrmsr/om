import collections.abc
import typing as ta

from ...... import check
from .....api.adapters import Adapter
from .....api.columns import Column
from .....api.columns import Columns
from .....api.dialects import Dialect
from .....params import ParamStyle
from ...dialect import PostgresDialect


##


def build_og8000_columns(
        cols: ta.Sequence[ta.Mapping[str, ta.Any]] | None,
) -> Columns:
    if cols is None:
        return Columns.empty()

    return Columns(*[
        Column(
            check.non_empty_str(col['name']),
        )
        for col in cols
    ])


def positional_og8000_params(
        params: ta.Sequence[ta.Any] | ta.Mapping[str, ta.Any],
) -> tuple[ta.Any, ...]:
    if isinstance(params, collections.abc.Mapping):
        raise TypeError('og8000 accepts only positional query parameters')
    return tuple(params)


##


class Og8000Adapter(Adapter):
    @property
    def param_style(self) -> ParamStyle | None:
        return ParamStyle.DOLLAR_NUMERIC

    @property
    def dialect(self) -> Dialect:
        return PostgresDialect()

    def scan_type(self, c: Column) -> type:
        raise NotImplementedError
