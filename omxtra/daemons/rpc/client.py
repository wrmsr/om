import functools
import typing as ta
import uuid

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore.io.pipelines.drivers.sync.sockets import SocketSyncIoPipelineDriver
from omcore.rpc.connection import SyncRpcConnection
from omcore.rpc.sync import SyncRpcRuntime
from omcore.sockets.endpoints import SocketEndpoint as RpcEndpoint
from omcore.sockets.endpoints import resolve_socket_endpoint as resolve_rpc_endpoint
from omcore.sockets.io import close_socket_immediately
from omcore.sockets.transports.sync import DEFAULT_SYNC_SOCKET_TRANSPORT as DEFAULT_SYNC_RPC_TRANSPORT
from omcore.sockets.transports.sync import SyncSocketTransport as SyncRpcTransport

from .connections import RpcClientRpcConnection
from .pipelines import rpc_client_pipeline
from .protocol import RPC_DEFAULT_MAX_FRAME_BYTES
from .protocol import RPC_PROTOCOL_VERSION
from .protocol import RpcCallIndeterminateError
from .protocol import RpcRequest
from .protocol import RpcUnavailableError


T = ta.TypeVar('T')


##


class RpcClientConnection(lang.Final):
    """A handshaken, single-request RPC connection: the shared client core, run synchronously."""

    def __init__(self, conn: RpcClientRpcConnection) -> None:
        super().__init__()

        self._conn = conn
        self._sync: SyncRpcConnection | None = SyncRpcConnection(conn)

    @property
    def instance_id(self) -> uuid.UUID:
        return self._conn.instance_id

    @property
    def closed(self) -> bool:
        return self._sync is None

    def _run(self, aw: ta.Awaitable[T]) -> T:
        if (sync := self._sync) is None:
            raise RuntimeError('RPC client connection is closed')
        return sync.run(aw)

    def send(self, request: RpcRequest) -> None:
        self._run(self._conn.send_rpc(request))

    def receive(self) -> ta.Any:
        return self._run(self._conn.receive_rpc())

    def call(self, request: RpcRequest) -> ta.Any:
        self.send(request)
        return self.receive()

    def close(self) -> bool:
        if (sync := self._sync) is None:
            return False
        self._sync = None
        sync.close(graceful=False)
        return True

    def __enter__(self) -> ta.Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class RpcClient(lang.Final):
    """A synchronous client for one-request-per-connection byte-stream RPC."""

    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        # socket_path is the compatibility spelling for UnixRpcEndpoint.
        socket_path: str = ''
        endpoint: RpcEndpoint | None = None

        protocol_version: int = RPC_PROTOCOL_VERSION
        connect_timeout_s: float | None = 5.
        io_timeout_s: float | None = 30.
        max_frame_bytes: int = RPC_DEFAULT_MAX_FRAME_BYTES

        @property
        def resolved_endpoint(self) -> RpcEndpoint:
            return resolve_rpc_endpoint(
                endpoint=self.endpoint,
                socket_path=self.socket_path,
            )

        def __post_init__(self) -> None:
            _ = self.resolved_endpoint
            check.arg(self.protocol_version > 0)
            check.arg(self.connect_timeout_s is None or self.connect_timeout_s > 0.)
            check.arg(self.io_timeout_s is None or self.io_timeout_s > 0.)
            check.arg(self.max_frame_bytes > 0)

    def __init__(
            self,
            config: Config,
            *,
            client_id: str | None = None,
            transport: SyncRpcTransport = DEFAULT_SYNC_RPC_TRANSPORT,
    ) -> None:
        super().__init__()

        self._config = config
        self._client_id = client_id or uuid.uuid7().hex
        self._transport = transport

    @property
    def config(self) -> Config:
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

    def connect(self) -> RpcClientConnection:
        try:
            sock = self._transport.connect(
                self.endpoint,
                timeout_s=self._config.connect_timeout_s,
            )
        except OSError as exc:
            raise RpcUnavailableError(str(exc)) from exc

        # Every timeout from here on is the session's.
        sock.settimeout(None)

        pipeline = rpc_client_pipeline(
            protocol_version=self._config.protocol_version,
            max_frame_bytes=self._config.max_frame_bytes,
            io_timeout_s=self._config.io_timeout_s,
        )
        conn = RpcClientRpcConnection(
            SyncRpcRuntime(
                SocketSyncIoPipelineDriver(pipeline.spec, sock),
                closers=[functools.partial(close_socket_immediately, sock)],
            ),
            pipeline.config,
            max_frame_bytes=self._config.max_frame_bytes,
            io_timeout_s=self._config.io_timeout_s,
        )
        client_conn = RpcClientConnection(conn)
        try:
            client_conn._run(conn.start())  # noqa
            client_conn._run(conn.handshake())  # noqa
        except BaseException:
            client_conn.close()
            raise
        return client_conn

    def ping(self) -> uuid.UUID:
        with self.connect() as conn:
            return conn.instance_id

    def call_request(
            self,
            request: RpcRequest,
            *,
            expected_instance_id: uuid.UUID | None = None,
    ) -> ta.Any:
        with self.connect() as conn:
            if expected_instance_id is not None and conn.instance_id != expected_instance_id:
                raise RpcCallIndeterminateError(
                    request,
                    instance_id=expected_instance_id,
                    actual_instance_id=conn.instance_id,
                )
            return conn.call(request)

    def call(self, method: str, params: ta.Any = None) -> ta.Any:
        return self.call_request(self.new_request(method, params))
