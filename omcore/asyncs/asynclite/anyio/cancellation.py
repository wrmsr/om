# ruff: noqa: UP006 UP045
import typing as ta

import anyio

from ..cancellation import AsyncliteCancellation
from .base import AnyioAsyncliteApi


##


class AnyioAsyncliteCancellation(AsyncliteCancellation, AnyioAsyncliteApi):
    def get_cancelled_exception_types(self) -> ta.Tuple[ta.Type[BaseException], ...]:
        return (anyio.get_cancelled_exc_class(),)

    def cancellation_shielded_finally(
            self,
            fn: ta.Callable[[], ta.Awaitable[ta.Any]],
            *,
            timeout: ta.Optional[float] = None,
    ) -> ta.AsyncContextManager[None]:
        raise NotImplementedError
