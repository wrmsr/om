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

from ..io.pipelines.core import IoPipelineHandler
from ..io.pipelines.core import IoPipelineHandlerContext
from ..io.pipelines.core import IoPipelineHandlerNotification
from ..io.pipelines.core import IoPipelineHandlerNotifications
from ..io.pipelines.core import IoPipelineMessages
from ..io.pipelines.flow.types import IoPipelineFlow
from ..io.pipelines.flow.types import IoPipelineFlowMessages
from ..io.pipelines.sched.timeouts import IdleStateIoPipelineEvent
from ..io.pipelines.sched.timeouts import IoPipelineIdleState
from ..io.pipelines.sched.types import IoPipelineScheduling
from ..lite.check import check
from ..logs.modules import get_module_logger
from .configs import RpcConfig
from .errors import RpcCancelledError
from .errors import RpcConnectionClosedError
from .errors import RpcErrorCodes
from .errors import RpcMessageTooLargeError
from .errors import RpcProtocolError
from .errors import RpcRemoteErrorData
from .errors import RpcTimeoutError
from .errors import RpcTooManyRequestsError
from .errors import rpc_exception_type_name
from .messages import RpcCancelMessage
from .messages import RpcEnvelope
from .messages import RpcErrorMessage
from .messages import RpcNotificationMessage
from .messages import RpcPingMessage
from .messages import RpcPongMessage
from .messages import RpcRequestMessage
from .messages import RpcResponseMessage
from .messages import RpcResultMessage
from .messages import RpcSessionMessages
from .messages import RpcUnspecified


RpcSessionState = ta.Literal['new', 'open', 'closing', 'closed']  # ta.TypeAlias


log = get_module_logger(globals())  # noqa


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

        # Under consolidate_flushes: the fence fed last and not yet completed, if any, and the fence the sends made
        # meanwhile share, fed once that one completes.
        self._inflight_fence: ta.Optional[IoPipelineFlowMessages.FlushOutput] = None
        self._pending_fence: ta.Optional[IoPipelineFlowMessages.FlushOutput] = None

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

    def _emit(self, ctx: IoPipelineHandlerContext, event: RpcSessionMessages.Event) -> None:
        ctx.feed_out(event)

    def _send(self, ctx: IoPipelineHandlerContext, envelope: RpcEnvelope) -> bool:
        """Feed an envelope toward the wire and flush. Returns False if the session closed reentrantly meanwhile."""

        if self._sent_final_output:
            return False

        ctx.feed_out(envelope)
        if self._is_closed():
            return False

        if ctx.services.find(IoPipelineFlow) is not None:
            if not self._config.consolidate_flushes:
                fence = IoPipelineFlowMessages.FlushOutput()
                self._current_fence = fence
                ctx.feed_out(fence)

            elif self._inflight_fence is not None:
                # A flush is under way: this send joins the one which follows it.
                if self._pending_fence is None:
                    self._pending_fence = IoPipelineFlowMessages.FlushOutput()
                self._current_fence = self._pending_fence

            else:
                fence = IoPipelineFlowMessages.FlushOutput()
                self._current_fence = fence
                self._feed_consolidated_fence(ctx, fence)

        return not self._is_closed()

    def _feed_consolidated_fence(
            self,
            ctx: IoPipelineHandlerContext,
            fence: IoPipelineFlowMessages.FlushOutput,
    ) -> None:
        self._inflight_fence = fence
        fence.add_listener(functools.partial(self._on_consolidated_fence_done, weakref.ref(ctx)))
        ctx.feed_out(fence)

    @staticmethod
    def _on_consolidated_fence_done(
            ctx_ref: ta.Callable[[], ta.Optional[IoPipelineHandlerContext]],
            fence: IoPipelineMessages.Completable[None],
    ) -> None:
        if (ctx := ctx_ref()) is None or ctx.invalidated:
            return
        h = ta.cast('RpcSessionIoPipelineHandler', ctx.handler)
        if h._inflight_fence is fence:  # noqa
            h._inflight_fence = None  # noqa
        if fence.is_succeeded():
            h._flush_pending_fence(ctx)  # noqa

    def _flush_pending_fence(self, ctx: IoPipelineHandlerContext) -> None:
        if (fence := self._pending_fence) is None or self._inflight_fence is not None:
            return
        self._pending_fence = None
        if ctx.invalidated or self._sent_final_output or ctx.pipeline.saw_final_output:
            # Closed meanwhile: the fence is never fed, and closure has failed whatever waited on it.
            return
        self._feed_consolidated_fence(ctx, fence)

    @staticmethod
    def _on_send_fence_done(
            ctx_ref: ta.Callable[[], ta.Optional[IoPipelineHandlerContext]],
            cmd: RpcSessionMessages.Command,
            fence: IoPipelineMessages.Completable[None],
    ) -> None:
        # Failure means the driver is closing, which the host learns of from Closed; only success is worth reporting.
        # Output after FinalOutput reached the terminal is rejected by the pipeline, so check for that too.
        if not fence.is_succeeded():
            return
        if (ctx := ctx_ref()) is None or ctx.invalidated or ctx.pipeline.saw_final_output:
            return
        ctx.feed_out(RpcSessionMessages.Sent(cmd))

    def _report_sent(self, ctx: IoPipelineHandlerContext, cmd: RpcSessionMessages.Command) -> None:
        """Emit Sent for a send command, now if nothing needed flushing, else once its fence completes."""

        fence = self._current_fence
        self._current_fence = None

        if self._is_closed():
            return

        if fence is not None and not fence.is_done():
            fence.add_listener(functools.partial(self._on_send_fence_done, weakref.ref(ctx), cmd))
        elif fence is None or fence.is_succeeded():
            self._emit(ctx, RpcSessionMessages.Sent(cmd))

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
        return RpcRemoteErrorData(code=code, remote_type=rpc_exception_type_name(exc_type), message=message)

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
            self._emit(ctx, RpcSessionMessages.RequestFailed(
                request,
                ValueError(f'duplicate outbound request id: {rid!r}'),
            ))
            return None

        if (mx := self._config.max_pending_outbound) is not None and len(self._pending_out) >= mx:
            self._emit(ctx, RpcSessionMessages.RequestFailed(request, RpcTooManyRequestsError(
                f'too many pending outbound requests: {mx}',
            )))
            return None

        entry = self._PendingOut(request)
        self._pending_out[rid] = entry
        return entry

    def _on_send_request(self, ctx: IoPipelineHandlerContext, cmd: RpcSessionMessages.SendRequest) -> None:
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

    def _on_send_notification(self, ctx: IoPipelineHandlerContext, cmd: RpcSessionMessages.SendNotification) -> None:
        self._send(ctx, cmd.notification)

    def _send_cancel(self, ctx: IoPipelineHandlerContext, rid: ta.Any) -> None:
        if self._state != 'open':
            return
        self._send(ctx, RpcCancelMessage(rid))

    def _on_request_timeout(self, ctx: IoPipelineHandlerContext, rid: ta.Any) -> None:
        if (entry := self._pending_out.pop(rid, None)) is None:
            return
        entry.handle = None

        self._emit(ctx, RpcSessionMessages.RequestFailed(entry.request, RpcTimeoutError(
            f'request {rid!r} ({entry.request.method}) timed out',
        )))
        if self._is_closed():
            return

        if self._config.cancel_abandoned_requests:
            self._send_cancel(ctx, rid)
            if self._is_closed():
                return

        self._after_pending_out_completed(ctx)

    def _on_cancel_request(self, ctx: IoPipelineHandlerContext, cmd: RpcSessionMessages.CancelRequest) -> None:
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
            self._emit(ctx, RpcSessionMessages.RequestFailed(entry.request, exc))

        pings = list(self._pending_pings.values())
        self._pending_pings.clear()
        for ping in pings:
            self._cancel_handle(ping)
            self._emit(ctx, RpcSessionMessages.PingFailed(ping.ping, exc))

    def _after_pending_out_completed(self, ctx: IoPipelineHandlerContext) -> None:
        if self._state == 'closing' and not self._pending_out and not self._inflight_in:
            self._finish_close(ctx, None)

    ##
    # pings

    def _on_send_ping(self, ctx: IoPipelineHandlerContext, cmd: RpcSessionMessages.SendPing) -> None:
        ping = cmd.ping
        if (pid := ping.id) in self._pending_pings:
            self._emit(ctx, RpcSessionMessages.PingFailed(ping, ValueError(f'duplicate outbound ping id: {pid!r}')))
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

        self._emit(ctx, RpcSessionMessages.PingFailed(entry.ping, RpcTimeoutError(f'ping {pid!r} timed out')))

    def _on_inbound_ping(self, ctx: IoPipelineHandlerContext, ping: RpcPingMessage) -> None:
        if self._state == 'closed':
            return

        self._send(ctx, RpcPongMessage(ping.id))

    def _on_inbound_pong(self, ctx: IoPipelineHandlerContext, pong: RpcPongMessage) -> None:
        if (entry := self._pending_pings.pop(pong.id, None)) is None:
            log.debug('Dropping unmatched pong: %r', pong)
            return

        self._cancel_handle(entry)
        self._emit(ctx, RpcSessionMessages.PongReceived(entry.ping, pong))

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
        self._emit(ctx, RpcSessionMessages.ResponseReceived(entry.request, response))

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

        self._emit(ctx, RpcSessionMessages.RequestReceived(request))

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

        self._emit(ctx, RpcSessionMessages.RequestHandlingAborted(entry.request, RpcTimeoutError(
            f'handling of inbound request {rid!r} ({entry.request.method}) timed out',
        )))

        self._after_inflight_in_completed(ctx)

    def _on_inbound_cancel(self, ctx: IoPipelineHandlerContext, cancel: RpcCancelMessage) -> None:
        if (entry := self._inflight_in.pop(cancel.id, None)) is None:
            # Already answered, or never seen: cancels race with responses by nature.
            return
        self._cancel_handle(entry)

        self._emit(ctx, RpcSessionMessages.RequestHandlingAborted(entry.request, RpcCancelledError(
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

    def _on_encode_failed(self, ctx: IoPipelineHandlerContext, msg: RpcSessionMessages.OutboundEncodeFailed) -> None:
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
                self._emit(ctx, RpcSessionMessages.RequestFailed(entry.request, fexc))

            self._after_pending_out_completed(ctx)
            return

        if isinstance(envelope, RpcPingMessage):
            if (ping := self._pending_pings.pop(envelope.id, None)) is not None:
                self._cancel_handle(ping)
                self._emit(ctx, RpcSessionMessages.PingFailed(ping.ping, exc))
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
            self._emit(ctx, RpcSessionMessages.RequestHandlingAborted(entry.request, closed_exc))

        self._emit(ctx, RpcSessionMessages.Closed(exc))

        if exc is not None and not transport_ok:
            # The transport itself is in trouble - it failed, stalled, or the peer stopped answering or sent garbage -
            # so flushing what is left is unlikely to complete. Surfacing the failure as a raw exception output tells
            # the host to abort rather than wait on the final flush. A failure with a healthy transport (a drain or idle
            # timeout, a peer protocol violation caught by policy) instead flushes normally, so the answers just queued
            # for the requests in flight still reach the peer.
            ctx.feed_out(exc)

        if not self._sent_final_output and not ctx.pipeline.saw_final_output:
            if transport_ok and (fence := self._pending_fence) is not None:
                # Sends awaiting a flush are reported sent once their bytes are out, as ever.
                self._pending_fence = None
                ctx.feed_out(fence)
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

    def _on_command(self, ctx: IoPipelineHandlerContext, cmd: RpcSessionMessages.Command) -> None:
        check.state(self._state != 'new', 'command received before initial input')

        if isinstance(cmd, RpcSessionMessages.Close):
            self._on_close(ctx, cmd.graceful)
            return

        if isinstance(cmd, RpcSessionMessages.CancelRequest):
            self._on_cancel_request(ctx, cmd)
            return

        if isinstance(cmd, RpcSessionMessages.SendResponse):
            self._on_send_response(ctx, cmd.response)
            return

        if self._state != 'open':
            closed_exc = self._closed_error()
            if isinstance(cmd, RpcSessionMessages.SendRequest):
                self._emit(ctx, RpcSessionMessages.RequestFailed(cmd.request, closed_exc))
            elif isinstance(cmd, RpcSessionMessages.SendPing):
                self._emit(ctx, RpcSessionMessages.PingFailed(cmd.ping, closed_exc))
            elif isinstance(cmd, RpcSessionMessages.SendNotification):
                log.debug('Dropping notification sent while %s: %r', self._state, cmd.notification)
            else:
                raise TypeError(cmd)
            return

        self._current_fence = None
        try:
            if isinstance(cmd, RpcSessionMessages.SendRequest):
                self._on_send_request(ctx, cmd)
            elif isinstance(cmd, RpcSessionMessages.SendNotification):
                self._on_send_notification(ctx, cmd)
            elif isinstance(cmd, RpcSessionMessages.SendPing):
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
            self._emit(ctx, RpcSessionMessages.NotificationReceived(msg))

        elif isinstance(msg, RpcCancelMessage):
            self._on_inbound_cancel(ctx, msg)

        elif isinstance(msg, RpcPingMessage):
            self._on_inbound_ping(ctx, msg)

        elif isinstance(msg, RpcPongMessage):
            self._on_inbound_pong(ctx, msg)

        else:
            raise TypeError(msg)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, RpcSessionMessages.Command):
            self._on_command(ctx, msg)

        elif isinstance(msg, RpcEnvelope):
            if self._state == 'closed':
                log.debug('Dropping envelope received after close: %r', msg)
                return
            self._on_envelope(ctx, msg)

        elif isinstance(msg, RpcSessionMessages.OutboundEncodeFailed):
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
            if self._state == 'closed':
                # A failure after closing - the final flush timed out, say. Nothing may be output after FinalOutput, and
                # there is nothing left to do but abort, so the error is let past: unhandled, it fails the driver, which
                # is the abort.
                ctx.feed_in(msg)
                return
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
                self._emit(ctx, RpcSessionMessages.OutputPaused())

        elif isinstance(msg, IoPipelineFlowMessages.ReadyForOutput):
            if self._output_paused:
                self._output_paused = False
                self._emit(ctx, RpcSessionMessages.OutputResumed())

        else:
            ctx.feed_in(msg)
