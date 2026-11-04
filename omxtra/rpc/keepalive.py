# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
An optional keepalive handler, installed between the envelope codec and the session only when configured.

After `interval_s` without receiving any envelope it sends a ping; if nothing at all is received within `timeout_s` of
that, it fails the connection with a timeout error, which the session treats as fatal. Any received envelope counts as
liveness, so an actively used connection never pings. Pongs answering this handler's own pings are consumed here and
never reach the session; the session answers the peer's pings itself.

Ping ids are drawn from a private string space so they never collide with the ids the connection issues for its own
explicit pings.
"""
import itertools
import math
import typing as ta

from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineHandlerNotification
from omcore.io.pipelines.core import IoPipelineHandlerNotifications
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.pipelines.flow.types import IoPipelineFlow
from omcore.io.pipelines.sched.types import IoPipelineScheduling
from omcore.lite.check import check

from .errors import RpcTimeoutError
from .messages import RpcEnvelope
from .messages import RpcPingMessage
from .messages import RpcPongMessage


##


class RpcKeepaliveIoPipelineHandler(IoPipelineHandler):
    ID_PREFIX: ta.ClassVar[str] = 'rpc-keepalive:'

    def __init__(
            self,
            *,
            interval_s: float,
            timeout_s: float,
    ) -> None:
        super().__init__()

        for t in (interval_s, timeout_s):
            if not math.isfinite(t) or t <= 0.:
                raise ValueError(t)
        self._interval_s = interval_s
        self._timeout_s = timeout_s

        self._ids = itertools.count(1)
        self._handle: ta.Optional[IoPipelineScheduling.Handle] = None
        self._outstanding: ta.Optional[str] = None
        self._active = False
        self._failed = False

    @property
    def outstanding_ping_id(self) -> ta.Optional[str]:
        return self._outstanding

    #

    def _cancel(self) -> None:
        if (handle := self._handle) is not None:
            self._handle = None
            handle.cancel()

    def _arm(self, ctx: IoPipelineHandlerContext, delay_s: float) -> None:
        self._cancel()
        self._handle = ctx.services[IoPipelineScheduling].schedule_context(
            ctx.ref,
            delay_s,
            lambda ctx2: check.isinstance(ctx2.handler, RpcKeepaliveIoPipelineHandler)._on_timer(ctx2),  # noqa
        )

    def _on_activity(self, ctx: IoPipelineHandlerContext) -> None:
        if not self._active or self._failed:
            return
        self._outstanding = None
        self._arm(ctx, self._interval_s)

    def _on_timer(self, ctx: IoPipelineHandlerContext) -> None:
        self._handle = None
        if not self._active or self._failed:
            return

        if self._outstanding is not None:
            self._failed = True
            ctx.feed_in(IoPipelineMessages.Error(
                RpcTimeoutError(f'keepalive timed out: no traffic within {self._timeout_s:g}s of ping'),
                direction='inbound',
                handler=ctx.ref,
            ))
            return

        pid = f'{self.ID_PREFIX}{next(self._ids)}'
        self._outstanding = pid
        ctx.feed_out(RpcPingMessage(pid))
        if not self._is_live(ctx):
            return
        IoPipelineFlow.maybe_flush_output(ctx)
        if not self._is_live(ctx):
            return
        self._arm(ctx, self._timeout_s)

    def _is_live(self, ctx: IoPipelineHandlerContext) -> bool:
        # Feeding output can reentrantly close the pipeline or remove this handler.
        return not ctx.invalidated and self._active and not self._failed

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            check.not_none(ctx.services.find(IoPipelineScheduling))
            self._cancel()
            self._active = False
            self._failed = False
            self._outstanding = None

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._active = False
            self._cancel()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            self._active = True
            self._failed = False
            self._outstanding = None
            self._arm(ctx, self._interval_s)

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            self._active = False
            self._cancel()

        elif isinstance(msg, RpcEnvelope):
            if isinstance(msg, RpcPongMessage) and isinstance(msg.id, str) and msg.id.startswith(self.ID_PREFIX):
                self._on_activity(ctx)
                return

            self._on_activity(ctx)

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalOutput):
            self._active = False
            self._cancel()

        ctx.feed_out(msg)
