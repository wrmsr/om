# ruff: noqa: UP006 UP045
# @om-lite
import asyncio
import time
import typing as ta

from ..cancellation import AsyncliteCancellation
from .base import AsyncioAsyncliteApi


T = ta.TypeVar('T')


##


class AsyncioAsyncliteCancellation(AsyncliteCancellation, AsyncioAsyncliteApi):
    def get_cancelled_exception_types(self) -> ta.Tuple[ta.Type[BaseException], ...]:
        return (asyncio.CancelledError,)

    def is_self_cancelling(self) -> bool:
        try:
            task = asyncio.current_task()
        except RuntimeError:  # no running event loop
            return False
        if task is None:
            return False

        # Cancellation requests are only counted from 3.11 on. Before that there is no telling a task's own cancellation
        # from a stray one, and every cancellation error is taken as the task's own.
        if (cancelling := getattr(task, 'cancelling', None)) is None:
            return True
        return cancelling() > 0

    async def cancellation_shield(
            self,
            fn: ta.Callable[[], ta.Awaitable[T]],
            *,
            timeout: ta.Optional[float] = None,
    ) -> T:
        task = asyncio.ensure_future(fn())

        deadline = time.monotonic() + timeout if timeout is not None else None

        # The first cancellation to arrive is kept, to be raised once the task is done. Any after it are dropped here -
        # the current task's cancellation count still reflects each of them.
        cancelled: ta.Optional[BaseException] = None
        timed_out = False

        while not task.done():
            remaining: ta.Optional[float] = None
            if deadline is not None and not timed_out:
                remaining = max(deadline - time.monotonic(), 0.)

            try:
                await asyncio.wait([task], timeout=remaining)
            except asyncio.CancelledError as e:
                if cancelled is None:
                    cancelled = e
                continue

            if not task.done() and not timed_out:
                timed_out = True
                task.cancel()

        if cancelled is not None:
            raise cancelled

        if timed_out:
            raise TimeoutError

        return task.result()
