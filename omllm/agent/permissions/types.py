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


if ta.TYPE_CHECKING:
    from ..types.tools import ToolContext


##


class PermissionState(enum.Enum):
    DENY = enum.auto()
    ASK = enum.auto()
    ALLOW = enum.auto()

    def __bool__(self) -> ta.Never:
        raise TypeError('Must not `bool` PermissionStates')


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class PermissionRequestor:
    tool_context: ToolContext | None = None


DecidedPermissionState: ta.TypeAlias = ta.Literal[
    PermissionState.DENY,
    PermissionState.ALLOW,
]


##


@dc.dataclass()
class PermissionDeniedError(Exception):
    target: PermissionTarget


@dc.dataclass()
class PermissionAskAbortedError(Exception):
    """
    An ask could not be answered: the asker withdrew it - the surface presenting it went away, or its turn ended - while
    the requesting tool was still live. Tools treat it as an execution error: it is neither a denial nor a cancellation.
    """

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
@msh.set_polymorphic(source='manifests', naming='snake', suffix_stripping='required')
class PermissionTarget(
    fh.FieldHashable,
    lang.Abstract,
    lang.PackageSealed,
    sealed_package='.'.join(__package__.split('.')[:2]),
):
    pass


##


@ta.final
@dc.dataclass(frozen=True)
class PermissionMatchContext:
    target: PermissionTarget

    _: dc.KW_ONLY

    requestor: PermissionRequestor | None = None


@msh.set_polymorphic(source='manifests', naming='snake', suffix_stripping='required')
class PermissionMatcher(
    fh.FieldHashable,
    lang.Abstract,
    lang.PackageSealed,
    sealed_package='.'.join(__package__.split('.')[:2]),
):
    @abc.abstractmethod
    def match(self, ctx: PermissionMatchContext) -> bool:
        raise NotImplementedError


##


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


##


class PermissionAsker(lang.Abstract):
    """
    Resolves an ASK rule into a decision by consulting someone - a user at a terminal, a policy service.

    Contract for implementations. Every ask must be resolved, in exactly one of three ways: `ask` returns a decision; it
    raises `PermissionAskAbortedError` because the ask can no longer be answered (the surface presenting it went away,
    its turn ended); or it unwinds because the *requesting task itself* was cancelled. An asker must never inject a
    cancellation error into a live requesting task that did not ask to be cancelled - the turn loop cannot tell that
    apart from the user cancelling the turn, and would report the turn CANCELLED and drop its messages. Withdraw with
    `PermissionAskAbortedError` instead.
    """

    @abc.abstractmethod
    def ask(
            self,
            requestor: PermissionRequestor,
            target: PermissionTarget,
            rule: PermissionRule,
    ) -> ta.Awaitable[DecidedPermissionState]:
        raise NotImplementedError
