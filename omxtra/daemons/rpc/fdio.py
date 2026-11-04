import socket
import threading
import time
import typing as ta
import uuid

from omcore import check
from omcore import lang
from omcore.io.fdio import all as fdio
from omcore.lite.asyncs import sync_await
from omcore.logs import all as logs
from omcore.rpc.connection import RpcConnection
from omcore.rpc.fdio import RpcSocketFdioHandler
from omcore.sockets.addresses import SocketAddress
from omcore.sockets.endpoints import SocketEndpoint as RpcEndpoint
from omcore.sockets.transports.sync import DEFAULT_SYNC_SOCKET_TRANSPORT as DEFAULT_SYNC_RPC_TRANSPORT
from omcore.sockets.transports.sync import SyncSocketListener as SyncRpcListener
from omcore.sockets.transports.sync import SyncSocketTransport as SyncRpcTransport

from .connections import RpcServerHandler
from .dispatch import RpcRequestDispatcher
from .pipelines import RpcWireResponse
from .pipelines import rpc_server_pipeline
from .protocol import RPC_PROTOCOL_VERSION
from .protocol import RpcRequest
from .registry import RpcResponseRegistry
from .server import RpcServerConfig
from .server import RpcServerDrainTimeoutError
from .server import RpcServerRuntime


log = logs.get_module_logger(globals())


##


class _FdioRpcListener(fdio.SocketHandler):
    def __init__(
            self,
            listener: SyncRpcListener,
            on_connect: ta.Callable[[socket.socket, SocketAddress], None],
    ) -> None:
        sock = listener.socket
        sock.setblocking(False)
        super().__init__(sock, sock.getsockname())

        self._listener = listener
        self._on_connect = on_connect

    def close(self) -> None:
        try:
            super().close()
        finally:
            self._listener.close()

    def readable(self) -> bool:
        return True

    def on_readable(self) -> None:
        while True:
            try:
                conn, addr = self._listener.accept()
            except BlockingIOError:
                return
            conn.setblocking(False)
            self._on_connect(conn, addr)


##


class FdioRpcServer(lang.Final):
    """A single-threaded fdio host for the runtime-neutral RPC pipeline."""

    def __init__(
            self,
            config: RpcServerConfig,
            *,
            transport: SyncRpcTransport = DEFAULT_SYNC_RPC_TRANSPORT,
    ) -> None:
        super().__init__()

        self._config = config
        self._transport = transport
        self._bound_endpoint: RpcEndpoint | None = None
        self._started = threading.Event()

    @property
    def config(self) -> RpcServerConfig:
        return self._config

    @property
    def bound_endpoint(self) -> RpcEndpoint:
        return check.not_none(self._bound_endpoint)

    def wait_started(self, timeout_s: float | None = None) -> bool:
        return self._started.wait(timeout_s)

    def run(
            self,
            runtime: RpcServerRuntime,
            *,
            instance_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        instance_id = instance_id or uuid.uuid7()
        dispatcher = RpcRequestDispatcher(
            self._config.handler,
            RpcResponseRegistry(max_entries=self._config.response_cache_size),
            max_frame_bytes=self._config.max_frame_bytes,
        )
        manager = fdio.Manager(fdio.SelectPoller())
        connections: set[RpcSocketFdioHandler] = set()

        socket_listener = self._transport.listen(
            self._config.resolved_endpoint,
            backlog=self._config.backlog,
            unix_socket_mode=self._config.socket_mode,
        )
        self._bound_endpoint = socket_listener.bound_endpoint
        self._started.set()
        try:
            async def dispatch(request: RpcRequest) -> RpcWireResponse:
                return dispatcher.dispatch(request)

            def on_connect(conn: socket.socket, addr: SocketAddress) -> None:
                pipeline = rpc_server_pipeline(
                    protocol_version=RPC_PROTOCOL_VERSION,
                    instance_id=instance_id,
                    max_frame_bytes=self._config.max_frame_bytes,
                    connection_timeout_s=self._config.connection_timeout_s,
                )
                connection = RpcSocketFdioHandler(conn, addr, pipeline.spec)

                handler = RpcServerHandler(dispatch, runtime.acquire_activity)
                rpc_conn = RpcConnection(connection.runtime, pipeline.config, handler=handler)
                rpc_conn.add_close_callback(handler.release_activity)

                # Starting brings the pipeline up without touching the socket; the manager does the rest.
                sync_await(rpc_conn.start())
                connections.add(connection)
                manager.register(connection)

            listener = _FdioRpcListener(socket_listener, on_connect)
            manager.register(listener)
            try:
                while not runtime.shutdown_requested:
                    manager.poll(timeout=.1)
                    connections = {connection for connection in connections if not connection.closed}
            finally:
                listener.close()
                if not runtime.shutdown_requested:
                    runtime.request_shutdown('fdio-rpc-server-exiting')

            deadline = (
                time.monotonic() + runtime.drain_timeout_s
                if runtime.drain_timeout_s is not None
                else None
            )
            while (connections := {connection for connection in connections if not connection.closed}):
                if deadline is not None and time.monotonic() >= deadline:
                    for connection in connections:
                        connection.close()
                    raise RpcServerDrainTimeoutError('RPC connections did not drain before timeout')
                timeout = None if deadline is None else max(0., deadline - time.monotonic())
                manager.poll(timeout=timeout)

            return instance_id
        finally:
            for connection in connections:
                connection.close()
            socket_listener.close()
