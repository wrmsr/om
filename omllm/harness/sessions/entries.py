import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from ... import agent as agn


##


@dc.dataclass(frozen=True)
@msh.set_polymorphic(source='manifests', naming=msh.Naming.SNAKE, suffix_stripping='required')
class SessionEntry(lang.Abstract, lang.Sealed):
    pass


##


# @om-manifest omcore.marshal.SubtypeManifest(base='$.harness.sessions.entries.SessionEntry')
@ta.final
@dc.dataclass(frozen=True)
class MessageSessionEntry(SessionEntry):
    message: agn.Message
