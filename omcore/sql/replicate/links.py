import contextlib
import datetime
import typing as ta
import uuid

from ... import check
from ... import dataclasses as dc
from ... import lang
from ..api.core import AsyncConn
from ..tabledefs.tabledefs import TableDef
from .applying import ApplyReport
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


class LinkConns(lang.Final):
    """
    A link's connections for the span of a step: at most one to each of its nodes, each made only when first called
    for - a step which finds nothing to do at its source never troubles its target - and all closed together.
    """

    def __init__(self, link: Link, aes: contextlib.AsyncExitStack) -> None:
        super().__init__()

        self._link = link
        self._aes = aes

        self._source: AsyncConn | None = None
        self._target: AsyncConn | None = None

    async def source(self) -> AsyncConn:
        if (conn := self._source) is None:
            conn = self._source = await self._aes.enter_async_context(self._link.source.db.connect())
        return conn

    async def target(self) -> AsyncConn:
        if (conn := self._target) is None:
            conn = self._target = await self._aes.enter_async_context(self._link.target.db.connect())
        return conn

    async def cursors(self) -> AsyncConn:
        return await (self.target() if self._link.spec.cursor_side is CursorSide.TARGET else self.source())


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
    def schema(self) -> ReplicationSchema:
        return self._schema

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

    def connect(self) -> ta.AsyncContextManager[LinkConns]:
        @contextlib.asynccontextmanager
        async def inner():
            async with contextlib.AsyncExitStack() as aes:
                try:
                    yield LinkConns(self, aes)
                except BaseException:
                    # What did and did not get written is now anyone's guess.
                    self._cursors.forget()
                    raise

        return inner()

    def connected(self, conns: LinkConns | None = None) -> ta.AsyncContextManager[LinkConns]:
        """The connections given, left as they are for whoever opened them - or, given none, the link's own."""

        if conns is not None:
            return lang.ValueAsyncContextManager(conns)
        return self.connect()

    async def origin_predicate(self) -> OriginPredicate:
        f = self._spec.origins
        if f is OriginFilter.SOURCE_OWN:
            return OriginPredicate(filter=f, node_id=await self._source.node_id())
        elif f is OriginFilter.ALL_EXCEPT_TARGET:
            return OriginPredicate(filter=f, node_id=await self._target.node_id())
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
class TailReport(lang.Final):
    entries: int  # log entries examined
    keys: int  # distinct keys looked up, in tables the link carries
    applied: int
    deleted: int
    skipped: int
    seq: int  # the log position after this step
    drained: bool  # fewer entries than the batch size: the tail has caught up with the log


@dc.dataclass(frozen=True, kw_only=True)
class LinkSyncReport(lang.Final):
    link: str
    tables: ta.Sequence[TableSyncReport]
    tail: TailReport | None = None  # absent when the source keeps no log

    @property
    def completed(self) -> bool:
        return all(t.completed for t in self.tables)

    @property
    def scanned(self) -> int:
        return sum(t.scanned for t in self.tables)


async def sync_table_once(
        link: Link,
        td: TableDef,
        *,
        conns: LinkConns | None = None,
        prune_tombstones_before: datetime.datetime | None = None,
) -> TableSyncReport:
    """
    One batch of one table's sweep: scan the shadows on from the cursor, compare them to the target's, apply whichever
    of their rows the target turns out to want, and advance the cursor. Only those rows are ever read whole - and a
    sweep mostly finds there are none.

    Given a time to prune before, the tombstones older than it go from the stretch of keys the batch covered, at both
    ends of the link - once whatever of them the batch had to ship has been. A sweep gets around the whole of the key
    space, so this gets around to every tombstone, by the one index a shadow has.
    """

    spec = link.spec
    name = td.name.last
    source = link.source
    target = link.target
    origins = await link.origin_predicate()

    async with link.connected(conns) as lc:
        cur = await link.cursors.read(spec.name, name, conn=lc.cursors)

        shadows = await source.backend.scan_shadows(
            await lc.source(),
            source.shadow_name(td),
            after=cur.position,
            limit=spec.batch_size,
            origins=origins,
        )

        # Whatever is not exactly where it should be goes to be applied, which is where what is wrong with it - if
        # something is - gets said.
        rep = ApplyReport()
        if shadows:
            states = await target.backend.fetch_shadow_states(
                await lc.target(),
                target.shadow_name(td),
                list(shadows),
            )
            if (wanted := [k for k, st in shadows.items() if states.get(k) != st]):
                rows = await source.backend.scan_keys(
                    await lc.source(),
                    td,
                    source.table_name(td),
                    source.shadow_name(td),
                    keys=wanted,
                    origins=origins,
                )
                rep = await apply_rows(target, td, rows, conn=await lc.target())

        completed = len(shadows) < spec.batch_size
        last = None if completed else next(reversed(shadows))

        if prune_tombstones_before is not None:
            for node, conn in ((source, await lc.source()), (target, await lc.target())):
                await node.backend.prune_tombstones(
                    conn,
                    node.shadow_name(td),
                    after=cur.position,
                    upto=last,
                    before=prune_tombstones_before,
                )

        new = CursorState(
            position=last,
            sweeps=cur.sweeps + (1 if completed else 0),
        )
        await link.cursors.write(spec.name, name, new, conn=lc.cursors)

    return TableSyncReport(
        table=name,
        scanned=len(shadows),
        applied=rep.applied,
        deleted=rep.deleted,
        skipped=len(shadows) - rep.applied - rep.deleted,
        completed=completed,
        position=new.position,
        sweeps=new.sweeps,
    )


async def sync_link_tail(link: Link, *, conns: LinkConns | None = None) -> TailReport | None:
    """
    One batch of the source's change log: the keys it names are looked up and applied exactly as the sweep would, then
    the log position advances past them. Freshness only - a change the tail misses waits for the sweep - which is also
    what makes this safe to call from a writer right after it commits.
    """

    source = link.source
    if not source.log:
        return None

    spec = link.spec

    async with link.connected(conns) as lc:
        after = await link.cursors.read_log(spec.name, conn=lc.cursors)

        entries = await source.backend.read_log(
            await lc.source(),
            source.log_table,
            after=after,
            limit=spec.tail_batch_size,
        )

        by_table: dict[str, list[uuid.UUID]] = {td.name.last: [] for td in link.tables}
        seen: set[tuple[str, uuid.UUID]] = set()
        for e in entries:
            if e.table in by_table and (e.table, e.key) not in seen:
                seen.add((e.table, e.key))
                by_table[e.table].append(e.key)

        applied = deleted = skipped = 0
        origins = await link.origin_predicate()
        for td in link.tables:
            keys = by_table[td.name.last]
            if not keys:
                continue
            rows = await source.backend.scan_keys(
                await lc.source(),
                td,
                source.table_name(td),
                source.shadow_name(td),
                keys=keys,
                origins=origins,
            )
            rep = await apply_rows(link.target, td, rows, conn=await lc.target())
            applied += rep.applied
            deleted += rep.deleted
            skipped += rep.skipped

        seq = entries[-1].seq if entries else after
        if entries:
            await link.cursors.write_log(spec.name, seq, conn=lc.cursors)

    return TailReport(
        entries=len(entries),
        keys=len(seen),
        applied=applied,
        deleted=deleted,
        skipped=skipped,
        seq=seq,
        drained=len(entries) < spec.tail_batch_size,
    )


async def sync_link_once(
        link: Link,
        *,
        conns: LinkConns | None = None,
        prune_tombstones_before: datetime.datetime | None = None,
) -> LinkSyncReport:
    """
    One step of a link, all there is of one: a batch of the log tail for freshness, then one sweep batch of every table
    for truth - all of it over the one connection to each node. A worker paces the two apart.
    """

    async with link.connected(conns) as lc:
        tail = await sync_link_tail(link, conns=lc)
        return LinkSyncReport(
            link=link.name,
            tables=[
                await sync_table_once(link, td, conns=lc, prune_tombstones_before=prune_tombstones_before)
                for td in link.tables
            ],
            tail=tail,
        )


async def sync_link_sweep(
        link: Link,
        *,
        max_steps: int = 10_000,
        prune_tombstones_before: datetime.datetime | None = None,
) -> LinkSyncReport:
    """
    Steps a link until every table has completed a sweep within this call, reporting each table's counts summed over its
    steps. For convergence in tests and tools.
    """

    done: dict[str, TableSyncReport] = {}
    acc: dict[str, list[TableSyncReport]] = {td.name.last: [] for td in link.tables}
    async with link.connect() as lc:
        for _ in range(max_steps):
            for td in link.tables:
                name = td.name.last
                if name in done:
                    continue
                rep = await sync_table_once(link, td, conns=lc, prune_tombstones_before=prune_tombstones_before)
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
