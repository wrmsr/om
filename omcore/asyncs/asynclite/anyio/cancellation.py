# ruff: noqa: UP045
import typing as ta

import anyio

from ..cancellation import AsyncliteCancellation
from .base import AnyioAsyncliteApi


T = ta.TypeVar('T')


##


class AnyioAsyncliteCancellation(AsyncliteCancellation, AnyioAsyncliteApi):
    def get_cancelled_exception_types(self) -> tuple[type[BaseException], ...]:
        return (anyio.get_cancelled_exc_class(),)

    def is_self_cancelling(self) -> bool:
        raise NotImplementedError

    def cancellation_shield(
            self,
            fn: ta.Callable[[], ta.Awaitable[T]],
            *,
            timeout: float | None = None,
    ) -> ta.Awaitable[T]:
        raise NotImplementedError
