import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ...types.lifecycle import UsageLedger
from ...types.messages import Message
from ...types.tools import ToolResultDetails
from ...types.turns import AgentEndReason
from ..types import SubagentRunId


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class SubagentToolResultDetails(ToolResultDetails, lang.Final):
    run_id: SubagentRunId
    profile: str

    reason: AgentEndReason
    num_turns: int

    usage: UsageLedger | None = None

    # The subagent's transcript, for a frontend which wants to show it. Not persisted anywhere: the parent's session
    # records the parent's transcript, in which the subagent is one tool call and its result.
    messages: ta.Sequence[Message] = ()
