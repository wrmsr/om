# ruff: noqa: UP006 UP045
# @om-lite
import asyncio
import typing as ta

from ...asyncio.utils import asyncio_shielded_finally
from ..cancellation import AsyncliteCancellation
from .base import AsyncioAsyncliteApi


##


class AsyncioAsyncliteCancellation(AsyncliteCancellation, AsyncioAsyncliteApi):
    def get_cancelled_exception_types(self) -> ta.Tuple[ta.Type[BaseException], ...]:
        return (asyncio.CancelledError,)

    def cancellation_shielded_finally(
            self,
            fn: ta.Callable[[], ta.Awaitable[ta.Any]],
            *,
            timeout: ta.Optional[float] = None,
    ) -> ta.AsyncContextManager[None]:
        return asyncio_shielded_finally(
            fn,
            timeout=timeout,
        )
