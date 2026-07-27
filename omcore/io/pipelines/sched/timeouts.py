# ruff: noqa: UP006 UP007 UP045
# @om-lite
import dataclasses as dc
import enum
import math
import typing as ta

from ....lite.check import check
from ..core import IoPipelineHandler
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineHandlerNotification
from ..core import IoPipelineHandlerNotifications
from ..core import IoPipelineMessages
from ..errors import TimeoutIoPipelineError
from ..flow.types import IoPipelineFlowMessages
from .types import IoPipelineScheduling


##


class IoPipelineIdleState(enum.Enum):
    READ_IDLE = 'read_idle'
    WRITE_IDLE = 'write_idle'
    ALL_IDLE = 'all_idle'


@ta.final
@dc.dataclass(frozen=True)
class IdleStateIoPipelineEvent(
    IoPipelineMessages.MayPropagate,
    IoPipelineMessages.NeverOutbound,
):
    """Signals that a configured pipeline inactivity interval elapsed."""

    state: IoPipelineIdleState
    first: bool


##


class IdleStateIoPipelineHandler(IoPipelineHandler):
    """
    Emits inbound idle-state events for configured read, write, and combined inactivity intervals.

    Each configured state uses an exact, independently reset scheduler deadline. Unconfigured states schedule nothing;
    when all intervals are omitted, this handler does not require an IoPipelineScheduling service and remains tickless.

    Read and write activity currently mean ordinary messages crossing this handler in their respective directions.
    Flow-control, lifecycle, error, and idle-event messages are not activity. Write completion tracking may refine write
    activity in the future without changing the emitted event contract.
    """

    _STATES: ta.ClassVar[ta.Tuple[IoPipelineIdleState, ...]] = (
        IoPipelineIdleState.READ_IDLE,
        IoPipelineIdleState.WRITE_IDLE,
        IoPipelineIdleState.ALL_IDLE,
    )

    def __init__(
            self,
            read_idle_timeout_s: ta.Optional[float] = None,
            write_idle_timeout_s: ta.Optional[float] = None,
            all_idle_timeout_s: ta.Optional[float] = None,
    ) -> None:
        super().__init__()

        self._timeouts: ta.Dict[IoPipelineIdleState, ta.Optional[float]] = {
            IoPipelineIdleState.READ_IDLE: read_idle_timeout_s,
            IoPipelineIdleState.WRITE_IDLE: write_idle_timeout_s,
            IoPipelineIdleState.ALL_IDLE: all_idle_timeout_s,
        }
        for timeout_s in self._timeouts.values():
            if timeout_s is not None and (not math.isfinite(timeout_s) or timeout_s <= 0.):
                raise ValueError(timeout_s)

        self._handles: ta.Dict[IoPipelineIdleState, IoPipelineScheduling.Handle] = {}
        self._first: ta.Dict[IoPipelineIdleState, bool] = {state: True for state in self._STATES}

        self._started = False
        self._read_open = False

    #

    def _is_active(self, state: IoPipelineIdleState) -> bool:
        return self._started and (state is not IoPipelineIdleState.READ_IDLE or self._read_open)

    def _cancel(self, state: ta.Optional[IoPipelineIdleState] = None) -> None:
        if state is not None:
            if (handle := self._handles.pop(state, None)) is not None:
                handle.cancel()
            return

        handles = tuple(self._handles.values())
        self._handles.clear()
        for handle in handles:
            handle.cancel()

    def _arm(self, ctx: IoPipelineHandlerContext, state: IoPipelineIdleState) -> None:
        self._cancel(state)

        if not self._is_active(state) or (timeout_s := self._timeouts[state]) is None:
            return

        self._handles[state] = ctx.services[IoPipelineScheduling].schedule(
            ctx.ref,
            timeout_s,
            lambda: self._on_idle(ctx, state),
        )

    def _record_activity(
            self,
            ctx: IoPipelineHandlerContext,
            states: ta.Iterable[IoPipelineIdleState],
    ) -> None:
        for state in states:
            if self._timeouts[state] is None or not self._is_active(state):
                continue

            self._first[state] = True
            self._arm(ctx, state)

    def _on_idle(self, ctx: IoPipelineHandlerContext, state: IoPipelineIdleState) -> None:
        self._handles.pop(state, None)
        if not self._is_active(state):
            return

        first = self._first[state]
        self._first[state] = False
        ctx.feed_in(IdleStateIoPipelineEvent(state, first))

        # Delivering the event can synchronously cause activity, closure, or handler removal. Only re-arm if none of
        # those paths already replaced this state's deadline.
        if state not in self._handles:
            self._arm(ctx, state)

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            if any(timeout_s is not None for timeout_s in self._timeouts.values()):
                check.not_none(ctx.services.find(IoPipelineScheduling))

            self._cancel()
            self._first = {state: True for state in self._STATES}
            self._started = False
            self._read_open = False

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._started = False
            self._read_open = False
            self._cancel()

    #

    _NON_READ_ACTIVITY_TYPES: ta.ClassVar[ta.Tuple[type, ...]] = (
        IoPipelineMessages.Error,
        IdleStateIoPipelineEvent,
        IoPipelineFlowMessages.FlushInput,
        IoPipelineFlowMessages.ReadyForOutput,
        IoPipelineFlowMessages.PauseOutput,
    )

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            self._cancel()
            self._first = {state: True for state in self._STATES}
            self._started = True
            self._read_open = True
            for state in self._STATES:
                self._arm(ctx, state)

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            self._read_open = False
            self._cancel(IoPipelineIdleState.READ_IDLE)

        elif not isinstance(msg, self._NON_READ_ACTIVITY_TYPES):
            self._record_activity(ctx, (
                IoPipelineIdleState.READ_IDLE,
                IoPipelineIdleState.ALL_IDLE,
            ))

        ctx.feed_in(msg)

    _NON_WRITE_ACTIVITY_TYPES: ta.ClassVar[ta.Tuple[type, ...]] = (
        IoPipelineFlowMessages.FlushOutput,
        IoPipelineFlowMessages.ReadyForInput,
    )

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalOutput):
            self._started = False
            self._read_open = False
            self._cancel()

        elif not isinstance(msg, self._NON_WRITE_ACTIVITY_TYPES):
            self._record_activity(ctx, (
                IoPipelineIdleState.WRITE_IDLE,
                IoPipelineIdleState.ALL_IDLE,
            ))

        ctx.feed_out(msg)


##


class ReadTimeoutIoPipelineHandler(IoPipelineHandler):
    """
    Emits an inbound timeout error when no ordinary inbound message is observed within the configured interval.

    Flow-control and error messages do not count as read activity. The handler is placement-sensitive: installed near
    the transport it observes raw input, while above decoders or transforms it observes their output.
    """

    def __init__(self, timeout_s: float) -> None:
        super().__init__()

        if not math.isfinite(timeout_s) or timeout_s <= 0.:
            raise ValueError(timeout_s)
        self._timeout_s = timeout_s

        self._handle: ta.Optional[IoPipelineScheduling.Handle] = None
        self._active = False
        self._timed_out = False

    #

    def _cancel(self) -> None:
        if (handle := self._handle) is not None:
            self._handle = None
            handle.cancel()

    def _arm(self, ctx: IoPipelineHandlerContext) -> None:
        self._cancel()
        self._handle = ctx.services[IoPipelineScheduling].schedule(
            ctx.ref,
            self._timeout_s,
            lambda: self._on_timeout(ctx),
        )

    def _on_timeout(self, ctx: IoPipelineHandlerContext) -> None:
        self._handle = None
        if not self._active or self._timed_out:
            return

        self._timed_out = True
        ctx.feed_in(IoPipelineMessages.Error(
            TimeoutIoPipelineError(f'Read timed out after {self._timeout_s:g} seconds'),
            direction='inbound',
            handler=ctx.ref,
        ))

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            check.not_none(ctx.services.find(IoPipelineScheduling))

            self._active = False
            self._timed_out = False
            self._cancel()

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._active = False
            self._cancel()

    #

    _NON_ACTIVITY_TYPES: ta.ClassVar[ta.Tuple[type, ...]] = (
        IoPipelineMessages.Error,
        IdleStateIoPipelineEvent,
        IoPipelineFlowMessages.FlushInput,
        IoPipelineFlowMessages.ReadyForOutput,
        IoPipelineFlowMessages.PauseOutput,
    )

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            self._active = True
            self._timed_out = False
            self._arm(ctx)

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            self._active = False
            self._cancel()

        elif self._active and not self._timed_out and not isinstance(msg, self._NON_ACTIVITY_TYPES):
            self._arm(ctx)

        ctx.feed_in(msg)
