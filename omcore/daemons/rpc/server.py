import collections
import contextlib
import errno
import os
import selectors
import socket
import stat
import threading
import time
import typing as ta
import uuid

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...logs import all as logs
from ...sockets.io import close_socket_immediately
from .protocol import RPC_DEFAULT_MAX_FRAME_BYTES
from .protocol import RPC_PROTOCOL_NAME
from .protocol import RPC_PROTOCOL_VERSION
from .protocol import RpcHandler
from .protocol import RpcProtocolError
from .protocol import RpcRequest
from .protocol import encode_rpc_message
from .protocol import error_message
from .protocol import exception_type_name
from .protocol import hello_message
from .protocol import recv_rpc_message
from .protocol import result_message
from .protocol import send_rpc_message


log = logs.get_module_logger(globals())


##


class RpcServerRuntime(ta.Protocol):
    """Lifecycle and activity interface required by RpcServer."""

    @property
    def shutdown_requested(self) -> bool:
        raise NotImplementedError

    @property
    def drain_timeout_s(self) -> float | None:
        raise NotImplementedError

    def wait_shutdown(self) -> None:
        raise NotImplementedError

    def request_shutdown(self, message: str) -> None:
        raise NotImplementedError

    def acquire_activity(self) -> ta.ContextManager[ta.Any] | None:
        raise NotImplementedError


class RpcServerDrainTimeoutError(TimeoutError):
    pass


@dc.dataclass(frozen=True, kw_only=True)
class RpcServerConfig:
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
                    return error_message(
                        request,
                        code='protocol',
                        remote_type='omcore.daemons.rpc.RpcProtocolError',
                        message='RPC request id was reused with different request data',
                    )
                response = self._wait_locked(entry)
                self._entries.move_to_end(key)
                return response

            if len(self._entries) >= self._max_entries:
                return error_message(
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
                response = error_message(
                    request,
                    code='remote',
                    remote_type=exception_type_name(exc),
                    message=str(exc)[:1_000],
                )
            else:
                response = result_message(request, result)

            try:
                encode_rpc_message(response, self._max_frame_bytes)
            except RpcProtocolError as exc:
                response = error_message(
                    request,
                    code='remote',
                    remote_type=exception_type_name(exc),
                    message=str(exc)[:1_000],
                )
                encode_rpc_message(response, self._max_frame_bytes)

        except BaseException as exc:  # noqa
            response = error_message(
                request,
                code='remote',
                remote_type=exception_type_name(exc),
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
            name='RpcServerConnection',
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


##


class RpcServer(lang.Final):
    """A concurrent Unix-socket RPC server driven by a pluggable runtime."""

    def __init__(self, config: RpcServerConfig) -> None:
        super().__init__()

        self._config = config

    @property
    def config(self) -> RpcServerConfig:
        return self._config

    @staticmethod
    def _parse_hello(obj: ta.Mapping[str, ta.Any]) -> int:
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
            instance_id: uuid.UUID,
            runtime: RpcServerRuntime,
            responses: _RpcResponseCache,
    ) -> None:
        conn.settimeout(self._config.connection_timeout_s)

        version = self._parse_hello(recv_rpc_message(conn, self._config.max_frame_bytes))
        send_rpc_message(
            conn,
            hello_message(
                version=RPC_PROTOCOL_VERSION,
                instance_id=instance_id,
            ),
            self._config.max_frame_bytes,
        )
        if version != RPC_PROTOCOL_VERSION:
            return

        request = self._parse_request(recv_rpc_message(conn, self._config.max_frame_bytes))

        if (activity := runtime.acquire_activity()) is None:
            response = error_message(
                request,
                code='unavailable',
                remote_type='omcore.daemons.rpc.RpcServerActivityRejectedError',
                message='RPC server is shutting down',
            )
            send_rpc_message(conn, response, self._config.max_frame_bytes)
            return

        with activity:
            response = responses.call(request)
            send_rpc_message(conn, response, self._config.max_frame_bytes)

    def _unlink_socket(self, identity: tuple[int, int] | None) -> None:
        if identity is None:
            return
        try:
            stat_result = os.lstat(self._config.socket_path)
        except FileNotFoundError:
            return
        if (stat_result.st_dev, stat_result.st_ino) == identity:
            os.unlink(self._config.socket_path)

    def _bind_listener(self, listener: socket.socket) -> None:
        try:
            listener.bind(self._config.socket_path)
            return
        except OSError as exc:
            if exc.errno != errno.EADDRINUSE:
                raise

        try:
            socket_stat = os.lstat(self._config.socket_path)
        except FileNotFoundError:
            listener.bind(self._config.socket_path)
            return
        if not stat.S_ISSOCK(socket_stat.st_mode):
            raise RuntimeError(f'Refusing to replace non-socket path: {self._config.socket_path!r}')

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
            try:
                probe.connect(self._config.socket_path)
            except (ConnectionRefusedError, FileNotFoundError):
                pass
            else:
                raise RuntimeError(f'RPC socket is already active: {self._config.socket_path!r}')

        try:
            os.unlink(self._config.socket_path)
        except FileNotFoundError:
            pass
        listener.bind(self._config.socket_path)

    def run(
            self,
            runtime: RpcServerRuntime,
            *,
            instance_id: uuid.UUID | None = None,
    ) -> uuid.UUID:
        instance_id = instance_id or uuid.uuid7()
        responses = _RpcResponseCache(
            self._config.handler,
            max_entries=self._config.response_cache_size,
            max_frame_bytes=self._config.max_frame_bytes,
        )
        connections = _RpcConnectionThreads()

        socket_identity: tuple[int, int] | None = None
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                self._bind_listener(listener)
                os.chmod(self._config.socket_path, self._config.socket_mode)
                socket_stat = os.lstat(self._config.socket_path)
                socket_identity = (socket_stat.st_dev, socket_stat.st_ino)

                listener.listen(self._config.backlog)
                listener.setblocking(False)

                shutdown_read_sock, shutdown_write_sock = socket.socketpair()
                with shutdown_read_sock, shutdown_write_sock:
                    def wake_for_shutdown() -> None:
                        runtime.wait_shutdown()
                        try:
                            shutdown_write_sock.sendall(b'X')
                        except OSError:
                            pass

                    shutdown_thread = threading.Thread(
                        target=wake_for_shutdown,
                        name='RpcServerShutdown',
                        daemon=True,
                    )
                    shutdown_thread.start()

                    try:
                        with selectors.DefaultSelector() as selector:
                            selector.register(listener, selectors.EVENT_READ, 'listener')
                            selector.register(shutdown_read_sock, selectors.EVENT_READ, 'shutdown')

                            while not runtime.shutdown_requested:
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
                        if not runtime.shutdown_requested:
                            runtime.request_shutdown('rpc-server-exiting')
                        shutdown_thread.join()

            if not connections.wait(runtime.drain_timeout_s):
                connections.close_sockets()
                raise RpcServerDrainTimeoutError('RPC connections did not drain before timeout')

            return instance_id

        finally:
            self._unlink_socket(socket_identity)


class SimpleRpcServerRuntime(lang.Final):
    """A manually stopped runtime for using RpcServer without daemon machinery."""

    def __init__(self, *, drain_timeout_s: float | None = 30.) -> None:
        super().__init__()

        check.arg(drain_timeout_s is None or drain_timeout_s > 0.)
        self._drain_timeout_s = drain_timeout_s
        self._shutdown = threading.Event()

    @property
    def shutdown_requested(self) -> bool:
        return self._shutdown.is_set()

    @property
    def drain_timeout_s(self) -> float | None:
        return self._drain_timeout_s

    def wait_shutdown(self) -> None:
        self._shutdown.wait()

    def request_shutdown(self, message: str = 'requested') -> None:
        self._shutdown.set()

    def acquire_activity(self) -> ta.ContextManager[ta.Any] | None:
        if self._shutdown.is_set():
            return None
        return contextlib.nullcontext()
