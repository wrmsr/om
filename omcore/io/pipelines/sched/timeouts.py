# ruff: noqa: UP006 UP007 UP045
# @om-lite
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
