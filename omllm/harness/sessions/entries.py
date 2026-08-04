import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ... import agent as agn


##


@dc.dataclass(frozen=True)
class SessionEntry(lang.Abstract, lang.Sealed):
    pass


##


@ta.final
@dc.dataclass(frozen=True)
class MessageSessionEntry(SessionEntry):
    message: agn.Message
