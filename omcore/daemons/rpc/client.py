import socket
import typing as ta
import uuid

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...io.pipelines.drivers.sync import SyncSocketIoPipelineDriver
from ...sockets.io import close_socket_immediately
from .pipelines import RpcClientConnected
from .pipelines import RpcClientRequestSent
from .pipelines import RpcClientResponse
from .pipelines import RpcClientSendRequest
from .pipelines import RpcPipelineFailure
from .pipelines import RpcWireError
from .pipelines import RpcWireRequest
from .pipelines import RpcWireResponse
from .pipelines import RpcWireResult
from .pipelines import rpc_client_pipeline_spec
from .pipelines.codecs import encode_rpc_wire_message_payload
from .protocol import RPC_DEFAULT_MAX_FRAME_BYTES
from .protocol import RPC_PROTOCOL_VERSION
from .protocol import RpcCallIndeterminateError
from .protocol import RpcProtocolError
from .protocol import RpcRemoteError
from .protocol import RpcRequest
from .protocol import RpcUnavailableError


##


class RpcClientConnection(lang.Final):
    """A pipeline-backed, handshaken, single-request RPC connection."""

    def __init__(
            self,
            sock: socket.socket,
            driver: SyncSocketIoPipelineDriver,
            *,
            instance_id: uuid.UUID,
            max_frame_bytes: int,
    ) -> None:
        super().__init__()

        self._sock: socket.socket | None = sock
        self._driver: SyncSocketIoPipelineDriver | None = driver
        self._instance_id = instance_id
        self._max_frame_bytes = max_frame_bytes

        self._request: RpcRequest | None = None
        self._response: RpcWireResponse | None = None
        self._response_received = False

    @property
    def instance_id(self) -> uuid.UUID:
        return self._instance_id

    @property
    def closed(self) -> bool:
        return self._sock is None

    def _pipeline_driver(self) -> SyncSocketIoPipelineDriver:
        if self._driver is None:
            raise RuntimeError('RPC client connection is closed')
        return self._driver

    def _indeterminate(self, request: RpcRequest, exc: BaseException | None = None) -> ta.NoReturn:
        error = RpcCallIndeterminateError(
            request,
            instance_id=self._instance_id,
        )
        if exc is None:
            raise error
        raise error from exc

    def send(self, request: RpcRequest) -> None:
        if self._request is not None:
            raise RuntimeError('RPC client connection already has a request')

        payload = encode_rpc_wire_message_payload(RpcWireRequest(request=request))
        if len(payload) > self._max_frame_bytes:
            raise RpcProtocolError(f'RPC frame is {len(payload)} bytes, exceeding limit {self._max_frame_bytes}')

        driver = self._pipeline_driver()
        self._request = request
        driver.enqueue(RpcClientSendRequest(request=request))
        try:
            while True:
                event = driver.next()
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

    def _receive_response(self, request: RpcRequest) -> RpcWireResponse:
        if (response := self._response) is not None:
            return response

        driver = self._pipeline_driver()
        try:
            while True:
                event = driver.next()
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

    def receive(self) -> ta.Any:
        request = check.not_none(self._request)
        if self._response_received:
            raise RuntimeError('RPC client connection already received its response')

        response = self._receive_response(request)
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

    def call(self, request: RpcRequest) -> ta.Any:
        self.send(request)
        return self.receive()

    def close(self) -> bool:
        if (sock := self._sock) is None:
            return False
        self._sock = None

        driver, self._driver = self._driver, None
        if driver is not None:
            driver.close()
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
        driver: SyncSocketIoPipelineDriver | None = None
        try:
            sock.settimeout(self._config.connect_timeout_s)
            sock.connect(self._config.socket_path)
            sock.settimeout(self._config.io_timeout_s)

            driver = SyncSocketIoPipelineDriver(
                rpc_client_pipeline_spec(
                    protocol_version=self._config.protocol_version,
                    max_frame_bytes=self._config.max_frame_bytes,
                ),
                sock,
            )
            while True:
                event = driver.next()
                if isinstance(event, RpcClientConnected):
                    return RpcClientConnection(
                        sock,
                        driver,
                        instance_id=event.instance_id,
                        max_frame_bytes=self._config.max_frame_bytes,
                    )
                if isinstance(event, RpcPipelineFailure):
                    if isinstance(event.exc, RpcProtocolError):
                        raise event.exc
                    raise RpcUnavailableError(str(event.exc)) from event.exc
                if event is not None:
                    raise RpcProtocolError(f'Unexpected RPC handshake event: {event!r}')

        except (RpcProtocolError, RpcUnavailableError):
            if driver is not None:
                driver.close()
            close_socket_immediately(sock)
            raise
        except (EOFError, OSError) as exc:
            if driver is not None:
                driver.close()
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
