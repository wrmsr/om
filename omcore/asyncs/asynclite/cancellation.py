# ruff: noqa: UP006 UP007 UP045
# @om-lite
import abc
import typing as ta

from ...lite.abstract import Abstract
from .base import AsyncliteApi


T = ta.TypeVar('T')


##


class AsyncliteCancellation(AsyncliteApi, Abstract):
    @abc.abstractmethod
    def get_cancelled_exception_types(self) -> ta.Tuple[ta.Type[BaseException], ...]:
        raise NotImplementedError

    def is_cancelled_exception(self, ex: ta.Union[BaseException, ta.Type[BaseException]]) -> bool:
        if isinstance(ex, type):
            return issubclass(ex, self.get_cancelled_exception_types())
        else:
            return isinstance(ex, self.get_cancelled_exception_types())

    @abc.abstractmethod
    def is_self_cancelling(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def cancellation_shield(
            self,
            fn: ta.Callable[[], ta.Awaitable[T]],
            *,
            timeout: ta.Optional[float] = None,
    ) -> ta.Awaitable[T]:
        raise NotImplementedError
