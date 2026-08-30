import collections.abc
import typing as ta

from ...... import check
from .....api.adapters import Adapter
from .....api.columns import Column
from .....api.columns import Columns
from .....api.dialects import Dialect
from .....drivers.omysql.protocol.messages import ColumnDefinition
from .....params import ParamStyle
from ...dialect import MysqlDialect


##


def build_omysql_columns(
        fields: ta.Sequence[ColumnDefinition] | None,
) -> Columns:
    if fields is None:
        return Columns.empty()

    return Columns(*[
        Column(
            check.non_empty_str(field.name),
        )
        for field in fields
    ])


def omysql_row_args(
        row: ta.Sequence[ta.Any] | ta.Mapping[str, ta.Any],
) -> tuple[ta.Any, ...] | dict[str, ta.Any]:
    """Coerces api params into the tuple-or-dict shape the driver's mogrify interpolates."""

    if isinstance(row, collections.abc.Mapping):
        return dict(row)
    return tuple(row)


##


class OmysqlAdapter(Adapter):
    @property
    def param_style(self) -> ParamStyle | None:
        return ParamStyle.PYFORMAT

    @property
    def dialect(self) -> Dialect:
        return MysqlDialect()

    def scan_type(self, c: Column) -> type:
        raise NotImplementedError
