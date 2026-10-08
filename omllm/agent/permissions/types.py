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
from ...core import ui
from ..types.errors import Error


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


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class PermissionRequest:
    """
    One request for permission, as handed to a decider and on to whoever it asks. The requestor and target are what
    rules match on; the preview is only ever shown.
    """

    requestor: PermissionRequestor
    target: PermissionTarget

    _: dc.KW_ONLY

    # A frontend-neutral account of what granting the request would do - the diff a write would make, say - for whoever
    # is asked to decide it. Never consulted by matching.
    preview: ui.Text | None = None


DecidedPermissionState: ta.TypeAlias = ta.Literal[
    PermissionState.DENY,
    PermissionState.ALLOW,
]


##


@dc.dataclass()
class PermissionDeniedError(Error):
    target: PermissionTarget


@dc.dataclass()
class PermissionAskAbortedError(Error):
    """
    An ask could not be answered: the asker withdrew it - the surface presenting it went away, or its turn ended - while
    the requesting tool was still live. Tools treat it as an execution error: it is neither a denial nor a cancellation.
    """

    target: PermissionTarget


class PermissionDecider(lang.Abstract):
    @abc.abstractmethod
    def decide(self, request: PermissionRequest) -> ta.Awaitable[DecidedPermissionState | None]:
        raise NotImplementedError

    @ta.final
    async def is_allowed(self, request: PermissionRequest) -> bool:
        return (await self.decide(request)) is PermissionState.ALLOW

    @ta.final
    async def check_allowed(self, request: PermissionRequest) -> None:
        if not await self.is_allowed(request):
            raise PermissionDeniedError(request.target)


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
            request: PermissionRequest,
            rule: PermissionRule,
    ) -> ta.Awaitable[DecidedPermissionState]:
        raise NotImplementedError
