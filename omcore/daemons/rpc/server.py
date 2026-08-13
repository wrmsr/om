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
from ...io.pipelines.drivers.sync import SyncSocketIoPipelineDriver
from ...logs import all as logs
from ...sockets.io import close_socket_immediately
from .dispatch import RpcRequestDispatcher
from .pipelines import RpcPipelineFailure
from .pipelines import RpcServerDispatch
from .pipelines import RpcServerSendResponse
from .pipelines import RpcWireError
from .pipelines import RpcWireResponse
from .pipelines import rpc_server_pipeline_spec
from .protocol import RPC_DEFAULT_MAX_FRAME_BYTES
from .protocol import RPC_PROTOCOL_VERSION
from .protocol import RpcHandler
from .protocol import RpcProtocolError
from .registry import RpcResponseRegistry


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

    def _handle_connection(
            self,
            conn: socket.socket,
            *,
            instance_id: uuid.UUID,
            runtime: RpcServerRuntime,
            dispatcher: RpcRequestDispatcher,
    ) -> None:
        conn.settimeout(self._config.connection_timeout_s)
        with SyncSocketIoPipelineDriver(
                rpc_server_pipeline_spec(
                    protocol_version=RPC_PROTOCOL_VERSION,
                    instance_id=instance_id,
                    max_frame_bytes=self._config.max_frame_bytes,
                ),
                conn,
        ) as driver:
            while True:
                event = driver.next()
                if isinstance(event, RpcPipelineFailure):
                    raise event.exc
                if isinstance(event, RpcServerDispatch):
                    request = event.request
                    break
                if event is not None:
                    raise RpcProtocolError(f'Unexpected RPC server event: {event!r}')
                if not driver.is_running:
                    return

            if (activity := runtime.acquire_activity()) is None:
                response: RpcWireResponse = RpcWireError(
                    client_id=request.client_id,
                    request_id=request.request_id,
                    code='unavailable',
                    remote_type='omcore.daemons.rpc.RpcServerActivityRejectedError',
                    message='RPC server is shutting down',
                )
                driver.enqueue(RpcServerSendResponse(response=response))
                while driver.is_running:
                    if (event := driver.next()) is not None:
                        if isinstance(event, RpcPipelineFailure):
                            raise event.exc
                        raise RpcProtocolError(f'Unexpected RPC server event: {event!r}')
                return

            with activity:
                response = dispatcher.dispatch(request)
                driver.enqueue(RpcServerSendResponse(response=response))
                while driver.is_running:
                    if (event := driver.next()) is not None:
                        if isinstance(event, RpcPipelineFailure):
                            raise event.exc
                        raise RpcProtocolError(f'Unexpected RPC server event: {event!r}')

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
        responses = RpcResponseRegistry(
            max_entries=self._config.response_cache_size,
        )
        dispatcher = RpcRequestDispatcher(
            self._config.handler,
            responses,
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
                                            dispatcher=dispatcher,
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
