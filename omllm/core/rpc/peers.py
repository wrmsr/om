# ruff: noqa: PYI034 UP006 UP007 UP037 UP045
import asyncio
import functools
import traceback
import typing as ta

from omcore.lite.check import check

from .channels import RpcChannel
from .errors import RpcConnectionClosedError
from .errors import RpcMethodNotFoundError
from .errors import RpcProtocolError
from .errors import RpcRemoteCancelledError
from .errors import RpcRemoteError
from .errors import RpcRemoteErrorData
from .handlers import RpcHandler
from .handlers import RpcNotificationErrorHandler
from .messages import RpcCancelMessage
from .messages import RpcErrorMessage
from .messages import RpcMessage
from .messages import RpcNotificationMessage
from .messages import RpcPingMessage
from .messages import RpcPongMessage
from .messages import RpcRequestMessage
from .messages import RpcResultMessage


##


DEFAULT_RPC_MAX_IN_FLIGHT = 1024
DEFAULT_RPC_MAX_TRACEBACK_CHARS = 64 * 1024


def _exception_type_name(exc: BaseException) -> str:
    cls = type(exc)
    return f'{cls.__module__}.{cls.__qualname__}'


def _error_data(
        exc: BaseException,
        *,
        code: str = 'remote',
        max_traceback_chars: int = DEFAULT_RPC_MAX_TRACEBACK_CHARS,
) -> RpcRemoteErrorData:
    tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    if len(tb) > max_traceback_chars:
        tb = tb[-max_traceback_chars:] if max_traceback_chars else ''
    return RpcRemoteErrorData(
        code=code,
        remote_type=_exception_type_name(exc),
        message=str(exc),
        traceback=tb,
    )


class _RejectingRpcHandler(RpcHandler):
    async def handle(self, method: str, params: ta.Any) -> ta.Any:
        raise RpcMethodNotFoundError(method)


class RpcPeer:
    def __init__(
            self,
            channel: RpcChannel,
            *,
            handler: ta.Optional[RpcHandler] = None,
            notification_error_handler: ta.Optional[RpcNotificationErrorHandler] = None,
            max_in_flight: int = DEFAULT_RPC_MAX_IN_FLIGHT,
            max_traceback_chars: int = DEFAULT_RPC_MAX_TRACEBACK_CHARS,
    ) -> None:
        super().__init__()

        check.arg(max_in_flight > 0)
        check.arg(max_traceback_chars >= 0)

        self._channel = channel
        self._handler = handler if handler is not None else _RejectingRpcHandler()
        self._notification_error_handler = notification_error_handler
        self._max_in_flight = max_in_flight
        self._max_traceback_chars = max_traceback_chars

        self._next_id = 1
        self._outgoing = {}  # type: ta.Dict[int, asyncio.Future]
        self._pings = {}  # type: ta.Dict[int, asyncio.Future]
        self._incoming = {}  # type: ta.Dict[int, asyncio.Task]
        self._notifications = set()  # type: ta.Set[asyncio.Task]

        self._receive_task = None  # type: ta.Optional[asyncio.Task]
        self._closed_event = asyncio.Event()
        self._closing = False
        self._finished = False
        self._failure = None  # type: ta.Optional[BaseException]
        self._background_failure = None  # type: ta.Optional[BaseException]

    @property
    def closed(self) -> bool:
        return self._closed_event.is_set()

    @property
    def failure(self) -> ta.Optional[BaseException]:
        return self._failure

    @property
    def num_outgoing(self) -> int:
        return len(self._outgoing)

    @property
    def num_incoming(self) -> int:
        return len(self._incoming)

    def _new_id(self) -> int:
        request_id = self._next_id
        self._next_id += 1
        return request_id

    def _check_running(self) -> None:
        if self._receive_task is None:
            raise RuntimeError('RPC peer has not been started')
        if self._closing or self._finished:
            raise RpcConnectionClosedError('RPC peer is closed')

    def _abort(self, exc: BaseException) -> None:
        if self._background_failure is None:
            self._background_failure = exc
        if self._receive_task is not None and not self._receive_task.done():
            self._receive_task.cancel()

    async def _try_send(self, message: RpcMessage) -> bool:
        if self._closing or self._finished:
            return False
        try:
            await self._channel.send(message)
            return True
        except Exception as e:  # noqa
            self._abort(e)
            return False

    async def _send(self, message: RpcMessage) -> None:
        try:
            await self._channel.send(message)
        except RpcConnectionClosedError as e:
            self._abort(e)
            raise

    async def start(self) -> None:
        if self._receive_task is not None or self._finished:
            raise RuntimeError('RPC peer has already been started')
        if self._channel.closed:
            raise RpcConnectionClosedError('RPC channel is closed')
        self._receive_task = asyncio.create_task(self._run(), name='omllm-rpc-receive')

    async def wait_closed(self) -> None:
        if self._receive_task is None and not self._finished:
            raise RuntimeError('RPC peer has not been started')
        await self._closed_event.wait()

    async def serve(self) -> None:
        await self.start()
        await self.wait_closed()
        if self._failure is not None:
            raise self._failure

    async def call(self, method: str, params: ta.Any = None) -> ta.Any:
        self._check_running()

        request_id = self._new_id()
        future = asyncio.get_running_loop().create_future()
        self._outgoing[request_id] = future

        may_have_sent = False
        try:
            may_have_sent = True
            await self._send(RpcRequestMessage(request_id, method, params))
            return await future

        except asyncio.CancelledError:
            future.cancel()
            if may_have_sent:
                await self._try_send(RpcCancelMessage(request_id))
            raise

        except BaseException:
            self._outgoing.pop(request_id, None)
            raise

    async def notify(self, method: str, params: ta.Any = None) -> None:
        self._check_running()
        await self._send(RpcNotificationMessage(method, params))

    async def ping(self) -> None:
        self._check_running()

        ping_id = self._new_id()
        future = asyncio.get_running_loop().create_future()
        self._pings[ping_id] = future
        try:
            await self._send(RpcPingMessage(ping_id))
            await future
        except BaseException:
            self._pings.pop(ping_id, None)
            raise

    def _request_done(self, request_id: int, task: asyncio.Task) -> None:
        if self._incoming.get(request_id) is task:
            self._incoming.pop(request_id, None)
        if not task.cancelled() and (exc := task.exception()) is not None:
            self._abort(exc)

    def _notification_done(self, task: asyncio.Task) -> None:
        self._notifications.discard(task)
        if not task.cancelled() and (exc := task.exception()) is not None:
            self._abort(exc)

    async def _send_handler_response(self, message: RpcMessage) -> None:
        try:
            await self._channel.send(message)
        except RpcProtocolError as e:
            if isinstance(message, RpcResultMessage):
                fallback = RpcErrorMessage(
                    message.id,
                    _error_data(
                        e,
                        code='result_encoding',
                        max_traceback_chars=self._max_traceback_chars,
                    ),
                )
                if await self._try_send(fallback):
                    return
            self._abort(e)
        except Exception as e:  # noqa
            self._abort(e)

    async def _handle_request(self, message: RpcRequestMessage) -> None:
        response = None  # type: ta.Optional[RpcMessage]
        try:
            result = await self._handler.handle(message.method, message.params)
        except asyncio.CancelledError as e:
            if self._closing:
                return
            response = RpcErrorMessage(
                message.id,
                _error_data(
                    e,
                    code='cancelled',
                    max_traceback_chars=self._max_traceback_chars,
                ),
            )
        except RpcMethodNotFoundError as e:
            response = RpcErrorMessage(
                message.id,
                _error_data(
                    e,
                    code='method_not_found',
                    max_traceback_chars=self._max_traceback_chars,
                ),
            )
        except Exception as e:  # noqa
            response = RpcErrorMessage(
                message.id,
                _error_data(e, max_traceback_chars=self._max_traceback_chars),
            )
        else:
            response = RpcResultMessage(message.id, result)

        if response is None:
            raise RuntimeError('RPC handler produced no response')
        await self._send_handler_response(response)

    async def _handle_notification(self, message: RpcNotificationMessage) -> None:
        try:
            await self._handler.handle(message.method, message.params)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa
            if self._notification_error_handler is not None:
                self._notification_error_handler(message, e)

    async def _dispatch(self, message: RpcMessage) -> None:
        if isinstance(message, RpcRequestMessage):
            if message.id in self._incoming:
                raise RpcProtocolError(f'Duplicate inbound RPC request id: {message.id}')
            if len(self._incoming) + len(self._notifications) >= self._max_in_flight:
                await self._channel.send(RpcErrorMessage(
                    message.id,
                    RpcRemoteErrorData(
                        code='busy',
                        remote_type='RpcTooManyRequestsError',
                        message=f'Too many in-flight RPC requests: {self._max_in_flight}',
                    ),
                ))
                return
            request_task = asyncio.create_task(self._handle_request(message), name=f'omllm-rpc-request-{message.id}')
            self._incoming[message.id] = request_task
            request_task.add_done_callback(functools.partial(self._request_done, message.id))
            return

        if isinstance(message, RpcNotificationMessage):
            if len(self._incoming) + len(self._notifications) >= self._max_in_flight:
                return
            notification_task = asyncio.create_task(
                self._handle_notification(message),
                name='omllm-rpc-notification',
            )
            self._notifications.add(notification_task)
            notification_task.add_done_callback(self._notification_done)
            return

        if isinstance(message, RpcCancelMessage):
            if (incoming_task := self._incoming.get(message.id)) is not None:
                incoming_task.cancel()
            return

        if isinstance(message, RpcResultMessage):
            try:
                future = self._outgoing.pop(message.id)
            except KeyError:
                raise RpcProtocolError(f'Unexpected RPC result id: {message.id}') from None
            if not future.done():
                future.set_result(message.result)
            return

        if isinstance(message, RpcErrorMessage):
            try:
                future = self._outgoing.pop(message.id)
            except KeyError:
                raise RpcProtocolError(f'Unexpected RPC error id: {message.id}') from None
            if not future.done():
                if message.error.code == 'cancelled':
                    future.set_exception(RpcRemoteCancelledError(message.error))
                else:
                    future.set_exception(RpcRemoteError(message.error))
            return

        if isinstance(message, RpcPingMessage):
            await self._channel.send(RpcPongMessage(message.id))
            return

        if isinstance(message, RpcPongMessage):
            try:
                future = self._pings.pop(message.id)
            except KeyError:
                raise RpcProtocolError(f'Unexpected RPC pong id: {message.id}') from None
            if not future.done():
                future.set_result(None)
            return

        raise TypeError(message)

    def _connection_error(self, message: str) -> RpcConnectionClosedError:
        error = RpcConnectionClosedError(message)
        if self._failure is not None:
            error.__cause__ = self._failure
        return error

    async def _finish(
            self,
            *,
            failure: ta.Optional[BaseException],
            message: str,
    ) -> None:
        if self._finished:
            return
        self._finished = True
        self._closing = True
        self._failure = failure

        try:
            await self._channel.aclose()
        finally:
            current = asyncio.current_task()
            tasks = [
                task
                for task in [*self._incoming.values(), *self._notifications]
                if task is not current and not task.done()
            ]
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            self._incoming.clear()
            self._notifications.clear()

            for future in [*self._outgoing.values(), *self._pings.values()]:
                if not future.done():
                    future.set_exception(self._connection_error(message))
            self._outgoing.clear()
            self._pings.clear()

            self._closed_event.set()

    async def _run(self) -> None:
        failure = None  # type: ta.Optional[BaseException]
        message = 'RPC connection closed by peer'
        try:
            while True:
                incoming = await self._channel.receive()
                if incoming is None:
                    break
                await self._dispatch(incoming)

        except asyncio.CancelledError:
            if self._background_failure is not None:
                failure = self._background_failure
                message = 'RPC connection failed'
            elif not self._closing:
                failure = RpcConnectionClosedError('RPC receive loop was cancelled unexpectedly')
                message = 'RPC connection failed'

        except BaseException as e:  # noqa
            failure = e
            message = 'RPC connection failed'

        finally:
            await self._finish(failure=failure, message=message)

    async def aclose(self) -> None:
        if self._finished:
            await self._closed_event.wait()
            return
        if self._receive_task is None:
            await self._finish(failure=None, message='RPC peer closed locally')
            return

        self._closing = True
        try:
            await self._channel.aclose()
        finally:
            if not self._receive_task.done():
                self._receive_task.cancel()
            await self._receive_task
            await self._closed_event.wait()

    async def __aenter__(self) -> 'RpcPeer':
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()
