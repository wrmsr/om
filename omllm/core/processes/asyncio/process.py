"""The asyncio `Process` handle: `BaseProcess` plus how to get from the exit-watcher thread back onto the loop."""
import asyncio
import typing as ta

from ..managers.process import BaseProcess


##


class AsyncioProcess(BaseProcess):
    def __init__(self, *, loop: asyncio.AbstractEventLoop, **kwargs: ta.Any) -> None:
        super().__init__(**kwargs)

        self._loop = loop

    def _post_threadsafe(self, fn: ta.Callable, *args: ta.Any) -> None:
        # Raises RuntimeError once the loop is closed - which is what the watcher expects.
        self._loop.call_soon_threadsafe(fn, *args)
