import threading
import typing as ta

from ..sessions import BusSession
from ..store import MessageStore
from ..types import Message
from ..types import WorkerId
from ..types import WorkerInfo
from .faults import DelegatingBusSession


##


class Gate:
    """A point a worker thread parks at until the test opens it. `arrived` is set once it's parked. Stays open."""

    def __init__(self, *, timeout: float) -> None:
        super().__init__()

        self._timeout = timeout

        self.arrived = threading.Event()
        self._open = threading.Event()

    def pass_through(self) -> None:
        self.arrived.set()
        if not self._open.wait(self._timeout):
            raise TimeoutError

    def open(self) -> None:
        self._open.set()


class GatedMessageStore(MessageStore):
    """Delegates everything, but parks at the gate on the way out of every `select_messages`."""

    def __init__(self, inner: MessageStore, gate: Gate) -> None:
        super().__init__()

        self._inner = inner
        self._gate = gate

    def register_worker(self, worker_id: WorkerId, name: str) -> None:
        self._inner.register_worker(worker_id, name)

    def load_seqs(self, worker_id: WorkerId) -> ta.Mapping[WorkerId, int]:
        return self._inner.load_seqs(worker_id)

    def heartbeat(self, worker_id: WorkerId) -> None:
        self._inner.heartbeat(worker_id)

    def list_workers(self) -> ta.Sequence[WorkerInfo]:
        return self._inner.list_workers()

    def insert_message(self, msg: Message) -> None:
        self._inner.insert_message(msg)

    def update_seqs(self, worker_id: WorkerId, seqs: ta.Mapping[WorkerId, int]) -> None:
        self._inner.update_seqs(worker_id, seqs)

    def select_messages(self, dst_id: WorkerId, *, limit: int) -> ta.Sequence[Message]:
        msgs = self._inner.select_messages(dst_id, limit=limit)
        self._gate.pass_through()  # after the inner call, so no storage lock is held while parked
        return msgs

    def delete_message(self, msg: Message) -> None:
        self._inner.delete_message(msg)


class GatedBusSession(DelegatingBusSession):
    def __init__(self, inner: BusSession, gate: Gate) -> None:
        super().__init__(inner)

        self._store = GatedMessageStore(inner.store, gate)

    @property
    def store(self) -> MessageStore:
        return self._store
