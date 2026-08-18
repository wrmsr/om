import asyncio
import typing as ta

from ..spool.spool import SpoolNotifier


##


class AsyncioSpoolNotifier(SpoolNotifier):
    """Broadcast wake-up: a version counter plus one shared future replaced on every notify. Loop-thread only."""

    def __init__(self, loop: asyncio.AbstractEventLoop | None = None) -> None:
        super().__init__()

        self._loop = loop
        self._fut: asyncio.Future[None] | None = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if (loop := self._loop) is None:
            loop = self._loop = asyncio.get_running_loop()
        return loop

    def notify(self) -> None:
        if (fut := self._fut) is not None:
            self._fut = None
            if not fut.done():
                fut.set_result(None)

    async def wait(self, timeout: float | None) -> bool:
        if (fut := self._fut) is None:
            fut = self._fut = self._get_loop().create_future()
        if timeout is None:
            await asyncio.shield(fut)
            return True
        try:
            await asyncio.wait_for(asyncio.shield(fut), timeout)
        except TimeoutError:
            return False
        return True

    def notify_threadsafe(self) -> None:
        self._get_loop().call_soon_threadsafe(self.notify)


class ImmediateSpoolNotifier(SpoolNotifier):
    """For synchronous tests: never blocks."""

    def notify(self) -> None:
        pass

    async def wait(self, timeout: float | None) -> bool:
        return False


NULL_SPOOL_NOTIFIER: ta.Final = ImmediateSpoolNotifier()
