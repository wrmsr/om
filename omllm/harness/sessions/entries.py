import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from ... import agent as agn


##


@dc.dataclass(frozen=True)
@msh.set_polymorphic_from_subclasses(naming=msh.Naming.SNAKE, suffix_stripping=msh.SuffixStripping.REQUIRED)
class SessionEntry(lang.Abstract, lang.Sealed):
    pass


##


@ta.final
@dc.dataclass(frozen=True)
class MessageSessionEntry(SessionEntry):
    message: agn.Message
