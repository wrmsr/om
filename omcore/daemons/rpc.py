import collections
import errno
import json
import os
import selectors
import socket
import stat
import struct
import threading
import time
import typing as ta
import uuid

from .. import check
from .. import dataclasses as dc
from .. import lang
from ..logs import all as logs
from ..sockets.io import close_socket_immediately
from .lazy import LazyDaemon
from .runtime import ActivityRejectedError
from .runtime import DrainTimeoutError
from .runtime import ServiceRuntime
from .services import RuntimeService
from .waiting import Wait
from .waiting import Waiter
from .waiting import waiter_for


log = logs.get_module_logger(globals())


##


RPC_PROTOCOL_NAME = 'omcore.daemons.rpc'
RPC_PROTOCOL_VERSION = 1
RPC_DEFAULT_MAX_FRAME_BYTES = 16 * 1024 * 1024


class RpcError(Exception):
    """Base exception for the local RPC protocol."""


class RpcProtocolError(RpcError):
    """Indicates an invalid or incompatible RPC exchange."""


class RpcUnavailableError(RpcError):
    """Indicates that an RPC request is known not to have executed and may be retried safely."""


class RpcRemoteError(RpcError):
    """Reports an exception raised while executing an RPC request."""

    def __init__(
            self,
            *,
            remote_type: str,
            message: str,
    ) -> None:
        super().__init__(f'{remote_type}: {message}')

        self._remote_type = remote_type
        self._message = message

    @property
    def remote_type(self) -> str:
        return self._remote_type

    @property
    def message(self) -> str:
        return self._message


class RpcCallIndeterminateError(RpcError):
    """Indicates that a request may have executed but no authoritative response was received."""

    def __init__(
            self,
            request: RpcRequest,
            *,
            instance_id: str,
            actual_instance_id: str | None = None,
    ) -> None:
        if actual_instance_id is None:
            detail = f'response from service instance {instance_id!r} was lost'
        else:
            detail = (
                f'service instance changed from {instance_id!r} '
                f'to {actual_instance_id!r}'
            )
        super().__init__(f'Outcome of RPC request {request.request_id!r} is indeterminate: {detail}')

        self._request = request
        self._instance_id = instance_id
        self._actual_instance_id = actual_instance_id

    @property
    def request(self) -> RpcRequest:
        return self._request

    @property
    def instance_id(self) -> str:
        return self._instance_id

    @property
    def actual_instance_id(self) -> str | None:
        return self._actual_instance_id


##


@dc.dataclass(frozen=True, kw_only=True)
class RpcRequest:
    """A stable request identity and its JSON-compatible invocation data."""

    client_id: str
    request_id: str
    method: str
    params: ta.Any = None

    def __post_init__(self) -> None:
        check.non_empty_str(self.client_id)
        check.non_empty_str(self.request_id)
        check.non_empty_str(self.method)


class RpcHandler(ta.Protocol):
    def __call__(self, request: RpcRequest) -> ta.Any:
        raise NotImplementedError


##


_FRAME_HEADER = struct.Struct('!I')


def _encode_rpc_message(obj: ta.Mapping[str, ta.Any], max_frame_bytes: int) -> bytes:
    try:
        payload = json.dumps(
            obj,
            allow_nan=False,
            separators=(',', ':'),
        ).encode('utf-8')
    except (TypeError, ValueError) as exc:
        raise RpcProtocolError(f'RPC message is not JSON-compatible: {exc}') from exc

    if len(payload) > max_frame_bytes:
        raise RpcProtocolError(
            f'RPC frame is {len(payload)} bytes, exceeding limit {max_frame_bytes}',
        )

    return _FRAME_HEADER.pack(len(payload)) + payload


def _send_rpc_message(
        sock: socket.socket,
        obj: ta.Mapping[str, ta.Any],
        max_frame_bytes: int,
) -> None:
    sock.sendall(_encode_rpc_message(obj, max_frame_bytes))


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    buf = bytearray()
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            if not buf:
                raise EOFError('RPC connection closed')
            raise RpcProtocolError('RPC connection closed within a frame')
        buf.extend(chunk)
    return bytes(buf)


def _recv_rpc_message(sock: socket.socket, max_frame_bytes: int) -> ta.Mapping[str, ta.Any]:
    header = _recv_exact(sock, _FRAME_HEADER.size)
    size = _FRAME_HEADER.unpack(header)[0]
    if size > max_frame_bytes:
        raise RpcProtocolError(
            f'RPC frame is {size} bytes, exceeding limit {max_frame_bytes}',
        )

    payload = _recv_exact(sock, size)
    try:
        obj = json.loads(payload.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RpcProtocolError(f'Invalid RPC JSON: {exc}') from exc
    if not isinstance(obj, dict):
        raise RpcProtocolError(f'RPC message must be an object, got {type(obj).__name__}')
    return obj


def _exception_type_name(exc: BaseException) -> str:
    cls = type(exc)
    return f'{cls.__module__}.{cls.__qualname__}'


def _hello_message(*, version: int, instance_id: str | None = None) -> ta.Mapping[str, ta.Any]:
    return {
        'type': 'hello',
        'protocol': RPC_PROTOCOL_NAME,
        'version': version,
        **({'instance_id': instance_id} if instance_id is not None else {}),
    }


def _request_message(request: RpcRequest) -> ta.Mapping[str, ta.Any]:
    return {
        'type': 'request',
        'client_id': request.client_id,
        'request_id': request.request_id,
        'method': request.method,
        'params': request.params,
    }


def _result_message(request: RpcRequest, result: ta.Any) -> ta.Mapping[str, ta.Any]:
    return {
        'type': 'result',
        'client_id': request.client_id,
        'request_id': request.request_id,
        'result': result,
    }


def _error_message(
        request: RpcRequest,
        *,
        code: str,
        remote_type: str,
        message: str,
) -> ta.Mapping[str, ta.Any]:
    return {
        'type': 'error',
        'client_id': request.client_id,
        'request_id': request.request_id,
        'error': {
            'code': code,
            'type': remote_type,
            'message': message,
        },
    }


##


class RpcClientConnection(lang.Final):
    """A handshaken, single-request RPC connection."""

    def __init__(
            self,
            sock: socket.socket,
            *,
            instance_id: str,
            max_frame_bytes: int,
    ) -> None:
        super().__init__()

        self._sock: socket.socket | None = sock
        self._instance_id = instance_id
        self._max_frame_bytes = max_frame_bytes

        self._request: RpcRequest | None = None
        self._response_received = False

    @property
    def instance_id(self) -> str:
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

        data = _encode_rpc_message(
            _request_message(request),
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
            obj = _recv_rpc_message(self._socket(), self._max_frame_bytes)
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
        self._client_id = client_id or uuid.uuid4().hex

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
            request_id=request_id or uuid.uuid4().hex,
            method=method,
            params=params,
        )

    def connect(self) -> RpcClientConnection:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.settimeout(self._config.connect_timeout_s)
            sock.connect(self._config.socket_path)
            sock.settimeout(self._config.io_timeout_s)

            _send_rpc_message(
                sock,
                _hello_message(version=self._config.protocol_version),
                self._config.max_frame_bytes,
            )
            hello = _recv_rpc_message(sock, self._config.max_frame_bytes)

            if hello.get('type') != 'hello':
                raise RpcProtocolError(f'Expected RPC hello, got {hello.get("type")!r}')
            if hello.get('protocol') != RPC_PROTOCOL_NAME:
                raise RpcProtocolError(f'Unexpected RPC protocol: {hello.get("protocol")!r}')
            if hello.get('version') != self._config.protocol_version:
                raise RpcProtocolError(
                    f'RPC protocol version mismatch: '
                    f'client={self._config.protocol_version}, server={hello.get("version")!r}',
                )
            instance_id = hello.get('instance_id')
            if not isinstance(instance_id, str) or not instance_id:
                raise RpcProtocolError(f'Invalid RPC service instance id: {instance_id!r}')

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

    def ping(self) -> str:
        with self.connect() as conn:
            return conn.instance_id

    def call_request(
            self,
            request: RpcRequest,
            *,
            expected_instance_id: str | None = None,
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


class _LazyRpcRetryError(RpcUnavailableError):
    pass


class LazyRpcClient(lang.Final):
    """Combines an RPC client with lazy daemon launch and safe same-instance replay."""

    def __init__(
            self,
            lazy_daemon: LazyDaemon,
            client: RpcClient,
    ) -> None:
        super().__init__()

        self._lazy_daemon = lazy_daemon
        self._client = client

    @property
    def lazy_daemon(self) -> LazyDaemon:
        return self._lazy_daemon

    @property
    def client(self) -> RpcClient:
        return self._client

    def call(
            self,
            method: str,
            params: ta.Any = None,
            *,
            timeout: lang.TimeoutLike = lang.Timeout.DEFAULT,
    ) -> ta.Any:
        request = self._client.new_request(method, params)
        expected_instance_id: str | None = None

        def attempt() -> ta.Any:
            nonlocal expected_instance_id

            try:
                return self._client.call_request(
                    request,
                    expected_instance_id=expected_instance_id,
                )
            except RpcCallIndeterminateError as exc:
                if exc.actual_instance_id is not None:
                    raise
                expected_instance_id = exc.instance_id
                raise _LazyRpcRetryError(str(exc)) from exc

        return self._lazy_daemon.call(
            attempt,
            is_unavailable=lambda exc: isinstance(exc, RpcUnavailableError),
            timeout=timeout,
        )


##


class RpcWait(Wait):
    """A daemon readiness probe that completes a full RPC handshake."""

    client: RpcClient.Config


class RpcWaiter(Waiter, dc.Frozen):
    wait: RpcWait

    def do_wait(self) -> bool:
        try:
            RpcClient(self.wait.client).ping()
        except RpcUnavailableError:
            return False
        else:
            return True


@waiter_for.register
def _(wait: RpcWait) -> RpcWaiter:
    return RpcWaiter(wait)


##


class _RpcResponseEntry:
    def __init__(self, request: RpcRequest) -> None:
        super().__init__()

        self.request = request
        self.response: ta.Mapping[str, ta.Any] | None = None


class _RpcResponseCache:
    def __init__(
            self,
            handler: RpcHandler,
            *,
            max_entries: int,
            max_frame_bytes: int,
    ) -> None:
        super().__init__()

        self._handler = handler
        self._max_entries = max_entries
        self._max_frame_bytes = max_frame_bytes

        self._condition = threading.Condition(threading.RLock())
        self._entries: collections.OrderedDict[tuple[str, str], _RpcResponseEntry] = collections.OrderedDict()

    def _wait_locked(self, entry: _RpcResponseEntry) -> ta.Mapping[str, ta.Any]:
        while entry.response is None:
            self._condition.wait()
        return entry.response

    def call(self, request: RpcRequest) -> ta.Mapping[str, ta.Any]:
        key = (request.client_id, request.request_id)

        with self._condition:
            if (entry := self._entries.get(key)) is not None:
                if entry.request != request:
                    return _error_message(
                        request,
                        code='protocol',
                        remote_type='omcore.daemons.rpc.RpcProtocolError',
                        message='RPC request id was reused with different request data',
                    )
                response = self._wait_locked(entry)
                self._entries.move_to_end(key)
                return response

            if len(self._entries) >= self._max_entries:
                return _error_message(
                    request,
                    code='remote',
                    remote_type='omcore.daemons.rpc.RpcRequestCacheFullError',
                    message='RPC request cache is full',
                )

            entry = _RpcResponseEntry(request)
            self._entries[key] = entry

        try:
            try:
                result = self._handler(request)
            except BaseException as exc:  # noqa
                response = _error_message(
                    request,
                    code='remote',
                    remote_type=_exception_type_name(exc),
                    message=str(exc)[:1_000],
                )
            else:
                response = _result_message(request, result)

            try:
                _encode_rpc_message(response, self._max_frame_bytes)
            except RpcProtocolError as exc:
                response = _error_message(
                    request,
                    code='remote',
                    remote_type=_exception_type_name(exc),
                    message=str(exc)[:1_000],
                )
                _encode_rpc_message(response, self._max_frame_bytes)

        except BaseException as exc:  # noqa
            response = _error_message(
                request,
                code='remote',
                remote_type=_exception_type_name(exc),
                message='Failed to construct RPC response',
            )

        with self._condition:
            entry.response = response
            self._entries.move_to_end(key)
            self._condition.notify_all()
            return response


class _RpcConnectionThreads:
    def __init__(self) -> None:
        super().__init__()

        self._condition = threading.Condition(threading.RLock())
        self._threads: set[threading.Thread] = set()
        self._sockets: set[socket.socket] = set()

    def start(
            self,
            conn: socket.socket,
            fn: ta.Callable[[socket.socket], None],
    ) -> None:
        def run() -> None:
            try:
                fn(conn)
            except (EOFError, OSError, RpcProtocolError):
                pass
            except BaseException:  # noqa
                log.exception('Unhandled RPC connection error')
            finally:
                close_socket_immediately(conn)
                with self._condition:
                    self._sockets.discard(conn)
                    self._threads.discard(threading.current_thread())
                    self._condition.notify_all()

        thread = threading.Thread(
            target=run,
            name='RpcServiceConnection',
            daemon=True,
        )
        with self._condition:
            self._threads.add(thread)
            self._sockets.add(conn)
        thread.start()

    def wait(self, timeout_s: float | None) -> bool:
        deadline = time.monotonic() + timeout_s if timeout_s is not None else None

        with self._condition:
            while self._threads:
                if deadline is None:
                    self._condition.wait()
                    continue

                remaining_s = deadline - time.monotonic()
                if remaining_s <= 0.:
                    return False
                self._condition.wait(remaining_s)
            return True

    def close_sockets(self) -> None:
        with self._condition:
            sockets = list(self._sockets)
        for sock in sockets:
            close_socket_immediately(sock)


class RpcService(RuntimeService['RpcService.Config']):
    """A concurrent Unix-socket RPC service governed by ServiceRuntime."""

    @dc.dataclass(frozen=True, kw_only=True)
    class Config(RuntimeService.Config):
        socket_path: str
        handler: RpcHandler

        socket_mode: int = 0o600
        connection_timeout_s: float | None = 30.
        max_frame_bytes: int = RPC_DEFAULT_MAX_FRAME_BYTES
        # Entries are never evicted: rejecting new requests at capacity preserves same-instance replay safety.
        response_cache_size: int = 1_024
        backlog: int = 128

        def __post_init__(self) -> None:
            check.non_empty_str(self.socket_path)
            check.arg(0 <= self.socket_mode <= 0o777)
            check.arg(self.connection_timeout_s is None or self.connection_timeout_s > 0.)
            check.arg(self.max_frame_bytes > 0)
            check.arg(self.response_cache_size > 0)
            check.arg(self.backlog > 0)

    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def _parse_hello(self, obj: ta.Mapping[str, ta.Any]) -> int:
        if obj.get('type') != 'hello' or obj.get('protocol') != RPC_PROTOCOL_NAME:
            raise RpcProtocolError('Invalid RPC hello')
        version = obj.get('version')
        if not isinstance(version, int):
            raise RpcProtocolError(f'Invalid RPC protocol version: {version!r}')
        return version

    @staticmethod
    def _parse_request(obj: ta.Mapping[str, ta.Any]) -> RpcRequest:
        if obj.get('type') != 'request':
            raise RpcProtocolError(f'Expected RPC request, got {obj.get("type")!r}')
        try:
            return RpcRequest(
                client_id=check.isinstance(obj['client_id'], str),
                request_id=check.isinstance(obj['request_id'], str),
                method=check.isinstance(obj['method'], str),
                params=obj.get('params'),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RpcProtocolError(f'Invalid RPC request: {exc}') from exc

    def _handle_connection(
            self,
            conn: socket.socket,
            *,
            instance_id: str,
            runtime: ServiceRuntime,
            responses: _RpcResponseCache,
    ) -> None:
        conn.settimeout(self.config.connection_timeout_s)

        version = self._parse_hello(_recv_rpc_message(conn, self.config.max_frame_bytes))
        _send_rpc_message(
            conn,
            _hello_message(
                version=RPC_PROTOCOL_VERSION,
                instance_id=instance_id,
            ),
            self.config.max_frame_bytes,
        )
        if version != RPC_PROTOCOL_VERSION:
            return

        request = self._parse_request(_recv_rpc_message(conn, self.config.max_frame_bytes))

        try:
            activity = runtime.activity.acquire()
        except ActivityRejectedError as exc:
            response = _error_message(
                request,
                code='unavailable',
                remote_type=_exception_type_name(exc),
                message=str(exc),
            )
            _send_rpc_message(conn, response, self.config.max_frame_bytes)
            return

        with activity:
            response = responses.call(request)
            _send_rpc_message(conn, response, self.config.max_frame_bytes)

    def _unlink_socket(self, identity: tuple[int, int] | None) -> None:
        if identity is None:
            return
        try:
            stat_result = os.lstat(self.config.socket_path)
        except FileNotFoundError:
            return
        if (stat_result.st_dev, stat_result.st_ino) == identity:
            os.unlink(self.config.socket_path)

    def _bind_listener(self, listener: socket.socket) -> None:
        try:
            listener.bind(self.config.socket_path)
            return
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise

        try:
            socket_stat = os.lstat(self.config.socket_path)
        except FileNotFoundError:
            listener.bind(self.config.socket_path)
            return
        if not stat.S_ISSOCK(socket_stat.st_mode):
            raise RuntimeError(f'Refusing to replace non-socket path: {self.config.socket_path!r}')

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
            try:
                probe.connect(self.config.socket_path)
            except (ConnectionRefusedError, FileNotFoundError):
                pass
            else:
                raise RuntimeError(f'RPC socket is already active: {self.config.socket_path!r}')

        try:
            os.unlink(self.config.socket_path)
        except FileNotFoundError:
            pass
        listener.bind(self.config.socket_path)

    def _run_runtime(self, runtime: ServiceRuntime) -> None:
        instance_id = uuid.uuid4().hex
        responses = _RpcResponseCache(
            self.config.handler,
            max_entries=self.config.response_cache_size,
            max_frame_bytes=self.config.max_frame_bytes,
        )
        connections = _RpcConnectionThreads()

        socket_identity: tuple[int, int] | None = None
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                self._bind_listener(listener)
                os.chmod(self.config.socket_path, self.config.socket_mode)
                socket_stat = os.lstat(self.config.socket_path)
                socket_identity = (socket_stat.st_dev, socket_stat.st_ino)

                listener.listen(self.config.backlog)
                listener.setblocking(False)

                shutdown_read_sock, shutdown_write_sock = socket.socketpair()
                with shutdown_read_sock, shutdown_write_sock:
                    def wake_for_shutdown() -> None:
                        runtime.shutdown.wait()
                        try:
                            shutdown_write_sock.sendall(b'X')
                        except OSError:
                            pass

                    shutdown_thread = threading.Thread(
                        target=wake_for_shutdown,
                        name='RpcServiceShutdown',
                        daemon=True,
                    )
                    shutdown_thread.start()

                    try:
                        with selectors.DefaultSelector() as selector:
                            selector.register(listener, selectors.EVENT_READ, 'listener')
                            selector.register(shutdown_read_sock, selectors.EVENT_READ, 'shutdown')

                            while not runtime.shutdown.requested:
                                for key, _ in selector.select():
                                    if key.data == 'shutdown':
                                        shutdown_read_sock.recv(4096)
                                        continue

                                    try:
                                        conn, _ = listener.accept()
                                    except BlockingIOError:
                                        continue

                                    connections.start(
                                        conn,
                                        lambda conn: self._handle_connection(
                                            conn,
                                            instance_id=instance_id,
                                            runtime=runtime,
                                            responses=responses,
                                        ),
                                    )

                    finally:
                        if not runtime.shutdown.requested:
                            runtime.shutdown.request(message='rpc-service-exiting')
                        shutdown_thread.join()

            if not connections.wait(runtime.config.drain_timeout_s):
                connections.close_sockets()
                raise DrainTimeoutError('RPC connections did not drain before timeout')

        finally:
            self._unlink_socket(socket_identity)
