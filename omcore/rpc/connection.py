# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
The connection: everything a host does with a session other than pumping its driver, written once, async-colored.

A connection sits on a runtime (see `runtime.py`), which owns the driver and decides how waiting, pumping, and handler
execution happen. The connection owns the rest: id assignment, the waiters callers block on, send fences, demultiplexing
session events, running handlers and turning their outcomes into responses, error conversion, and close sequencing.

Under a sync runtime nothing in here ever actually suspends, so `SyncRpcConnection` drives it with `sync_await`. Under
an asyncio runtime it is used directly. Handlers are likewise written once, as coroutines; under a sync runtime they run
inline on the pump and must never actually suspend.

The split:
 - `BaseRpcConnection` is protocol-agnostic: lifecycle, waiters and send fences keyed by opaque keys, the request /
   abandon pattern, close sequencing, and close callbacks. It knows nothing of envelopes, events, or handlers, so a
   connection for another session vocabulary - JSON-RPC's, say - is a subclass which demultiplexes its own events onto
   these helpers.
 - `RpcConnection` is this toolbox's protocol: its envelopes, its session events, `RpcHandler`, and its error mapping.

The connection speaks wire values: params and results are whatever the envelope codec's value codec carries. Typed
calls and typed handlers sit above it, in `serde.py`.
"""
import abc
import functools
import threading
import traceback
import typing as ta

from ..asyncs.asynclite.promises import AsynclitePromise
from ..asyncs.asynclite.promises import AsynclitePromiseWaitTimeoutError
from ..lite.abstract import Abstract
from ..lite.asyncs import sync_await
from ..lite.check import check
from ..logs.modules import get_module_logger
from .configs import RpcConfig
from .dispatch import RpcHandler
from .errors import RpcConnectionClosedError
from .errors import RpcErrorCodes
from .errors import RpcHandlerError
from .errors import RpcMethodNotFoundError
from .errors import RpcRemoteErrorData
from .errors import RpcTimeoutError
from .errors import rpc_exception_type_name
from .errors import rpc_remote_error_for_data
from .ids import RpcIdCreatorLike
from .ids import rpc_id_creator_of
from .messages import RpcErrorMessage
from .messages import RpcInfoEvent
from .messages import RpcNotificationMessage
from .messages import RpcPingMessage
from .messages import RpcRequestMessage
from .messages import RpcResponseMessage
from .messages import RpcResultMessage
from .messages import RpcSessionMessages
from .messages import RpcUnspecified
from .runtime import RpcRuntime
from .runtime import RpcRuntimeSink


T = ta.TypeVar('T')
BaseRpcConnectionT = ta.TypeVar('BaseRpcConnectionT', bound='BaseRpcConnection')
BaseSyncRpcConnectionT = ta.TypeVar('BaseSyncRpcConnectionT', bound='BaseSyncRpcConnection')

RpcConnectionCloseCallback = ta.Callable[[ta.Any], None]  # ta.TypeAlias
RpcNotificationErrorHandler = ta.Callable[['RpcNotificationMessage', BaseException], None]  # ta.TypeAlias

RpcTimeoutArg = ta.Union[float, None, ta.Type['RpcUnspecified']]  # ta.TypeAlias


log = get_module_logger(globals())  # noqa


##


class BaseRpcConnection(RpcRuntimeSink, Abstract):
    """
    Must be started (via `start` or `async with`) before use. Closing is graceful by default: new outbound requests are
    refused, in-flight work on both sides is given the session's drain time to finish, and output is flushed.

    A handler which wants to close its own connection should not await a graceful close from within a request handler:
    the close waits for in-flight requests - that one included - to be answered, so it would wait out the drain
    timeout. Respond first, and close from elsewhere.

    Subclasses implement `on_event`, demultiplexing their session's events onto the helpers here, and the hooks naming
    their session's close and cancel commands.
    """

    def __init__(
            self,
            runtime: RpcRuntime,
            *,
            send_timeout_s: ta.Optional[float] = None,
    ) -> None:
        """
        `send_timeout_s` bounds how long a send waits for its bytes to reach the transport when the peer is not keeping
        up; None waits indefinitely, in which case the session's write timeout still bounds a stalled transport.
        """

        super().__init__()

        self._runtime = runtime
        self._send_timeout_s = send_timeout_s

        self._started = False
        self._closing = False
        self._closed = False
        self._close_exc: ta.Optional[BaseException] = None
        self._driver_done = False
        self._finished = False
        self._output_paused = False

        # Created on start, so that under asyncio it is made on the loop which will use it.
        self._done: ta.Optional[AsynclitePromise] = None

        self._waiters: ta.Dict[ta.Any, AsynclitePromise] = {}
        self._send_fences: ta.Dict[ta.Any, AsynclitePromise] = {}

        self._close_callbacks: ta.List[RpcConnectionCloseCallback] = []

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._runtime!r}>'

    ##
    # hooks

    @abc.abstractmethod
    def _make_close_command(self, graceful: bool) -> ta.Any:
        raise NotImplementedError

    @abc.abstractmethod
    def _default_close_timeout_s(self, graceful: bool) -> ta.Optional[float]:
        """
        How long `close` waits by default before aborting the transport. The session bounds draining and the write
        timeout handler bounds flushing, but the driver's final transport flush happens outside the pipeline's reach,
        so closing needs its own bound: a peer which stops reading would otherwise hang a close forever.
        """

        raise NotImplementedError

    ##
    # properties

    @property
    def runtime(self) -> RpcRuntime:
        return self._runtime

    @property
    def is_started(self) -> bool:
        return self._started

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def close_exception(self) -> ta.Optional[BaseException]:
        """Why the connection failed, if it did. A clean close leaves this None."""

        return self._close_exc

    @property
    def output_paused(self) -> bool:
        """Whether the transport's write buffer is over its high watermark. Advisory: sends block on their own."""

        return self._output_paused

    ##
    # lifecycle

    def add_close_callback(self, callback: RpcConnectionCloseCallback) -> None:
        """
        Registers a callback, given the connection, run synchronously as the last step of teardown: after every pending
        call has been failed and before `wait_closed` returns. Runs right away if the connection has already finished.
        """

        if self._finished:
            callback(self)
            return
        self._close_callbacks.append(callback)

    async def start(self) -> None:
        check.state(not self._started, 'already started')
        check.state(not self._closed, 'already closed')

        self._started = True
        self._done = self._runtime.make_promise()
        await self._runtime.start(self)

    async def __aenter__(self: BaseRpcConnectionT) -> BaseRpcConnectionT:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close(graceful=exc_type is None)

    async def close(
            self,
            *,
            graceful: bool = True,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> None:
        """
        Closes the connection and waits for it to finish, gracefully by default.

        The wait is bounded: by `timeout_s` if given, else by `_default_close_timeout_s`. On expiry the transport is
        aborted. Never raises for a connection which failed earlier - the failure is available as `close_exception`.
        """

        if timeout_s is RpcUnspecified:
            timeout_s = self._default_close_timeout_s(graceful)

        self._closing = True

        if not self._started:
            self._mark_closed(None)
            await self._runtime.close()
            self._finish()
            return

        done = check.not_none(self._done)
        if not done.is_done():
            if not self._closed:
                self._runtime.enqueue(self._make_close_command(graceful))

            try:
                await done.wait(timeout=ta.cast(ta.Optional[float], timeout_s))

            except AsynclitePromiseWaitTimeoutError:
                log.warning('Close did not complete within %r seconds, aborting transport', timeout_s)

            except BaseException:
                # Interrupted - cancelled, say: nothing may be left open.
                await self._runtime.close()
                raise

        await self._runtime.close()
        await self.wait_closed()

    async def wait_closed(self) -> None:
        """
        Waits until the connection has closed for any reason and its runtime has finished: under asyncio the pump and
        every handler task. Under a sync runtime this pumps the connection until the peer goes away, which makes it the
        serving loop of a sync server - see `serve`.
        """

        if not self._started:
            check.state(self._closed, 'connection neither started nor closed')
            return

        await check.not_none(self._done).wait()
        await self._runtime.wait_closed()

    async def serve(self) -> None:
        """Serves until the connection closes. Equivalent to `wait_closed`; reads better at the end of a server."""

        await self.wait_closed()

    ##
    # closure

    def _closed_error(self) -> BaseException:
        """The error closure fails things with. A subclass for another vocabulary may raise its own closed error."""

        if (exc := self._close_exc) is not None:
            err = RpcConnectionClosedError(f'connection failed: {exc!r}')
            err.__cause__ = exc
            return err
        return RpcConnectionClosedError('connection closed')

    def _send_timeout_error(self) -> BaseException:
        return RpcTimeoutError(f'send timed out after {self._send_timeout_s!r} seconds waiting for the transport')

    def _check_usable(self) -> None:
        check.state(self._started, 'connection not started')
        if self._closed or self._closing:
            raise self._closed_error()

    def _mark_closed(self, exc: ta.Optional[BaseException]) -> None:
        """Records closure and fails everything still waiting. Idempotent: the first reason wins."""

        if self._closed:
            return
        self._closed = True
        self._close_exc = exc

        for dct in (self._waiters, self._send_fences):
            ps = list(dct.values())
            dct.clear()
            for p in ps:
                if not p.is_done():
                    # A fresh error each: raising one instance from many places tangles its traceback.
                    p.set_error(self._closed_error())

        self._runtime.cancel_all()

    def _finish(self) -> None:
        if self._finished:
            return
        self._finished = True

        callbacks, self._close_callbacks = self._close_callbacks, []
        for cb in callbacks:
            try:
                cb(self)
            except Exception:  # noqa
                # A close callback is a courtesy to its registrant; its failure is not the connection's, and nothing
                # here may prevent the connection from finishing.
                log.exception('Error in rpc connection close callback %r', cb)

        if (done := self._done) is not None and not done.is_done():
            done.set_value(None)

    def on_driver_done(self, exc: ta.Optional[BaseException]) -> None:
        self._driver_done = True
        self._mark_closed(exc)
        self._finish()

    ##
    # sending and waiting

    def _enqueue(self, *commands: ta.Any) -> bool:
        """Hands commands to the driver without waiting, returning False if it is no longer accepting them."""

        if self._driver_done:
            return False
        return self._runtime.enqueue(*commands)

    async def _send(self, cmd: ta.Any, key: ta.Any) -> None:
        """
        Hands a send command to the driver and waits until its fence, registered under `key`, is resolved - by the
        session reporting the command sent - or failed - by the command failing before it could be.

        Waiting is what makes backpressure real: sent means the bytes crossed into the transport, so a peer which stops
        reading stalls the sender here rather than growing buffers without bound. The wait is bounded by
        `send_timeout_s`.
        """

        self._check_usable()

        check.not_in(key, self._send_fences)
        fence = self._runtime.make_promise()
        self._send_fences[key] = fence
        try:
            if not self._enqueue(cmd):
                raise self._closed_error()

            try:
                await fence.wait(timeout=self._send_timeout_s)
            except AsynclitePromiseWaitTimeoutError as e:
                raise self._send_timeout_error() from e

        finally:
            if self._send_fences.get(key) is fence:
                del self._send_fences[key]

    def _add_waiter(self, key: ta.Any) -> AsynclitePromise:
        check.not_in(key, self._waiters, 'duplicate waiter key')
        waiter = self._runtime.make_promise()
        self._waiters[key] = waiter
        return waiter

    def _discard_waiter(self, key: ta.Any, waiter: AsynclitePromise) -> bool:
        """Drops a waiter if still registered. Returns whether it was abandoned: dropped with no outcome."""

        if self._waiters.get(key) is not waiter:
            return False
        del self._waiters[key]
        return not waiter.is_done()

    async def _send_and_wait(
            self,
            cmd: ta.Any,
            send_key: ta.Any,
            waiter_key: ta.Any,
            abandon_command: ta.Optional[ta.Callable[[], ta.Any]] = None,
    ) -> ta.Any:
        """
        Sends a command and waits for the outcome resolved under `waiter_key`. A caller which gives up first -
        cancelled, or its send timed out - abandons it, and `abandon_command`, if given, makes the command telling the
        session so.
        """

        waiter = self._add_waiter(waiter_key)
        try:
            await self._send(cmd, send_key)
            return await waiter.wait()

        except BaseException:
            if self._discard_waiter(waiter_key, waiter) and abandon_command is not None:
                self._enqueue(abandon_command())
            raise

        finally:
            self._discard_waiter(waiter_key, waiter)

    #

    @staticmethod
    def _resolve(dct: ta.Dict[ta.Any, AsynclitePromise], key: ta.Any, value: ta.Any) -> None:
        if (p := dct.pop(key, None)) is not None and not p.is_done():
            p.set_value(value)

    @staticmethod
    def _fail(dct: ta.Dict[ta.Any, AsynclitePromise], key: ta.Any, exc: BaseException) -> None:
        if (p := dct.pop(key, None)) is not None and not p.is_done():
            p.set_error(exc)

    def _resolve_waiter(self, key: ta.Any, value: ta.Any) -> None:
        self._resolve(self._waiters, key, value)

    def _fail_waiter(self, key: ta.Any, exc: BaseException) -> None:
        self._fail(self._waiters, key, exc)

    def _resolve_fence(self, key: ta.Any) -> None:
        self._resolve(self._send_fences, key, None)

    def _fail_fence(self, key: ta.Any, exc: BaseException) -> None:
        self._fail(self._send_fences, key, exc)

    def _set_output_paused(self, paused: bool) -> None:
        self._output_paused = paused

    ##
    # handlers

    async def _spawn(self, key: ta.Any, fn: ta.Callable[[], ta.Awaitable[None]]) -> None:
        await self._runtime.spawn(key, fn)

    def _cancel_handler(self, key: ta.Any) -> None:
        self._runtime.cancel(key)

    def _is_cancelled_exception(self, exc: BaseException) -> bool:
        return self._runtime.is_cancelled_exception(exc)


##


class RpcConnection(BaseRpcConnection):
    """A connection speaking this toolbox's protocol, to a session built by `rpc_build_pipeline_spec`."""

    def __init__(
            self,
            runtime: RpcRuntime,
            config: RpcConfig = RpcConfig.DEFAULT,
            *,
            handler: ta.Optional[RpcHandler] = None,
            id_creator: ta.Optional[RpcIdCreatorLike] = None,
            send_timeout_s: ta.Optional[float] = None,
            notification_error_handler: ta.Optional[RpcNotificationErrorHandler] = None,
    ) -> None:
        super().__init__(
            runtime,
            send_timeout_s=send_timeout_s,
        )

        self._config = config
        self._handler = handler
        self._id_creator = rpc_id_creator_of(id_creator)
        self._notification_error_handler = notification_error_handler

    @property
    def config(self) -> RpcConfig:
        return self._config

    @property
    def handler(self) -> ta.Optional[RpcHandler]:
        return self._handler

    def set_handler(self, handler: ta.Optional[RpcHandler]) -> None:
        """May be called at any time; requests already being handled keep the handler they started with."""

        self._handler = handler

    ##
    # hooks

    def _make_close_command(self, graceful: bool) -> ta.Any:
        return RpcSessionMessages.Close(graceful=graceful)

    def _default_close_timeout_s(self, graceful: bool) -> ta.Optional[float]:
        c = self._config
        parts = [t for t in ((c.close_drain_timeout_s if graceful else None), c.write_timeout_s) if t is not None]
        return sum(parts) if parts else None

    ##
    # outbound

    async def send_request(
            self,
            method: str,
            params: ta.Any = None,
            *,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> RpcResponseMessage:
        """
        Sends a request and waits for its raw response envelope.

        A timeout of RpcUnspecified uses the configured default; None waits indefinitely. A caller which gives up -
        cancelled, or its send timed out - abandons the request, which also tells the peer if so configured.
        """

        self._check_usable()

        rid = self._id_creator()
        request = RpcRequestMessage(rid, method, params)

        return await self._send_and_wait(
            RpcSessionMessages.SendRequest(request, timeout_s),
            ('request', rid),
            ('request', rid),
            lambda: RpcSessionMessages.CancelRequest(rid, notify_peer=self._config.cancel_abandoned_requests),
        )

    @staticmethod
    def result_of(response: RpcResponseMessage) -> ta.Any:
        """The result a response carries, or its error raised as an RpcRemoteError."""

        if isinstance(response, RpcResultMessage):
            return response.result
        elif isinstance(response, RpcErrorMessage):
            raise rpc_remote_error_for_data(response.error)
        else:
            raise TypeError(response)

    async def request(
            self,
            method: str,
            params: ta.Any = None,
            *,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> ta.Any:
        return self.result_of(await self.send_request(method, params, timeout_s=timeout_s))

    async def notify(self, method: str, params: ta.Any = None) -> None:
        cmd = RpcSessionMessages.SendNotification(RpcNotificationMessage(method, params))
        await self._send(cmd, ('command', id(cmd)))

    def notify_nowait(self, method: str, params: ta.Any = None) -> None:
        """
        Sends a notification without waiting for its bytes to reach the transport: no backpressure, but usable where
        nothing may wait, as in an fdio callback. Notifications sent either way keep their order.
        """

        self._check_usable()
        if not self._enqueue(RpcSessionMessages.SendNotification(RpcNotificationMessage(method, params))):
            raise self._closed_error()

    async def ping(self, *, timeout_s: RpcTimeoutArg = RpcUnspecified) -> None:
        """Round-trips a ping, which the peer's session answers without involving its handler."""

        self._check_usable()

        pid = self._id_creator()
        await self._send_and_wait(
            RpcSessionMessages.SendPing(RpcPingMessage(pid), timeout_s),
            ('ping', pid),
            ('ping', pid),
        )

    ##
    # inbound

    def _error_data_for(self, exc: BaseException, code: ta.Optional[str] = None) -> RpcRemoteErrorData:
        if code is None:
            code = RpcErrorCodes.METHOD_NOT_FOUND if isinstance(exc, RpcMethodNotFoundError) else RpcErrorCodes.REMOTE

        tb: ta.Optional[str] = None
        if self._config.include_tracebacks and (mx := self._config.max_traceback_chars):
            tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            if len(tb) > mx:
                tb = tb[-mx:]

        return RpcRemoteErrorData(
            code=code,
            remote_type=rpc_exception_type_name(exc),
            message=str(exc),
            traceback=tb,
        )

    async def _run_request_handler(self, request: RpcRequestMessage) -> None:
        response: RpcResponseMessage
        try:
            if (h := self._handler) is None:
                raise RpcMethodNotFoundError(request.method)

            result = await h.handle_request_message(request)

        except BaseException as e:  # noqa
            if self._is_cancelled_exception(e):
                # The session drops this if it already gave up on the request - the peer cancelled it, or it timed out
                # - but a handler cancelled from elsewhere leaves a peer still waiting, which deserves an answer.
                self._enqueue(RpcSessionMessages.SendResponse(RpcErrorMessage(
                    request.id,
                    self._error_data_for(e, RpcErrorCodes.CANCELLED),
                )))
                raise

            if not isinstance(e, Exception):
                raise

            if isinstance(e, RpcHandlerError):
                # An answer the handler chose: sent exactly as it is.
                response = RpcErrorMessage(request.id, e.data)
            else:
                response = RpcErrorMessage(request.id, self._error_data_for(e))

        else:
            response = RpcResultMessage(request.id, result)

        self._enqueue(RpcSessionMessages.SendResponse(response))

    def _report_notification_error(self, notification: RpcNotificationMessage, exc: BaseException) -> None:
        if (neh := self._notification_error_handler) is None:
            log.error('Unhandled error handling rpc notification %r', notification.method, exc_info=exc)
            return

        try:
            neh(notification, exc)
        except Exception:  # noqa
            log.exception('Error in rpc notification error handler')

    async def _run_notification_handler(self, h: RpcHandler, notification: RpcNotificationMessage) -> None:
        try:
            await h.handle_notification(notification.method, notification.params)

        except BaseException as e:  # noqa
            if self._is_cancelled_exception(e) or not isinstance(e, Exception):
                raise

            self._report_notification_error(notification, e)

    async def _on_notification_received(self, notification: RpcNotificationMessage) -> None:
        if (h := self._handler) is None:
            log.debug('Dropping rpc notification with no handler: %r', notification.method)
            return

        try:
            if h.handle_notification_inline(notification.method, notification.params):
                return
        except Exception as e:  # noqa
            self._report_notification_error(notification, e)
            return

        await self._spawn(None, functools.partial(self._run_notification_handler, h, notification))

    ##
    # RpcRuntimeSink

    @staticmethod
    def _send_key(cmd: RpcSessionMessages.Command) -> ta.Any:
        if isinstance(cmd, RpcSessionMessages.SendRequest):
            return ('request', cmd.request.id)
        if isinstance(cmd, RpcSessionMessages.SendPing):
            return ('ping', cmd.ping.id)
        return ('command', id(cmd))

    async def on_event(self, event: ta.Any) -> None:
        if isinstance(event, RpcSessionMessages.RequestReceived):
            await self._spawn(event.request.id, functools.partial(self._run_request_handler, event.request))

        elif isinstance(event, RpcSessionMessages.ResponseReceived):
            self._resolve_waiter(('request', event.request.id), event.response)

        elif isinstance(event, RpcSessionMessages.NotificationReceived):
            await self._on_notification_received(event.notification)

        elif isinstance(event, RpcSessionMessages.Sent):
            self._resolve_fence(self._send_key(event.command))

        elif isinstance(event, RpcSessionMessages.RequestFailed):
            key = ('request', event.request.id)
            self._fail_fence(key, event.exc)
            self._fail_waiter(key, event.exc)

        elif isinstance(event, RpcSessionMessages.RequestHandlingAborted):
            self._cancel_handler(event.request.id)

        elif isinstance(event, RpcSessionMessages.PongReceived):
            self._resolve_waiter(('ping', event.ping.id), None)

        elif isinstance(event, RpcSessionMessages.PingFailed):
            key = ('ping', event.ping.id)
            self._fail_fence(key, event.exc)
            self._fail_waiter(key, event.exc)

        elif isinstance(event, RpcSessionMessages.OutputPaused):
            self._set_output_paused(True)

        elif isinstance(event, RpcSessionMessages.OutputResumed):
            self._set_output_paused(False)

        elif isinstance(event, RpcSessionMessages.Closed):
            self._mark_closed(event.exc)

        else:
            await self._on_other_event(event)

    async def _on_other_event(self, event: ta.Any) -> None:
        """
        An output which is not a session event: one from an optional handler, such as a completed handshake. Subclasses
        which install such handlers handle their events here.
        """

        if isinstance(event, RpcInfoEvent):
            log.debug('Unconsumed rpc connection event: %r', event)
        else:
            log.warning('Unexpected rpc connection event: %r', event)


##


class BaseSyncRpcConnection(Abstract):
    """
    The sync facade over a connection on a sync-pumping runtime: every method drives the async connection with
    `sync_await`, and pumps the driver in the calling thread while it waits.

    Not thread-safe. Nested use from the thread already using it - a handler calling back out to the peer while running
    inline on the pump - is permitted; use from a second thread at the same time raises.
    """

    def __init__(self, connection: BaseRpcConnection) -> None:
        super().__init__()

        self._c = connection
        self._lock = threading.RLock()

    def __repr__(self) -> str:
        return f'{type(self).__name__}<{self._c!r}>'

    def run(self, aw: ta.Awaitable[T]) -> T:
        """
        Drives an awaitable written against the async connection - a typed caller's call, say - to completion in this
        thread, pumping the connection while it waits. The awaitable must await nothing but this connection.
        """

        if not self._lock.acquire(blocking=False):
            if hasattr(aw, 'close'):
                aw.close()
            raise RuntimeError(f'{type(self).__name__} is in use by another thread')
        try:
            return sync_await(aw)
        finally:
            self._lock.release()

    #

    @property
    def is_started(self) -> bool:
        return self._c.is_started

    @property
    def is_closed(self) -> bool:
        return self._c.is_closed

    @property
    def close_exception(self) -> ta.Optional[BaseException]:
        return self._c.close_exception

    def add_close_callback(self, callback: RpcConnectionCloseCallback) -> None:
        self._c.add_close_callback(callback)

    #

    def start(self) -> None:
        self.run(self._c.start())

    def __enter__(self: BaseSyncRpcConnectionT) -> BaseSyncRpcConnectionT:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close(graceful=exc_type is None)

    def close(
            self,
            *,
            graceful: bool = True,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> None:
        self.run(self._c.close(graceful=graceful, timeout_s=timeout_s))

    def wait_closed(self) -> None:
        self.run(self._c.wait_closed())

    def serve(self) -> None:
        self.run(self._c.serve())


class SyncRpcConnection(BaseSyncRpcConnection):
    def __init__(self, connection: RpcConnection) -> None:
        super().__init__(connection)

        self._rc = connection

    @property
    def connection(self) -> RpcConnection:
        return self._rc

    @property
    def config(self) -> RpcConfig:
        return self._rc.config

    def set_handler(self, handler: ta.Optional[RpcHandler]) -> None:
        self._rc.set_handler(handler)

    #

    def send_request(
            self,
            method: str,
            params: ta.Any = None,
            *,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> RpcResponseMessage:
        return self.run(self._rc.send_request(method, params, timeout_s=timeout_s))

    def request(
            self,
            method: str,
            params: ta.Any = None,
            *,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> ta.Any:
        return self.run(self._rc.request(method, params, timeout_s=timeout_s))

    def notify(self, method: str, params: ta.Any = None) -> None:
        self.run(self._rc.notify(method, params))

    def ping(self, *, timeout_s: RpcTimeoutArg = RpcUnspecified) -> None:
        self.run(self._rc.ping(timeout_s=timeout_s))
