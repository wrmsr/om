import asyncio

from omdev import minitui as mt

from .promptpump import PromptPump


##


class Shutdown:
    """
    The quit sequence: drain the pump first - cancelling any in-flight turn while the driver is still bound, so the
    abort's cards and marker reach scrollback - then stop the driver. Runs as its own task because `/quit` arrives from
    inside the pump's own task, which cannot await its own teardown.
    """

    def __init__(
            self,
            *,
            pump: PromptPump,
            driver: mt.AsyncioDriver,
    ) -> None:
        super().__init__()

        self._pump = pump
        self._driver = driver

        self._task: asyncio.Task | None = None

    async def _run(self) -> None:
        try:
            await self._pump.aclose()
        finally:
            self._driver.stop()

    def request(self) -> None:
        if self._task is None:
            self._task = asyncio.get_running_loop().create_task(self._run())
