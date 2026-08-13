import errno
import os
import socket
import stat
import time
import typing as ta
import uuid

from ... import check
from ... import lang
from ...io.fdio.handlers import SocketFdioHandler
from ...io.fdio.manager import FdioManager
from ...io.fdio.pollers import SelectFdioPoller
from ...io.pipelines.drivers.fdio import IoPipelineDriverSocketFdioHandler
from ...logs import all as logs
from ...sockets.addresses import SocketAddress
from .dispatch import RpcRequestDispatcher
from .pipelines import RpcPipelineFailure
from .pipelines import RpcServerDispatch
from .pipelines import RpcServerSendResponse
from .pipelines import RpcWireError
from .pipelines import RpcWireResponse
from .pipelines import rpc_server_pipeline_spec
from .protocol import RPC_PROTOCOL_VERSION
from .protocol import RpcProtocolError
from .registry import RpcResponseRegistry
from .server import RpcServerConfig
from .server import RpcServerDrainTimeoutError
from .server import RpcServerRuntime


log = logs.get_module_logger(globals())


##


class _FdioRpcConnection(IoPipelineDriverSocketFdioHandler):
    def __init__(
            self,
            sock: socket.socket,
            addr: SocketAddress,
            *,
            config: RpcServerConfig,
            instance_id: uuid.UUID,
            runtime: RpcServerRuntime,
            dispatcher: RpcRequestDispatcher,
    ) -> None:
        super().__init__(
            sock,
            addr,
            rpc_server_pipeline_spec(
                protocol_version=RPC_PROTOCOL_VERSION,
                instance_id=instance_id,
                max_frame_bytes=config.max_frame_bytes,
            ),
        )

        self._connection_timeout_s = config.connection_timeout_s
        self._runtime = runtime
        self._dispatcher = dispatcher
        self._activity: ta.ContextManager[ta.Any] | None = None
        self._connection_deadline: float | None = None
        self._reset_connection_deadline()
        self.next(read=False)

    def _reset_connection_deadline(self) -> None:
        if self._connection_timeout_s is not None:
            self._connection_deadline = time.monotonic() + self._connection_timeout_s

    def _release_activity(self) -> None:
        if (activity := self._activity) is None:
            return
        self._activity = None
        activity.__exit__(None, None, None)

    def close(self) -> None:
        try:
            super().close()
        finally:
            self._release_activity()

    def _handle_event(self, event: ta.Any) -> None:
        if isinstance(event, RpcPipelineFailure):
            raise event.exc
        if not isinstance(event, RpcServerDispatch):
            raise RpcProtocolError(f'Unexpected fdio RPC server event: {event!r}')

        request = event.request
        if (activity := self._runtime.acquire_activity()) is None:
            response: RpcWireResponse = RpcWireError(
                client_id=request.client_id,
                request_id=request.request_id,
                code='unavailable',
                remote_type='omcore.daemons.rpc.RpcServerActivityRejectedError',
                message='RPC server is shutting down',
            )
        else:
            activity.__enter__()
            self._activity = activity
            response = self._dispatcher.dispatch(request)

        self.enqueue(RpcServerSendResponse(response=response))

    def _drive(self, *, read: bool) -> None:
        try:
            first = True
            while self.is_active:
                event = self.next(
                    read=read if first else False,
                    raise_on_stall=False,
                )
                first = False
                if event is None:
                    break
                self._handle_event(event)
        finally:
            if self.closed:
                self._release_activity()

    def on_readable(self) -> None:
        self._reset_connection_deadline()
        try:
            self._drive(read=True)
        except (EOFError, OSError, RpcProtocolError):
            self.close()
        except BaseException:  # noqa
            log.exception('Unhandled fdio RPC connection error')
            self.close()

    def on_writable(self) -> None:
        try:
            super().on_writable()
            if self.closed:
                self._release_activity()
            elif self.is_active:
                self._drive(read=False)
        except (EOFError, OSError, RpcProtocolError):
            self.close()
        except BaseException:  # noqa
            log.exception('Unhandled fdio RPC connection error')
            self.close()

    def next_deadline(self) -> float | None:
        deadlines = [
            deadline
            for deadline in (
                super().next_deadline(),
                self._connection_deadline,
            )
            if deadline is not None
        ]
        return min(deadlines) if deadlines else None

    def on_timeout(self) -> None:
        if (
                self._connection_deadline is not None and
                self._connection_deadline <= time.monotonic()
        ):
            self.close()
        else:
            super().on_timeout()


class _FdioRpcListener(SocketFdioHandler):
    def __init__(
            self,
            sock: socket.socket,
            on_connect: ta.Callable[[socket.socket, SocketAddress], None],
    ) -> None:
        sock.setblocking(False)
        super().__init__(sock, sock.getsockname())

        self._on_connect = on_connect

    def readable(self) -> bool:
        return True

    def on_readable(self) -> None:
        while True:
            try:
                conn, addr = check.not_none(self._sock).accept()
            except BlockingIOError:
                return
            conn.setblocking(False)
            self._on_connect(conn, addr)


##


class FdioRpcServer(lang.Final):
    """A single-threaded fdio host for the runtime-neutral RPC pipeline."""

    def __init__(self, config: RpcServerConfig) -> None:
        super().__init__()

        self._config = config

    @property
    def config(self) -> RpcServerConfig:
        return self._config

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
        dispatcher = RpcRequestDispatcher(
            self._config.handler,
            RpcResponseRegistry(max_entries=self._config.response_cache_size),
            max_frame_bytes=self._config.max_frame_bytes,
        )
        manager = FdioManager(SelectFdioPoller())
        connections: set[_FdioRpcConnection] = set()

        socket_identity: tuple[int, int] | None = None
        try:
            listener_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._bind_listener(listener_sock)
            os.chmod(self._config.socket_path, self._config.socket_mode)
            socket_stat = os.lstat(self._config.socket_path)
            socket_identity = (socket_stat.st_dev, socket_stat.st_ino)
            listener_sock.listen(self._config.backlog)

            def on_connect(conn: socket.socket, addr: SocketAddress) -> None:
                connection = _FdioRpcConnection(
                    conn,
                    addr,
                    config=self._config,
                    instance_id=instance_id,
                    runtime=runtime,
                    dispatcher=dispatcher,
                )
                connections.add(connection)
                manager.register(connection)

            listener = _FdioRpcListener(listener_sock, on_connect)
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
            self._unlink_socket(socket_identity)
