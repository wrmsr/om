import typing as ta
import uuid

from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from ... import agent as agn


##


@dc.dataclass(frozen=True)
@msh.set_polymorphic(source='manifests', naming='snake', suffix_stripping='required')
class SessionEntry(lang.Abstract, lang.PackageSealed, sealed_package='.'.join(__package__.split('.')[:2])):
    _: dc.KW_ONLY

    id: uuid.UUID = dc.xfield(default_factory=uuid.uuid7, repr_priority=-10)


##


# @om-manifest omcore.marshal.SubtypeManifest(base='$.harness.sessions.entries.SessionEntry')
@ta.final
@dc.dataclass(frozen=True)
class MessageSessionEntry(SessionEntry):
    message: agn.Message
