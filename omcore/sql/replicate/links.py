import typing as ta
import uuid

from ... import check
from ... import dataclasses as dc
from ... import lang
from ..tabledefs.tabledefs import TableDef
from .applying import apply_rows
from .config import CursorSide
from .config import LinkSpec
from .config import OriginFilter
from .config import ReplicationSchema
from .cursors import CursorState
from .cursors import CursorStore
from .nodes import Node
from .rows import OriginPredicate


##


class Link(lang.Final):
    """A link spec joined to its live nodes."""

    def __init__(
            self,
            spec: LinkSpec,
            schema: ReplicationSchema,
            source: Node,
            target: Node,
    ) -> None:
        super().__init__()

        check.equal(spec.source, source.name)
        check.equal(spec.target, target.name)

        self._spec = spec
        self._schema = schema
        self._source = source
        self._target = target

        self._tables = [schema.table(n) for n in spec.tables] if spec.tables is not None else list(schema.tables)
        self._cursors = CursorStore(target if spec.cursor_side is CursorSide.TARGET else source)

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._spec.name!r}: {self._source!r} -> {self._target!r})'

    @property
    def spec(self) -> LinkSpec:
        return self._spec

    @property
    def name(self) -> str:
        return self._spec.name

    @property
    def source(self) -> Node:
        return self._source

    @property
    def target(self) -> Node:
        return self._target

    @property
    def tables(self) -> ta.Sequence[TableDef]:
        return self._tables

    @property
    def cursors(self) -> CursorStore:
        return self._cursors

    def origin_predicate(self) -> OriginPredicate:
        f = self._spec.origins
        if f is OriginFilter.SOURCE_OWN:
            return OriginPredicate(filter=f, node_id=self._source.node_id)
        elif f is OriginFilter.ALL_EXCEPT_TARGET:
            return OriginPredicate(filter=f, node_id=self._target.node_id)
        elif f is OriginFilter.ALL:
            return OriginPredicate(filter=f)
        else:
            raise ValueError(f)


##


@dc.dataclass(frozen=True, kw_only=True)
class TableSyncReport(lang.Final):
    table: str
    scanned: int
    applied: int
    deleted: int
    skipped: int
    completed: bool  # this step finished a sweep of the table
    position: uuid.UUID | None
    sweeps: int


@dc.dataclass(frozen=True, kw_only=True)
class LinkSyncReport(lang.Final):
    link: str
    tables: ta.Sequence[TableSyncReport]

    @property
    def completed(self) -> bool:
        return all(t.completed for t in self.tables)

    @property
    def scanned(self) -> int:
        return sum(t.scanned for t in self.tables)


def sync_table_once(link: Link, td: TableDef) -> TableSyncReport:
    """One batch of one table's sweep: scan from the cursor, apply by comparison, advance the cursor."""

    spec = link.spec
    name = td.name.last
    cur = link.cursors.read(spec.name, name)

    with link.source.db.connect() as conn:
        rows = link.source.backend.scan(
            conn,
            td,
            link.source.table_name(td),
            link.source.shadow_name(td),
            after=cur.position,
            limit=spec.batch_size,
            origins=link.origin_predicate(),
        )

    rep = apply_rows(link.target, td, rows)

    completed = len(rows) < spec.batch_size
    new = CursorState(
        position=None if completed else rows[-1].key,
        sweeps=cur.sweeps + (1 if completed else 0),
    )
    link.cursors.write(spec.name, name, new)

    return TableSyncReport(
        table=name,
        scanned=len(rows),
        applied=rep.applied,
        deleted=rep.deleted,
        skipped=rep.skipped,
        completed=completed,
        position=new.position,
        sweeps=new.sweeps,
    )


def sync_link_once(link: Link) -> LinkSyncReport:
    """One step of a link: one batch of every table."""

    return LinkSyncReport(link=link.name, tables=[sync_table_once(link, td) for td in link.tables])


def sync_link_sweep(link: Link, *, max_steps: int = 10_000) -> LinkSyncReport:
    """
    Steps a link until every table has completed a sweep within this call, reporting each table's counts summed over its
    steps. For convergence in tests and tools.
    """

    done: dict[str, TableSyncReport] = {}
    acc: dict[str, list[TableSyncReport]] = {td.name.last: [] for td in link.tables}
    for _ in range(max_steps):
        for td in link.tables:
            name = td.name.last
            if name in done:
                continue
            rep = sync_table_once(link, td)
            acc[name].append(rep)
            if rep.completed:
                steps = acc[name]
                done[name] = dc.replace(
                    rep,
                    scanned=sum(r.scanned for r in steps),
                    applied=sum(r.applied for r in steps),
                    deleted=sum(r.deleted for r in steps),
                    skipped=sum(r.skipped for r in steps),
                )
        if len(done) == len(link.tables):
            return LinkSyncReport(link=link.name, tables=[done[td.name.last] for td in link.tables])
    raise RuntimeError(f'{link!r} did not complete a sweep within {max_steps} steps')
