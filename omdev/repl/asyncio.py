"""
The asyncio implementations of the package's two runtime seams - the one module here which imports asyncio. Everything
else is written to run the same under any loop, or none.
"""
import asyncio
import typing as ta

from .executors import Executor
from .runners import Runner
from .runners import Running


T = ta.TypeVar('T')


##


class AsyncioThreadExecutor(Executor):
    """
    Each call runs on a thread of the loop's default pool. A cancelled wait calls `interrupt` and leaves the thread to
    notice and finish on its own - the loop never blocks on it.
    """

    async def run(
            self,
            fn: ta.Callable[[], T],
            *,
            interrupt: ta.Callable[[], None] | None = None,
    ) -> T:
        try:
            return await asyncio.to_thread(fn)
        except asyncio.CancelledError:
            if interrupt is not None:
                interrupt()
            raise


##


class AsyncioRunning(Running):
    def __init__(self, future: asyncio.Future) -> None:
        super().__init__()

        self._future = future

    @property
    def future(self) -> asyncio.Future:
        return self._future

    @property
    def done(self) -> bool:
        return self._future.done()

    def cancel(self) -> None:
        self._future.cancel()


class AsyncioRunner(Runner):
    """Each execution is a task on the running loop, tracked until done so `aclose` can cancel the stragglers."""

    def __init__(self) -> None:
        super().__init__()

        self._futures: set[asyncio.Future] = set()
        self._closed = False

    @property
    def num_running(self) -> int:
        return len(self._futures)

    def start(self, fn: ta.Callable[[], ta.Awaitable[None]]) -> Running:
        if self._closed:
            raise RuntimeError('Runner is closed')

        future = asyncio.ensure_future(fn())
        self._futures.add(future)
        future.add_done_callback(self._futures.discard)
        return AsyncioRunning(future)

    async def aclose(self) -> None:
        self._closed = True

        futures = list(self._futures)
        for f in futures:
            f.cancel()
        if futures:
            await asyncio.gather(*futures, return_exceptions=True)
