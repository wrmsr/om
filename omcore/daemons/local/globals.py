import threading
import typing as ta

from ... import lang
from .coordinators import LocalWorkerCoordinator
from .coordinators import LocalWorkerLease
from .coordinators import ThreadedLocalWorkerCoordinator
from .workers import LocalWorkerSpec


T = ta.TypeVar('T')
R = ta.TypeVar('R')


##


_GLOBAL_LOCK = threading.RLock()


@lang.cached_function(lock=_GLOBAL_LOCK)
def global_local_worker_coordinator() -> LocalWorkerCoordinator:
    return ThreadedLocalWorkerCoordinator()


def acquire_local_worker(
        worker: LocalWorkerSpec[T],
        *,
        timeout: lang.TimeoutLike = None,
) -> LocalWorkerLease[T]:
    return global_local_worker_coordinator().acquire(worker, timeout=timeout)


def call_local_worker(
        worker: LocalWorkerSpec[T],
        fn: ta.Callable[[T], R],
        *,
        timeout: lang.TimeoutLike = None,
) -> R:
    return global_local_worker_coordinator().call(worker, fn, timeout=timeout)
