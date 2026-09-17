import datetime
import threading
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .locks import IdentityLock
from .sessions import BusSession
from .sessions import BusSessionFactory
from .signaling import Signaling
from .store import MessageStore
from .types import Message
from .types import WorkerId
from .types import WorkerInfo
from .waker import Waker


##


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class DictBusStorage(MessageStore):
    """
    A process-local stand-in for both tables plus the lock and notify primitives, shared by every session opened on it.
    Useful beyond tests: it's a perfectly good bus for workers that all live in one process.
    """

    def __init__(self) -> None:
        super().__init__()

        self._lock = threading.RLock()

        self._workers: dict[WorkerId, WorkerInfo] = {}
        self._seqs: dict[WorkerId, dict[WorkerId, int]] = {}
        self._messages: dict[tuple[WorkerId, WorkerId, int], Message] = {}
        self._held: set[WorkerId] = set()
        self._wakers: dict[WorkerId, Waker] = {}

    def transaction(self) -> ta.ContextManager[None]:
        return self._lock  # type: ignore[return-value]  # coarse but atomic, which is all a stand-in needs

    ## identity

    def try_acquire(self, worker_id: WorkerId) -> bool:
        with self._lock:
            if worker_id in self._held:
                return False
            self._held.add(worker_id)
            return True

    def release(self, worker_id: WorkerId) -> None:
        with self._lock:
            self._held.discard(worker_id)
            self._wakers.pop(worker_id, None)

    ## signaling

    def set_waker(self, worker_id: WorkerId, waker: Waker) -> None:
        self._wakers[worker_id] = waker

    def wake(self, dst_ids: ta.Iterable[WorkerId]) -> None:
        for dst_id in dst_ids:
            if (w := self._wakers.get(dst_id)) is not None:
                w.wake()

    ## store

    def register_worker(self, worker_id: WorkerId, name: str) -> None:
        with self._lock:
            now = _now()
            self._workers[worker_id] = WorkerInfo(worker_id, name, now, now)
            self._seqs.setdefault(worker_id, {})  # preserved across restarts, like the row

    def load_seqs(self, worker_id: WorkerId) -> ta.Mapping[WorkerId, int]:
        with self._lock:
            return dict(self._seqs[worker_id])

    def heartbeat(self, worker_id: WorkerId) -> None:
        with self._lock:
            self._workers[worker_id] = dc.replace(self._workers[worker_id], heartbeat_at=_now())

    def list_workers(self) -> ta.Sequence[WorkerInfo]:
        with self._lock:
            return list(self._workers.values())

    def insert_message(self, msg: Message) -> None:
        with self._lock:
            msg = dc.replace(msg, created_at=_now())
            key = (msg.dst_id, msg.src_id, msg.seq)
            check.not_in(key, self._messages)  # the pk tripwire
            self._messages[key] = msg

    def update_seqs(self, worker_id: WorkerId, seqs: ta.Mapping[WorkerId, int]) -> None:
        with self._lock:
            self._seqs[worker_id] = dict(seqs)

    def select_messages(self, dst_id: WorkerId, *, limit: int) -> ta.Sequence[Message]:
        with self._lock:
            msgs = [m for (d, _, _), m in self._messages.items() if d == dst_id]
        msgs.sort(key=lambda m: (m.created_at, m.src_id, m.seq))
        return msgs[:limit]

    def delete_message(self, msg: Message) -> None:
        with self._lock:
            self._messages.pop((msg.dst_id, msg.src_id, msg.seq), None)


##


class DictIdentityLock(IdentityLock):
    def __init__(self, storage: DictBusStorage, worker_id: WorkerId) -> None:
        super().__init__()

        self._storage = storage
        self._worker_id = worker_id

    def try_acquire(self) -> bool:
        return self._storage.try_acquire(self._worker_id)


class DictSignaling(Signaling):
    def __init__(self, storage: DictBusStorage, worker_id: WorkerId) -> None:
        super().__init__()

        self._storage = storage
        self._worker_id = worker_id

    def listen(self) -> None:
        pass

    def notify(self, dst_ids: ta.Iterable[WorkerId]) -> None:
        # Fires before 'commit', but the woken side then blocks on the storage lock until the transaction ends.
        self._storage.wake(dst_ids)

    def wait(self, timeout: float, waker: Waker) -> None:
        self._storage.set_waker(self._worker_id, waker)
        waker.wait(timeout)


class DictBusSession(BusSession):
    def __init__(self, storage: DictBusStorage, worker_id: WorkerId) -> None:
        super().__init__()

        self._storage = storage
        self._worker_id = worker_id

        self._lock = DictIdentityLock(storage, worker_id)
        self._signaling = DictSignaling(storage, worker_id)

    @property
    def store(self) -> MessageStore:
        return self._storage

    @property
    def lock(self) -> IdentityLock:
        return self._lock

    @property
    def signaling(self) -> Signaling:
        return self._signaling

    def transaction(self) -> ta.ContextManager[None]:
        return self._storage.transaction()

    def close(self) -> None:
        self._storage.release(self._worker_id)


class DictBusSessionFactory(BusSessionFactory):
    def __init__(self, storage: DictBusStorage | None = None) -> None:
        super().__init__()

        self._storage = storage if storage is not None else DictBusStorage()

    @property
    def storage(self) -> DictBusStorage:
        return self._storage

    def open(self, worker_id: WorkerId, *, timeout: float) -> BusSession:
        return DictBusSession(self._storage, worker_id)
