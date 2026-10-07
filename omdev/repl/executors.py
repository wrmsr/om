"""
Where an interpreter's blocking work runs: inline on the caller, or off on a thread the caller waits for. The seam is
loop-neutral; the asyncio implementation lives in `asyncio.py`, and a host with its own job infrastructure (a pool, a
runner with timeouts) adapts it to this interface rather than the other way round.
"""
import abc
import typing as ta

from omcore import lang


T = ta.TypeVar('T')


##


class Executor(lang.Abstract):
    @abc.abstractmethod
    def run(
            self,
            fn: ta.Callable[[], T],
            *,
            interrupt: ta.Callable[[], None] | None = None,
    ) -> ta.Awaitable[T]:
        """
        Run `fn` and await its value. `interrupt`, when given, is what to call should the caller stop waiting - a
        cancellation, a timeout - so a `fn` that can be stopped (an engine with an interrupt flag) is.
        """

        raise NotImplementedError


class ImmediateExecutor(Executor):
    """
    Runs the work inline, on the caller's own thread, and hands back an already-complete awaitable. Nothing is ever
    interrupted, since nothing is ever waited for. The default: correct under any loop and under `lang.sync_await`.
    """

    def run(
            self,
            fn: ta.Callable[[], T],
            *,
            interrupt: ta.Callable[[], None] | None = None,
    ) -> ta.Awaitable[T]:
        async def inner() -> T:
            return fn()

        return inner()
