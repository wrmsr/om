# ruff: noqa: UP007
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from ... import llm


##


@dc.dataclass(frozen=True)
@msh.set_polymorphic(naming='snake', suffix_stripping='required')
class AgentMessage(lang.Abstract, lang.Sealed):
    pass


##


type Message = ta.Union[
    llm.Message,
    AgentMessage,
]


MESSAGE_TYPES: ta.Final[tuple[type[Message], ...]] = (
    llm.Message,
    AgentMessage,
)


##


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True, terse_repr=True)
class InfoAgentMessage(AgentMessage):
    info: str
