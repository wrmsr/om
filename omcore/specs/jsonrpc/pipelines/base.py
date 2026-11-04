"""
The JSON-RPC connection, written once: everything a host does with a JSON-RPC session other than pumping its driver.

It is an `omcore.rpc` connection - `BaseRpcConnection` supplies the lifecycle, waiters, send fences, close sequencing,
and close callbacks, and an `omcore.rpc` runtime decides how waiting, pumping, and handler execution happen - over the
JSON-RPC session's own vocabulary, which this class demultiplexes onto the base's helpers. The session stays JSON-RPC's:
batches, spec-mandated error responses, id rules, and integer error codes are its business alone.

The same class serves every runtime. Under asyncio (`AsyncioRpcRuntime`) one pump task drives the driver and each
inbound request runs as a tracked task; under a sync runtime the caller's thread pumps and handlers run inline, and
`SyncJsonrpcConnection` drives it with `sync_await`. Dispatchers here are async; the sync connection adapts sync ones.
"""
import functools
import typing as ta

from .... import check
from ....logs import all as logs
from ....rpc import all as rpc
from ..conns import AsyncJsonrpcConnection
from ..dispatch import AsyncJsonrpcDispatcher
from ..dispatch import jsonrpc_error_for_exception
from ..errors import JsonrpcConnectionClosedError
from ..errors import JsonrpcMethodError
from ..errors import JsonrpcRemoteError
from ..errors import JsonrpcTimeoutError
from ..errors import KnownErrors
from ..ids import JsonrpcIdCreator
from ..ids import JsonrpcIdCreatorLike
from ..ids import jsonrpc_id_creator_of
from ..types import Batch
from ..types import Error
from ..types import NotSpecified
from ..types import Params
from ..types import Request
from ..types import Response
from ..types import notification
from ..types import request
from .configs import JsonrpcPipelineConfig
from .messages import JsonrpcPipelineMessages as Jpm


log = logs.get_module_logger(globals())


type TimeoutArg = float | None | type[NotSpecified]

type AsyncJsonrpcNotificationHandler = ta.Callable[
    [ta.Any, Request],
    ta.Awaitable[None],
]


##


class BaseJsonrpcConnection(rpc.BaseConnection, AsyncJsonrpcConnection):
    """
    Must be started (via `start` or `async with`) before use. Under asyncio it pumps only while its runtime's pump task
    runs: a connection which is never started never reads its transport.
    """

    def __init__(
            self,
            runtime: rpc.Runtime,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            dispatcher: AsyncJsonrpcDispatcher | None = None,
            notification_handler: AsyncJsonrpcNotificationHandler | None = None,
            id_creator: JsonrpcIdCreatorLike | None = None,
            include_error_details: bool = False,
            send_timeout_s: float | None = None,
    ) -> None:
        """
        `send_timeout_s` bounds how long a send waits for its bytes to reach the transport when the peer is not keeping
        up; None waits indefinitely, in which case the session's write timeout still bounds a stalled transport.
        """

        super().__init__(
            runtime,
            send_timeout_s=send_timeout_s,
        )

        self._config = config
        self._dispatcher = dispatcher
        self._notification_handler = notification_handler
        self._id_creator: JsonrpcIdCreator = jsonrpc_id_creator_of(id_creator)
        self._include_error_details = include_error_details

    @property
    def config(self) -> JsonrpcPipelineConfig:
        return self._config

    @property
    def dispatcher(self) -> AsyncJsonrpcDispatcher | None:
        return self._dispatcher

    def set_dispatcher(self, dispatcher: AsyncJsonrpcDispatcher | None) -> None:
        """May be called at any time; requests already being handled keep the dispatcher they started with."""

        self._dispatcher = dispatcher

    @property
    def notification_handler(self) -> AsyncJsonrpcNotificationHandler | None:
        return self._notification_handler

    def set_notification_handler(self, handler: AsyncJsonrpcNotificationHandler | None) -> None:
        self._notification_handler = handler

    ##
    # BaseRpcConnection hooks

    def _make_close_command(self, graceful: bool) -> ta.Any:
        return Jpm.Close(graceful=graceful)

    def _default_close_timeout_s(self, graceful: bool) -> float | None:
        c = self._config
        parts = [t for t in ((c.close_drain_timeout_s if graceful else None), c.write_timeout_s) if t is not None]
        return sum(parts) if parts else None

    def _closed_error(self) -> JsonrpcConnectionClosedError:
        if (exc := self._close_exc) is not None:
            err = JsonrpcConnectionClosedError(f'connection failed: {exc!r}')
            err.__cause__ = exc
            return err
        return JsonrpcConnectionClosedError('connection closed')

    def _send_timeout_error(self) -> BaseException:
        return JsonrpcTimeoutError(f'send timed out after {self._send_timeout_s!r} seconds waiting for the transport')

    async def close(
            self,
            *,
            graceful: bool = True,
            timeout_s: type[NotSpecified | rpc.Unspecified] | float | None = NotSpecified,
    ) -> None:
        """
        Close the connection, gracefully by default (see Close), waiting for closure to complete.

        The wait is bounded: by `timeout_s` if given, else by the sum of the configured drain and write timeouts (or
        not at all if both are None). On expiry the transport is aborted. Never raises for a connection which failed
        earlier - the failure is available as `close_exception`.
        """

        await super().close(
            graceful=graceful,
            timeout_s=rpc.Unspecified if timeout_s is NotSpecified else ta.cast('float | None', timeout_s),
        )

    ##
    # building messages

    def _new_request(self, method: str, params: Params | None) -> Request:
        return request(self._id_creator(), method, params)

    def _error_response(self, req: Request, exc: BaseException) -> Response:
        return Response(
            req.id_value(),
            error=jsonrpc_error_for_exception(exc, include_details=self._include_error_details),
        )

    @staticmethod
    def _result_of(response: Response) -> ta.Any:
        if response.is_error:
            raise JsonrpcRemoteError(ta.cast(Error, response.error))
        return response.result

    ##
    # sending

    async def send_request(
            self,
            req: Request,
            *,
            timeout_s: TimeoutArg = NotSpecified,
    ) -> Response:
        """
        Send a prepared request (with id) and await its raw response. A caller which gives up - cancelled, or its send
        timed out - abandons the request: the session stops waiting for it, and a late response is dropped.
        """

        check.arg(not req.is_notification, 'request must have an id')
        self._check_usable()

        rid = req.id_value()
        return await self._send_and_wait(
            Jpm.SendRequest(req, timeout_s=timeout_s),
            ('request', rid),
            ('request', rid),
            lambda: Jpm.CancelRequest(rid),
        )

    async def request(
            self,
            method: str,
            params: Params | None = None,
            *,
            timeout_s: TimeoutArg = NotSpecified,
    ) -> ta.Any:
        self._check_usable()
        return self._result_of(await self.send_request(self._new_request(method, params), timeout_s=timeout_s))

    async def notify(self, method: str, params: Params | None = None) -> None:
        cmd = Jpm.SendNotification(notification(method, params))
        await self._send(cmd, ('command', id(cmd)))

    async def send_batch(
            self,
            reqs: ta.Sequence[Request],
            *,
            timeout_s: TimeoutArg = NotSpecified,
    ) -> list[Response | None]:
        """
        Send prepared requests and notifications as one batch, returning responses in order (None for notifications).

        Raises for the first request which fails; the others are abandoned.
        """

        self._check_usable()

        waiters = [
            (req, None if req.is_notification else self._add_waiter(('request', req.id_value())))
            for req in reqs
        ]

        cmd = Jpm.SendBatch(Batch(reqs), timeout_s=timeout_s)
        try:
            await self._send(cmd, ('command', id(cmd)))
            return [await w.wait() if w is not None else None for _, w in waiters]

        finally:
            for req, w in waiters:
                if w is not None and self._discard_waiter(('request', req.id_value()), w):
                    self._enqueue(Jpm.CancelRequest(req.id_value()))

    ##
    # receiving

    async def _run_request(self, req: Request) -> None:
        response: Response
        try:
            if (d := self._dispatcher) is None:
                raise JsonrpcMethodError(KnownErrors.METHOD_NOT_FOUND, data=req.method)

            result = await d.dispatch(self, req)
            response = Response(req.id_value(), result=result)

        except BaseException as e:  # noqa
            if self._is_cancelled_exception(e) or not isinstance(e, Exception):
                raise

            if isinstance(e, JsonrpcMethodError):
                response = Response(req.id_value(), error=e.error)
            else:
                log.exception('Unhandled error handling request %r', req.method)
                response = self._error_response(req, e)

        self._enqueue(Jpm.SendResponse(response))

    async def _run_notification(self, h: AsyncJsonrpcNotificationHandler, note: Request) -> None:
        try:
            await h(self, note)

        except BaseException as e:  # noqa
            if self._is_cancelled_exception(e) or not isinstance(e, Exception):
                raise

            log.exception('Unhandled error handling notification %r', note.method)

    @staticmethod
    def _send_key(cmd: ta.Any) -> ta.Any:
        if isinstance(cmd, Jpm.SendRequest):
            return ('request', cmd.request.id_value())
        return ('command', id(cmd))

    async def on_event(self, event: ta.Any) -> None:
        if isinstance(event, Jpm.RequestReceived):
            req = event.request
            await self._spawn(req.id_value(), functools.partial(self._run_request, req))

        elif isinstance(event, Jpm.ResponseReceived):
            self._resolve_waiter(('request', event.request.id_value()), event.response)

        elif isinstance(event, Jpm.NotificationReceived):
            if (h := self._notification_handler) is None:
                log.debug('Dropping notification with no handler: %r', event.notification.method)
            else:
                await self._spawn(None, functools.partial(self._run_notification, h, event.notification))

        elif isinstance(event, Jpm.Sent):
            self._resolve_fence(self._send_key(event.command))

        elif isinstance(event, Jpm.RequestFailed):
            key = ('request', event.request.id_value())
            self._fail_fence(key, event.exc)
            self._fail_waiter(key, event.exc)

        elif isinstance(event, Jpm.RequestHandlingAborted):
            self._cancel_handler(event.request.id_value())

        elif isinstance(event, Jpm.OutputPaused):
            self._set_output_paused(True)

        elif isinstance(event, Jpm.OutputResumed):
            self._set_output_paused(False)

        elif isinstance(event, Jpm.Closed):
            self._mark_closed(event.exc)

        else:
            log.warning('Unexpected pipeline output: %r', event)
