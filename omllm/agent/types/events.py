import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from ... import llm
from .contexts import Context
from .messages import Message
from .progress import ToolProgressUpdate
from .states import State
from .tools import Tool
from .tools import ToolContext
from .tools import ToolResult
from .turns import AgentEndReason


##


@dc.dataclass(frozen=True)
class Event(lang.Abstract):
    """Explicitly *not* a marshal polymorphism."""


##


@ta.final
@dc.dataclass(frozen=True)
class LlmAiStreamEvent(Event):
    event: llm.AiStreamEvent


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class LlmRetryEvent(Event):
    """Published between a transiently failed LLM call and its retry, ahead of the backoff delay."""

    # The number of attempts made so far, counting the one which just failed.
    attempts: int

    delay_s: float

    error: BaseException


##


@ta.final
@dc.dataclass(frozen=True)
class AgentStartEvent(Event):
    pass


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class AgentEndEvent(Event):
    context: Context

    # Everything the run appended, the prompt included, in order.
    new_messages: ta.Sequence[Message] = ()

    reason: AgentEndReason = AgentEndReason.COMPLETED
    error: BaseException | None = None


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class MessageAddedEvent(Event):
    """
    A message appended to the run's transcript, announced as it lands. What an interrupted run appends on its way out -
    the results of tool calls which completed as their batch was cancelled, and the repair messages - is not announced
    this way, that path being deliberately synchronous, and reaches subscribers only through the terminal event's
    `new_messages`.
    """

    message: Message

    # Its position in the run's `new_messages`, so a subscriber storing as it goes can take the terminal event's tail.
    index: int


##


@dc.dataclass(frozen=True)
class TurnEvent(Event, lang.Abstract):
    pass


@ta.final
@dc.dataclass(frozen=True)
class TurnStartEvent(TurnEvent):
    pass


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class TurnEndEvent(TurnEvent):
    message: Message


##


@dc.dataclass(frozen=True, kw_only=True)
class ToolExecutionEvent(Event, lang.Abstract):
    # None when the model called a tool the context does not have: the call is still surfaced, and gets an error
    # result, but there is no tool to name here.
    tool: Tool | None
    context: ToolContext

    @property
    def tool_name(self) -> str:
        if (tool := self.tool) is not None:
            return tool.name
        return check.not_none(self.context.llm_tool_call).name


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ToolExecutionStartEvent(ToolExecutionEvent):
    pass


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ToolExecutionUpdateEvent(ToolExecutionEvent):
    update: ToolProgressUpdate


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ToolExecutionEndEvent(ToolExecutionEvent):
    result: ToolResult


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class StateUpdateEvent(Event):
    new_state: State
    old_state: State
