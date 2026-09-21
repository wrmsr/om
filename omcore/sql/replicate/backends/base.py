# ruff: noqa: S608
"""
The dialect-specific half of replication. Nearly every statement is standard sql shared here; a dialect supplies only
its upsert syntax, its boolean literals for trigger bodies, its capture-trigger renderer, and its facets (ddl renderer,
inspector, dtype codec).
"""
import abc
import datetime
import itertools
import typing as ta
import uuid

from .... import check
from .... import lang
from ...api import querierfuncs as qf
from ...api.queriers import AsyncQuerier
from ...dtypes import BOOLEAN
from ...dtypes import DATETIME
from ...dtypes import UUID
from ...dtypes import Integer
from ...dtypes.codecs import DtypeCodec
from ...inspect.inspectors import Inspector
from ...params import ParamsPreparer
from ...params import make_params_preparer
from ...params import substitute_params
from ...qualifiedname import QualifiedName
from ...queries import Q
from ...tabledefs.elements import Column
from ...tabledefs.rendering import Renderer
from ...tabledefs.tabledefs import TableDef
from ..config import OriginFilter
from ..config import table_key_column
from ..rows import LogEntry
from ..rows import OriginPredicate
from ..rows import ShadowState
from ..rows import SourceRow
from ..shadows import CURSOR_LINK
from ..shadows import CURSOR_POSITION
from ..shadows import CURSOR_SWEEPS
from ..shadows import CURSOR_TABLE
from ..shadows import CURSOR_UPDATED_AT
from ..shadows import LOG_CHANGED_AT
from ..shadows import LOG_KEY
from ..shadows import LOG_SEQ
from ..shadows import LOG_TABLE
from ..shadows import LOG_VERSION
from ..shadows import NODE_CREATED_AT
from ..shadows import NODE_ID
from ..shadows import SHADOW_CHANGED_AT
from ..shadows import SHADOW_DELETED
from ..shadows import SHADOW_KEY
from ..shadows import SHADOW_ORIGIN
from ..shadows import SHADOW_VERSION


##


@lang.cached_function
def _version_dtype() -> Integer:
    return Integer(bits=64)


@ta.final
class CursorRow(ta.NamedTuple):
    position: str | None  # opaque to the backend: a key for a sweep, a sequence number for a log tail
    sweeps: int


def sql_string_literal(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


# The most parameters put in one statement by default: sqlite's historical limit, which is the lowest going and so holds
# everywhere.
DEFAULT_MAX_STATEMENT_PARAMS: int = 999


class ReplicateBackend(lang.Abstract):
    def __init__(
            self,
            *,
            max_statement_params: int = DEFAULT_MAX_STATEMENT_PARAMS,
    ) -> None:
        super().__init__()

        check.arg(max_statement_params > 0)
        self._max_statement_params = max_statement_params

    @property
    @abc.abstractmethod
    def tabledef_renderer(self) -> Renderer:
        """Must have this dialect's capture-trigger renderer registered."""

        raise NotImplementedError

    @property
    @abc.abstractmethod
    def inspector(self) -> Inspector:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def dtype_codec(self) -> DtypeCodec:
        raise NotImplementedError

    ##
    # dialect hooks

    @abc.abstractmethod
    def upsert_sql(
            self,
            table: str,
            columns: ta.Sequence[str],
            keys: ta.Sequence[str],
            rows: ta.Sequence[ta.Sequence[str]],
    ) -> str:
        """
        An insert of rows of placeholders for the (already quoted) columns, each of which becomes an update of the
        non-key columns on a key clash. No two of the rows may share a key.
        """

        raise NotImplementedError

    def now_sql(self) -> str:
        return 'current_timestamp'

    ##
    # rendering helpers

    def quote(self, s: str) -> str:
        return self.tabledef_renderer.quote_ident(s)

    def qname(self, n: QualifiedName) -> str:
        return self.tabledef_renderer.qname(n)

    def _preparer(self, q: AsyncQuerier) -> ParamsPreparer:
        return make_params_preparer(check.not_none(q.adapter.param_style))

    def _bind(self, pp: ParamsPreparer, values: ta.Mapping[str, ta.Any]) -> ta.Any:
        return substitute_params(ta.cast('ta.Any', pp.prepare()), ta.cast('ta.Any', values), strict=True)

    ##
    # node

    async def read_node_id(self, q: AsyncQuerier, node_table: QualifiedName) -> uuid.UUID | None:
        rows = await qf.query_all(q, Q.select([Q.i(NODE_ID)], Q.n(tuple(node_table))))
        if not rows:
            return None
        return self.dtype_codec.decode(UUID, check.single(rows).values[0])

    async def insert_node_id(self, q: AsyncQuerier, node_table: QualifiedName, node_id: uuid.UUID) -> None:
        await qf.exec(
            q,
            Q.insert(
                [
                    Q.i(NODE_ID),
                    Q.i(NODE_CREATED_AT),
                ],
                Q.n(tuple(node_table)),
                [
                    Q.p.id,
                    Q.p.created_at,
                ],
            ),
            {
                Q.p.id: self.dtype_codec.encode(UUID, node_id),
                Q.p.created_at: self.dtype_codec.encode(DATETIME, datetime.datetime.now(datetime.UTC)),
            },
        )

    ##
    # cursors

    async def read_cursor(
            self,
            q: AsyncQuerier,
            cursor_table: QualifiedName,
            link: str,
            table: str,
    ) -> CursorRow | None:
        rows = await qf.query_all(
            q,
            Q.select(
                [
                    Q.i(CURSOR_POSITION),
                    Q.i(CURSOR_SWEEPS),
                ],
                Q.n(tuple(cursor_table)),
                Q.and_(
                    Q.eq(Q.i(CURSOR_LINK), Q.p.link),
                    Q.eq(Q.i(CURSOR_TABLE), Q.p.table),
                ),
            ),
            {Q.p.link: link, Q.p.table: table},
        )
        if not rows:
            return None
        pos, sweeps = check.single(rows).values
        return CursorRow(pos, int(sweeps))

    async def write_cursor(
            self,
            q: AsyncQuerier,
            cursor_table: QualifiedName,
            link: str,
            table: str,
            row: CursorRow,
    ) -> None:
        await self._upsert(
            q,
            cursor_table,
            [
                CURSOR_LINK,
                CURSOR_TABLE,
                CURSOR_POSITION,
                CURSOR_SWEEPS,
                CURSOR_UPDATED_AT,
            ],
            [
                CURSOR_LINK,
                CURSOR_TABLE,
            ],
            [[
                link,
                table,
                row.position,
                row.sweeps,
                self.dtype_codec.encode(DATETIME, datetime.datetime.now(datetime.UTC)),
            ]],
        )

    ##
    # upserts

    async def _upsert(
            self,
            q: AsyncQuerier,
            table: QualifiedName,
            columns: ta.Sequence[str],
            keys: ta.Sequence[str],
            rows: ta.Sequence[ta.Sequence[ta.Any]],
    ) -> None:
        """Upserts rows of already encoded values, in as few statements as the parameter limit allows."""

        for chunk in itertools.batched(rows, max(self._max_statement_params // len(columns), 1)):
            pp = self._preparer(q)
            values: dict[str, ta.Any] = {}
            placeholders: list[list[str]] = []
            for i, row in enumerate(chunk):
                check.equal(len(row), len(columns))
                placeholders.append([pp.add(n) for n in (f'r{i}c{j}' for j in range(len(row)))])
                values.update((f'r{i}c{j}', v) for j, v in enumerate(row))

            await qf.exec(
                q,
                self.upsert_sql(
                    self.qname(table),
                    [self.quote(c) for c in columns],
                    [self.quote(k) for k in keys],
                    placeholders,
                ),
                self._bind(pp, values),
            )

    ##
    # shadows

    def _shadow_columns_sql(self) -> str:
        return ', '.join(self.quote(c) for c in (
            SHADOW_KEY,
            SHADOW_VERSION,
            SHADOW_ORIGIN,
            SHADOW_DELETED,
            SHADOW_CHANGED_AT,
        ))

    async def backfill_shadow(
            self,
            q: AsyncQuerier,
            td: TableDef,
            table: QualifiedName,
            shadow: QualifiedName,
            node_id: uuid.UUID,
    ) -> None:
        """Gives every base row that has no shadow row one at version one, authored by this node."""

        key = self.quote(table_key_column(td).name)
        pp = self._preparer(q)
        sql = (
            f'insert into {self.qname(shadow)} ({self._shadow_columns_sql()}) '
            f'select b.{key}, 1, {pp.add("origin")}, {pp.add("deleted")}, {self.now_sql()} '
            f'from {self.qname(table)} b '
            f'where not exists (select 1 from {self.qname(shadow)} s where s.{self.quote(SHADOW_KEY)} = b.{key})'
        )
        await qf.exec(q, sql, self._bind(pp, {
            'origin': self.dtype_codec.encode(UUID, node_id),
            'deleted': self.dtype_codec.encode(BOOLEAN, False),
        }))

    async def scan_shadows(
            self,
            q: AsyncQuerier,
            shadow: QualifiedName,
            *,
            after: uuid.UUID | None,
            limit: int,
            origins: OriginPredicate,
    ) -> dict[uuid.UUID, ShadowState]:
        """
        The next batch of the key-space sweep, in key order - and of the shadows alone: a sweep mostly finds that what
        it looks at is where it should be already, so what is in a base row is read (by `scan_keys`) only once the row
        is known to be wanted.
        """

        codec = self.dtype_codec
        pp = self._preparer(q)
        values: dict[str, ta.Any] = {}

        wheres: list[str] = []
        if after is not None:
            wheres.append(f's.{self.quote(SHADOW_KEY)} > {pp.add("after")}')
            values['after'] = codec.encode(UUID, after)
        self._origin_where(pp, values, wheres, origins)

        values['limit'] = limit
        sql = (
            'select '
            + ', '.join(f's.{self.quote(c)}' for c in (SHADOW_KEY, SHADOW_VERSION, SHADOW_ORIGIN, SHADOW_DELETED))
            + f' from {self.qname(shadow)} s '
            + (f'where {" and ".join(wheres)} ' if wheres else '')
            + f'order by s.{self.quote(SHADOW_KEY)} '
            + f'limit {pp.add("limit")}'
        )

        out: dict[uuid.UUID, ShadowState] = {}
        for r in await qf.query_all(q, sql, self._bind(pp, values)):
            k, ver, org, dl = r.values
            out[codec.decode(UUID, k)] = ShadowState(
                version=codec.decode(_version_dtype(), ver),
                origin=codec.decode(UUID, org),
                deleted=codec.decode(BOOLEAN, dl),
            )
        return out

    async def scan_keys(
            self,
            q: AsyncQuerier,
            td: TableDef,
            table: QualifiedName,
            shadow: QualifiedName,
            *,
            keys: ta.Sequence[uuid.UUID],
            origins: OriginPredicate,
    ) -> list[SourceRow]:
        """Whole rows for a given set of keys: what a log tail looks up, and a sweep once it knows what it wants."""

        if not keys:
            return []

        codec = self.dtype_codec
        pp = self._preparer(q)
        values: dict[str, ta.Any] = {}

        ps = [pp.add(f'k{i}') for i in range(len(keys))]
        for i, k in enumerate(keys):
            values[f'k{i}'] = codec.encode(UUID, k)
        wheres = [f's.{self.quote(SHADOW_KEY)} in ({", ".join(ps)})']
        self._origin_where(pp, values, wheres, origins)

        return await self._select_rows(q, td, table, shadow, pp, values, wheres)

    def _origin_where(
            self,
            pp: ParamsPreparer,
            values: dict[str, ta.Any],
            wheres: list[str],
            origins: OriginPredicate,
    ) -> None:
        codec = self.dtype_codec
        if origins.filter is OriginFilter.SOURCE_OWN:
            wheres.append(f's.{self.quote(SHADOW_ORIGIN)} = {pp.add("origin")}')
            values['origin'] = codec.encode(UUID, check.not_none(origins.node_id))
        elif origins.filter is OriginFilter.ALL_EXCEPT_TARGET:
            wheres.append(f's.{self.quote(SHADOW_ORIGIN)} <> {pp.add("origin")}')
            values['origin'] = codec.encode(UUID, check.not_none(origins.node_id))
        elif origins.filter is OriginFilter.ALL:
            pass
        else:
            raise ValueError(origins.filter)

    async def _select_rows(
            self,
            q: AsyncQuerier,
            td: TableDef,
            table: QualifiedName,
            shadow: QualifiedName,
            pp: ParamsPreparer,
            values: ta.Mapping[str, ta.Any],
            wheres: ta.Sequence[str],
    ) -> list[SourceRow]:
        codec = self.dtype_codec
        cols = list(td.elements[Column])
        key = self.quote(table_key_column(td).name)

        # Every selected column gets a positional alias: the shadow key and the base key share a name otherwise.
        sql = (
            'select '
            + ', '.join([
                *(
                    f's.{self.quote(c)} as {self.quote(f"s{i}")}'
                    for i, c in enumerate((
                        SHADOW_KEY,
                        SHADOW_VERSION,
                        SHADOW_ORIGIN,
                        SHADOW_DELETED,
                    ))
                ),
                *(f'b.{self.quote(c.name)} as {self.quote(f"c{i}")}' for i, c in enumerate(cols)),
            ])
            + f' from {self.qname(shadow)} s '
            f'left join {self.qname(table)} b on b.{key} = s.{self.quote(SHADOW_KEY)} '
            + (f'where {" and ".join(wheres)} ' if wheres else '')
            + f'order by s.{self.quote(SHADOW_KEY)}'
        )

        out: list[SourceRow] = []
        for r in await qf.query_all(q, sql, self._bind(pp, values)):
            vs = list(r.values)
            k, ver, org, dl = vs[:4]
            deleted = codec.decode(BOOLEAN, dl)
            out.append(SourceRow(
                key=codec.decode(UUID, k),
                version=codec.decode(_version_dtype(), ver),
                origin=codec.decode(UUID, org),
                deleted=deleted,
                values=None if deleted else {
                    c.name: codec.decode(c.type, v)
                    for c, v in zip(cols, vs[4:])
                },
            ))
        return out

    async def fetch_shadow_states(
            self,
            q: AsyncQuerier,
            shadow: QualifiedName,
            keys: ta.Sequence[uuid.UUID],
    ) -> dict[uuid.UUID, ShadowState]:
        if not keys:
            return {}

        codec = self.dtype_codec
        ps = [Q.p(f'k{i}') for i in range(len(keys))]
        out: dict[uuid.UUID, ShadowState] = {}

        for r in await qf.query_all(
            q,
            Q.select(
                [
                    Q.i(c) for c in (
                        SHADOW_KEY,
                        SHADOW_VERSION,
                        SHADOW_ORIGIN,
                        SHADOW_DELETED,
                    )
                ],
                Q.n(tuple(shadow)),
                Q.in_(Q.i(SHADOW_KEY), ps),
            ),
            {
                p: codec.encode(UUID, k)
                for p, k in zip(ps, keys)
            },
        ):
            k, ver, org, dl = r.values

            out[codec.decode(UUID, k)] = ShadowState(
                version=codec.decode(_version_dtype(), ver),
                origin=codec.decode(UUID, org),
                deleted=codec.decode(BOOLEAN, dl),
            )

        return out

    async def upsert_shadows(
            self,
            q: AsyncQuerier,
            shadow: QualifiedName,
            states: ta.Mapping[uuid.UUID, ShadowState],
    ) -> None:
        codec = self.dtype_codec
        now = codec.encode(DATETIME, datetime.datetime.now(datetime.UTC))

        await self._upsert(
            q,
            shadow,
            [
                SHADOW_KEY,
                SHADOW_VERSION,
                SHADOW_ORIGIN,
                SHADOW_DELETED,
                SHADOW_CHANGED_AT,
            ],
            [SHADOW_KEY],
            [
                [
                    codec.encode(UUID, key),
                    codec.encode(_version_dtype(), state.version),
                    codec.encode(UUID, state.origin),
                    codec.encode(BOOLEAN, state.deleted),
                    now,
                ]
                for key, state in states.items()
            ],
        )

    ##
    # base rows

    async def upsert_rows(
            self,
            q: AsyncQuerier,
            td: TableDef,
            table: QualifiedName,
            rows: ta.Sequence[ta.Mapping[str, ta.Any]],
    ) -> None:
        codec = self.dtype_codec
        cols = list(td.elements[Column])
        names = {c.name for c in cols}
        for values in rows:
            check.equal(set(values), names)

        await self._upsert(
            q,
            table,
            [c.name for c in cols],
            [table_key_column(td).name],
            [
                [codec.encode(c.type, values[c.name]) for c in cols]
                for values in rows
            ],
        )

    async def delete_rows(
            self,
            q: AsyncQuerier,
            td: TableDef,
            table: QualifiedName,
            keys: ta.Sequence[uuid.UUID],
    ) -> None:
        kc = table_key_column(td)
        for chunk in itertools.batched(keys, self._max_statement_params):
            ps = [Q.p(f'k{i}') for i in range(len(chunk))]
            await qf.exec(
                q,
                Q.delete(
                    Q.n(tuple(table)),
                    where=Q.in_(Q.i(kc.name), ps),
                ),
                {p: self.dtype_codec.encode(UUID, k) for p, k in zip(ps, chunk)},
            )

    ##
    # log

    async def read_log(
            self,
            q: AsyncQuerier,
            log_table: QualifiedName,
            *,
            after: int,
            limit: int,
    ) -> list[LogEntry]:
        codec = self.dtype_codec
        out: list[LogEntry] = []
        for r in await qf.query_all(
                q,
                Q.select(
                    [
                        Q.i(c)
                        for c in (
                            LOG_SEQ,
                            LOG_TABLE,
                            LOG_KEY,
                            LOG_VERSION,
                        )
                    ],
                    Q.n(tuple(log_table)),
                    Q.gt(Q.i(LOG_SEQ), Q.p.after),
                    order_by=[(Q.i(LOG_SEQ), 'asc')],
                    limit=Q.p.limit,
                ),
                {Q.p.after: after, Q.p.limit: limit},
        ):
            seq, tbl, k, ver = r.values
            out.append(LogEntry(
                seq=int(seq),
                table=check.isinstance(tbl, str),
                key=codec.decode(UUID, k),
                version=codec.decode(_version_dtype(), ver),
            ))
        return out

    async def prune_log(self, q: AsyncQuerier, log_table: QualifiedName, *, before: datetime.datetime) -> None:
        """
        Drops the entries older than `before` - but for the newest there is, however old. A link holds its place in the
        log by sequence number, so the numbers must never come around again, behind every link's place, where whatever
        came next would go unseen by them until the numbers had caught back up. A log's sequence is an identity, which
        sees to that by itself - but has not always on sqlite, where a log made before it did numbers an entry one past
        the highest still there, and would start over from an emptied one. Leaving the newest costs nothing, and holds
        for those too.
        """

        # FIXME: FIXME: FIXME: this is a scan of the whole log, there being - deliberately - no index on when an entry
        #  was made. It has to become something which walks the log by its key, as the pruning of tombstones does the
        #  shadows by theirs: entries are made in sequence, so the ones to go are a prefix of it, and what is wanted is
        #  where that prefix ends.
        pp = self._preparer(q)
        seq = self.quote(LOG_SEQ)
        await qf.exec(
            q,
            (
                f'delete from {self.qname(log_table)} '
                f'where {self.quote(LOG_CHANGED_AT)} < {pp.add("before")} '
                # Through a derived table, as mysql will not have a delete's own table in a subquery of it otherwise.
                f'and {seq} < (select m from (select max({seq}) as m from {self.qname(log_table)}) x)'
            ),
            self._bind(pp, {'before': self.dtype_codec.encode(DATETIME, before)}),
        )

    async def prune_tombstones(
            self,
            q: AsyncQuerier,
            shadow: QualifiedName,
            *,
            after: uuid.UUID | None,
            upto: uuid.UUID | None,
            before: datetime.datetime,
    ) -> None:
        """
        Drops the tombstones older than `before` within a range of keys - after the one, up to and including the other,
        either of which may be open. It is only ever done by range: a shadow is indexed by its key and nothing else, so
        this is a walk of a stretch of that index, where doing it by age alone would be a scan of the whole table.
        """

        codec = self.dtype_codec

        wheres = [
            Q.eq(Q.i(SHADOW_DELETED), Q.p.deleted),
            Q.lt(Q.i(SHADOW_CHANGED_AT), Q.p.before),
        ]
        values: dict[ta.Any, ta.Any] = {
            Q.p.deleted: codec.encode(BOOLEAN, True),
            Q.p.before: codec.encode(DATETIME, before),
        }
        if after is not None:
            wheres.append(Q.gt(Q.i(SHADOW_KEY), Q.p.after))
            values[Q.p.after] = codec.encode(UUID, after)
        if upto is not None:
            wheres.append(Q.le(Q.i(SHADOW_KEY), Q.p.upto))
            values[Q.p.upto] = codec.encode(UUID, upto)

        await qf.exec(q, Q.delete(Q.n(tuple(shadow)), where=Q.and_(*wheres)), values)


##


class OnConflictReplicateBackend(ReplicateBackend, lang.Abstract):
    """The `insert ... on conflict do update` form shared by postgres and sqlite."""

    def upsert_sql(
            self,
            table: str,
            columns: ta.Sequence[str],
            keys: ta.Sequence[str],
            rows: ta.Sequence[ta.Sequence[str]],
    ) -> str:
        sets = [f'{c} = excluded.{c}' for c in columns if c not in keys]
        action = f'do update set {", ".join(sets)}' if sets else 'do nothing'
        return (
            f'insert into {table} ({", ".join(columns)}) '
            f'values {", ".join(f"({", ".join(row)})" for row in rows)} '
            f'on conflict ({", ".join(keys)}) {action}'
        )
