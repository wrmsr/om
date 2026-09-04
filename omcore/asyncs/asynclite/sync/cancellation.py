# ruff: noqa: UP006 UP045
# @om-lite
import typing as ta

from ..cancellation import AsyncliteCancellation
from .base import SyncAsyncliteApi


T = ta.TypeVar('T')


##


class SyncAsyncliteCancellation(AsyncliteCancellation, SyncAsyncliteApi):
    def get_cancelled_exception_types(self) -> ta.Tuple[ta.Type[BaseException], ...]:
        return ()

    def is_self_cancelling(self) -> bool:
        return False

    def cancellation_shield(
            self,
            fn: ta.Callable[[], ta.Awaitable[T]],
            *,
            timeout: ta.Optional[float] = None,
    ) -> ta.Awaitable[T]:
        raise NotImplementedError
