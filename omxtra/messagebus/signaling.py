import abc
import select
import typing as ta

from omcore import check
from omcore import lang

from .sql import NotifyingSqlConn
from .types import WorkerId
from .waker import Waker


##


class Signaling(lang.Abstract):
    """
    Wakeups only, never transport: a notification can be dropped, so the loop polls on wake *and* on a timer. `listen`
    subscribes and names the waker wakeups are delivered to; it runs before the first poll so nothing slips between a
    poll and the following wait. `notify` is called inside the send transaction so it fires on commit and never for a
    rolled-back batch.
    """

    @abc.abstractmethod
    def listen(self, waker: Waker) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def notify(self, dst_ids: ta.Iterable[WorkerId]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def wait(self, timeout: float) -> None:
        raise NotImplementedError


class PollingSignaling(Signaling):
    """Mysql / sqlite: no server-side wakeup, but local sends and stops still interrupt the wait through the waker."""

    def __init__(self) -> None:
        super().__init__()

        self._waker: Waker | None = None

    def listen(self, waker: Waker) -> None:
        self._waker = waker

    def notify(self, dst_ids: ta.Iterable[WorkerId]) -> None:
        pass

    def wait(self, timeout: float) -> None:
        check.not_none(self._waker).wait(timeout)


class PostgresSignaling(Signaling):
    def __init__(self, conn: NotifyingSqlConn, worker_id: WorkerId) -> None:
        super().__init__()

        self._conn = conn
        self._worker_id = worker_id

        self._waker: Waker | None = None

    @staticmethod
    def _channel(worker_id: WorkerId) -> str:
        return f'bus_{worker_id.hex}'  # 36 chars, under the 63-char identifier limit

    def listen(self, waker: Waker) -> None:
        self._waker = waker
        self._conn.execute(f'listen {self._channel(self._worker_id)}')

    def notify(self, dst_ids: ta.Iterable[WorkerId]) -> None:
        for dst_id in dst_ids:
            self._conn.execute('select pg_notify(%s, %s)', [self._channel(dst_id), ''])  # deduped within the txn

    def wait(self, timeout: float) -> None:
        waker = check.not_none(self._waker)
        conn_fd = self._conn.fileno()
        r, _, _ = select.select([conn_fd, waker.fileno()], [], [], timeout)
        if conn_fd in r:
            self._conn.drain_notifies()  # payloads are ignored: a wake is a wake, the poll finds out what changed
        if waker.fileno() in r:
            waker.drain()
