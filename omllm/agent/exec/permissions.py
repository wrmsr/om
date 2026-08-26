import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ...core import fieldhash as fh
from ..permissions.types import PermissionMatchContext
from ..permissions.types import PermissionMatcher
from ..permissions.types import PermissionTarget


##


# @om-manifest omcore.marshal.SubtypeManifest(base='$.agent.permissions.types.PermissionTarget')
@ta.final
@dc.dataclass(frozen=True)
class ExecPermissionTarget(PermissionTarget, lang.Final):
    cmd: lang.SequenceNotStr[str]

    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('exec', (
            fh.FieldHashField('cmd', tuple(self.cmd)),
        ))


# @om-manifest omcore.marshal.SubtypeManifest(base='$.agent.permissions.types.PermissionMatcher')
@ta.final
@dc.dataclass(frozen=True)
class ExecPermissionMatcher(PermissionMatcher, lang.Final):
    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('exec', ())

    def match(self, ctx: PermissionMatchContext) -> bool:
        return isinstance(ctx.target, ExecPermissionTarget)
