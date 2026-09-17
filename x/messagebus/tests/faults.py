import contextlib
import enum
import threading
import typing as ta

from ..locks import IdentityLock
from ..sessions import BusSession
from ..sessions import BusSessionFactory
from ..signaling import Signaling
from ..store import MessageStore
from ..types import WorkerId


##


class ConnectionLostError(Exception):
    pass


class FaultBudget:
    """Fires a fixed number of times, then never again."""

    def __init__(self, count: int) -> None:
        super().__init__()

        self._remaining = count

    def take(self) -> bool:
        if self._remaining <= 0:
            return False
        self._remaining -= 1
        return True


##


class DelegatingBusSession(BusSession):
    def __init__(self, inner: BusSession) -> None:
        super().__init__()

        self._inner = inner

    @property
    def store(self) -> MessageStore:
        return self._inner.store

    @property
    def lock(self) -> IdentityLock:
        return self._inner.lock

    @property
    def signaling(self) -> Signaling:
        return self._inner.signaling

    def transaction(self) -> ta.ContextManager[None]:
        return self._inner.transaction()

    def close(self) -> None:
        self._inner.close()


class FaultPoint(enum.Enum):
    BEFORE_COMMIT = enum.auto()  # the connection dies before anything in the transaction is written
    AFTER_COMMIT = enum.auto()  # the commit lands, but the connection dies before we hear back


class FaultyBusSession(DelegatingBusSession):
    def __init__(self, inner: BusSession, point: FaultPoint, budget: FaultBudget) -> None:
        super().__init__(inner)

        self._point = point
        self._budget = budget

    @contextlib.contextmanager
    def _transaction(self) -> ta.Iterator[None]:
        if self._point is FaultPoint.BEFORE_COMMIT and self._budget.take():
            raise ConnectionLostError
        with self._inner.transaction():
            yield
        if self._point is FaultPoint.AFTER_COMMIT and self._budget.take():
            raise ConnectionLostError

    def transaction(self) -> ta.ContextManager[None]:
        return self._transaction()


class ObservedBusSession(DelegatingBusSession):
    """Sets `committed` after each transaction exits."""

    def __init__(self, inner: BusSession, committed: threading.Event) -> None:
        super().__init__(inner)

        self._committed = committed

    @contextlib.contextmanager
    def _transaction(self) -> ta.Iterator[None]:
        with self._inner.transaction():
            yield
        self._committed.set()

    def transaction(self) -> ta.ContextManager[None]:
        return self._transaction()


##


class WrappingBusSessionFactory(BusSessionFactory):
    def __init__(self, inner: BusSessionFactory, wrap: ta.Callable[[BusSession], BusSession]) -> None:
        super().__init__()

        self._inner = inner
        self._wrap = wrap

    def open(self, worker_id: WorkerId, *, timeout: float) -> BusSession:
        return self._wrap(self._inner.open(worker_id, timeout=timeout))


class FaultyBusSessionFactory(BusSessionFactory):
    """Wraps another factory: counts opens, fails the first `failed_opens` of them, and injects `faults` at `point`."""

    def __init__(
            self,
            inner: BusSessionFactory,
            *,
            failed_opens: int = 0,
            point: FaultPoint | None = None,
            faults: int = 0,
    ) -> None:
        super().__init__()

        self._inner = inner
        self._open_budget = FaultBudget(failed_opens)
        self._point = point
        self._fault_budget = FaultBudget(faults)

        self._cond = threading.Condition()
        self.opens = 0

    def wait_for_opens(self, n: int, *, timeout: float) -> bool:
        with self._cond:
            return self._cond.wait_for(lambda: self.opens >= n, timeout)

    def open(self, worker_id: WorkerId, *, timeout: float) -> BusSession:
        with self._cond:
            self.opens += 1
            self._cond.notify_all()
        if self._open_budget.take():
            raise ConnectionLostError
        sess = self._inner.open(worker_id, timeout=timeout)
        if self._point is None:
            return sess
        return FaultyBusSession(sess, self._point, self._fault_budget)
