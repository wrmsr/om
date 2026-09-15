# ruff: noqa: S608
"""
The dialect-specific half of replication. Nearly every statement is standard sql shared here; a dialect supplies only
its upsert syntax, its boolean literals for trigger bodies, its capture-trigger renderer, and its facets (ddl renderer,
inspector, dtype codec).
"""
import abc
import datetime
import typing as ta
import uuid

from .... import check
from .... import lang
from ...api import querierfuncs as qf
from ...api.queriers import Querier
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
from ..rows import OriginPredicate
from ..rows import ShadowState
from ..rows import SourceRow
from ..shadows import CURSOR_LINK
from ..shadows import CURSOR_POSITION
from ..shadows import CURSOR_SWEEPS
from ..shadows import CURSOR_TABLE
from ..shadows import CURSOR_UPDATED_AT
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
    position: uuid.UUID | None
    sweeps: int


class ReplicateBackend(lang.Abstract):
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
            key: str,
            placeholders: ta.Sequence[str],
    ) -> str:
        """An insert of the (already quoted) columns that becomes an update of the non-key ones on a key clash."""

        raise NotImplementedError

    def now_sql(self) -> str:
        return 'current_timestamp'

    ##
    # rendering helpers

    def quote(self, s: str) -> str:
        return self.tabledef_renderer.quote_ident(s)

    def qname(self, n: QualifiedName) -> str:
        return self.tabledef_renderer.qname(n)

    def _preparer(self, q: Querier) -> ParamsPreparer:
        return make_params_preparer(check.not_none(q.adapter.param_style))

    def _bind(self, pp: ParamsPreparer, values: ta.Mapping[str, ta.Any]) -> ta.Any:
        return substitute_params(ta.cast('ta.Any', pp.prepare()), ta.cast('ta.Any', values), strict=True)

    ##
    # node

    def read_node_id(self, q: Querier, node_table: QualifiedName) -> uuid.UUID | None:
        rows = qf.query_all(q, Q.select([Q.i(NODE_ID)], Q.n(tuple(node_table))))
        if not rows:
            return None
        return self.dtype_codec.decode(UUID, check.single(rows).values[0])

    def insert_node_id(self, q: Querier, node_table: QualifiedName, node_id: uuid.UUID) -> None:
        qf.exec(
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

    def read_cursor(self, q: Querier, cursor_table: QualifiedName, link: str, table: str) -> CursorRow | None:
        rows = qf.query_all(
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
        return CursorRow(uuid.UUID(pos) if pos is not None else None, int(sweeps))

    def write_cursor(self, q: Querier, cursor_table: QualifiedName, link: str, table: str, row: CursorRow) -> None:
        # A cursor row has exactly one writer, so read-then-write is race-free.
        t = Q.n(tuple(cursor_table))

        pos = str(row.position) if row.position is not None else None
        now = self.dtype_codec.encode(DATETIME, datetime.datetime.now(datetime.UTC))

        if self.read_cursor(q, cursor_table, link, table) is None:
            qf.exec(
                q,
                Q.insert(
                    [
                        Q.i(c)
                        for c in (
                            CURSOR_LINK,
                            CURSOR_TABLE,
                            CURSOR_POSITION,
                            CURSOR_SWEEPS,
                            CURSOR_UPDATED_AT,
                        )
                    ],
                    t,
                    [
                        Q.p.link,
                        Q.p.table,
                        Q.p.position,
                        Q.p.sweeps,
                        Q.p.updated_at,
                    ],
                ),
                {
                    Q.p.link: link,
                    Q.p.table: table,
                    Q.p.position: pos,
                    Q.p.sweeps: row.sweeps,
                    Q.p.updated_at: now,
                },
            )

        else:
            qf.exec(
                q,
                Q.update(
                    t,
                    [
                        (Q.i(CURSOR_POSITION), Q.p.position),
                        (Q.i(CURSOR_SWEEPS), Q.p.sweeps),
                        (Q.i(CURSOR_UPDATED_AT), Q.p.updated_at),
                    ],  # noqa
                    where=Q.and_(
                        Q.eq(Q.i(CURSOR_LINK), Q.p.link),
                        Q.eq(Q.i(CURSOR_TABLE), Q.p.table),
                    ),
                ),
                {
                    Q.p.position: pos,
                    Q.p.sweeps: row.sweeps,
                    Q.p.updated_at: now,
                    Q.p.link: link,
                    Q.p.table: table,
                },
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

    def backfill_shadow(
            self,
            q: Querier,
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
        qf.exec(q, sql, self._bind(pp, {
            'origin': self.dtype_codec.encode(UUID, node_id),
            'deleted': self.dtype_codec.encode(BOOLEAN, False),
        }))

    def scan(
            self,
            q: Querier,
            td: TableDef,
            table: QualifiedName,
            shadow: QualifiedName,
            *,
            after: uuid.UUID | None,
            limit: int,
            origins: OriginPredicate,
    ) -> list[SourceRow]:
        """The next batch of the key-space sweep: shadow rows in key order, joined to whatever base row remains."""

        codec = self.dtype_codec
        cols = list(td.elements[Column])
        key = self.quote(table_key_column(td).name)
        pp = self._preparer(q)
        values: dict[str, ta.Any] = {}

        wheres: list[str] = []
        if after is not None:
            wheres.append(f's.{self.quote(SHADOW_KEY)} > {pp.add("after")}')
            values['after'] = codec.encode(UUID, after)
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
            + f'order by s.{self.quote(SHADOW_KEY)} '
            f'limit {pp.add("limit")}'
        )
        values['limit'] = limit

        out: list[SourceRow] = []
        for r in qf.query_all(q, sql, self._bind(pp, values)):
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

    def fetch_shadow_states(
            self,
            q: Querier,
            shadow: QualifiedName,
            keys: ta.Sequence[uuid.UUID],
    ) -> dict[uuid.UUID, ShadowState]:
        if not keys:
            return {}

        codec = self.dtype_codec
        ps = [Q.p(f'k{i}') for i in range(len(keys))]
        out: dict[uuid.UUID, ShadowState] = {}

        for r in qf.query_all(
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

    def upsert_shadow(
            self,
            q: Querier,
            shadow: QualifiedName,
            key: uuid.UUID,
            state: ShadowState,
    ) -> None:
        codec = self.dtype_codec
        pp = self._preparer(q)

        cols = (
            SHADOW_KEY,
            SHADOW_VERSION,
            SHADOW_ORIGIN,
            SHADOW_DELETED,
            SHADOW_CHANGED_AT,
        )

        sql = self.upsert_sql(
            self.qname(shadow),
            [self.quote(c) for c in cols],
            self.quote(SHADOW_KEY),
            [pp.add(c) for c in cols],
        )

        qf.exec(q, sql, self._bind(pp, {
            SHADOW_KEY: codec.encode(UUID, key),
            SHADOW_VERSION: codec.encode(_version_dtype(), state.version),
            SHADOW_ORIGIN: codec.encode(UUID, state.origin),
            SHADOW_DELETED: codec.encode(BOOLEAN, state.deleted),
            SHADOW_CHANGED_AT: codec.encode(DATETIME, datetime.datetime.now(datetime.UTC)),
        }))

    ##
    # base rows

    def upsert_row(
            self,
            q: Querier,
            td: TableDef,
            table: QualifiedName,
            values: ta.Mapping[str, ta.Any],
    ) -> None:
        codec = self.dtype_codec
        cols = list(td.elements[Column])
        check.equal(set(values), {c.name for c in cols})
        pp = self._preparer(q)
        sql = self.upsert_sql(
            self.qname(table),
            [self.quote(c.name) for c in cols],
            self.quote(table_key_column(td).name),
            [pp.add(c.name) for c in cols],
        )
        qf.exec(
            q,
            sql,
            self._bind(
                pp,
                {
                    c.name: codec.encode(c.type, values[c.name])
                    for c in cols
                },
            ),
        )

    def delete_row(self, q: Querier, td: TableDef, table: QualifiedName, key: uuid.UUID) -> None:
        kc = table_key_column(td)
        qf.exec(
            q,
            Q.delete(
                Q.n(tuple(table)),
                where=Q.eq(Q.i(kc.name), Q.p.key),
            ),
            {Q.p.key: self.dtype_codec.encode(UUID, key)},
        )


##


class OnConflictReplicateBackend(ReplicateBackend, lang.Abstract):
    """The `insert ... on conflict do update` form shared by postgres and sqlite."""

    def upsert_sql(
            self,
            table: str,
            columns: ta.Sequence[str],
            key: str,
            placeholders: ta.Sequence[str],
    ) -> str:
        sets = [f'{c} = excluded.{c}' for c in columns if c != key]
        action = f'do update set {", ".join(sets)}' if sets else 'do nothing'
        return (
            f'insert into {table} ({", ".join(columns)}) values ({", ".join(placeholders)}) '
            f'on conflict ({key}) {action}'
        )
