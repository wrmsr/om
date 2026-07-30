"""
TODO:
 - move to agent.types.permissions
  - need to figure out _marshal.py deprecation
"""
import abc
import enum
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ...core import fieldhash as fh


##


class PermissionState(enum.Enum):
    DENY = enum.auto()
    ASK = enum.auto()
    ALLOW = enum.auto()


DecidedPermissionState: ta.TypeAlias = ta.Literal[
    PermissionState.DENY,
    PermissionState.ALLOW,
]


@dc.dataclass()
class PermissionDeniedError(Exception):
    target: PermissionTarget


class PermissionDecider(lang.Abstract):
    @abc.abstractmethod
    def decide(self, target: PermissionTarget) -> ta.Awaitable[DecidedPermissionState | None]:
        raise NotImplementedError

    @ta.final
    async def is_allowed(self, target: PermissionTarget) -> bool:
        return (await self.decide(target)) is PermissionState.ALLOW

    @ta.final
    async def check_allowed(self, target: PermissionTarget) -> None:
        if not await self.is_allowed(target):
            raise PermissionDeniedError(target)


##


@dc.dataclass(frozen=True)
class PermissionTarget(fh.FieldHashable, lang.Abstract, lang.PackageSealed):
    pass


class PermissionMatcher(fh.FieldHashable, lang.Abstract):
    @abc.abstractmethod
    def match(self, target: PermissionTarget) -> bool:
        raise NotImplementedError


@ta.final
@dc.dataclass(frozen=True)
class PermissionRule(fh.FieldHashable, lang.Final):
    matcher: PermissionMatcher = dc.xfield(check_type=True)
    result: PermissionState = dc.xfield(check_type=True)

    def _field_hash(self) -> fh.FieldHashValue:
        return fh.FieldHashObject('rule', (
            fh.FieldHashField('matcher', self.matcher),
            fh.FieldHashField('result', self.result.name),
        ))
