import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ... import llm
from .contexts import Context
from .messages import Message
from .states import State


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


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class AgentEndEvent(Event):
    context: Context

    new_messages: ta.Sequence[Message] | None = None


##


@ta.final
@dc.dataclass(frozen=True)
class TurnStartEvent(Event):
    pass


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class TurnEndEvent(Event):
    message: Message


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class StateUpdateEvent(Event):
    new_state: State
    old_state: State
