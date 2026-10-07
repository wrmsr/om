"""
Where repl code runs relative to where its connection is served: the same context (the default), or another - a host
application's event loop, so that the manhole's python can await the host's coroutines and touch its loop-bound objects
from a connection served on a thread of its own. The seam is loop-neutral; `asyncio.py` has the cross-loop
implementation.
"""
import abc
import typing as ta

from omcore import lang


T = ta.TypeVar('T')


##


class Dispatcher(lang.Abstract):
    @abc.abstractmethod
    def dispatch(self, fn: ta.Callable[[], ta.Awaitable[T]]) -> ta.Awaitable[T]:
        """Run `fn` where the code should run and await its result here."""

        raise NotImplementedError


class InlineDispatcher(Dispatcher):
    """Runs the code right here, in the serving context."""

    def dispatch(self, fn: ta.Callable[[], ta.Awaitable[T]]) -> ta.Awaitable[T]:
        return fn()
