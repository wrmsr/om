import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ... import agent as agn


##


@dc.dataclass(frozen=True)
class SessionEvent(lang.Abstract, lang.PackageSealed, sealed_package='.'.join(__package__.split('.')[:2])):
    """Explicitly *not* a marshal polymorphism."""


##


@ta.final
@dc.dataclass(frozen=True)
class AgentSessionEvent(SessionEvent):
    event: agn.Event
