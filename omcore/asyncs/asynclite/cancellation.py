# ruff: noqa: UP006 UP007 UP045
# @om-lite
import abc
import typing as ta

from ...lite.abstract import Abstract
from .base import AsyncliteApi


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
    def cancellation_shielded_finally(
            self,
            fn: ta.Callable[[], ta.Awaitable[ta.Any]],
            *,
            timeout: ta.Optional[float] = None,
    ) -> ta.AsyncContextManager[None]:
        raise NotImplementedError
