import abc

from omcore import check
from omcore import lang

from .locks import IdentityLock
from .locks import MysqlIdentityLock
from .locks import NopIdentityLock
from .locks import PostgresAdvisoryIdentityLock
from .signaling import PollingSignaling
from .signaling import PostgresSignaling
from .signaling import Signaling
from .sql import NotifyingSqlConn
from .sql import SqlConn
from .statements import MYSQL_STATEMENTS
from .statements import POSTGRES_STATEMENTS
from .statements import SQLITE_STATEMENTS
from .statements import Statements
from .types import WorkerId


##


class SqlDialect(lang.Abstract):
    @property
    @abc.abstractmethod
    def statements(self) -> Statements:
        raise NotImplementedError

    @abc.abstractmethod
    def make_lock(self, conn: SqlConn, worker_id: WorkerId) -> IdentityLock:
        raise NotImplementedError

    @abc.abstractmethod
    def make_signaling(self, conn: SqlConn, worker_id: WorkerId) -> Signaling:
        raise NotImplementedError


class PostgresSqlDialect(SqlDialect):
    @property
    def statements(self) -> Statements:
        return POSTGRES_STATEMENTS

    def make_lock(self, conn: SqlConn, worker_id: WorkerId) -> IdentityLock:
        return PostgresAdvisoryIdentityLock(conn, worker_id)

    def make_signaling(self, conn: SqlConn, worker_id: WorkerId) -> Signaling:
        return PostgresSignaling(check.isinstance(conn, NotifyingSqlConn), worker_id)


class MysqlSqlDialect(SqlDialect):
    @property
    def statements(self) -> Statements:
        return MYSQL_STATEMENTS

    def make_lock(self, conn: SqlConn, worker_id: WorkerId) -> IdentityLock:
        return MysqlIdentityLock(conn, worker_id)

    def make_signaling(self, conn: SqlConn, worker_id: WorkerId) -> Signaling:
        return PollingSignaling()


class SqliteSqlDialect(SqlDialect):
    """Single-host only, and only the heartbeat says who's alive. Fine for tests and one-box setups."""

    @property
    def statements(self) -> Statements:
        return SQLITE_STATEMENTS

    def make_lock(self, conn: SqlConn, worker_id: WorkerId) -> IdentityLock:
        return NopIdentityLock()

    def make_signaling(self, conn: SqlConn, worker_id: WorkerId) -> Signaling:
        return PollingSignaling()
