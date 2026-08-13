import re
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from ...core import fieldhash as fh
from ..permissions.types import PermissionMatcher
from ..permissions.types import PermissionTarget


##


# @om-manifest omcore.marshal.SubtypeManifest(base='$.agent.permissions.types.PermissionTarget')
@ta.final
@dc.dataclass(frozen=True)
class UrlPermissionTarget(PermissionTarget, lang.Final):
    url: str

    _: dc.KW_ONLY

    method: str | None = None

    @dc.validate
    def _validate_method(self) -> bool:
        return (m := self.method) is None or (bool(m) and m.isupper())

    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('url', (
            fh.FieldHashField('url', self.url),
            fh.FieldHashField('method', self.method),
        ))


# @om-manifest omcore.marshal.SubtypeManifest(base='$.agent.permissions.types.PermissionMatcher')
@ta.final
@dc.dataclass(frozen=True)
class RegexUrlPermissionMatcher(PermissionMatcher, lang.Final):
    pat: str

    _: dc.KW_ONLY

    methods: ta.Container[str] | None = dc.xfield(
        default=None,
    ) | dc.with_extra_field_params(
        coerce=lambda v: tuple(sorted({check.non_empty_str(m).upper() for m in v})) if v is not None else None,
    ) | msh.dc_field_options(
        omit_if=lang.is_none,
        marshal_via=msh.MarshalVia(ta.Sequence[str] | None),
        unmarshal_via=msh.UnmarshalVia(ta.Sequence[str] | None),
    )

    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('regex_url', (
            fh.FieldHashField('pat', self.pat),
            fh.FieldHashField('methods', check.isinstance(self.methods, tuple) if self.methods is not None else None),
        ))

    @lang.cached_function
    def compiled_pat(self) -> re.Pattern:
        return re.compile(self.pat)

    def match(self, target: PermissionTarget) -> bool:
        if not isinstance(target, UrlPermissionTarget):
            return False

        return (
            self.compiled_pat().fullmatch(target.url) is not None and
            (self.methods is None or (target.method is not None and target.method in self.methods))
        )
