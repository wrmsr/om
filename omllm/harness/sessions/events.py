import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ... import agent as agn


##


@dc.dataclass(frozen=True)
class SessionEvent(lang.Abstract):
    pass


##


@ta.final
@dc.dataclass(frozen=True)
class AgentSessionEvent(SessionEvent):
    event: agn.Event
