import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from ...core import fieldhash as fh
from ..permissions.types import PermissionMatchContext
from ..permissions.types import PermissionMatcher
from ..permissions.types import PermissionTarget


##


# @om-manifest omcore.marshal.SubtypeManifest(base='$.agent.permissions.types.PermissionTarget')
@ta.final
@dc.dataclass(frozen=True)
class SubagentPermissionTarget(PermissionTarget, lang.Final):
    """Spawning a subagent of the given profile."""

    profile: str

    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('subagent', (
            fh.FieldHashField('profile', self.profile),
        ))


# @om-manifest omcore.marshal.SubtypeManifest(base='$.agent.permissions.types.PermissionMatcher')
@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class SubagentPermissionMatcher(PermissionMatcher, lang.Final):
    """Matches spawning a subagent - of any profile, or of the one named."""

    profile: str | None = dc.xfield(None) | msh.dc_field_options(omit_if=lang.is_none)

    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('subagent', (
            fh.FieldHashField('profile', self.profile),
        ))

    def match(self, ctx: PermissionMatchContext) -> bool:
        if not isinstance(target := ctx.target, SubagentPermissionTarget):
            return False

        return self.profile is None or target.profile == self.profile
