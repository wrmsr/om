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
    """

    def __init__(self, ev: AsyncliteEvent) -> None:
        super().__init__()

        self._ev = ev
        self._mtx = threading.Lock()
        self._has_out = False
        self._val: ta.Optional[T] = None
        self._exc: ta.Optional[BaseException] = None

    def is_done(self) -> bool:
        return self._ev.is_set()

    def _result(self) -> T:
        # Only valid once _ev is set - _val / _exc are written (under _mtx) strictly before _ev.set().
        if (e := self._exc) is not None:
            raise e
        return ta.cast(T, self._val)

    def poll(self) -> Maybe[T]:
        if not self._ev.is_set():
            return Maybe.empty()
        return Maybe.just(self._result())

    def _set(self, val: ta.Optional[T], exc: ta.Optional[BaseException]) -> None:
        with self._mtx:
            if self._has_out:
                raise AsynclitePromiseAlreadySetError(self)
            self._has_out = True
            self._val = val
            self._exc = exc

        self._ev.set()

    def set_value(self, v: T) -> None:
        self._set(v, None)

    def set_error(self, e: BaseException) -> None:
        if not isinstance(e, BaseException):
            raise TypeError(e)
        self._set(None, e)

    async def wait(self, *, timeout: ta.Optional[float] = None) -> T:
        if not self._ev.is_set():
            try:
                await self._ev.wait(timeout=timeout)
            except TimeoutError as te:
                # A timeout racing completion is completion.
                if not self._ev.is_set():
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
