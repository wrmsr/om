"""
Test support: nodes over sandboxes, direct row manipulation on a node, and a fault-injecting db. A sandbox hands out a
sync db, so by default a node's is that behind the async interface, run in place - which is what lets a scenario be
driven with no event loop at all.
"""
import contextlib
import typing as ta
import uuid

from .... import check
from ...api import querierfuncs as qf
from ...api.adapters import Adapter
from ...api.asyncs import ImmediateSyncToAsyncRunner
from ...api.asyncs import SyncToAsyncDb
from ...api.core import AsyncConn
from ...api.core import AsyncDb
from ...api.core import AsyncRows
from ...api.core import AsyncTxn
from ...api.queries import Query
from ...api.queries import Queryable
from ...queries import Q
from ...tabledefs.elements import Column
from ...tabledefs.tabledefs import TableDef
from ...testing.sandboxes import Sandbox
from ..backends.mysql import MysqlReplicateBackend
from ..backends.postgres import PostgresReplicateBackend
from ..backends.sqlite import SqliteReplicateBackend
from ..config import OriginFilter
from ..config import table_key_column
from ..nodes import Node
from ..rows import OriginPredicate
from ..rows import SourceRow


##


def sandbox_async_db(sb: Sandbox) -> AsyncDb:
    return SyncToAsyncDb(ImmediateSyncToAsyncRunner, sb.db())


def postgres_node(name: str, sb: Sandbox, db: AsyncDb | None = None, **kwargs: ta.Any) -> Node:
    return Node(name, db if db is not None else sandbox_async_db(sb), PostgresReplicateBackend(), **kwargs)


def sqlite_node(name: str, sb: Sandbox, db: AsyncDb | None = None, **kwargs: ta.Any) -> Node:
    return Node(name, db if db is not None else sandbox_async_db(sb), SqliteReplicateBackend(), **kwargs)


def mysql_node(name: str, sb: Sandbox, db: AsyncDb | None = None, **kwargs: ta.Any) -> Node:
    return Node(name, db if db is not None else sandbox_async_db(sb), MysqlReplicateBackend(), **kwargs)


##


async def insert_row(node: Node, td: TableDef, values: ta.Mapping[str, ta.Any]) -> None:
    codec = node.backend.dtype_codec
    cols = list(td.elements[Column])
    check.equal(set(values), {c.name for c in cols})
    async with node.db.connect() as conn:
        await qf.exec(
            conn,
            Q.insert([Q.i(c.name) for c in cols], Q.n(tuple(node.table_name(td))), [Q.p(c.name) for c in cols]),
            {Q.p(c.name): codec.encode(c.type, values[c.name]) for c in cols},
        )


async def update_row(node: Node, td: TableDef, key: uuid.UUID, values: ta.Mapping[str, ta.Any]) -> None:
    codec = node.backend.dtype_codec
    cols = {c.name: c for c in td.elements[Column]}
    kc = table_key_column(td)
    async with node.db.connect() as conn:
        await qf.exec(
            conn,
            Q.update(
                Q.n(tuple(node.table_name(td))),
                [(Q.i(k), Q.p(k)) for k in values],
                where=Q.eq(Q.i(kc.name), Q.p.key__),
            ),
            {
                **{Q.p(k): codec.encode(cols[k].type, v) for k, v in values.items()},
                Q.p.key__: codec.encode(kc.type, key),
            },
        )


async def delete_row(node: Node, td: TableDef, key: uuid.UUID) -> None:
    kc = table_key_column(td)
    async with node.db.connect() as conn:
        await qf.exec(
            conn,
            Q.delete(Q.n(tuple(node.table_name(td))), where=Q.eq(Q.i(kc.name), Q.p.key)),
            {Q.p.key: node.backend.dtype_codec.encode(kc.type, key)},
        )


async def read_rows(node: Node, td: TableDef) -> dict[uuid.UUID, dict[str, ta.Any]]:
    """Every base row, decoded to canonical values, by key."""

    codec = node.backend.dtype_codec
    cols = list(td.elements[Column])
    kc = table_key_column(td)
    async with node.db.connect() as conn:
        rows = await qf.query_all(conn, Q.select([Q.i(c.name) for c in cols], Q.n(tuple(node.table_name(td)))))
    out: dict[uuid.UUID, dict[str, ta.Any]] = {}
    for r in rows:
        d = {c.name: codec.decode(c.type, v) for c, v in zip(cols, r.values)}
        out[d[kc.name]] = d
    return out


async def read_shadow(node: Node, td: TableDef) -> dict[uuid.UUID, SourceRow]:
    """Every shadow row, via the backend's own sweep with no filter."""

    origins = OriginPredicate(filter=OriginFilter.ALL)
    async with node.db.connect() as conn:
        shadows = await node.backend.scan_shadows(
            conn,
            node.shadow_name(td),
            after=None,
            limit=1_000_000,
            origins=origins,
        )
        rows = await node.backend.scan_keys(
            conn,
            td,
            node.table_name(td),
            node.shadow_name(td),
            keys=list(shadows),
            origins=origins,
        )
    check.equal({r.key: r.state for r in rows}, shadows)
    return {r.key: r for r in rows}


##


class InjectedFaultError(Exception):
    pass


class FailingDb(AsyncDb):
    """
    A db that raises on any statement the (mutable) predicate matches, for staging crashes at chosen points - and which
    keeps count of the connections made and the statements run through it, for seeing what a step costs.
    """

    def __init__(self, db: AsyncDb) -> None:
        super().__init__()

        self._db = db
        self.fail_when: ta.Callable[[str], bool] = lambda _: False

        self.num_connects = 0
        self.statements: list[str] = []

    def reset_counts(self) -> None:
        self.num_connects = 0
        self.statements.clear()

    @property
    def writes(self) -> list[str]:
        return [s for s in self.statements if s.lstrip().lower().startswith(('insert', 'update', 'delete'))]

    @property
    def adapter(self) -> Adapter:
        return self._db.adapter

    def _check(self, query: Queryable) -> None:
        if isinstance(query, Query):
            self.statements.append(query.text)
            if self.fail_when(query.text):
                raise InjectedFaultError(query.text)

    def connect(self) -> ta.AsyncContextManager[AsyncConn]:
        @contextlib.asynccontextmanager
        async def inner():
            self.num_connects += 1
            async with self._db.connect() as conn:
                yield _FailingConn(self, conn)

        return inner()

    def query(self, query: Queryable) -> ta.AsyncContextManager[AsyncRows]:
        self._check(query)
        return self._db.query(query)


class _FailingConn(AsyncConn):
    def __init__(self, db: FailingDb, conn: AsyncConn) -> None:
        super().__init__()

        self._db = db
        self._conn = conn

    @property
    def adapter(self) -> Adapter:
        return self._conn.adapter

    def query(self, query: Queryable) -> ta.AsyncContextManager[AsyncRows]:
        self._db._check(query)  # noqa
        return self._conn.query(query)

    def begin(self) -> ta.AsyncContextManager[AsyncTxn]:
        @contextlib.asynccontextmanager
        async def inner():
            async with self._conn.begin() as txn:
                yield _FailingTxn(self._db, txn)

        return inner()


class _FailingTxn(AsyncTxn):
    def __init__(self, db: FailingDb, txn: AsyncTxn) -> None:
        super().__init__()

        self._db = db
        self._txn = txn

    @property
    def adapter(self) -> Adapter:
        return self._txn.adapter

    def query(self, query: Queryable) -> ta.AsyncContextManager[AsyncRows]:
        self._db._check(query)  # noqa
        return self._txn.query(query)

    async def commit(self) -> None:
        await self._txn.commit()

    async def rollback(self) -> None:
        await self._txn.rollback()
