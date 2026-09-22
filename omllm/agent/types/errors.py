from omcore import dataclasses as dc

from ... import llm


##


class Error(Exception):
    pass


##


class AgentError(Error):
    pass


class AgentBusyError(AgentError):
    """A prompt, or an exclusive state update, was submitted to an agent still running a previous one."""


##


class ContextCompactionError(AgentError):
    pass


class NoContextCompactorError(ContextCompactionError):
    """Compaction was asked of a lifecycle manager with no compactor to do it."""


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
