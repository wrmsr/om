import asyncio
import contextlib
import inspect
import typing as ta
import uuid

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore.io.pipelines.drivers.asyncio.streams import PollAsyncioStreamIoPipelineDriver
from omcore.logs import all as logs
from omcore.rpc.asyncios import AsyncioRpcRuntime
from omcore.rpc.connection import RpcConnection
from omcore.sockets.endpoints import SocketEndpoint as RpcEndpoint
from omcore.sockets.endpoints import resolve_socket_endpoint as resolve_rpc_endpoint
from omcore.sockets.transports.asyncio import DEFAULT_ASYNCIO_SOCKET_TRANSPORT as DEFAULT_ASYNCIO_RPC_TRANSPORT
from omcore.sockets.transports.asyncio import AsyncioSocketListener as AsyncioRpcListener
from omcore.sockets.transports.asyncio import AsyncioSocketTransport as AsyncioRpcTransport

from .client import RpcClient
from .connections import RpcClientRpcConnection
from .connections import RpcServerHandler
from .dispatch import rpc_remote_error_response
from .dispatch import validate_rpc_response
from .pipelines import RpcWireResponse
from .pipelines import RpcWireResult
from .pipelines import rpc_client_pipeline
from .pipelines import rpc_server_pipeline
from .protocol import RPC_DEFAULT_MAX_FRAME_BYTES
from .protocol import RPC_PROTOCOL_VERSION
from .protocol import RpcCallIndeterminateError
from .protocol import RpcHandler
from .protocol import RpcRequest
from .protocol import RpcUnavailableError
from .registry import RpcResponseExecute
from .registry import RpcResponsePending
from .registry import RpcResponseRegistry
from .registry import RpcResponseRejected
from .registry import RpcResponseReplay
from .server import RpcServerDrainTimeoutError


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
    """A handshaken, single-request RPC connection: the shared client core, on asyncio."""

    def __init__(self, conn: RpcClientRpcConnection) -> None:
        super().__init__()

        self._conn: RpcClientRpcConnection | None = conn
        self._instance_id: uuid.UUID | None = None

    @property
    def instance_id(self) -> uuid.UUID:
        if (conn := self._conn) is not None:
            return conn.instance_id
        return check.not_none(self._instance_id)

    @property
    def closed(self) -> bool:
        return self._conn is None

    def _live(self) -> RpcClientRpcConnection:
        if (conn := self._conn) is None:
            raise RuntimeError('RPC client connection is closed')
        return conn

    async def send(self, request: RpcRequest) -> None:
        await self._live().send_rpc(request)

    async def receive(self) -> ta.Any:
        return await self._live().receive_rpc()

    async def call(self, request: RpcRequest) -> ta.Any:
        await self.send(request)
        return await self.receive()

    async def close(self) -> bool:
        if (conn := self._conn) is None:
            return False
        self._conn = None
        try:
            self._instance_id = conn.instance_id
        except Exception:  # noqa
            pass
        await conn.close(graceful=False)
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

        pipeline = rpc_client_pipeline(
            protocol_version=self._config.protocol_version,
            max_frame_bytes=self._config.max_frame_bytes,
            io_timeout_s=self._config.io_timeout_s,
        )
        conn = RpcClientRpcConnection(
            AsyncioRpcRuntime(PollAsyncioStreamIoPipelineDriver(pipeline.spec, reader, writer)),
            pipeline.config,
            max_frame_bytes=self._config.max_frame_bytes,
            io_timeout_s=self._config.io_timeout_s,
        )
        client_conn = AsyncioRpcClientConnection(conn)
        try:
            await conn.start()
            await conn.handshake()
        except BaseException:
            await client_conn.close()
            raise
        return client_conn

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
        self._rpc_connections: dict[asyncio.Task[ta.Any], RpcConnection] = {}
        self._dispatches: set[asyncio.Task[RpcWireResponse]] = set()
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

    def _acquire_activity(self) -> ta.ContextManager[ta.Any] | None:
        if self._closing:
            return None
        return contextlib.nullcontext()

    async def _dispatch(self, request: RpcRequest) -> RpcWireResponse:
        # Run apart from the connection, so a client vanishing mid-request does not cancel it: its answer must still
        # reach the replay registry, for the retry. The drain waits for it all the same.
        task = asyncio.create_task(check.not_none(self._dispatcher).dispatch(request))
        self._dispatches.add(task)
        task.add_done_callback(self._dispatches.discard)
        return await asyncio.shield(task)

    async def _run_connection(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
    ) -> None:
        task = check.not_none(asyncio.current_task())

        pipeline = rpc_server_pipeline(
            protocol_version=RPC_PROTOCOL_VERSION,
            instance_id=self.instance_id,
            max_frame_bytes=self._config.max_frame_bytes,
            connection_timeout_s=self._config.connection_timeout_s,
        )
        handler = RpcServerHandler(self._dispatch, self._acquire_activity)
        conn = RpcConnection(
            AsyncioRpcRuntime(PollAsyncioStreamIoPipelineDriver(pipeline.spec, reader, writer)),
            pipeline.config,
            handler=handler,
        )
        conn.add_close_callback(handler.release_activity)

        self._rpc_connections[task] = conn
        try:
            await conn.start()
            await conn.wait_closed()
            if (exc := conn.close_exception) is not None:
                log.debug('Asyncio RPC connection failed: %r', exc)
        except asyncio.CancelledError:
            raise
        except BaseException:  # noqa
            log.exception('Unhandled asyncio RPC connection error')
        finally:
            self._rpc_connections.pop(task, None)

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

        waiting: set[asyncio.Task[ta.Any]] = {*self._connections, *self._dispatches}
        if waiting:
            done, pending = await asyncio.wait(
                waiting,
                timeout=self._config.drain_timeout_s,
            )
            for task in done:
                if task in self._connections or not task.cancelled():
                    task.result()
            if pending:
                for task in pending:
                    if (conn := self._rpc_connections.get(task)) is not None:
                        await conn.close(graceful=False)
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                raise RpcServerDrainTimeoutError('Asyncio RPC connections did not drain before timeout')
        return True

    async def __aenter__(self) -> ta.Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
