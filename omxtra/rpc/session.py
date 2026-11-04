# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
The sans-io rpc session: the innermost pipeline handler, owning all protocol state for one connection.

The protocol is symmetric - either peer may send requests, notifications, cancels, and pings at any time - so one
session handler serves both ends. It correlates responses to the requests this side sent, surfaces the requests the peer
sent for the host to answer, answers pings itself, and enforces every timeout and limit which can be expressed without
touching a transport. Timers come from the driver's IoPipelineScheduling service, so they behave identically under every
driver and can be exercised deterministically with the pure driver's manual clock.

Everything the host needs to know arrives as an event fed outbound (see `messages.py`); everything the host wants done
arrives as a command fed inbound. The session never executes anything: a received request becomes a RequestReceived
event, and how and where the host runs its handler is the host's business. Peer misbehavior which can be tolerated is
tolerated by policy; the rest closes the connection with a protocol error.

Reentrancy: feeding a message outbound can synchronously deliver an Error back into this handler and change its state (a
failed write, an unencodable envelope reported by the codec). Every method therefore re-checks state after any
`feed_out`, and the terminal `_finish_close` is idempotent.
"""
import dataclasses as dc
import functools
import typing as ta
import weakref

from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineHandlerContext
from omcore.io.pipelines.core import IoPipelineHandlerNotification
from omcore.io.pipelines.core import IoPipelineHandlerNotifications
from omcore.io.pipelines.core import IoPipelineMessages
from omcore.io.pipelines.flow.types import IoPipelineFlow
from omcore.io.pipelines.flow.types import IoPipelineFlowMessages
from omcore.io.pipelines.sched.timeouts import IdleStateIoPipelineEvent
from omcore.io.pipelines.sched.timeouts import IoPipelineIdleState
from omcore.io.pipelines.sched.types import IoPipelineScheduling
from omcore.lite.check import check
from omcore.logs.modules import get_module_logger

from .configs import RpcConfig
from .errors import RpcCancelledError
from .errors import RpcConnectionClosedError
from .errors import RpcErrorCodes
from .errors import RpcMessageTooLargeError
from .errors import RpcProtocolError
from .errors import RpcRemoteErrorData
from .errors import RpcTimeoutError
from .errors import RpcTooManyRequestsError
from .messages import RpcCancelMessage
from .messages import RpcEnvelope
from .messages import RpcErrorMessage
from .messages import RpcNotificationMessage
from .messages import RpcPingMessage
from .messages import RpcPongMessage
from .messages import RpcRequestMessage
from .messages import RpcResponseMessage
from .messages import RpcResultMessage
from .messages import RpcSessionMessages as Rsm
from .messages import RpcUnspecified


log = get_module_logger(globals())  # noqa


RpcSessionState = ta.Literal['new', 'open', 'closing', 'closed']  # ta.TypeAlias


##


class RpcSessionIoPipelineHandler(IoPipelineHandler):
    @dc.dataclass()
    class _PendingOut:
        request: RpcRequestMessage
        handle: ta.Optional[IoPipelineScheduling.Handle] = None

    @dc.dataclass()
    class _PendingPing:
        ping: RpcPingMessage
        handle: ta.Optional[IoPipelineScheduling.Handle] = None

    @dc.dataclass()
    class _InflightIn:
        request: RpcRequestMessage
        handle: ta.Optional[IoPipelineScheduling.Handle] = None

    def __init__(self, config: RpcConfig = RpcConfig.DEFAULT) -> None:
        super().__init__()

        self._config = config

        self._state: RpcSessionState = 'new'

        self._pending_out: ta.Dict[ta.Any, RpcSessionIoPipelineHandler._PendingOut] = {}
        self._pending_pings: ta.Dict[ta.Any, RpcSessionIoPipelineHandler._PendingPing] = {}
        self._inflight_in: ta.Dict[ta.Any, RpcSessionIoPipelineHandler._InflightIn] = {}

        self._output_paused = False
        self._ready_for_input_issued = False

        self._close_handle: ta.Optional[IoPipelineScheduling.Handle] = None
        self._close_exc: ta.Optional[BaseException] = None
        self._sent_final_output = False

        self._sending_substitute = False

        # The flush fence issued while handling the current send command, if any, so completion can be reported.
        self._current_fence: ta.Optional[IoPipelineFlowMessages.FlushOutput] = None

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}@{id(self):x}'
            f'<{self._state}, pending_out={len(self._pending_out)}, inflight_in={len(self._inflight_in)}>'
        )

    @property
    def config(self) -> RpcConfig:
        return self._config

    @property
    def state(self) -> RpcSessionState:
        return self._state

    @property
    def pending_outbound_ids(self) -> ta.AbstractSet[ta.Any]:
        return self._pending_out.keys()

    @property
    def pending_ping_ids(self) -> ta.AbstractSet[ta.Any]:
        return self._pending_pings.keys()

    @property
    def inflight_inbound_ids(self) -> ta.AbstractSet[ta.Any]:
        return self._inflight_in.keys()

    @property
    def output_paused(self) -> bool:
        return self._output_paused

    def _is_closed(self) -> bool:
        # A method rather than a direct comparison so re-checks after reentrant calls are not narrowed away.
        return self._state == 'closed'

    ##
    # utilities

    def _needs_scheduling(self) -> bool:
        c = self._config
        return any(t is not None for t in (
            c.default_request_timeout_s,
            c.default_ping_timeout_s,
            c.inbound_handling_timeout_s,
            c.close_drain_timeout_s,
        ))

    def _schedule(
            self,
            ctx: IoPipelineHandlerContext,
            delay_s: float,
            fn: ta.Callable[[IoPipelineHandlerContext], None],
    ) -> IoPipelineScheduling.Handle:
        if (sched := ctx.services.find(IoPipelineScheduling)) is None:
            raise RuntimeError('rpc session timeouts require an IoPipelineScheduling service')
        return sched.schedule_context(ctx.ref, delay_s, fn)

    @staticmethod
    def _cancel_handle(entry: ta.Union[_PendingOut, _PendingPing, _InflightIn]) -> None:
        if (handle := entry.handle) is not None:
            entry.handle = None
            handle.cancel()

    def _emit(self, ctx: IoPipelineHandlerContext, event: Rsm.Event) -> None:
        ctx.feed_out(event)

    def _send(self, ctx: IoPipelineHandlerContext, envelope: RpcEnvelope) -> bool:
        """Feed an envelope toward the wire and flush. Returns False if the session closed reentrantly meanwhile."""

        if self._sent_final_output:
            return False

        ctx.feed_out(envelope)
        if self._is_closed():
            return False

        if ctx.services.find(IoPipelineFlow) is not None:
            fence = IoPipelineFlowMessages.FlushOutput()
            self._current_fence = fence
            ctx.feed_out(fence)

        return not self._is_closed()

    @staticmethod
    def _on_send_fence_done(
            ctx_ref: ta.Callable[[], ta.Optional[IoPipelineHandlerContext]],
            cmd: Rsm.Command,
            fence: IoPipelineMessages.Completable[None],
    ) -> None:
        # Failure means the driver is closing, which the host learns of from Closed; only success is worth reporting.
        # Output after FinalOutput reached the terminal is rejected by the pipeline, so check for that too.
        if not fence.is_succeeded():
            return
        if (ctx := ctx_ref()) is None or ctx.invalidated or ctx.pipeline.saw_final_output:
            return
        ctx.feed_out(Rsm.Sent(cmd))

    def _report_sent(self, ctx: IoPipelineHandlerContext, cmd: Rsm.Command) -> None:
        """Emit Sent for a send command, now if nothing needed flushing, else once its fence completes."""

        fence = self._current_fence
        self._current_fence = None

        if self._is_closed():
            return

        if fence is not None and not fence.is_done():
            fence.add_listener(functools.partial(self._on_send_fence_done, weakref.ref(ctx), cmd))
        elif fence is None or fence.is_succeeded():
            self._emit(ctx, Rsm.Sent(cmd))

    def _closed_error(self) -> RpcConnectionClosedError:
        if (exc := self._close_exc) is not None:
            err = RpcConnectionClosedError(f'connection failed: {exc!r}')
            err.__cause__ = exc
            return err
        return RpcConnectionClosedError('connection closed')

    def _effective_timeout(
            self,
            timeout_s: ta.Union[float, None, ta.Type[RpcUnspecified]],
            default: ta.Optional[float],
    ) -> ta.Optional[float]:
        if timeout_s is RpcUnspecified:
            return default
        return ta.cast(ta.Optional[float], timeout_s)

    ##
    # session-generated errors

    @staticmethod
    def _error_data(code: str, exc_type: ta.Type[BaseException], message: str) -> RpcRemoteErrorData:
        return RpcRemoteErrorData(code=code, remote_type=exc_type.__name__, message=message)

    def _busy_response(self, rid: ta.Any) -> RpcErrorMessage:
        return RpcErrorMessage(rid, self._error_data(
            RpcErrorCodes.BUSY,
            RpcTooManyRequestsError,
            'Too many concurrent requests',
        ))

    def _shutting_down_response(self, rid: ta.Any) -> RpcErrorMessage:
        return RpcErrorMessage(rid, self._error_data(
            RpcErrorCodes.SHUTTING_DOWN,
            RpcConnectionClosedError,
            'Connection shutting down',
        ))

    def _handling_timeout_response(self, rid: ta.Any) -> RpcErrorMessage:
        return RpcErrorMessage(rid, self._error_data(
            RpcErrorCodes.HANDLING_TIMEOUT,
            RpcTimeoutError,
            'Request handling timed out',
        ))

    ##
    # outbound requests

    def _track_pending_out(
            self,
            ctx: IoPipelineHandlerContext,
            request: RpcRequestMessage,
    ) -> ta.Optional[_PendingOut]:
        """Register an outbound request, or emit RequestFailed and return None if it cannot be sent."""

        if (rid := request.id) in self._pending_out:
            self._emit(ctx, Rsm.RequestFailed(request, ValueError(f'duplicate outbound request id: {rid!r}')))
            return None

        if (mx := self._config.max_pending_outbound) is not None and len(self._pending_out) >= mx:
            self._emit(ctx, Rsm.RequestFailed(request, RpcTooManyRequestsError(
                f'too many pending outbound requests: {mx}',
            )))
            return None

        entry = self._PendingOut(request)
        self._pending_out[rid] = entry
        return entry

    def _on_send_request(self, ctx: IoPipelineHandlerContext, cmd: Rsm.SendRequest) -> None:
        if (entry := self._track_pending_out(ctx, cmd.request)) is None:
            return

        if not self._send(ctx, cmd.request):
            return

        rid = entry.request.id
        if self._pending_out.get(rid) is not entry:
            # Failed reentrantly while being sent.
            return

        if (t := self._effective_timeout(cmd.timeout_s, self._config.default_request_timeout_s)) is not None:
            entry.handle = self._schedule(
                ctx,
                t,
                lambda ctx2: check.isinstance(ctx2.handler, RpcSessionIoPipelineHandler)._on_request_timeout(ctx2, rid),  # noqa
            )

    def _on_send_notification(self, ctx: IoPipelineHandlerContext, cmd: Rsm.SendNotification) -> None:
        self._send(ctx, cmd.notification)

    def _send_cancel(self, ctx: IoPipelineHandlerContext, rid: ta.Any) -> None:
        if self._state != 'open':
            return
        self._send(ctx, RpcCancelMessage(rid))

    def _on_request_timeout(self, ctx: IoPipelineHandlerContext, rid: ta.Any) -> None:
        if (entry := self._pending_out.pop(rid, None)) is None:
            return
        entry.handle = None

        self._emit(ctx, Rsm.RequestFailed(entry.request, RpcTimeoutError(
            f'request {rid!r} ({entry.request.method}) timed out',
        )))
        if self._is_closed():
            return

        if self._config.cancel_abandoned_requests:
            self._send_cancel(ctx, rid)
            if self._is_closed():
                return

        self._after_pending_out_completed(ctx)

    def _on_cancel_request(self, ctx: IoPipelineHandlerContext, cmd: Rsm.CancelRequest) -> None:
        if (entry := self._pending_out.pop(cmd.id, None)) is None:
            return
        self._cancel_handle(entry)

        if cmd.notify_peer:
            self._send_cancel(ctx, cmd.id)
            if self._is_closed():
                return

        self._after_pending_out_completed(ctx)

    def _fail_pending_out(self, ctx: IoPipelineHandlerContext, exc: Exception) -> None:
        entries = list(self._pending_out.values())
        self._pending_out.clear()
        for entry in entries:
            self._cancel_handle(entry)
            self._emit(ctx, Rsm.RequestFailed(entry.request, exc))

        pings = list(self._pending_pings.values())
        self._pending_pings.clear()
        for ping in pings:
            self._cancel_handle(ping)
            self._emit(ctx, Rsm.PingFailed(ping.ping, exc))

    def _after_pending_out_completed(self, ctx: IoPipelineHandlerContext) -> None:
        if self._state == 'closing' and not self._pending_out and not self._inflight_in:
            self._finish_close(ctx, None)

    ##
    # pings

    def _on_send_ping(self, ctx: IoPipelineHandlerContext, cmd: Rsm.SendPing) -> None:
        ping = cmd.ping
        if (pid := ping.id) in self._pending_pings:
            self._emit(ctx, Rsm.PingFailed(ping, ValueError(f'duplicate outbound ping id: {pid!r}')))
            return

        entry = self._PendingPing(ping)
        self._pending_pings[pid] = entry

        if not self._send(ctx, ping):
            return

        if self._pending_pings.get(pid) is not entry:
            return

        if (t := self._effective_timeout(cmd.timeout_s, self._config.default_ping_timeout_s)) is not None:
            entry.handle = self._schedule(
                ctx,
                t,
                lambda ctx2: check.isinstance(ctx2.handler, RpcSessionIoPipelineHandler)._on_ping_timeout(ctx2, pid),  # noqa
            )

    def _on_ping_timeout(self, ctx: IoPipelineHandlerContext, pid: ta.Any) -> None:
        if (entry := self._pending_pings.pop(pid, None)) is None:
            return
        entry.handle = None

        self._emit(ctx, Rsm.PingFailed(entry.ping, RpcTimeoutError(f'ping {pid!r} timed out')))

    def _on_inbound_ping(self, ctx: IoPipelineHandlerContext, ping: RpcPingMessage) -> None:
        if self._state == 'closed':
            return

        self._send(ctx, RpcPongMessage(ping.id))

    def _on_inbound_pong(self, ctx: IoPipelineHandlerContext, pong: RpcPongMessage) -> None:
        if (entry := self._pending_pings.pop(pong.id, None)) is None:
            log.debug('Dropping unmatched pong: %r', pong)
            return

        self._cancel_handle(entry)
        self._emit(ctx, Rsm.PongReceived(entry.ping, pong))

    ##
    # inbound responses

    def _on_inbound_response(self, ctx: IoPipelineHandlerContext, response: RpcResponseMessage) -> None:
        if (entry := self._pending_out.pop(response.id, None)) is None:
            if self._config.on_unmatched_response == 'close':
                self._finish_close(ctx, RpcProtocolError(f'unmatched response id: {response.id!r}'))
            else:
                log.debug('Dropping unmatched response: %r', response)
            return

        self._cancel_handle(entry)
        self._emit(ctx, Rsm.ResponseReceived(entry.request, response))

        self._after_pending_out_completed(ctx)

    ##
    # inbound requests

    def _at_inflight_limit(self) -> bool:
        return (mx := self._config.max_inflight_inbound) is not None and len(self._inflight_in) >= mx

    def _on_inbound_request(self, ctx: IoPipelineHandlerContext, request: RpcRequestMessage) -> None:
        rid = request.id

        if self._state != 'open':
            self._send(ctx, self._shutting_down_response(rid))
            return

        if rid in self._inflight_in:
            self._finish_close(ctx, RpcProtocolError(f'duplicate inbound request id: {rid!r}'))
            return

        if self._at_inflight_limit() and self._config.inflight_limit_policy == 'reject':
            self._send(ctx, self._busy_response(rid))
            return

        entry = self._InflightIn(request)
        self._inflight_in[rid] = entry

        if (t := self._config.inbound_handling_timeout_s) is not None:
            entry.handle = self._schedule(
                ctx,
                t,
                lambda ctx2: check.isinstance(ctx2.handler, RpcSessionIoPipelineHandler)._on_inbound_handling_timeout(ctx2, rid),  # noqa
            )

        self._emit(ctx, Rsm.RequestReceived(request))

    def _on_send_response(self, ctx: IoPipelineHandlerContext, response: RpcResponseMessage) -> None:
        if (entry := self._inflight_in.pop(response.id, None)) is None:
            log.debug('Dropping response to unknown or aborted inbound request: %r', response)
            return
        self._cancel_handle(entry)

        if not self._send(ctx, response):
            return

        self._after_inflight_in_completed(ctx)

    def _on_inbound_handling_timeout(self, ctx: IoPipelineHandlerContext, rid: ta.Any) -> None:
        if (entry := self._inflight_in.pop(rid, None)) is None:
            return
        entry.handle = None

        if self._config.respond_to_aborted_inbound:
            if not self._send(ctx, self._handling_timeout_response(rid)):
                return

        self._emit(ctx, Rsm.RequestHandlingAborted(entry.request, RpcTimeoutError(
            f'handling of inbound request {rid!r} ({entry.request.method}) timed out',
        )))

        self._after_inflight_in_completed(ctx)

    def _on_inbound_cancel(self, ctx: IoPipelineHandlerContext, cancel: RpcCancelMessage) -> None:
        if (entry := self._inflight_in.pop(cancel.id, None)) is None:
            # Already answered, or never seen: cancels race with responses by nature.
            return
        self._cancel_handle(entry)

        self._emit(ctx, Rsm.RequestHandlingAborted(entry.request, RpcCancelledError(
            f'inbound request {cancel.id!r} ({entry.request.method}) cancelled by peer',
        )))

        self._after_inflight_in_completed(ctx)

    def _after_inflight_in_completed(self, ctx: IoPipelineHandlerContext) -> None:
        if self._state == 'closing':
            if not self._pending_out and not self._inflight_in:
                self._finish_close(ctx, None)
            return

        self._maybe_ready_for_input(ctx)

    ##
    # encoding failures

    def _on_encode_failed(self, ctx: IoPipelineHandlerContext, msg: Rsm.OutboundEncodeFailed) -> None:
        envelope = msg.envelope
        exc = msg.exc

        if self._sending_substitute:
            # Even the minimal error response would not fit: the frame limit is misconfigured. Dropping the response is
            # the least bad option - the peer times out and the connection stays usable for smaller messages.
            log.error('Cannot send even a substitute error response, dropping: %r', exc)
            return

        if isinstance(envelope, RpcRequestMessage):
            if (entry := self._pending_out.pop(envelope.id, None)) is not None:
                self._cancel_handle(entry)
                fexc: Exception
                if isinstance(exc, RpcMessageTooLargeError):
                    fexc = exc
                else:
                    fexc = ValueError(f'request could not be encoded: {exc!r}')
                    fexc.__cause__ = exc
                self._emit(ctx, Rsm.RequestFailed(entry.request, fexc))

            self._after_pending_out_completed(ctx)
            return

        if isinstance(envelope, RpcPingMessage):
            if (ping := self._pending_pings.pop(envelope.id, None)) is not None:
                self._cancel_handle(ping)
                self._emit(ctx, Rsm.PingFailed(ping.ping, exc))
            return

        if isinstance(envelope, (RpcResultMessage, RpcErrorMessage)):
            log.warning('Substituting error for unencodable response %r: %r', envelope.id, exc)
            substitute: RpcErrorMessage
            if isinstance(exc, RpcMessageTooLargeError):
                substitute = RpcErrorMessage(envelope.id, self._error_data(
                    RpcErrorCodes.RESULT_TOO_LARGE,
                    RpcMessageTooLargeError,
                    'Response too large',
                ))
            else:
                substitute = RpcErrorMessage(envelope.id, self._error_data(
                    RpcErrorCodes.RESULT_ENCODING,
                    type(exc),
                    f'Response could not be encoded: {exc}',
                ))

            self._sending_substitute = True
            try:
                self._send(ctx, substitute)
            finally:
                self._sending_substitute = False
            return

        if isinstance(envelope, RpcNotificationMessage):
            log.warning('Dropping unencodable notification %r: %r', envelope.method, exc)
            return

        # Cancels and pongs carry only an id: if one is unencodable the peer will not miss it much.
        log.debug('Dropping unencodable envelope %r: %r', envelope, exc)

    ##
    # flow control

    def _maybe_ready_for_input(self, ctx: IoPipelineHandlerContext) -> None:
        """Under the 'pause' policy, lets the driver read again once there is room for more inbound requests."""

        if (flow := ctx.services.find(IoPipelineFlow)) is None or flow.is_auto_read():
            return
        if self._state == 'closed' or self._ready_for_input_issued or self._at_inflight_limit():
            return

        self._ready_for_input_issued = True
        ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

    def _on_flush_input(self, ctx: IoPipelineHandlerContext) -> None:
        # The driver has consumed its current read batch; it reads again only when told to.
        self._ready_for_input_issued = False

        if self._state != 'closed':
            ctx.defer(lambda ctx2: check.isinstance(ctx2.handler, RpcSessionIoPipelineHandler)._maybe_ready_for_input(ctx2))  # noqa

    ##
    # lifecycle

    def _arm_close_drain(self, ctx: IoPipelineHandlerContext) -> None:
        if self._close_handle is not None:
            return
        if (t := self._config.close_drain_timeout_s) is None:
            return

        self._close_handle = self._schedule(
            ctx,
            t,
            lambda ctx2: check.isinstance(ctx2.handler, RpcSessionIoPipelineHandler)._on_close_drain_timeout(ctx2),  # noqa
        )

    def _on_close_drain_timeout(self, ctx: IoPipelineHandlerContext) -> None:
        self._close_handle = None
        if self._state != 'closing':
            return

        self._finish_close(ctx, RpcTimeoutError('close drain timed out with work still in flight'))

    def _on_close(self, ctx: IoPipelineHandlerContext, graceful: bool) -> None:
        if self._state == 'closed':
            return

        if not graceful:
            self._finish_close(ctx, None)
            return

        if self._state == 'closing':
            return
        self._state = 'closing'

        if not self._pending_out and not self._inflight_in:
            self._finish_close(ctx, None)
            return

        self._arm_close_drain(ctx)

    def _on_peer_eof(self, ctx: IoPipelineHandlerContext) -> None:
        if self._state == 'closed':
            return

        # No further responses can arrive.
        self._fail_pending_out(ctx, RpcConnectionClosedError('peer closed the connection'))
        if self._is_closed():
            return

        if self._config.on_peer_eof == 'drain' and self._inflight_in:
            # Keep answering what is already in flight; the peer may only have half-closed.
            self._state = 'closing'
            self._arm_close_drain(ctx)
            return

        self._finish_close(ctx, None)

    def _finish_close(
            self,
            ctx: IoPipelineHandlerContext,
            exc: ta.Optional[BaseException],
            *,
            transport_ok: bool = True,
    ) -> None:
        """
        Enter the terminal state exactly once: fail everything pending, abort everything in flight, announce Closed, and
        complete pipeline output.
        """

        if self._state == 'closed':
            return
        self._state = 'closed'
        self._close_exc = exc

        if (h := self._close_handle) is not None:
            self._close_handle = None
            h.cancel()

        closed_exc = self._closed_error()

        self._fail_pending_out(ctx, closed_exc)

        inflight = list(self._inflight_in.values())
        self._inflight_in.clear()
        for entry in inflight:
            self._cancel_handle(entry)
            if transport_ok and self._config.respond_to_aborted_inbound and not self._sent_final_output:
                ctx.feed_out(self._shutting_down_response(entry.request.id))
            self._emit(ctx, Rsm.RequestHandlingAborted(entry.request, closed_exc))

        self._emit(ctx, Rsm.Closed(exc))

        if exc is not None:
            # Also surface the failure as a raw exception output: drivers return those to the host immediately even
            # while ordinary output is held behind a stalled transport flush, which is exactly when a failing close most
            # needs to wake the host up.
            ctx.feed_out(exc)

        if not self._sent_final_output and not ctx.pipeline.saw_final_output:
            self._sent_final_output = True
            ctx.feed_final_output()

    ##
    # handler interface

    def notify(self, ctx: IoPipelineHandlerContext, no: IoPipelineHandlerNotification) -> None:
        if isinstance(no, IoPipelineHandlerNotifications.Added):
            if self._needs_scheduling():
                check.not_none(ctx.services.find(IoPipelineScheduling))

        elif isinstance(no, IoPipelineHandlerNotifications.Removed):
            for po in self._pending_out.values():
                self._cancel_handle(po)
            for pp in self._pending_pings.values():
                self._cancel_handle(pp)
            for ii in self._inflight_in.values():
                self._cancel_handle(ii)
            if (h := self._close_handle) is not None:
                self._close_handle = None
                h.cancel()

    def _on_command(self, ctx: IoPipelineHandlerContext, cmd: Rsm.Command) -> None:
        check.state(self._state != 'new', 'command received before initial input')

        if isinstance(cmd, Rsm.Close):
            self._on_close(ctx, cmd.graceful)
            return

        if isinstance(cmd, Rsm.CancelRequest):
            self._on_cancel_request(ctx, cmd)
            return

        if isinstance(cmd, Rsm.SendResponse):
            self._on_send_response(ctx, cmd.response)
            return

        if self._state != 'open':
            closed_exc = self._closed_error()
            if isinstance(cmd, Rsm.SendRequest):
                self._emit(ctx, Rsm.RequestFailed(cmd.request, closed_exc))
            elif isinstance(cmd, Rsm.SendPing):
                self._emit(ctx, Rsm.PingFailed(cmd.ping, closed_exc))
            elif isinstance(cmd, Rsm.SendNotification):
                log.debug('Dropping notification sent while %s: %r', self._state, cmd.notification)
            else:
                raise TypeError(cmd)
            return

        self._current_fence = None
        try:
            if isinstance(cmd, Rsm.SendRequest):
                self._on_send_request(ctx, cmd)
            elif isinstance(cmd, Rsm.SendNotification):
                self._on_send_notification(ctx, cmd)
            elif isinstance(cmd, Rsm.SendPing):
                self._on_send_ping(ctx, cmd)
            else:
                raise TypeError(cmd)
        finally:
            self._report_sent(ctx, cmd)

    def _on_envelope(self, ctx: IoPipelineHandlerContext, msg: RpcEnvelope) -> None:
        if isinstance(msg, RpcRequestMessage):
            self._on_inbound_request(ctx, msg)

        elif isinstance(msg, (RpcResultMessage, RpcErrorMessage)):
            self._on_inbound_response(ctx, msg)

        elif isinstance(msg, RpcNotificationMessage):
            self._emit(ctx, Rsm.NotificationReceived(msg))

        elif isinstance(msg, RpcCancelMessage):
            self._on_inbound_cancel(ctx, msg)

        elif isinstance(msg, RpcPingMessage):
            self._on_inbound_ping(ctx, msg)

        elif isinstance(msg, RpcPongMessage):
            self._on_inbound_pong(ctx, msg)

        else:
            raise TypeError(msg)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, Rsm.Command):
            self._on_command(ctx, msg)

        elif isinstance(msg, RpcEnvelope):
            if self._state == 'closed':
                log.debug('Dropping envelope received after close: %r', msg)
                return
            self._on_envelope(ctx, msg)

        elif isinstance(msg, Rsm.OutboundEncodeFailed):
            self._on_encode_failed(ctx, msg)

        elif isinstance(msg, IoPipelineMessages.InitialInput):
            check.state(self._state == 'new', 'duplicate initial input')
            self._state = 'open'
            ctx.feed_in(msg)
            self._maybe_ready_for_input(ctx)

        elif isinstance(msg, IoPipelineMessages.FinalInput):
            self._on_peer_eof(ctx)
            ctx.feed_in(msg)

        elif isinstance(msg, IoPipelineMessages.Error):
            self._finish_close(ctx, msg.exc, transport_ok=False)

        elif isinstance(msg, IdleStateIoPipelineEvent):
            # Idle means no messages *and* nothing in flight: a long-running handler or a slow peer answering a request
            # is covered by the per-request timeouts, not this one.
            if (
                    msg.state is IoPipelineIdleState.ALL_IDLE and
                    not self._pending_out and
                    not self._pending_pings and
                    not self._inflight_in
            ):
                self._finish_close(ctx, RpcTimeoutError('connection idle timed out'))

        elif isinstance(msg, IoPipelineFlowMessages.FlushInput):
            self._on_flush_input(ctx)
            ctx.feed_in(msg)

        elif isinstance(msg, IoPipelineFlowMessages.PauseOutput):
            if not self._output_paused:
                self._output_paused = True
                self._emit(ctx, Rsm.OutputPaused())

        elif isinstance(msg, IoPipelineFlowMessages.ReadyForOutput):
            if self._output_paused:
                self._output_paused = False
                self._emit(ctx, Rsm.OutputResumed())

        else:
            ctx.feed_in(msg)
