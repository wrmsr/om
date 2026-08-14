import asyncio
import inspect
import typing as ta
import uuid

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...io.pipelines.drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ...logs import all as logs
from .client import RpcClient
from .dispatch import rpc_remote_error_response
from .dispatch import validate_rpc_response
from .endpoints import RpcEndpoint
from .endpoints import resolve_rpc_endpoint
from .pipelines import RpcClientConnected
from .pipelines import RpcClientRequestSent
from .pipelines import RpcClientResponse
from .pipelines import RpcClientSendRequest
from .pipelines import RpcPipelineFailure
from .pipelines import RpcServerDispatch
from .pipelines import RpcServerSendResponse
from .pipelines import RpcWireError
from .pipelines import RpcWireRequest
from .pipelines import RpcWireResponse
from .pipelines import RpcWireResult
from .pipelines import rpc_client_pipeline_spec
from .pipelines import rpc_server_pipeline_spec
from .pipelines.codecs import encode_rpc_wire_message_payload
from .protocol import RPC_DEFAULT_MAX_FRAME_BYTES
from .protocol import RPC_PROTOCOL_VERSION
from .protocol import RpcCallIndeterminateError
from .protocol import RpcHandler
from .protocol import RpcProtocolError
from .protocol import RpcRemoteError
from .protocol import RpcRequest
from .protocol import RpcUnavailableError
from .registry import RpcResponseExecute
from .registry import RpcResponsePending
from .registry import RpcResponseRegistry
from .registry import RpcResponseRejected
from .registry import RpcResponseReplay
from .server import RpcServerDrainTimeoutError
from .transports import DEFAULT_ASYNCIO_RPC_TRANSPORT
from .transports import AsyncioRpcListener
from .transports import AsyncioRpcTransport


log = logs.get_module_logger(globals())


##


class AsyncRpcHandler(ta.Protocol):
    async def __call__(self, request: RpcRequest) -> ta.Any:
        raise NotImplementedError


class ThreadedAsyncRpcHandler(lang.Final):
    """Adapt a synchronous RPC handler without running it on the event-loop thread."""

    def __init__(self, handler: RpcHandler) -> None:
        super().__init__()

        self._handler = handler

    async def __call__(self, request: RpcRequest) -> ta.Any:
        return await asyncio.to_thread(self._handler, request)


##


class AsyncRpcRequestDispatcher:
    def __init__(
            self,
            handler: AsyncRpcHandler,
            registry: RpcResponseRegistry,
            *,
            max_frame_bytes: int,
    ) -> None:
        super().__init__()

        self._handler = handler
        self._registry = registry
        self._max_frame_bytes = max_frame_bytes

    @staticmethod
    async def _wait_pending(entry) -> RpcWireResponse:
        loop = asyncio.get_running_loop()
        future: asyncio.Future[RpcWireResponse] = loop.create_future()

        def set_result(response: RpcWireResponse) -> None:
            def set_result_in_loop() -> None:
                if not future.done():
                    future.set_result(response)

            loop.call_soon_threadsafe(set_result_in_loop)

        entry.add_done_callback(set_result)
        return await future

    async def dispatch(self, request: RpcRequest) -> RpcWireResponse:
        claim = self._registry.claim(request)
        if isinstance(claim, (RpcResponseReplay, RpcResponseRejected)):
            return claim.response
        if isinstance(claim, RpcResponsePending):
            return await self._wait_pending(claim.entry)
        if not isinstance(claim, RpcResponseExecute):
            raise TypeError(claim)

        try:
            try:
                result = await self._handler(request)
            except asyncio.CancelledError:
                raise
            except BaseException as exc:  # noqa
                response: RpcWireResponse = rpc_remote_error_response(request, exc)
            else:
                response = RpcWireResult(
                    client_id=request.client_id,
                    request_id=request.request_id,
                    result=result,
                )
            response = validate_rpc_response(
                request,
                response,
                max_frame_bytes=self._max_frame_bytes,
            )
        except asyncio.CancelledError:
            raise
        except BaseException as exc:  # noqa
            response = rpc_remote_error_response(
                request,
                exc,
                message='Failed to construct RPC response',
            )

        self._registry.complete(claim.entry, response)
        return response


##


class AsyncioRpcClientConnection(lang.Final):
    def __init__(
            self,
            driver: PollAsyncioStreamIoPipelineDriver,
            *,
            instance_id: uuid.UUID,
            io_timeout_s: float | None,
            max_frame_bytes: int,
    ) -> None:
        super().__init__()

        self._driver: PollAsyncioStreamIoPipelineDriver | None = driver
        self._instance_id = instance_id
        self._io_timeout_s = io_timeout_s
        self._max_frame_bytes = max_frame_bytes
        self._request: RpcRequest | None = None
        self._response: RpcWireResponse | None = None
        self._response_received = False

    @property
    def instance_id(self) -> uuid.UUID:
        return self._instance_id

    @property
    def closed(self) -> bool:
        return self._driver is None

    def _pipeline_driver(self) -> PollAsyncioStreamIoPipelineDriver:
        if self._driver is None:
            raise RuntimeError('RPC client connection is closed')
        return self._driver

    async def _next(self) -> ta.Any:
        return await asyncio.wait_for(
            self._pipeline_driver().next(),
            self._io_timeout_s,
        )

    def _indeterminate(self, request: RpcRequest, exc: BaseException | None = None) -> ta.NoReturn:
        error = RpcCallIndeterminateError(
            request,
            instance_id=self._instance_id,
        )
        if exc is None:
            raise error
        raise error from exc

    async def send(self, request: RpcRequest) -> None:
        if self._request is not None:
            raise RuntimeError('RPC client connection already has a request')

        payload = encode_rpc_wire_message_payload(RpcWireRequest(request=request))
        if len(payload) > self._max_frame_bytes:
            raise RpcProtocolError(
                f'RPC frame is {len(payload)} bytes, exceeding limit {self._max_frame_bytes}',
            )

        self._request = request
        self._pipeline_driver().enqueue(RpcClientSendRequest(request=request))
        try:
            while True:
                event = await self._next()
                if isinstance(event, RpcClientRequestSent):
                    if event.request is not request:
                        self._indeterminate(request)
                    return
                if isinstance(event, RpcClientResponse):
                    self._response = event.response
                    continue
                if isinstance(event, RpcPipelineFailure):
                    self._indeterminate(request, event.exc)
                if event is not None:
                    self._indeterminate(request)
        except RpcCallIndeterminateError:
            raise
        except (EOFError, OSError, RpcProtocolError) as exc:
            self._indeterminate(request, exc)

    async def _receive_response(self, request: RpcRequest) -> RpcWireResponse:
        if (response := self._response) is not None:
            return response

        try:
            while True:
                event = await self._next()
                if isinstance(event, RpcClientResponse):
                    self._response = event.response
                    return event.response
                if isinstance(event, RpcPipelineFailure):
                    self._indeterminate(request, event.exc)
                if event is not None:
                    self._indeterminate(request)
        except RpcCallIndeterminateError:
            raise
        except (EOFError, OSError, RpcProtocolError) as exc:
            self._indeterminate(request, exc)

    async def receive(self) -> ta.Any:
        request = check.not_none(self._request)
        if self._response_received:
            raise RuntimeError('RPC client connection already received its response')

        response = await self._receive_response(request)
        self._response_received = True
        if response.client_id != request.client_id or response.request_id != request.request_id:
            self._indeterminate(request)

        if isinstance(response, RpcWireResult):
            return response.result
        if not isinstance(response, RpcWireError):
            self._indeterminate(request)

        if response.code == 'unavailable':
            raise RpcUnavailableError(response.message)
        if response.code == 'remote':
            raise RpcRemoteError(
                remote_type=response.remote_type,
                message=response.message,
            )
        if response.code == 'protocol':
            raise RpcProtocolError(response.message)
        return self._indeterminate(request)

    async def call(self, request: RpcRequest) -> ta.Any:
        await self.send(request)
        return await self.receive()

    async def close(self) -> bool:
        if (driver := self._driver) is None:
            return False
        self._driver = None
        await driver.close()
        return True

    async def __aenter__(self) -> ta.Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()


class AsyncioRpcClient(lang.Final):
    Config = RpcClient.Config

    def __init__(
            self,
            config: RpcClient.Config,
            *,
            client_id: str | None = None,
            transport: AsyncioRpcTransport = DEFAULT_ASYNCIO_RPC_TRANSPORT,
    ) -> None:
        super().__init__()

        self._config = config
        self._client_id = client_id or uuid.uuid7().hex
        self._transport = transport

    @property
    def config(self) -> RpcClient.Config:
        return self._config

    @property
    def client_id(self) -> str:
        return self._client_id

    @property
    def endpoint(self) -> RpcEndpoint:
        return self._config.resolved_endpoint

    def new_request(
            self,
            method: str,
            params: ta.Any = None,
            *,
            request_id: str | None = None,
    ) -> RpcRequest:
        return RpcRequest(
            client_id=self._client_id,
            request_id=request_id or uuid.uuid7().hex,
            method=method,
            params=params,
        )

    async def connect(self) -> AsyncioRpcClientConnection:
        try:
            reader, writer = await asyncio.wait_for(
                self._transport.connect(self.endpoint),
                self._config.connect_timeout_s,
            )
        except OSError as exc:
            raise RpcUnavailableError(str(exc)) from exc

        driver = PollAsyncioStreamIoPipelineDriver(
            rpc_client_pipeline_spec(
                protocol_version=self._config.protocol_version,
                max_frame_bytes=self._config.max_frame_bytes,
            ),
            reader,
            writer,
        )
        try:
            while True:
                event = await asyncio.wait_for(driver.next(), self._config.io_timeout_s)
                if isinstance(event, RpcClientConnected):
                    return AsyncioRpcClientConnection(
                        driver,
                        instance_id=event.instance_id,
                        io_timeout_s=self._config.io_timeout_s,
                        max_frame_bytes=self._config.max_frame_bytes,
                    )
                if isinstance(event, RpcPipelineFailure):
                    if isinstance(event.exc, RpcProtocolError):
                        raise event.exc
                    raise RpcUnavailableError(str(event.exc)) from event.exc
                if event is not None:
                    raise RpcProtocolError(f'Unexpected RPC handshake event: {event!r}')
        except (RpcProtocolError, RpcUnavailableError):
            await driver.close()
            raise
        except (EOFError, OSError) as exc:
            await driver.close()
            raise RpcUnavailableError(str(exc)) from exc

    async def ping(self) -> uuid.UUID:
        async with await self.connect() as conn:
            return conn.instance_id

    async def call_request(
            self,
            request: RpcRequest,
            *,
            expected_instance_id: uuid.UUID | None = None,
    ) -> ta.Any:
        async with await self.connect() as conn:
            if expected_instance_id is not None and conn.instance_id != expected_instance_id:
                raise RpcCallIndeterminateError(
                    request,
                    instance_id=expected_instance_id,
                    actual_instance_id=conn.instance_id,
                )
            return await conn.call(request)

    async def call(self, method: str, params: ta.Any = None) -> ta.Any:
        return await self.call_request(self.new_request(method, params))


##


@dc.dataclass(frozen=True, kw_only=True)
class AsyncioRpcServerConfig:
    # socket_path is the compatibility spelling for UnixRpcEndpoint.
    socket_path: str = ''
    endpoint: RpcEndpoint | None = None
    handler: AsyncRpcHandler

    socket_mode: int = 0o600
    connection_timeout_s: float | None = 30.
    drain_timeout_s: float | None = 30.
    max_frame_bytes: int = RPC_DEFAULT_MAX_FRAME_BYTES
    response_cache_size: int = 1_024
    backlog: int = 128

    @property
    def resolved_endpoint(self) -> RpcEndpoint:
        return resolve_rpc_endpoint(
            endpoint=self.endpoint,
            socket_path=self.socket_path,
        )

    def __post_init__(self) -> None:
        _ = self.resolved_endpoint
        check.callable(self.handler)
        check.arg(
            inspect.iscoroutinefunction(self.handler) or
            inspect.iscoroutinefunction(self.handler.__call__),
            'Asyncio RPC handlers must be async; wrap synchronous handlers in ThreadedAsyncRpcHandler',
        )
        check.arg(0 <= self.socket_mode <= 0o777)
        check.arg(self.connection_timeout_s is None or self.connection_timeout_s > 0.)
        check.arg(self.drain_timeout_s is None or self.drain_timeout_s > 0.)
        check.arg(self.max_frame_bytes > 0)
        check.arg(self.response_cache_size > 0)
        check.arg(self.backlog > 0)


class AsyncioRpcServer(lang.Final):
    """An asyncio byte-stream host for the runtime-neutral RPC pipeline."""

    def __init__(
            self,
            config: AsyncioRpcServerConfig,
            *,
            transport: AsyncioRpcTransport = DEFAULT_ASYNCIO_RPC_TRANSPORT,
    ) -> None:
        super().__init__()

        self._config = config
        self._transport = transport
        self._listener: AsyncioRpcListener | None = None
        self._bound_endpoint: RpcEndpoint | None = None
        self._instance_id: uuid.UUID | None = None
        self._dispatcher: AsyncRpcRequestDispatcher | None = None
        self._connections: set[asyncio.Task[None]] = set()
        self._drivers: dict[asyncio.Task[None], PollAsyncioStreamIoPipelineDriver] = {}
        self._closing = False

    @property
    def config(self) -> AsyncioRpcServerConfig:
        return self._config

    @property
    def instance_id(self) -> uuid.UUID:
        return check.not_none(self._instance_id)

    @property
    def started(self) -> bool:
        return self._listener is not None

    @property
    def bound_endpoint(self) -> RpcEndpoint:
        return check.not_none(self._bound_endpoint)

    async def start(self, *, instance_id: uuid.UUID | None = None) -> uuid.UUID:
        if self._listener is not None or self._closing:
            raise RuntimeError('Asyncio RPC server is already started or closed')

        self._instance_id = instance_id or uuid.uuid7()
        self._dispatcher = AsyncRpcRequestDispatcher(
            self._config.handler,
            RpcResponseRegistry(max_entries=self._config.response_cache_size),
            max_frame_bytes=self._config.max_frame_bytes,
        )

        self._listener = await self._transport.listen(
            self._config.resolved_endpoint,
            self._accept_connection,
            backlog=self._config.backlog,
            unix_socket_mode=self._config.socket_mode,
        )
        self._bound_endpoint = self._listener.bound_endpoint
        return self._instance_id

    def _accept_connection(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
    ) -> None:
        task = asyncio.create_task(self._run_connection(reader, writer))
        self._connections.add(task)
        task.add_done_callback(self._connections.discard)

    async def _driver_next(self, driver: PollAsyncioStreamIoPipelineDriver) -> ta.Any:
        return await asyncio.wait_for(
            driver.next(),
            self._config.connection_timeout_s,
        )

    async def _handle_connection(self, driver: PollAsyncioStreamIoPipelineDriver) -> None:
        while True:
            event = await self._driver_next(driver)
            if isinstance(event, RpcPipelineFailure):
                raise event.exc
            if isinstance(event, RpcServerDispatch):
                request = event.request
                break
            if event is not None:
                raise RpcProtocolError(f'Unexpected RPC server event: {event!r}')
            if not driver.is_running:
                return

        if self._closing:
            response: RpcWireResponse = RpcWireError(
                client_id=request.client_id,
                request_id=request.request_id,
                code='unavailable',
                remote_type='omcore.daemons.rpc.RpcServerActivityRejectedError',
                message='RPC server is shutting down',
            )
        else:
            response = await check.not_none(self._dispatcher).dispatch(request)

        driver.enqueue(RpcServerSendResponse(response=response))
        while driver.is_running:
            if (event := await self._driver_next(driver)) is not None:
                if isinstance(event, RpcPipelineFailure):
                    raise event.exc
                raise RpcProtocolError(f'Unexpected RPC server event: {event!r}')

    async def _run_connection(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
    ) -> None:
        task = check.not_none(asyncio.current_task())
        driver = PollAsyncioStreamIoPipelineDriver(
            rpc_server_pipeline_spec(
                protocol_version=RPC_PROTOCOL_VERSION,
                instance_id=self.instance_id,
                max_frame_bytes=self._config.max_frame_bytes,
            ),
            reader,
            writer,
        )
        self._drivers[task] = driver
        try:
            async with driver:
                await self._handle_connection(driver)
        except (EOFError, OSError, RpcProtocolError):
            pass
        except asyncio.CancelledError:
            raise
        except BaseException:  # noqa
            log.exception('Unhandled asyncio RPC connection error')
        finally:
            self._drivers.pop(task, None)

    async def serve_forever(self) -> ta.NoReturn:
        await check.not_none(self._listener).serve_forever()
        raise RuntimeError('Asyncio RPC server stopped serving')

    async def close(self) -> bool:
        if self._closing:
            return False
        self._closing = True

        if (listener := self._listener) is not None:
            self._listener = None
            await listener.close()

        if self._connections:
            done, pending = await asyncio.wait(
                self._connections,
                timeout=self._config.drain_timeout_s,
            )
            for task in done:
                task.result()
            if pending:
                for task in pending:
                    if (driver := self._drivers.get(task)) is not None:
                        await driver.close()
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                raise RpcServerDrainTimeoutError('Asyncio RPC connections did not drain before timeout')
        return True

    async def __aenter__(self) -> ta.Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
