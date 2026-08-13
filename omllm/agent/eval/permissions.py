import enum
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ...core import fieldhash as fh
from ..permissions.types import PermissionMatcher
from ..permissions.types import PermissionTarget


##


class EvalLanguage(enum.StrEnum):
    JS = 'js'


# @om-manifest omcore.marshal.SubtypeManifest(base='$.agent.permissions.types.PermissionTarget')
@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class EvalPermissionTarget(PermissionTarget, lang.Final):
    language: EvalLanguage
    code: str

    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('eval', (
            fh.FieldHashField('langauge', self.language.value),
            fh.FieldHashField('code', tuple(self.code)),
        ))


# @om-manifest omcore.marshal.SubtypeManifest(base='$.agent.permissions.types.PermissionMatcher')
@ta.final
@dc.dataclass(frozen=True)
class EvalPermissionMatcher(PermissionMatcher, lang.Final):
    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('eval', ())

    def match(self, target: PermissionTarget) -> bool:
        return isinstance(target, EvalPermissionTarget)
