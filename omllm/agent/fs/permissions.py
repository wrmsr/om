import glob
import re
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from ...core import fieldhash as fh
from ..permissions.types import PermissionMatchContext
from ..permissions.types import PermissionMatcher
from ..permissions.types import PermissionTarget


##


FsPermissionMode: ta.TypeAlias = ta.Literal['r', 'w']

FS_TOOL_PERMISSION_MODES: ta.Sequence[FsPermissionMode] = ('r', 'w')


# @om-manifest omcore.marshal.SubtypeManifest(base='$.agent.permissions.types.PermissionTarget')
@ta.final
@dc.dataclass(frozen=True)
class FsPermissionTarget(PermissionTarget, lang.Final):
    path: str

    mode: FsPermissionMode

    @dc.validate
    def _validate_mode(self) -> bool:
        return self.mode in FS_TOOL_PERMISSION_MODES

    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('fs', (
            fh.FieldHashField('path', self.path),
            fh.FieldHashField('mode', self.mode),
        ))


# @om-manifest omcore.marshal.SubtypeManifest(base='$.agent.permissions.types.PermissionMatcher')
@ta.final
@dc.dataclass(frozen=True)
class GlobFsPermissionMatcher(PermissionMatcher, lang.Final):
    glob: str

    modes: ta.Container[FsPermissionMode] | None = dc.xfield(
        default=None,
    ) | dc.with_extra_field_params(
        coerce=lambda v: tuple(sorted({check.in_(m.lower(), FS_TOOL_PERMISSION_MODES) for m in v})) if v is not None else None,  # noqa
    ) | msh.dc_field_options(
        omit_if=lang.is_none,
        marshal_via=msh.MarshalVia(ta.Sequence[FsPermissionMode] | None),
        unmarshal_via=msh.UnmarshalVia(ta.Sequence[FsPermissionMode] | None),
    )

    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('glob_fs', (
            fh.FieldHashField('glob', self.glob),
            fh.FieldHashField('modes', check.isinstance(self.modes, tuple) if self.modes is not None else None),
        ))

    @lang.cached_function
    def compiled_glob_pats(self) -> ta.Sequence[re.Pattern]:
        pats = [
            re.compile(glob.translate(
                self.glob,
                recursive=True,
                include_hidden=True,
            )),
        ]

        if self.glob.endswith('/**'):
            pats.append(re.compile(glob.translate(
                self.glob[:-3],
                recursive=True,
                include_hidden=True,
            )))

        return tuple(pats)

    def match(self, ctx: PermissionMatchContext) -> bool:
        if not isinstance(target := ctx.target, FsPermissionTarget):
            return False

        return (
            any(p.fullmatch(target.path) is not None for p in self.compiled_glob_pats()) and
            (self.modes is None or target.mode in self.modes)
        )
