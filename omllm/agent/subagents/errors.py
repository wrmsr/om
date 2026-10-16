import typing as ta

from omcore import dataclasses as dc

from ..types.errors import AgentError


##


class SubagentError(AgentError):
    pass


@dc.dataclass()
class UnknownSubagentProfileError(SubagentError):
    profile: str
    known: ta.Sequence[str] = ()


@dc.dataclass()
class UnknownSubagentToolsError(SubagentError):
    """A profile names tools which are not in the pool it is to pick from."""

    profile: str
    tool_names: ta.Sequence[str]
