# ruff: noqa: UP045
# @om-lite
import abc
import typing as ta

from ...lite.abstract import Abstract
from ...lite.maybes import Maybe
from .base import AsyncliteApi
from .base import AsyncliteObject


T = ta.TypeVar('T')


##


class AsynclitePromiseError(Exception):
    pass


class AsynclitePromiseAlreadySetError(AsynclitePromiseError):
    pass


class AsynclitePromiseWaitTimeoutError(AsynclitePromiseError, TimeoutError):
    pass


class AsynclitePromise(AsyncliteObject, Abstract, ta.Generic[T]):
    """
    A one-shot, write-once result cell - one producer, any number of waiters. Waiter-side timeouts and cancellation
    only ever affect that waiter - never the promise itself or any other waiter.
    """

    @abc.abstractmethod
    def is_done(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def poll(self) -> Maybe[T]:
        """Never blocks - empty while pending, otherwise the value, raising if the promise was set to an error."""

        raise NotImplementedError

    @abc.abstractmethod
    def set_value(self, v: T) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def set_error(self, e: BaseException) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def wait(self, *, timeout: ta.Optional[float] = None) -> ta.Awaitable[T]:
        raise NotImplementedError


class AsynclitePromises(AsyncliteApi, Abstract):
    @abc.abstractmethod
    def make_promise(self) -> AsynclitePromise:
        raise NotImplementedError
