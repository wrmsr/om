from omcore import dataclasses as dc

from ... import llm


##


class AgentError(Exception):
    pass


class AgentBusyError(AgentError):
    """A prompt was submitted to an agent still running a previous one."""


##


class TurnError(AgentError):
    pass


@dc.dataclass()
class UnknownToolError(TurnError):
    tool_name: str


@dc.dataclass()
class ErrorStopReasonError(TurnError):
    """The model ended its output with an error stop reason - a refusal, a content filter - rather than a result."""

    message: llm.AiMessage
