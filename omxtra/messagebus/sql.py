"""
The seam onto the existing sql abstraction. Whatever adapts to this must hand out a dedicated, pinned connection in
autocommit mode: the advisory lock, the listen subscription, and the seq counter all live on it, so it must never be
pooled or proxied (pgbouncer transaction mode, rds proxy). Set tcp keepalives in the dsn - this connection's liveness
*is* the identity lock.
"""
import abc
import typing as ta

from omcore import lang


##


class SqlConn(lang.Abstract):
    @abc.abstractmethod
    def execute(self, sql: str, params: ta.Sequence[ta.Any] = ()) -> ta.Sequence[ta.Sequence[ta.Any]]:
        raise NotImplementedError

    @abc.abstractmethod
    def transaction(self) -> ta.ContextManager[None]:
        raise NotImplementedError

    @abc.abstractmethod
    def fileno(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def close(self) -> None:
        raise NotImplementedError


class NotifyingSqlConn(SqlConn, lang.Abstract):
    """
    Driver-specific: pull any pending async notifications off the socket once select() says it's readable (psycopg2:
    conn.poll() then conn.notifies; psycopg3: conn.notifies(timeout=0)). Only postgres needs this.
    """

    @abc.abstractmethod
    def drain_notifies(self) -> ta.Sequence[str]:
        raise NotImplementedError


class SqlConnector(lang.Abstract):
    @abc.abstractmethod
    def connect(self, *, timeout: float) -> SqlConn:
        raise NotImplementedError
