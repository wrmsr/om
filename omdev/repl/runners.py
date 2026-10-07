"""
How a frontend starts an execution from inside a synchronous event handler - a key press - and keeps hold of it. Like
the executors this is a loop-neutral seam: the asyncio implementation makes a task, and the immediate one drives the
execution to completion on the spot, for frontends with no loop at all and for tests.
"""
import abc
import typing as ta

from omcore import lang


##


class Running(lang.Abstract):
    """A handle on a started execution."""

    @property
    @abc.abstractmethod
    def done(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def cancel(self) -> None:
        raise NotImplementedError


class Runner(lang.Abstract):
    @abc.abstractmethod
    def start(self, fn: ta.Callable[[], ta.Awaitable[None]]) -> Running:
        raise NotImplementedError

    async def aclose(self) -> None:
        """Cancel whatever is still running and wait for it. Idempotent."""

    async def __aenter__(self) -> ta.Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()


##


class _DoneRunning(Running):
    @property
    def done(self) -> bool:
        return True

    def cancel(self) -> None:
        pass


class ImmediateRunner(Runner):
    """
    Runs the execution to completion before returning (`lang.sync_await`): sources which actually await something fail
    there, as they should with no loop to await on.
    """

    def start(self, fn: ta.Callable[[], ta.Awaitable[None]]) -> Running:
        lang.sync_await(fn())
        return _DoneRunning()
