import asyncio
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .events import FeedEvent


##


@ta.final
@dc.dataclass(frozen=True)
class FeedEntry:
    # Counts from 1, so that 0 can mean 'before everything'.
    seq: int

    event: FeedEvent


class Feed:
    """
    Everything the session has shown, in order: an append-only log of sequence-numbered events which any number of
    readers follow at their own pace, each from a cursor - the last seq it has seen. Nothing is ever dropped, so a
    reader which falls behind, or comes late, misses nothing, and a page reload replays the whole of it.

    Belongs to one event loop, and is not thread-safe.
    """

    def __init__(self) -> None:
        super().__init__()

        self._entries: list[FeedEntry] = []

        self._waiter: asyncio.Future[None] | None = None

    @property
    def last_seq(self) -> int:
        return len(self._entries)

    def append(self, *events: FeedEvent) -> int:
        """Appends the events, waking any reader waiting for them, and returns the last one's seq."""

        for event in events:
            check.isinstance(event, FeedEvent)
            self._entries.append(FeedEntry(len(self._entries) + 1, event))

        if events and (waiter := self._waiter) is not None:
            self._waiter = None
            if not waiter.done():
                waiter.set_result(None)

        return self.last_seq

    def entries_after(self, seq: int) -> ta.Sequence[FeedEntry]:
        check.arg(seq >= 0)

        return self._entries[seq:]

    def changed(self) -> asyncio.Future[None]:
        """
        A future resolved by the next append. Shared between everyone waiting at the same time, so a reader giving up
        on it must not cancel it: `asyncio.wait` on it, with a timeout, leaves it be.
        """

        if (waiter := self._waiter) is None or waiter.done():
            waiter = self._waiter = asyncio.get_running_loop().create_future()
        return waiter
