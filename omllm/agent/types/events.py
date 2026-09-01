import enum
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ... import llm
from .contexts import Context
from .messages import Message
from .states import State
from .tools import Tool
from .tools import ToolContext
from .tools import ToolResult


##


@dc.dataclass(frozen=True)
class Event(lang.Abstract):
    """Explicitly *not* a marshal polymorphism."""


##


@ta.final
@dc.dataclass(frozen=True)
class LlmAiStreamEvent(Event):
    event: llm.AiStreamEvent


##


@ta.final
@dc.dataclass(frozen=True)
class AgentStartEvent(Event):
    pass


class AgentEndReason(enum.Enum):
    COMPLETED = enum.auto()
    FAILED = enum.auto()
    CANCELLED = enum.auto()


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class AgentEndEvent(Event):
    context: Context

    new_messages: ta.Sequence[Message] | None = None

    reason: AgentEndReason = AgentEndReason.COMPLETED
    error: BaseException | None = None


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
    tool: Tool
    context: ToolContext


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ToolExecutionStartEvent(ToolExecutionEvent):
    pass


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
