import abc
import typing as ta

from omcore import lang

from .dialects import SqlDialect
from .locks import IdentityLock
from .signaling import Signaling
from .sql import SqlConn
from .sql import SqlConnector
from .store import MessageStore
from .store import SqlMessageStore
from .types import WorkerId


##


class BusSession(lang.Abstract):
    """Everything bound to one connection's lifetime. Torn down and rebuilt wholesale on any connection failure."""

    @property
    @abc.abstractmethod
    def store(self) -> MessageStore:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def lock(self) -> IdentityLock:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def signaling(self) -> Signaling:
        raise NotImplementedError

    @abc.abstractmethod
    def transaction(self) -> ta.ContextManager[None]:
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class BusSessionFactory(lang.Abstract):
    @abc.abstractmethod
    def open(self, worker_id: WorkerId, *, timeout: float) -> BusSession:
        raise NotImplementedError


##


class SqlBusSession(BusSession):
    def __init__(self, conn: SqlConn, dialect: SqlDialect, worker_id: WorkerId) -> None:
        super().__init__()

        self._conn = conn

        self._store = SqlMessageStore(conn, dialect.statements)
        self._lock = dialect.make_lock(conn, worker_id)
        self._signaling = dialect.make_signaling(conn, worker_id)

    @property
    def store(self) -> MessageStore:
        return self._store

    @property
    def lock(self) -> IdentityLock:
        return self._lock

    @property
    def signaling(self) -> Signaling:
        return self._signaling

    def transaction(self) -> ta.ContextManager[None]:
        return self._conn.transaction()

    def close(self) -> None:
        self._conn.close()  # also releases the advisory lock and drops the listen subscription


class SqlBusSessionFactory(BusSessionFactory):
    def __init__(self, connector: SqlConnector, dialect: SqlDialect) -> None:
        super().__init__()

        self._connector = connector
        self._dialect = dialect

    def open(self, worker_id: WorkerId, *, timeout: float) -> BusSession:
        return SqlBusSession(self._connector.connect(timeout=timeout), self._dialect, worker_id)
