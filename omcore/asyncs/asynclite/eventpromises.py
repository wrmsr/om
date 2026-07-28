# ruff: noqa: UP045
# @om-lite
import threading
import typing as ta

from ...lite.abstract import Abstract
from ...lite.maybes import Maybe
from .base import AsyncliteApi
from .events import AsyncliteEvent
from .events import AsyncliteEvents
from .promises import AsynclitePromise
from .promises import AsynclitePromiseAlreadySetError
from .promises import AsynclitePromises
from .promises import AsynclitePromiseWaitTimeoutError


T = ta.TypeVar('T')


##


class EventAsynclitePromise(AsynclitePromise[T]):
    """
    Generic implementation backed by any AsyncliteEvent - waiting inherits the event's backend semantics, including
    which contexts may legally wait on it.

    Once completed the promise sheds its internal synchronization machinery: the set-once lock and the backing event
    are released, leaving only the outcome. This makes long-lived done promises (such as once-per-key caches) cost
    little more than the value itself.

    Maintainer invariants:
     - The outcome slots are written strictly before `_has_out`, which is the unlocked publication point - `_has_out`
       must always be the last write under the lock.
     - `_ev` and `_mtx` are None once done, and are nulled only after the outcome is published (and, for `_ev`, after
       it is set). All paths must operate on locally-captured refs, never re-read the attributes.
    """

    def __init__(self, ev: AsyncliteEvent) -> None:
        super().__init__()

        self._ev: ta.Optional[AsyncliteEvent] = ev
        self._mtx: ta.Optional[threading.Lock] = threading.Lock()
        self._has_out = False
        self._val: ta.Optional[T] = None
        self._exc: ta.Optional[BaseException] = None

    def is_done(self) -> bool:
        return self._has_out

    def _result(self) -> T:
        # Only valid once _has_out is set - _val / _exc are written (under _mtx) strictly before it.
        if (e := self._exc) is not None:
            raise e
        return ta.cast(T, self._val)

    def poll(self) -> Maybe[T]:
        if not self._has_out:
            return Maybe.empty()
        return Maybe.just(self._result())

    def _set(self, val: ta.Optional[T], exc: ta.Optional[BaseException]) -> None:
        if (mtx := self._mtx) is None:
            raise AsynclitePromiseAlreadySetError(self)

        with mtx:
            if self._has_out:
                raise AsynclitePromiseAlreadySetError(self)
            self._val = val
            self._exc = exc
            self._has_out = True  # must be the last write - the unlocked publication point for _val / _exc

        if (ev := self._ev) is not None:  # always the case for the sole arbitrated completer
            ev.set()

        self._ev = None
        self._mtx = None

    def set_value(self, v: T) -> None:
        self._set(v, None)

    def set_error(self, e: BaseException) -> None:
        if not isinstance(e, BaseException):
            raise TypeError(e)
        self._set(None, e)

    async def wait(self, *, timeout: ta.Optional[float] = None) -> T:
        # The local ref is grabbed before the done check: the completer nulls _ev only after publishing the outcome,
        # so observing a live event and a not-done flag guarantees the event will still be set.
        ev = self._ev
        if ev is not None and not self._has_out:
            try:
                await ev.wait(timeout=timeout)
            except TimeoutError as te:
                # A timeout racing completion is completion.
                if not self._has_out:
                    raise AsynclitePromiseWaitTimeoutError(self) from te

        return self._result()


class EventAsynclitePromises(
    AsyncliteEvents,
    AsynclitePromises,
    AsyncliteApi,
    Abstract,
):
    def make_promise(self) -> AsynclitePromise:
        return EventAsynclitePromise(self.make_event())
