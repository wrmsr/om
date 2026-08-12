import socket
import typing as ta
import uuid

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...sockets.io import close_socket_immediately
from .protocol import RPC_DEFAULT_MAX_FRAME_BYTES
from .protocol import RPC_PROTOCOL_NAME
from .protocol import RPC_PROTOCOL_VERSION
from .protocol import RpcCallIndeterminateError
from .protocol import RpcProtocolError
from .protocol import RpcRemoteError
from .protocol import RpcRequest
from .protocol import RpcUnavailableError
from .protocol import encode_rpc_message
from .protocol import hello_message
from .protocol import recv_rpc_message
from .protocol import request_message
from .protocol import send_rpc_message


##


class RpcClientConnection(lang.Final):
    """A handshaken, single-request RPC connection."""

    def __init__(
            self,
            sock: socket.socket,
            *,
            instance_id: uuid.UUID,
            max_frame_bytes: int,
    ) -> None:
        super().__init__()

        self._sock: socket.socket | None = sock
        self._instance_id = instance_id
        self._max_frame_bytes = max_frame_bytes

        self._request: RpcRequest | None = None
        self._response_received = False

    @property
    def instance_id(self) -> uuid.UUID:
        return self._instance_id

    @property
    def closed(self) -> bool:
        return self._sock is None

    def _socket(self) -> socket.socket:
        if self._sock is None:
            raise RuntimeError('RPC client connection is closed')
        return self._sock

    def send(self, request: RpcRequest) -> None:
        if self._request is not None:
            raise RuntimeError('RPC client connection already has a request')

        data = encode_rpc_message(
            request_message(request),
            self._max_frame_bytes,
        )
        self._request = request
        try:
            self._socket().sendall(data)
        except OSError as exc:
            raise RpcCallIndeterminateError(
                request,
                instance_id=self._instance_id,
            ) from exc

    def receive(self) -> ta.Any:
        request = check.not_none(self._request)
        if self._response_received:
            raise RuntimeError('RPC client connection already received its response')

        try:
            obj = recv_rpc_message(self._socket(), self._max_frame_bytes)
        except (EOFError, OSError, RpcProtocolError) as exc:
            raise RpcCallIndeterminateError(
                request,
                instance_id=self._instance_id,
            ) from exc

        self._response_received = True

        if obj.get('client_id') != request.client_id or obj.get('request_id') != request.request_id:
            raise RpcCallIndeterminateError(
                request,
                instance_id=self._instance_id,
            )

        message_type = obj.get('type')
        if message_type == 'result':
            if 'result' not in obj:
                raise RpcCallIndeterminateError(
                    request,
                    instance_id=self._instance_id,
                )
            return obj['result']

        if message_type != 'error':
            raise RpcCallIndeterminateError(
                request,
                instance_id=self._instance_id,
            )

        error = obj.get('error')
        if not isinstance(error, dict):
            raise RpcCallIndeterminateError(
                request,
                instance_id=self._instance_id,
            )

        code = error.get('code')
        remote_type = error.get('type')
        message = error.get('message')
        if not isinstance(remote_type, str) or not isinstance(message, str):
            raise RpcCallIndeterminateError(
                request,
                instance_id=self._instance_id,
            )

        if code == 'unavailable':
            raise RpcUnavailableError(message)
        if code == 'remote':
            raise RpcRemoteError(
                remote_type=remote_type,
                message=message,
            )
        if code == 'protocol':
            raise RpcProtocolError(message)
        raise RpcCallIndeterminateError(
            request,
            instance_id=self._instance_id,
        )

    def call(self, request: RpcRequest) -> ta.Any:
        self.send(request)
        return self.receive()

    def close(self) -> bool:
        if (sock := self._sock) is None:
            return False
        self._sock = None
        close_socket_immediately(sock)
        return True

    def __enter__(self) -> ta.Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class RpcClient(lang.Final):
    """A synchronous client for one-request-per-connection local RPC."""

    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        socket_path: str

        protocol_version: int = RPC_PROTOCOL_VERSION
        connect_timeout_s: float | None = 5.
        io_timeout_s: float | None = 30.
        max_frame_bytes: int = RPC_DEFAULT_MAX_FRAME_BYTES

        def __post_init__(self) -> None:
            check.non_empty_str(self.socket_path)
            check.arg(self.protocol_version > 0)
            check.arg(self.connect_timeout_s is None or self.connect_timeout_s > 0.)
            check.arg(self.io_timeout_s is None or self.io_timeout_s > 0.)
            check.arg(self.max_frame_bytes > 0)

    def __init__(
            self,
            config: Config,
            *,
            client_id: str | None = None,
    ) -> None:
        super().__init__()

        self._config = config
        self._client_id = client_id or uuid.uuid7().hex

    @property
    def config(self) -> Config:
        return self._config

    @property
    def client_id(self) -> str:
        return self._client_id

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
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.settimeout(self._config.connect_timeout_s)
            sock.connect(self._config.socket_path)
            sock.settimeout(self._config.io_timeout_s)

            send_rpc_message(
                sock,
                hello_message(version=self._config.protocol_version),
                self._config.max_frame_bytes,
            )
            hello = recv_rpc_message(sock, self._config.max_frame_bytes)

            if hello.get('type') != 'hello':
                raise RpcProtocolError(f'Expected RPC hello, got {hello.get("type")!r}')
            if hello.get('protocol') != RPC_PROTOCOL_NAME:
                raise RpcProtocolError(f'Unexpected RPC protocol: {hello.get("protocol")!r}')
            if hello.get('version') != self._config.protocol_version:
                raise RpcProtocolError(
                    f'RPC protocol version mismatch: '
                    f'client={self._config.protocol_version}, server={hello.get("version")!r}',
                )
            raw_instance_id = hello.get('instance_id')
            if not isinstance(raw_instance_id, str) or not raw_instance_id:
                raise RpcProtocolError(f'Invalid RPC service instance id: {raw_instance_id!r}')
            try:
                instance_id = uuid.UUID(raw_instance_id)
            except ValueError as exc:
                raise RpcProtocolError(f'Invalid RPC service instance id: {raw_instance_id!r}') from exc

            return RpcClientConnection(
                sock,
                instance_id=instance_id,
                max_frame_bytes=self._config.max_frame_bytes,
            )

        except RpcProtocolError:
            close_socket_immediately(sock)
            raise
        except (EOFError, OSError) as exc:
            close_socket_immediately(sock)
            raise RpcUnavailableError(str(exc)) from exc

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
