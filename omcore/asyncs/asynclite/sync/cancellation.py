# ruff: noqa: UP006 UP045
# @om-lite
import typing as ta

from ..cancellation import AsyncliteCancellation
from .base import SyncAsyncliteApi


##


class SyncAsyncliteCancellation(AsyncliteCancellation, SyncAsyncliteApi):
    def get_cancelled_exception_types(self) -> ta.Tuple[ta.Type[BaseException], ...]:
        return ()

    def cancellation_shielded_finally(
            self,
            fn: ta.Callable[[], ta.Awaitable[ta.Any]],
            *,
            timeout: ta.Optional[float] = None,
    ) -> ta.AsyncContextManager[None]:
        raise NotImplementedError
