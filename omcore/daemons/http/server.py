import contextlib
import selectors
import socket
import threading
import time
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ...http.pipelines.responses import FullIoPipelineHttpResponse
from ...io.pipelines.drivers.sync import SyncSocketIoPipelineDriver
from ...logs import all as logs
from ...sockets.io import close_socket_immediately
from .dispatch import HttpHandler
from .dispatch import HttpHealthConfig
from .dispatch import HttpRequestDispatcher
from .pipelines import HttpPipelineFailure
from .pipelines import HttpServerRequest
from .pipelines import HttpServerSendResponse
from .pipelines import pipeline_http_server_spec


log = logs.get_module_logger(globals())


##


class HttpServerRuntime(ta.Protocol):
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


class PipelineHttpServerDrainTimeoutError(TimeoutError):
    pass


@dc.dataclass(frozen=True, kw_only=True)
class PipelineHttpServerConfig:
    host: str
    port: int
    handler: HttpHandler

    health: HttpHealthConfig | None = HttpHealthConfig()
    connection_timeout_s: float | None = 30.
    max_request_body_bytes: int = 64 * 1024
    backlog: int = 128

    def __post_init__(self) -> None:
        check.non_empty_str(self.host)
        check.arg(0 <= self.port <= 65_535)
        check.callable(self.handler)
        check.arg(self.connection_timeout_s is None or self.connection_timeout_s > 0.)
        check.arg(self.max_request_body_bytes >= 0)
        check.arg(self.backlog > 0)


##


class _HttpConnectionThreads:
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
            except (EOFError, OSError):
                pass
            except BaseException as exc:  # noqa
                log.exception(exc)  # noqa: TRY401
            finally:
                close_socket_immediately(conn)
                with self._condition:
                    self._sockets.discard(conn)
                    self._threads.discard(threading.current_thread())
                    self._condition.notify_all()

        thread = threading.Thread(
            target=run,
            name='PipelineHttpServerConnection',
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


class PipelineHttpServer(lang.Final):
    """A concurrent synchronous TCP host for one-request HTTP pipelines."""

    def __init__(self, config: PipelineHttpServerConfig) -> None:
        super().__init__()

        self._config = config
        self._bound_address: tuple[str, int] | None = None
        self._started = threading.Event()

    @property
    def config(self) -> PipelineHttpServerConfig:
        return self._config

    @property
    def bound_address(self) -> tuple[str, int]:
        return check.not_none(self._bound_address)

    def wait_started(self, timeout_s: float | None = None) -> bool:
        return self._started.wait(timeout_s)

    @staticmethod
    def _send_response(
            driver: SyncSocketIoPipelineDriver,
            response: FullIoPipelineHttpResponse,
    ) -> None:
        driver.enqueue(HttpServerSendResponse(response=response))
        while driver.is_running:
            event = driver.next()
            if isinstance(event, HttpPipelineFailure):
                raise event.exc
            if event is not None:
                raise RuntimeError(f'Unexpected HTTP server event: {event!r}')

    def _handle_connection(
            self,
            conn: socket.socket,
            *,
            runtime: HttpServerRuntime,
            dispatcher: HttpRequestDispatcher,
    ) -> None:
        conn.settimeout(self._config.connection_timeout_s)
        with SyncSocketIoPipelineDriver(
                pipeline_http_server_spec(
                    max_request_body_bytes=self._config.max_request_body_bytes,
                ),
                conn,
        ) as driver:
            while True:
                event = driver.next()
                if isinstance(event, HttpPipelineFailure):
                    raise event.exc
                if isinstance(event, HttpServerRequest):
                    request = event.request
                    break
                if event is not None:
                    raise RuntimeError(f'Unexpected HTTP server event: {event!r}')
                if not driver.is_running:
                    return

            if dispatcher.is_health_request(request):
                self._send_response(
                    driver,
                    dispatcher.health_response(
                        request,
                        healthy=not runtime.shutdown_requested,
                    ),
                )
                return

            if (activity := runtime.acquire_activity()) is None:
                self._send_response(driver, FullIoPipelineHttpResponse.simple(
                    status=503,
                    body=b'shutting down',
                ))
                return

            with activity:
                self._send_response(driver, dispatcher.dispatch(request))

    def run(self, runtime: HttpServerRuntime) -> tuple[str, int]:
        dispatcher = HttpRequestDispatcher(
            self._config.handler,
            health=self._config.health,
        )
        connections = _HttpConnectionThreads()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((self._config.host, self._config.port))
            listener.listen(self._config.backlog)
            listener.setblocking(False)

            raw_address = listener.getsockname()
            self._bound_address = (
                check.isinstance(raw_address[0], str),
                check.isinstance(raw_address[1], int),
            )
            self._started.set()

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
                    name='PipelineHttpServerShutdown',
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
                                        runtime=runtime,
                                        dispatcher=dispatcher,
                                    ),
                                )
                finally:
                    if not runtime.shutdown_requested:
                        runtime.request_shutdown('pipeline-http-server-exiting')
                    shutdown_thread.join()

        if not connections.wait(runtime.drain_timeout_s):
            connections.close_sockets()
            raise PipelineHttpServerDrainTimeoutError('HTTP connections did not drain before timeout')

        return self.bound_address


##


class SimpleHttpServerRuntime(lang.Final):
    """A manually stopped runtime for standalone PipelineHttpServer use."""

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
