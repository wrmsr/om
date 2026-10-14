"""
Pointer-motion coalescing. With any-event tracking on, one read of the input can carry a run of motion reports - one per
cell a quick sweep crossed - and only where the pointer ended up matters to a hover.
"""
import typing as ta

from .types import Event
from .types import MouseEvent
from .types import MouseEventKind


##


def coalesce_mouse_motion(events: ta.Iterable[Event]) -> ta.Iterator[Event]:
    """
    `events` with each run of consecutive motion events collapsed to its last. Anything else flushes the run ahead of
    itself, so ordering against clicks and keys holds exactly.
    """

    pending: Event | None = None
    for event in events:
        if isinstance(event, MouseEvent) and event.kind is MouseEventKind.MOVE:
            pending = event
            continue
        if pending is not None:
            yield pending
            pending = None
        yield event
    if pending is not None:
        yield pending
