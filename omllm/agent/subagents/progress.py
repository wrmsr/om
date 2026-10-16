"""
How a subagent's events reach whoever is watching its parent: wrapped, as progress of the tool call which spawned it. A
subagent's events must never land raw on the parent's bus - a session on the parent stores every message announced
there and resets its count on every run start, so a child's run would be recorded as the parent's own.
"""
import typing as ta

from omcore import dataclasses as dc

from ..types.events import Event
from ..types.progress import ToolProgressSink
from ..types.progress import ToolProgressUpdate
from .profiles import SubagentProfile
from .types import SubagentRunId


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class SubagentEventToolProgressUpdate(ToolProgressUpdate):
    run_id: SubagentRunId

    # The profile's name: for display, which is all this update is for.
    profile: str

    # The subagent's own event, verbatim.
    event: Event


##


class SubagentEventRelay:
    """A subscriber to a subagent's bus, reporting each of its events to the parent's progress sink."""

    def __init__(
            self,
            *,
            progress: ToolProgressSink,
            run_id: SubagentRunId,
            profile: SubagentProfile,
    ) -> None:
        super().__init__()

        self._progress = progress
        self._run_id = run_id
        self._profile = profile

    async def __call__(self, event: Event) -> None:
        await self._progress.report(SubagentEventToolProgressUpdate(
            run_id=self._run_id,
            profile=self._profile.name,
            event=event,
        ))
