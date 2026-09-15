import enum
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ..dtypes import Uuid
from ..tabledefs.elements import Column
from ..tabledefs.elements import PrimaryKey
from ..tabledefs.tabledefs import TableDef
from .errors import ReplicationSchemaError
from .names import PREFIX


##


class OriginFilter(enum.Enum):
    SOURCE_OWN = 'source_own'  # only rows the source node authored: an edge uploading to the hub
    ALL_EXCEPT_TARGET = 'all_except_target'  # everything but the target's own rows: the hub fanning out to an edge
    ALL = 'all'


class CursorSide(enum.Enum):
    SOURCE = 'source'
    TARGET = 'target'


@dc.dataclass(frozen=True, kw_only=True)
class LinkSpec(lang.Final):
    name: str

    source: str  # node names; the live nodes are joined in by the host
    target: str

    tables: ta.Sequence[str] | None = None  # bare table names, or every table in the schema

    origins: OriginFilter = OriginFilter.SOURCE_OWN
    batch_size: int = 100  # rows per sweep step
    tail_batch_size: int = 1000  # log entries per tail step
    cursor_side: CursorSide = CursorSide.TARGET

    def __post_init__(self) -> None:
        check.non_empty_str(self.name)
        check.arg(self.source != self.target, 'a link needs two distinct nodes')
        check.arg(self.batch_size > 0)
        check.arg(self.tail_batch_size > 0)


##


def table_key_column(td: TableDef) -> Column:
    """The single uuid column every replicated table is keyed by."""

    pk = td.elements.get(PrimaryKey)
    if pk is None or len(pk.columns) != 1:
        raise ReplicationSchemaError(f'table {td.name.dotted!r} must have a single-column primary key')
    [kc] = [c for c in td.elements[Column] if c.name == pk.columns[0]]
    if not isinstance(kc.type, Uuid):
        raise ReplicationSchemaError(f'table {td.name.dotted!r} must be keyed by a uuid, not {kc.type!r}')
    return kc


@dc.dataclass(frozen=True)
class ReplicationSchema(lang.Final):
    """
    The tables under replication, identical on every node. Names are bare: each node qualifies them for its own layout
    (a schema on the hub, say). The definitions are the source of truth for every column's dtype, which is what lets a
    row cross dialects.
    """

    tables: ta.Sequence[TableDef] = dc.xfield(coerce=tuple)

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for td in self.tables:
            if len(td.name) != 1:
                raise ReplicationSchemaError(f'table names in a replication schema are bare: {td.name.dotted!r}')
            if td.name.last in seen:
                raise ReplicationSchemaError(f'duplicate table {td.name.last!r}')
            if td.name.last.startswith(PREFIX):
                raise ReplicationSchemaError(f'table names under {PREFIX!r} are reserved: {td.name.last!r}')
            seen.add(td.name.last)
            table_key_column(td)

    def table(self, name: str) -> TableDef:
        for td in self.tables:
            if td.name.last == name:
                return td
        raise KeyError(name)

    @property
    def table_names(self) -> ta.Sequence[str]:
        return [td.name.last for td in self.tables]
