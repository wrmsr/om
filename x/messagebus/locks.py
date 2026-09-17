import abc

from omcore import lang

from .sql import SqlConn
from .types import WorkerId


##


class IdentityLock(lang.Abstract):
    """
    Exclusive, session-scoped ownership of a worker identity. It's released implicitly when the session's connection
    dies, which is the point: it cannot outlive the connection that does the writing.
    """

    @abc.abstractmethod
    def try_acquire(self) -> bool:
        raise NotImplementedError


class NopIdentityLock(IdentityLock):
    """Sqlite has no cross-process primitive worth having here; the heartbeat is the only liveness signal."""

    def try_acquire(self) -> bool:
        return True


class PostgresAdvisoryIdentityLock(IdentityLock):
    def __init__(self, conn: SqlConn, worker_id: WorkerId) -> None:
        super().__init__()

        self._conn = conn
        self._worker_id = worker_id

    def try_acquire(self) -> bool:
        # Session level, not _xact_, and it must be the pinned bus connection. Advisory keys are int8, so fold the uuid.
        key = int.from_bytes(self._worker_id.bytes[:8], 'big', signed=True)
        [[ok]] = self._conn.execute('select pg_try_advisory_lock(%s)', [key])
        return bool(ok)


class MysqlIdentityLock(IdentityLock):
    def __init__(self, conn: SqlConn, worker_id: WorkerId) -> None:
        super().__init__()

        self._conn = conn
        self._worker_id = worker_id

    def try_acquire(self) -> bool:
        [[ok]] = self._conn.execute('select get_lock(%s, 0)', [f'bus_worker_{self._worker_id.hex}'])
        return ok == 1  # 0: held by another session, null: error
