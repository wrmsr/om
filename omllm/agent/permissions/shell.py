import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ...core import fieldhash as fh
from .types import PermissionMatcher
from .types import PermissionTarget


##


@ta.final
@dc.dataclass(frozen=True)
class ShellPermissionTarget(PermissionTarget, lang.Final):
    cmd: str

    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('shell', (
            fh.FieldHashField('cmd', self.cmd),
        ))


@ta.final
@dc.dataclass(frozen=True)
class ShellPermissionMatcher(PermissionMatcher, lang.Final):
    @lang.cached_function
    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('shell', ())

    def match(self, target: PermissionTarget) -> bool:
        return isinstance(target, ShellPermissionTarget)
