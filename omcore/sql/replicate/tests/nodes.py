"""Test support: nodes over sandboxes, direct row manipulation on a node, and a fault-injecting db."""
import contextlib
import typing as ta
import uuid

from .... import check
from ...api import querierfuncs as qf
from ...api.adapters import Adapter
from ...api.core import Conn
from ...api.core import Db
from ...api.core import Rows
from ...api.core import Txn
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


def postgres_node(name: str, sb: Sandbox, db: Db | None = None) -> Node:
    return Node(name, db if db is not None else sb.db(), PostgresReplicateBackend())


def sqlite_node(name: str, sb: Sandbox, db: Db | None = None) -> Node:
    return Node(name, db if db is not None else sb.db(), SqliteReplicateBackend())


def mysql_node(name: str, sb: Sandbox, db: Db | None = None) -> Node:
    return Node(name, db if db is not None else sb.db(), MysqlReplicateBackend())


##


def insert_row(node: Node, td: TableDef, values: ta.Mapping[str, ta.Any]) -> None:
    codec = node.backend.dtype_codec
    cols = list(td.elements[Column])
    check.equal(set(values), {c.name for c in cols})
    with node.db.connect() as conn:
        qf.exec(
            conn,
            Q.insert([Q.i(c.name) for c in cols], Q.n(tuple(node.table_name(td))), [Q.p(c.name) for c in cols]),
            {Q.p(c.name): codec.encode(c.type, values[c.name]) for c in cols},
        )


def update_row(node: Node, td: TableDef, key: uuid.UUID, values: ta.Mapping[str, ta.Any]) -> None:
    codec = node.backend.dtype_codec
    cols = {c.name: c for c in td.elements[Column]}
    kc = table_key_column(td)
    with node.db.connect() as conn:
        qf.exec(
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


def delete_row(node: Node, td: TableDef, key: uuid.UUID) -> None:
    kc = table_key_column(td)
    with node.db.connect() as conn:
        qf.exec(
            conn,
            Q.delete(Q.n(tuple(node.table_name(td))), where=Q.eq(Q.i(kc.name), Q.p.key)),
            {Q.p.key: node.backend.dtype_codec.encode(kc.type, key)},
        )


def read_rows(node: Node, td: TableDef) -> dict[uuid.UUID, dict[str, ta.Any]]:
    """Every base row, decoded to canonical values, by key."""

    codec = node.backend.dtype_codec
    cols = list(td.elements[Column])
    kc = table_key_column(td)
    with node.db.connect() as conn:
        rows = qf.query_all(conn, Q.select([Q.i(c.name) for c in cols], Q.n(tuple(node.table_name(td)))))
    out: dict[uuid.UUID, dict[str, ta.Any]] = {}
    for r in rows:
        d = {c.name: codec.decode(c.type, v) for c, v in zip(cols, r.values)}
        out[d[kc.name]] = d
    return out


def read_shadow(node: Node, td: TableDef) -> dict[uuid.UUID, SourceRow]:
    """Every shadow row, via the backend's own sweep with no filter."""

    with node.db.connect() as conn:
        rows = node.backend.scan(
            conn,
            td,
            node.table_name(td),
            node.shadow_name(td),
            after=None,
            limit=1_000_000,
            origins=OriginPredicate(filter=OriginFilter.ALL),
        )
    return {r.key: r for r in rows}


##


class InjectedFaultError(Exception):
    pass


class FailingDb(Db):
    """A db that raises on any statement the (mutable) predicate matches; for staging crashes at chosen points."""

    def __init__(self, db: Db) -> None:
        super().__init__()

        self._db = db
        self.fail_when: ta.Callable[[str], bool] = lambda _: False

    @property
    def adapter(self) -> Adapter:
        return self._db.adapter

    def _check(self, query: Queryable) -> None:
        if isinstance(query, Query) and self.fail_when(query.text):
            raise InjectedFaultError(query.text)

    def connect(self) -> ta.ContextManager[Conn]:
        @contextlib.contextmanager
        def inner():
            with self._db.connect() as conn:
                yield _FailingConn(self, conn)

        return inner()

    def query(self, query: Queryable) -> ta.ContextManager[Rows]:
        self._check(query)
        return self._db.query(query)


class _FailingConn(Conn):
    def __init__(self, db: FailingDb, conn: Conn) -> None:
        super().__init__()

        self._db = db
        self._conn = conn

    @property
    def adapter(self) -> Adapter:
        return self._conn.adapter

    def query(self, query: Queryable) -> ta.ContextManager[Rows]:
        self._db._check(query)  # noqa
        return self._conn.query(query)

    def begin(self) -> ta.ContextManager[Txn]:
        @contextlib.contextmanager
        def inner():
            with self._conn.begin() as txn:
                yield _FailingTxn(self._db, txn)

        return inner()


class _FailingTxn(Txn):
    def __init__(self, db: FailingDb, txn: Txn) -> None:
        super().__init__()

        self._db = db
        self._txn = txn

    @property
    def adapter(self) -> Adapter:
        return self._txn.adapter

    def query(self, query: Queryable) -> ta.ContextManager[Rows]:
        self._db._check(query)  # noqa
        return self._txn.query(query)

    def commit(self) -> None:
        self._txn.commit()

    def rollback(self) -> None:
        self._txn.rollback()
