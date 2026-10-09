import asyncio


##


class AsyncioNotifier:
    """
    Wakes everything waiting on it at each notification. A waiter passes the generation it observed before checking its
    condition, so a notification arriving between the check and the wait is never lost.
    """

    def __init__(self) -> None:
        super().__init__()

        self._generation = 0
        self._waiters: set[asyncio.Future[None]] = set()

    @property
    def generation(self) -> int:
        return self._generation

    def notify(self) -> None:
        self._generation += 1
        waiters, self._waiters = self._waiters, set()
        for f in waiters:
            if not f.done():
                f.set_result(None)

    async def wait(self, generation: int, deadline: float | None) -> None:
        """Return once notified after `generation`, raising TimeoutError at `deadline` (in event loop time)."""

        if self._generation != generation:
            return

        fut: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._waiters.add(fut)
        try:
            if deadline is None:
                await fut
            else:
                async with asyncio.timeout_at(deadline):
                    await fut

        finally:
            self._waiters.discard(fut)
            if not fut.done():
                fut.cancel()
