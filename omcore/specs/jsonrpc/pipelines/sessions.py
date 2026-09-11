"""
The sans-io JSON-RPC session: the innermost pipeline handler, owning all protocol state for one connection.

JSON-RPC is symmetric - either peer may send requests, notifications, and responses at any time - so one session handler
serves both the client and server roles. It correlates responses to the requests this side sent, surfaces the requests
the peer sent for the host to answer, and enforces every timeout and limit which can be expressed without touching a
transport. Timers come from the driver's IoPipelineScheduling service, so they behave identically under every driver and
can be exercised deterministically with the pure driver's manual clock.

Everything the host needs to know arrives as an event fed outbound (see `messages.py`); everything the host wants done
arrives as a command fed inbound. The session never raises on peer misbehavior: it answers, ignores, or closes by
policy.

Reentrancy: feeding a message outbound can synchronously deliver an Error back into this handler and change its state (a
failed write, an oversized message reported by the codec). Every method therefore re-checks state after any `feed_out`,
and the terminal `_finish_close` is idempotent.
"""
import functools
import typing as ta
import weakref

from .... import check
from .... import dataclasses as dc
from ....io.pipelines import all as ipl
from ....logs import all as logs
from ..errors import REQUEST_TIMED_OUT_ERROR_CODE
from ..errors import RESPONSE_TOO_LARGE_ERROR_CODE
from ..errors import SERVER_BUSY_ERROR_CODE
from ..errors import SERVER_SHUTTING_DOWN_ERROR_CODE
from ..errors import JsonrpcConnectionClosedError
from ..errors import JsonrpcMessageTooLargeError
from ..errors import JsonrpcProtocolError
from ..errors import JsonrpcTimeoutError
from ..errors import JsonrpcTooManyRequestsError
from ..errors import KnownErrors
from ..types import Batch
from ..types import Error
from ..types import Id
from ..types import InvalidMessage
from ..types import NotSpecified
from ..types import Request
from ..types import Response
from .configs import JsonrpcPipelineConfig
from .messages import JsonrpcPipelineMessages as Jpm


log = logs.get_module_logger(globals())


JsonrpcSessionState: ta.TypeAlias = ta.Literal['new', 'open', 'closing', 'closed']


##


class JsonrpcSessionHandler(ipl.Handler):
    @dc.dataclass()
    class _InBatch:
        """
        An inbound batch whose responses are collected and sent together once every member has been answered. The spec
        permits any order, but responses are kept in request order for determinism.
        """

        remaining: int
        responses: list[Response | None]

    @dc.dataclass(frozen=True)
    class _InBatchSlot:
        batch: JsonrpcSessionHandler._InBatch
        index: int

    @dc.dataclass()
    class _PendingOut:
        request: Request
        handle: ipl.Scheduling.Handle | None = None

    @dc.dataclass()
    class _InflightIn:
        request: Request
        handle: ipl.Scheduling.Handle | None = None
        slot: JsonrpcSessionHandler._InBatchSlot | None = None

    def __init__(self, config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT) -> None:
        super().__init__()

        self._config = config

        self._state: JsonrpcSessionState = 'new'

        self._pending_out: dict[Id, JsonrpcSessionHandler._PendingOut] = {}
        self._inflight_in: dict[Id, JsonrpcSessionHandler._InflightIn] = {}

        self._consecutive_invalid = 0
        self._output_paused = False
        self._ready_for_input_issued = False

        self._close_handle: ipl.Scheduling.Handle | None = None
        self._close_exc: BaseException | None = None
        self._sent_final_output = False

        self._sending_substitute = False

        # The flush fence issued while handling the current send command, if any, so completion can be reported.
        self._current_fence: ipl.FlowMessages.FlushOutput | None = None

    def __repr__(self) -> str:
        return (
            f'{type(self).__name__}@{id(self):x}'
            f'<{self._state}, pending_out={len(self._pending_out)}, inflight_in={len(self._inflight_in)}>'
        )

    @property
    def config(self) -> JsonrpcPipelineConfig:
        return self._config

    @property
    def state(self) -> JsonrpcSessionState:
        return self._state

    @property
    def pending_outbound_ids(self) -> ta.AbstractSet[Id]:
        return self._pending_out.keys()

    @property
    def inflight_inbound_ids(self) -> ta.AbstractSet[Id]:
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
            c.inbound_handling_timeout_s,
            c.close_drain_timeout_s,
        ))

    def _schedule(
            self,
            ctx: ipl.HandlerContext,
            delay_s: float,
            fn: ta.Callable[[ipl.HandlerContext], None],
    ) -> ipl.Scheduling.Handle:
        return ctx.services[ipl.Scheduling].schedule_context(ctx.ref, delay_s, fn)

    @staticmethod
    def _cancel_handle(entry: _PendingOut | _InflightIn) -> None:
        if (handle := entry.handle) is not None:
            entry.handle = None
            handle.cancel()

    def _emit(self, ctx: ipl.HandlerContext, event: Jpm.Event) -> None:
        ctx.feed_out(event)

    def _send(self, ctx: ipl.HandlerContext, payload: ta.Any) -> bool:
        """Feed a payload toward the wire and flush. Returns False if the session closed reentrantly while doing so."""

        if self._sent_final_output:
            return False

        ctx.feed_out(payload)
        if self._is_closed():
            return False

        if ctx.services.find(ipl.Flow) is not None:
            fence = ipl.FlowMessages.FlushOutput()
            self._current_fence = fence
            ctx.feed_out(fence)

        return not self._is_closed()

    @staticmethod
    def _on_send_fence_done(
            ctx_ref: ta.Callable[[], ipl.HandlerContext | None],
            cmd: Jpm.Command,
            fence: ipl.Messages.Completable[None],
    ) -> None:
        # Failure means the driver is closing, which the host learns of from Closed; only success is worth reporting.
        # Output after FinalOutput reached the terminal is rejected by the pipeline, so check for that too.
        if not fence.is_succeeded():
            return
        if (ctx := ctx_ref()) is None or ctx.invalidated or ctx.pipeline.saw_final_output:
            return
        ctx.feed_out(Jpm.Sent(cmd))

    def _report_sent(self, ctx: ipl.HandlerContext, cmd: Jpm.Command) -> None:
        """Emit Sent for a send command, now if nothing needed flushing, else once its fence completes."""

        fence = self._current_fence
        self._current_fence = None

        if self._is_closed():
            return

        if fence is not None and not fence.is_done():
            fence.add_listener(functools.partial(self._on_send_fence_done, weakref.ref(ctx), cmd))
        elif fence is None or fence.is_succeeded():
            self._emit(ctx, Jpm.Sent(cmd))

    def _closed_error(self) -> JsonrpcConnectionClosedError:
        if (exc := self._close_exc) is not None:
            err = JsonrpcConnectionClosedError(f'connection failed: {exc!r}')
            err.__cause__ = exc
            return err
        return JsonrpcConnectionClosedError('connection closed')

    ##
    # answering inbound requests

    def _answer(
            self,
            ctx: ipl.HandlerContext,
            response: Response | None,
            slot: _InBatchSlot | None,
    ) -> None:
        """
        Deliver a response for an inbound request, or account for one which will never be sent (response None).

        Members of an inbound batch are held until the whole batch is answered, per the spec.
        """

        if slot is None:
            if response is not None:
                self._send(ctx, response)
            return

        batch = slot.batch
        check.none(batch.responses[slot.index])
        batch.responses[slot.index] = response
        batch.remaining -= 1
        check.state(batch.remaining >= 0)

        if batch.remaining == 0:
            responses = [r for r in batch.responses if r is not None]
            if responses:
                self._send(ctx, Batch(responses))

    def _error_response(self, id: Id, code: int, message: str) -> Response:  # noqa
        return Response(id, error=Error(code, message))

    ##
    # outbound requests

    def _effective_timeout(self, timeout_s: float | None | type[NotSpecified]) -> float | None:
        if timeout_s is NotSpecified:
            return self._config.default_request_timeout_s
        return ta.cast('float | None', timeout_s)

    def _track_pending_out(self, ctx: ipl.HandlerContext, request: Request) -> _PendingOut | None:
        """Register an outbound request, or emit RequestFailed and return None if it cannot be sent."""

        if request.is_notification:
            self._emit(ctx, Jpm.RequestFailed(request, ValueError('cannot track a notification as a request')))
            return None

        if (rid := request.id_value()) in self._pending_out:
            self._emit(ctx, Jpm.RequestFailed(request, ValueError(f'duplicate outbound request id: {rid!r}')))
            return None

        if (mx := self._config.max_pending_outbound) is not None and len(self._pending_out) >= mx:
            self._emit(ctx, Jpm.RequestFailed(request, JsonrpcTooManyRequestsError(
                f'too many pending outbound requests: {mx}',
            )))
            return None

        entry = self._PendingOut(request)
        self._pending_out[rid] = entry
        return entry

    def _arm_pending_out(
            self,
            ctx: ipl.HandlerContext,
            entry: _PendingOut,
            timeout_s: float | None | type[NotSpecified],
    ) -> None:
        rid = entry.request.id_value()
        if self._pending_out.get(rid) is not entry:
            # Failed reentrantly while being sent.
            return

        if (t := self._effective_timeout(timeout_s)) is not None:
            entry.handle = self._schedule(
                ctx,
                t,
                lambda ctx2: check.isinstance(ctx2.handler, JsonrpcSessionHandler)._on_request_timeout(ctx2, rid),  # noqa
            )

    def _on_send_request(self, ctx: ipl.HandlerContext, cmd: Jpm.SendRequest) -> None:
        if (entry := self._track_pending_out(ctx, cmd.request)) is None:
            return

        if not self._send(ctx, cmd.request):
            return

        self._arm_pending_out(ctx, entry, cmd.timeout_s)

    def _on_send_batch(self, ctx: ipl.HandlerContext, cmd: Jpm.SendBatch) -> None:
        entries: list[JsonrpcSessionHandler._PendingOut] = []
        items: list[Request] = []

        for item in cmd.batch.items:
            if not isinstance(item, Request):
                # Only the peer's requests get responses; a batch of our own must be requests and notifications.
                for e in entries:
                    self._pending_out.pop(e.request.id_value(), None)
                    self._emit(ctx, Jpm.RequestFailed(e.request, TypeError(f'cannot send in a batch: {item!r}')))
                return

            items.append(item)
            if item.is_notification:
                continue

            if (entry := self._track_pending_out(ctx, item)) is None:
                continue
            entries.append(entry)

        if not items:
            return

        if not self._send(ctx, Batch(items)):
            return

        for entry in entries:
            self._arm_pending_out(ctx, entry, cmd.timeout_s)

    def _on_send_notification(self, ctx: ipl.HandlerContext, cmd: Jpm.SendNotification) -> None:
        if not cmd.notification.is_notification:
            log.warning('Dropping non-notification sent as a notification: %r', cmd.notification)
            return

        self._send(ctx, cmd.notification)

    def _on_request_timeout(self, ctx: ipl.HandlerContext, rid: Id) -> None:
        if (entry := self._pending_out.pop(rid, None)) is None:
            return
        entry.handle = None

        self._emit(ctx, Jpm.RequestFailed(entry.request, JsonrpcTimeoutError(
            f'request {rid!r} ({entry.request.method}) timed out',
        )))

        self._after_pending_out_completed(ctx)

    def _on_cancel_request(self, ctx: ipl.HandlerContext, rid: Id) -> None:
        if (entry := self._pending_out.pop(rid, None)) is None:
            return
        self._cancel_handle(entry)

        self._after_pending_out_completed(ctx)

    def _fail_pending_out(self, ctx: ipl.HandlerContext, exc: Exception) -> None:
        entries = list(self._pending_out.values())
        self._pending_out.clear()
        for entry in entries:
            self._cancel_handle(entry)
            self._emit(ctx, Jpm.RequestFailed(entry.request, exc))

    def _after_pending_out_completed(self, ctx: ipl.HandlerContext) -> None:
        if self._state == 'closing' and not self._pending_out and not self._inflight_in:
            self._finish_close(ctx, None)

    ##
    # inbound responses

    def _on_inbound_response(self, ctx: ipl.HandlerContext, response: Response) -> None:
        self._consecutive_invalid = 0

        if (entry := self._pending_out.pop(response.id, None)) is None:
            if self._config.on_unmatched_response == 'close':
                self._finish_close(ctx, JsonrpcProtocolError(f'unmatched response id: {response.id!r}'))
            else:
                log.debug('Dropping unmatched response: %r', response)
            return

        self._cancel_handle(entry)
        self._emit(ctx, Jpm.ResponseReceived(entry.request, response))

        self._after_pending_out_completed(ctx)

    ##
    # inbound requests

    def _at_inflight_limit(self) -> bool:
        return (mx := self._config.max_inflight_inbound) is not None and len(self._inflight_in) >= mx

    def _on_inbound_request(
            self,
            ctx: ipl.HandlerContext,
            request: Request,
            slot: _InBatchSlot | None,
    ) -> None:
        self._consecutive_invalid = 0

        if request.is_notification:
            self._emit(ctx, Jpm.NotificationReceived(request))
            return

        rid = request.id_value()

        if self._state != 'open':
            self._answer(
                ctx,
                self._error_response(rid, SERVER_SHUTTING_DOWN_ERROR_CODE, 'Server shutting down'),
                slot,
            )
            return

        if rid in self._inflight_in:
            self._answer(
                ctx,
                self._error_response(rid, KnownErrors.INVALID_REQUEST.code, 'Duplicate request id'),
                slot,
            )
            return

        if self._at_inflight_limit() and self._config.inflight_limit_policy == 'reject':
            self._answer(
                ctx,
                self._error_response(rid, SERVER_BUSY_ERROR_CODE, 'Too many concurrent requests'),
                slot,
            )
            return

        entry = self._InflightIn(request, slot=slot)
        self._inflight_in[rid] = entry

        if (t := self._config.inbound_handling_timeout_s) is not None:
            entry.handle = self._schedule(
                ctx,
                t,
                lambda ctx2: check.isinstance(ctx2.handler, JsonrpcSessionHandler)._on_inbound_handling_timeout(ctx2, rid),  # noqa
            )

        self._emit(ctx, Jpm.RequestReceived(request))

    def _on_send_response(self, ctx: ipl.HandlerContext, response: Response) -> None:
        if (entry := self._inflight_in.pop(response.id, None)) is None:
            log.debug('Dropping response to unknown or aborted inbound request: %r', response)
            return
        self._cancel_handle(entry)

        self._answer(ctx, response, entry.slot)

        self._after_inflight_in_completed(ctx)

    def _on_inbound_handling_timeout(self, ctx: ipl.HandlerContext, rid: Id) -> None:
        if (entry := self._inflight_in.pop(rid, None)) is None:
            return
        entry.handle = None

        self._answer(
            ctx,
            (
                self._error_response(rid, REQUEST_TIMED_OUT_ERROR_CODE, 'Request handling timed out')
                if self._config.respond_to_aborted_inbound else None
            ),
            entry.slot,
        )
        if self._is_closed():
            return

        self._emit(ctx, Jpm.RequestHandlingAborted(entry.request, JsonrpcTimeoutError(
            f'handling of inbound request {rid!r} ({entry.request.method}) timed out',
        )))

        self._after_inflight_in_completed(ctx)

    def _after_inflight_in_completed(self, ctx: ipl.HandlerContext) -> None:
        if self._state == 'closing':
            if not self._pending_out and not self._inflight_in:
                self._finish_close(ctx, None)
            return

        self._maybe_ready_for_input(ctx)

    ##
    # batches and invalid messages

    def _on_inbound_batch(self, ctx: ipl.HandlerContext, batch: Batch) -> None:
        if not self._config.accept_batches:
            self._on_invalid(ctx, InvalidMessage(
                KnownErrors.INVALID_REQUEST.to_error(message='Batches not accepted'),
                raw=batch,
            ), None)
            return

        if (mx := self._config.max_batch_size) is not None and len(batch) > mx:
            self._on_invalid(ctx, InvalidMessage(
                KnownErrors.INVALID_REQUEST.to_error(message=f'Batch exceeds maximum size of {mx}'),
                raw=batch,
            ), None)
            return

        answerable = [
            (
                (isinstance(item, Request) and not item.is_notification) or
                (isinstance(item, InvalidMessage) and not item.looks_like_response)
            )
            for item in batch.items
        ]
        inb: JsonrpcSessionHandler._InBatch | None = None
        if (n := sum(answerable)):
            inb = self._InBatch(n, [None] * len(batch.items))

        for i, item in enumerate(batch.items):
            slot = self._InBatchSlot(inb, i) if inb is not None and answerable[i] else None

            if isinstance(item, Request):
                self._on_inbound_request(ctx, item, slot)
            elif isinstance(item, Response):
                self._on_inbound_response(ctx, item)
            elif isinstance(item, InvalidMessage):
                self._on_invalid(ctx, item, slot)
            else:
                raise TypeError(item)

            if self._is_closed():
                return

    def _on_invalid(self, ctx: ipl.HandlerContext, inv: InvalidMessage, slot: _InBatchSlot | None) -> None:
        self._consecutive_invalid += 1
        log.debug('Received invalid message: %r', inv)

        exc = JsonrpcProtocolError(f'invalid message received: {inv.exc!r}')

        if self._config.on_invalid_message == 'close':
            self._finish_close(ctx, exc)
            return

        if not inv.looks_like_response:
            self._answer(ctx, inv.to_response(), slot)
            if self._is_closed():
                return

        if (mx := self._config.max_consecutive_invalid) is not None and self._consecutive_invalid >= mx:
            self._finish_close(ctx, JsonrpcProtocolError(
                f'received {self._consecutive_invalid} consecutive invalid messages',
            ))

    def _on_encode_failed(self, ctx: ipl.HandlerContext, msg: Jpm.OutboundEncodeFailed) -> None:
        payload = msg.payload
        exc = msg.exc

        if self._sending_substitute:
            # Even the minimal error response would not fit: the frame limit is misconfigured. Dropping the response is
            # the least bad option - the peer times out and the connection stays usable for smaller messages.
            log.error('Cannot send even a substitute error response, dropping: %r', exc)
            return

        items: ta.Sequence[ta.Any] = payload.items if isinstance(payload, Batch) else [payload]
        substitutes: list[Response] = []

        for item in items:
            if isinstance(item, Request):
                if item.is_notification:
                    log.warning('Dropping unencodable notification: %r', exc)
                    continue

                if (entry := self._pending_out.pop(item.id_value(), None)) is not None:
                    self._cancel_handle(entry)
                    fexc: Exception
                    if isinstance(exc, JsonrpcMessageTooLargeError):
                        fexc = exc
                    else:
                        fexc = ValueError(f'request could not be encoded: {exc!r}')
                        fexc.__cause__ = exc
                    self._emit(ctx, Jpm.RequestFailed(entry.request, fexc))

            elif isinstance(item, Response):
                log.warning('Substituting error for unencodable response %r: %r', item.id, exc)
                if isinstance(exc, JsonrpcMessageTooLargeError):
                    substitutes.append(self._error_response(item.id, RESPONSE_TOO_LARGE_ERROR_CODE, 'Response too large'))  # noqa
                else:
                    substitutes.append(self._error_response(item.id, KnownErrors.INTERNAL_ERROR.code, 'Response could not be encoded'))  # noqa

            elif isinstance(item, InvalidMessage):
                substitutes.append(item.to_response())

        if substitutes:
            sub: Response | Batch = Batch(substitutes) if isinstance(payload, Batch) else substitutes[0]
            self._sending_substitute = True
            try:
                if not self._send(ctx, sub):
                    return
            finally:
                self._sending_substitute = False

        self._after_pending_out_completed(ctx)

    ##
    # flow control

    def _maybe_ready_for_input(self, ctx: ipl.HandlerContext) -> None:
        """Under the 'pause' policy, lets the driver read again once there is room for more inbound requests."""

        if (flow := ctx.services.find(ipl.Flow)) is None or flow.is_auto_read():
            return
        if self._state == 'closed' or self._ready_for_input_issued or self._at_inflight_limit():
            return

        self._ready_for_input_issued = True
        ctx.feed_out(ipl.FlowMessages.ReadyForInput())

    def _on_flush_input(self, ctx: ipl.HandlerContext) -> None:
        # The driver has consumed its current read batch; it reads again only when told to.
        self._ready_for_input_issued = False

        if self._state != 'closed':
            ctx.defer(lambda ctx2: check.isinstance(ctx2.handler, JsonrpcSessionHandler)._maybe_ready_for_input(ctx2))  # noqa

    ##
    # lifecycle

    def _arm_close_drain(self, ctx: ipl.HandlerContext) -> None:
        if self._close_handle is not None:
            return
        if (t := self._config.close_drain_timeout_s) is None:
            return

        self._close_handle = self._schedule(
            ctx,
            t,
            lambda ctx2: check.isinstance(ctx2.handler, JsonrpcSessionHandler)._on_close_drain_timeout(ctx2),  # noqa
        )

    def _on_close_drain_timeout(self, ctx: ipl.HandlerContext) -> None:
        self._close_handle = None
        if self._state != 'closing':
            return

        self._finish_close(ctx, JsonrpcTimeoutError('close drain timed out with work still in flight'))

    def _on_close(self, ctx: ipl.HandlerContext, graceful: bool) -> None:
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

    def _on_peer_eof(self, ctx: ipl.HandlerContext) -> None:
        if self._state == 'closed':
            return

        # No further responses can arrive.
        self._fail_pending_out(ctx, JsonrpcConnectionClosedError('peer closed the connection'))
        if self._is_closed():
            return

        if self._config.on_peer_eof == 'drain' and self._inflight_in:
            # Keep answering what is already in flight; the peer may only have half-closed.
            self._state = 'closing'
            self._arm_close_drain(ctx)
            return

        self._finish_close(ctx, None)

    def _finish_close(self, ctx: ipl.HandlerContext, exc: BaseException | None, *, transport_ok: bool = True) -> None:
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
            self._answer(
                ctx,
                (
                    self._error_response(entry.request.id_value(), SERVER_SHUTTING_DOWN_ERROR_CODE, 'Server shutting down')  # noqa
                    if transport_ok and self._config.respond_to_aborted_inbound else None
                ),
                entry.slot,
            )
            self._emit(ctx, Jpm.RequestHandlingAborted(entry.request, closed_exc))

        self._emit(ctx, Jpm.Closed(exc))

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

    def notify(self, ctx: ipl.HandlerContext, no: ipl.HandlerNotification) -> None:
        if isinstance(no, ipl.HandlerNotifications.Added):
            if self._needs_scheduling():
                check.not_none(ctx.services.find(ipl.Scheduling))

        elif isinstance(no, ipl.HandlerNotifications.Removed):
            for po in self._pending_out.values():
                self._cancel_handle(po)
            for ii in self._inflight_in.values():
                self._cancel_handle(ii)
            if (h := self._close_handle) is not None:
                self._close_handle = None
                h.cancel()

    def _on_command(self, ctx: ipl.HandlerContext, cmd: Jpm.Command) -> None:
        check.state(self._state != 'new', 'command received before initial input')

        if isinstance(cmd, Jpm.Close):
            self._on_close(ctx, cmd.graceful)
            return

        if isinstance(cmd, Jpm.CancelRequest):
            self._on_cancel_request(ctx, cmd.id)
            return

        if isinstance(cmd, Jpm.SendResponse):
            self._on_send_response(ctx, cmd.response)
            return

        if self._state != 'open':
            closed_exc = self._closed_error()
            if isinstance(cmd, Jpm.SendRequest):
                self._emit(ctx, Jpm.RequestFailed(cmd.request, closed_exc))
            elif isinstance(cmd, Jpm.SendBatch):
                for item in cmd.batch.items:
                    if isinstance(item, Request) and not item.is_notification:
                        self._emit(ctx, Jpm.RequestFailed(item, closed_exc))
            elif isinstance(cmd, Jpm.SendNotification):
                log.debug('Dropping notification sent while %s: %r', self._state, cmd.notification)
            else:
                raise TypeError(cmd)
            return

        self._current_fence = None
        try:
            if isinstance(cmd, Jpm.SendRequest):
                self._on_send_request(ctx, cmd)
            elif isinstance(cmd, Jpm.SendNotification):
                self._on_send_notification(ctx, cmd)
            elif isinstance(cmd, Jpm.SendBatch):
                self._on_send_batch(ctx, cmd)
            else:
                raise TypeError(cmd)
        finally:
            self._report_sent(ctx, cmd)

    def inbound(self, ctx: ipl.HandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, Jpm.Command):
            self._on_command(ctx, msg)

        elif isinstance(msg, Request):
            self._on_inbound_request(ctx, msg, None)

        elif isinstance(msg, Response):
            self._on_inbound_response(ctx, msg)

        elif isinstance(msg, Batch):
            self._on_inbound_batch(ctx, msg)

        elif isinstance(msg, InvalidMessage):
            self._on_invalid(ctx, msg, None)

        elif isinstance(msg, Jpm.OutboundEncodeFailed):
            self._on_encode_failed(ctx, msg)

        elif isinstance(msg, ipl.Messages.InitialInput):
            check.state(self._state == 'new', 'duplicate initial input')
            self._state = 'open'
            ctx.feed_in(msg)
            self._maybe_ready_for_input(ctx)

        elif isinstance(msg, ipl.Messages.FinalInput):
            self._on_peer_eof(ctx)
            ctx.feed_in(msg)

        elif isinstance(msg, ipl.Messages.Error):
            self._finish_close(ctx, msg.exc, transport_ok=False)

        elif isinstance(msg, ipl.IdleStateEvent):
            # Idle means no messages *and* nothing in flight: a long-running handler or a slow peer answering a request
            # is covered by the per-request timeouts, not this one.
            if msg.state is ipl.IdleState.ALL_IDLE and not self._pending_out and not self._inflight_in:
                self._finish_close(ctx, JsonrpcTimeoutError('connection idle timed out'))

        elif isinstance(msg, ipl.FlowMessages.FlushInput):
            self._on_flush_input(ctx)
            ctx.feed_in(msg)

        elif isinstance(msg, ipl.FlowMessages.PauseOutput):
            if not self._output_paused:
                self._output_paused = True
                self._emit(ctx, Jpm.OutputPaused())

        elif isinstance(msg, ipl.FlowMessages.ReadyForOutput):
            if self._output_paused:
                self._output_paused = False
                self._emit(ctx, Jpm.OutputResumed())

        else:
            ctx.feed_in(msg)
