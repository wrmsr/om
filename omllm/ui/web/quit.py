import asyncio

from ...core import ui
from .feed import events as fe
from .feed.feed import Feed


##


class WebQuitSignal(ui.QuitSignal):
    """
    Quitting is asked for here - by `/quit`, in the main - and done by whoever waits on it: the frontend's main, which
    winds the session down and then `announce`s its end, the last thing the feed carries.

    Streams of submissions ending once quitting has been asked for go on through that announcement, rather than ending
    with their submissions, so that the stream of the `/quit` which asked carries the news back.
    """

    def __init__(self, *, feed: Feed) -> None:
        super().__init__()

        self._feed = feed

        self._event = asyncio.Event()
        self._announced = asyncio.Event()

    @property
    def is_set(self) -> bool:
        return self._event.is_set()

    async def quit(self) -> None:
        self._event.set()

    async def wait(self) -> None:
        await self._event.wait()

    def announce(self) -> None:
        """Tells the pages the session has ended, once, however many ways it ends."""

        if not self._announced.is_set():
            self._event.set()
            self._announced.set()
            self._feed.append(fe.ShutdownFeedEvent())

    async def wait_announced(self) -> None:
        await self._announced.wait()
