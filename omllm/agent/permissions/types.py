"""
TODO:
 - move to agent.types.permissions
  - need to figure out _marshal.py deprecation
 - PermissionRequestor lol
"""
import abc
import enum
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh

from ...core import fieldhash as fh


##


class PermissionState(enum.Enum):
    DENY = enum.auto()
    ASK = enum.auto()
    ALLOW = enum.auto()

    def __bool__(self) -> ta.Never:
        raise TypeError('Must not `bool` PermissionStates')


##


PermissionRequestor: ta.TypeAlias = ta.Any


DecidedPermissionState: ta.TypeAlias = ta.Literal[
    PermissionState.DENY,
    PermissionState.ALLOW,
]


@dc.dataclass()
class PermissionDeniedError(Exception):
    target: PermissionTarget


class PermissionDecider(lang.Abstract):
    @abc.abstractmethod
    def decide(
            self,
            requestor: PermissionRequestor,
            target: PermissionTarget,
    ) -> ta.Awaitable[DecidedPermissionState | None]:
        raise NotImplementedError

    @ta.final
    async def is_allowed(self, requestor: PermissionRequestor, target: PermissionTarget) -> bool:
        return (await self.decide(requestor, target)) is PermissionState.ALLOW

    @ta.final
    async def check_allowed(self, requestor: PermissionRequestor, target: PermissionTarget) -> None:
        if not await self.is_allowed(requestor, target):
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


class PermissionAsker(lang.Abstract):
    @abc.abstractmethod
    def ask(
            self,
            requestor: PermissionRequestor,
            target: PermissionTarget,
            rule: PermissionRule,
    ) -> ta.Awaitable[DecidedPermissionState]:
        raise NotImplementedError


##


@msh.register_global_lazy_init
def _install_standard_marshaling(cfgs: msh.ConfigRegistry) -> None:
    for cls in [
        PermissionMatcher,
        PermissionTarget,
    ]:
        msh.install_standard_factories(
            cfgs,
            *msh.standard_polymorphism_factories(
                msh.polymorphism_from_subclasses(
                    cls,
                    naming=msh.Naming.SNAKE,
                    suffix_stripping=msh.SuffixStripping(mode='required'),
                ),
            ),
        )
