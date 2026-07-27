# ruff: noqa: UP006 UP007 UP045
# @om-lite
import math
import typing as ta

from ....io.pipelines.core import IoPipelineHandler
from ....io.pipelines.core import IoPipelineHandlerContext
from ....io.pipelines.core import IoPipelineHandlerNotification
from ....io.pipelines.core import IoPipelineHandlerNotifications
from ....io.pipelines.core import IoPipelineMessages
from ....io.pipelines.errors import TimeoutIoPipelineError
from ....io.pipelines.sched.types import IoPipelineScheduling
from ....lite.check import check
from ..requests import FullIoPipelineHttpRequest
from ..requests import IoPipelineHttpRequestAborted
from ..requests import IoPipelineHttpRequestHead
from ..responses import FullIoPipelineHttpResponse
from ..responses import IoPipelineHttpResponseAborted
from ..responses import IoPipelineHttpResponseEnd
from ..responses import IoPipelineHttpResponseHead


##


class IoPipelineHttpClientRequestTimeoutHandler(IoPipelineHandler):
    """
    Enforces an absolute deadline from an outbound HTTP request head through final inbound response completion.

    Request-body and response-body activity do not reset the deadline. The handler must remain on the application side
    of the request encoder and response decoder so it observes semantic HTTP objects in both directions. Only one
    exchange may be active, matching IoPipelineHttpClientHandler's current single-request connection model.

    Expiry emits one inbound TimeoutIoPipelineError. When timeout_s is omitted, the handler is a
    scheduler-independent, tickless pass-through.
    """

    def __init__(self, timeout_s: ta.Optional[float] = None) -> None:
        super().__init__()

        if timeout_s is not None and (not math.isfinite(timeout_s) or timeout_s <= 0.):
            raise ValueError(timeout_s)
        self._timeout_s = timeout_s

        self._handle: ta.Optional[IoPipelineScheduling.Handle] = None
        self._active = False
        self._timed_out = False
        self._response_is_final = True

    #

    def _cancel(self) -> None:
        if (handle := self._handle) is not None:
            self._handle = None
            handle.cancel()

    def _reset(self) -> None:
        self._cancel()
        self._active = False
        self._timed_out = False
        self._response_is_final = True

    def _start(self, ctx: IoPipelineHandlerContext) -> None:
        if self._active:
            raise RuntimeError('Overlapping HTTP client requests are not supported')

        self._active = True
        self._timed_out = False
        self._response_is_final = True
        self._handle = ctx.services[IoPipelineScheduling].schedule(
            ctx.ref,
            check.not_none(self._timeout_s),
            lambda: self._on_timeout(ctx),
        )

    def _on_timeout(self, ctx: IoPipelineHandlerContext) -> None:
        self._handle = None
        if not self._active or self._timed_out:
            return

        self._timed_out = True
        timeout_s = check.not_none(self._timeout_s)
        ctx.feed_in(IoPipelineMessages.Error(
            TimeoutIoPipelineError(f'HTTP client request timed out after {timeout_s:g} seconds'),
            direction='inbound',
            handler=ctx.ref,
        ))

    #

    @staticmethod
    def _is_final_response_head(head: IoPipelineHttpResponseHead) -> bool:
        return not (100 <= head.status < 200 and head.status != 101)

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            if self._timeout_s is not None:
                check.not_none(ctx.services.find(IoPipelineScheduling))
            self._reset()

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._reset()

    #

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if self._timeout_s is None:
            ctx.feed_in(msg)
            return

        if isinstance(msg, IoPipelineMessages.InitialInput):
            self._reset()

        elif isinstance(msg, (IoPipelineMessages.Error, IoPipelineMessages.FinalInput)):
            self._reset()

        elif isinstance(msg, FullIoPipelineHttpResponse):
            if self._is_final_response_head(msg.head):
                self._reset()

        elif isinstance(msg, IoPipelineHttpResponseHead):
            self._response_is_final = self._is_final_response_head(msg)

        elif isinstance(msg, IoPipelineHttpResponseEnd):
            if self._response_is_final:
                self._reset()
            else:
                self._response_is_final = True

        elif isinstance(msg, IoPipelineHttpResponseAborted):
            self._reset()

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if self._timeout_s is None:
            ctx.feed_out(msg)
            return

        if isinstance(msg, IoPipelineMessages.FinalOutput):
            self._reset()

        elif isinstance(msg, (FullIoPipelineHttpRequest, IoPipelineHttpRequestHead)):
            self._start(ctx)

        elif isinstance(msg, IoPipelineHttpRequestAborted):
            self._reset()

        ctx.feed_out(msg)
