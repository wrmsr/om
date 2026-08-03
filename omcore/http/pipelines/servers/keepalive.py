# ruff: noqa: UP006 UP007 UP045
# @om-lite
import math
import typing as ta

from ....io.pipelines.core import IoPipelineHandler
from ....io.pipelines.core import IoPipelineHandlerContext
from ....io.pipelines.core import IoPipelineHandlerNotification
from ....io.pipelines.core import IoPipelineHandlerNotifications
from ....io.pipelines.core import IoPipelineMessages
from ....io.pipelines.sched.types import IoPipelineScheduling
from ....lite.check import check
from ...headers import HttpHeaders
from ...versions import HttpVersion
from ...versions import HttpVersions
from ..requests import FullIoPipelineHttpRequest
from ..requests import IoPipelineHttpRequestAborted
from ..requests import IoPipelineHttpRequestHead
from ..responses import FullIoPipelineHttpResponse
from ..responses import IoPipelineHttpResponseAborted
from ..responses import IoPipelineHttpResponseEnd
from ..responses import IoPipelineHttpResponseHead


##


class IoPipelineHttpServerKeepAliveHandler(IoPipelineHandler):
    """
    Duplex handler managing HTTP/1.x connection persistence.

    Observes inbound request heads to determine keep-alive from the Connection header and HTTP version, then
    conditionally emits FinalOutput after outbound response completion. App handlers should NOT emit FinalOutput
    themselves when this handler is present.

    HTTP/1.1 defaults to keep-alive; HTTP/1.0 defaults to close. The decision is made from - and echoed back per - the
    *request's* version, as applications build responses defaulting to HTTP/1.1 regardless of what the client spoke.

    Interim (1xx) responses do not complete an exchange and are passed through untouched. Aborted requests and
    responses do end the exchange, and always close the connection.

    When idle_timeout_s is set, the connection is closed normally if no request is active before the interval elapses.
    This includes the period before the first request and requires an IoPipelineScheduling service.
    """

    def __init__(self, idle_timeout_s: ta.Optional[float] = None) -> None:
        super().__init__()

        if idle_timeout_s is not None and (not math.isfinite(idle_timeout_s) or idle_timeout_s <= 0.):
            raise ValueError(idle_timeout_s)
        self._idle_timeout_s = idle_timeout_s

        self._keep_alive = True
        self._idle = True
        self._closing = False

        self._request_version: HttpVersion = HttpVersions.HTTP_1_1
        self._response_is_final = True

        self._handle: ta.Optional[IoPipelineScheduling.Handle] = None

    #

    def _cancel(self) -> None:
        if (handle := self._handle) is not None:
            self._handle = None
            handle.cancel()

    def _arm(self, ctx: IoPipelineHandlerContext) -> None:
        if self._idle_timeout_s is None or not self._idle or self._closing:
            return

        self._cancel()
        self._handle = ctx.services[IoPipelineScheduling].schedule_context(
            ctx.ref,
            self._idle_timeout_s,
            lambda ctx2: check.isinstance(ctx2.handler, IoPipelineHttpServerKeepAliveHandler)._on_timeout(ctx2),  # noqa
        )

    def _close_output(self, ctx: IoPipelineHandlerContext) -> None:
        if self._closing:
            return

        self._closing = True
        self._cancel()
        ctx.feed_final_output()

    def _on_timeout(self, ctx: IoPipelineHandlerContext) -> None:
        self._handle = None
        if not self._idle or self._closing:
            return

        self._close_output(ctx)

    def _complete_response(self, ctx: IoPipelineHandlerContext) -> None:
        self._idle = True
        if self._keep_alive:
            self._arm(ctx)
        else:
            self._close_output(ctx)

    #

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            if self._idle_timeout_s is not None:
                check.not_none(ctx.services.find(IoPipelineScheduling))

            self._keep_alive = True
            self._idle = True
            self._closing = False
            self._request_version = HttpVersions.HTTP_1_1
            self._response_is_final = True
            self._cancel()

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            self._closing = True
            self._cancel()

    #

    @staticmethod
    def is_request_keep_alive(head: IoPipelineHttpRequestHead) -> bool:
        if head.version >= HttpVersions.HTTP_1_1:
            return not head.headers.contains_list_value('connection', 'close', ignore_case=True)
        else:
            return head.headers.contains_list_value('connection', 'keep-alive', ignore_case=True)

    def _observe_request_head(self, head: IoPipelineHttpRequestHead) -> None:
        self._cancel()
        self._idle = False
        self._response_is_final = True
        self._keep_alive = self.is_request_keep_alive(head)
        self._request_version = head.version

    #

    def _set_response_connection_header(
            self,
            head: IoPipelineHttpResponseHead,
    ) -> IoPipelineHttpResponseHead:
        # Interim (1xx) responses do not end the exchange and carry no connection-persistence semantics.
        if head.is_interim:
            return head

        # Only set if the response doesn't already have a Connection header.
        if head.headers.lower.get('connection'):
            return head

        # Persistence is negotiated against the *request's* version - applications build responses defaulting to
        # HTTP/1.1 regardless of what the client spoke. `close` is always stated explicitly: the response head's own
        # version need not match the request's, so silently relying on the HTTP/1.0 default is not safe.
        conn_value: ta.Optional[str] = None
        if self._keep_alive:
            if self._request_version < HttpVersions.HTTP_1_1:
                conn_value = 'keep-alive'
        else:
            conn_value = 'close'

        if conn_value is None:
            return head

        return IoPipelineHttpResponseHead(
            status=head.status,
            reason=head.reason,
            headers=HttpHeaders([*head.headers.raw, ('Connection', conn_value)]),
            parsed=head.parsed,
            version=head.version,
        )

    #

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            self._arm(ctx)
            return

        if isinstance(msg, FullIoPipelineHttpRequest):
            self._observe_request_head(msg.head)
            ctx.feed_in(msg)
            return

        if isinstance(msg, IoPipelineHttpRequestHead):
            self._observe_request_head(msg)
            ctx.feed_in(msg)
            return

        if isinstance(msg, IoPipelineHttpRequestAborted):
            self._cancel()
            # An aborted request loses request framing and parks the decoder - nothing further can be read from this
            # connection, so it must not be reused regardless of what the application answers with.
            self._keep_alive = False
            ctx.feed_in(msg)
            self._close_output(ctx)
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            self._cancel()
            if self._idle:
                ctx.feed_in(msg)
                self._close_output(ctx)
                return

            self._keep_alive = False
            ctx.feed_in(msg)
            return

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, FullIoPipelineHttpResponse):
            msg = FullIoPipelineHttpResponse(
                head=self._set_response_connection_header(msg.head),
                body=msg.body,
            )
            ctx.feed_out(msg)
            if not msg.head.is_interim:
                self._complete_response(ctx)
            return

        if isinstance(msg, IoPipelineHttpResponseHead):
            self._response_is_final = not msg.is_interim
            msg = self._set_response_connection_header(msg)
            ctx.feed_out(msg)
            return

        if isinstance(msg, IoPipelineHttpResponseEnd):
            ctx.feed_out(msg)
            if self._response_is_final:
                self._complete_response(ctx)
            else:
                self._response_is_final = True
            return

        if isinstance(msg, IoPipelineHttpResponseAborted):
            ctx.feed_out(msg)
            self._response_is_final = True
            self._keep_alive = False
            self._complete_response(ctx)
            return

        if isinstance(msg, IoPipelineMessages.FinalOutput):
            self._closing = True
            self._cancel()
            ctx.feed_out(msg)
            return

        ctx.feed_out(msg)
