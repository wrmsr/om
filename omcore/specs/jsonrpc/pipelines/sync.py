"""
The synchronous connection: a session handler taped to a SyncIoPipelineDriver (socket or file descriptor pair).

There is no pump task: the calling thread pumps the driver while it waits for what it asked for. Inbound requests are
dispatched inline between driver steps, so a handler may itself call back into the peer. One thread at a time may use
the connection; a nested use from a handler on that same thread is fine.
"""
import errno
import os
import socket
import subprocess
import sys
import threading
import typing as ta

from .... import check
from .... import lang
from ....io.pipelines import all as ipl
from ....logs import all as logs
from ..dispatch import JsonrpcDispatcher
from ..errors import JsonrpcConnectionClosedError
from ..errors import JsonrpcMethodError
from ..errors import KnownErrors
from ..ids import JsonrpcIdCreatorLike
from ..types import Batch
from ..types import NotSpecified
from ..types import Params
from ..types import Request
from ..types import Response
from .base import BaseSyncJsonrpcConnection
from .base import JsonrpcResponseWaiter
from .configs import JsonrpcPipelineConfig
from .messages import JsonrpcPipelineMessages as Jpm
from .specs import build_jsonrpc_pipeline_spec


log = logs.get_module_logger(globals())


type SyncJsonrpcNotificationHandler = ta.Callable[
    [SyncJsonrpcConnection, Request],
    None,
]


##


class _SyncWaiter(JsonrpcResponseWaiter):
    def __init__(self) -> None:
        super().__init__()

        self.response: Response | None = None
        self.exc: BaseException | None = None

    @property
    def done(self) -> bool:
        return self.response is not None or self.exc is not None

    def set_response(self, response: Response) -> None:
        if not self.done:
            self.response = response

    def set_exception(self, exc: BaseException) -> None:
        if not self.done:
            self.exc = exc

    def result(self) -> Response:
        if (exc := self.exc) is not None:
            raise exc
        return check.not_none(self.response)


##


class SyncJsonrpcConnection(BaseSyncJsonrpcConnection):
    def __init__(
            self,
            driver: ipl.SyncDriver,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            dispatcher: JsonrpcDispatcher | None = None,
            notification_handler: SyncJsonrpcNotificationHandler | None = None,
            id_creator: JsonrpcIdCreatorLike | None = None,
            include_error_details: bool = False,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
    ) -> None:
        """
        `closers` run once the driver has been shut down, in order: the sync drivers leave their caller-owned transport
        open, so whoever owns it registers its closing here (which is also what lets the peer see EOF).
        """

        super().__init__(
            config,
            id_creator=id_creator,
            include_error_details=include_error_details,
        )

        self._driver = driver
        self._dispatcher = dispatcher
        self._notification_handler = notification_handler
        self._closers = list(closers)

        self._owner_thread: int | None = None
        self._sent: set[int] = set()
        self._driver_done = False

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._driver!r}>'

    @property
    def driver(self) -> ipl.SyncDriver:
        return self._driver

    ##
    # lifecycle

    def start(self) -> None:
        """Bring the pipeline up without touching the transport. Optional: the first operation does this too."""

        with self._owned():
            self._step(read=False)

    def __enter__(self) -> ta.Self:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close(graceful=exc_type is None)

    def _default_close_timeout_s(self, graceful: bool) -> float | None:
        c = self._config
        parts = [t for t in ((c.close_drain_timeout_s if graceful else None), c.write_timeout_s) if t is not None]
        return sum(parts) if parts else None

    def close(
            self,
            *,
            graceful: bool = True,
            timeout_s: float | None | type[NotSpecified] = NotSpecified,
    ) -> None:
        """
        Close the connection, gracefully by default (see Close), pumping until closure completes.

        The wait is bounded like the asyncio connection's: by `timeout_s` if given, else by the sum of the configured
        drain and write timeouts, after which the transport is abandoned. Never raises for a connection which failed
        earlier.
        """

        if timeout_s is NotSpecified:
            timeout_s = self._default_close_timeout_s(graceful)

        with self._owned():
            if self._driver_done:
                self._mark_closed(None)
                return

            if not self._closed:
                if not self._enqueue(Jpm.Close(graceful=graceful)):
                    self._mark_closed(None)

            prev_wait = self._driver.wait_timeout_s
            self._driver.wait_timeout_s = ta.cast('float | None', timeout_s)
            try:
                self._pump_until(lambda: self._driver_done)
            except (TimeoutError, OSError) as e:
                log.warning('Close did not complete cleanly, abandoning transport: %r', e)
            finally:
                self._driver.wait_timeout_s = prev_wait
                self._finish_driver()

    def _finish_driver(self) -> None:
        if self._driver_done:
            return
        self._driver_done = True
        try:
            self._driver.close()
        except Exception:  # noqa
            log.debug('Error closing driver', exc_info=True)
        for c in self._closers:
            try:
                c()
            except Exception:  # noqa
                log.debug('Error in closer', exc_info=True)
        self._mark_closed(self._close_exc)

    def serve(self) -> None:
        """
        Pump the connection until it closes, dispatching whatever the peer sends: the server side's main loop.

        Raises nothing for a peer which simply goes away; the reason, if any, is left in `close_exception`.
        """

        with self._owned():
            try:
                self._pump_until(lambda: self._driver_done)
            except JsonrpcConnectionClosedError:
                pass

    ##
    # pumping

    class _Owned:
        def __init__(self, conn: SyncJsonrpcConnection) -> None:
            self._conn = conn
            self._acquired = False

        def __enter__(self) -> None:
            conn = self._conn
            me = threading.get_ident()
            if conn._owner_thread is None:  # noqa
                conn._owner_thread = me  # noqa
                self._acquired = True
            elif conn._owner_thread != me:  # noqa
                raise RuntimeError('SyncJsonrpcConnection is in use by another thread')

        def __exit__(self, exc_type, exc_val, exc_tb) -> None:
            if self._acquired:
                self._conn._owner_thread = None  # noqa

    def _owned(self) -> _Owned:
        """Guards against use from two threads at once while permitting nested use from handlers."""

        return self._Owned(self)

    def _enqueue(self, *cmds: Jpm.Command) -> bool:
        if self._closed or self._driver_done:
            return False
        try:
            self._driver.enqueue(*cmds)
        except Exception:  # noqa
            log.debug('Driver refused commands', exc_info=True)
            return False
        return True

    def _step(self, *, read: bool = True) -> None:
        """Advance the driver one step, routing whatever it returns."""

        try:
            out = self._driver.next(read=read, raise_on_stall=False)
        except TimeoutError:
            raise
        except Exception as e:  # noqa
            # Transport failure: the driver has failed itself and destroyed the pipeline.
            self._mark_closed(e)
            self._finish_driver()
            raise self._closed_error() from e

        if out is None:
            if not self._driver.is_running:
                self._finish_driver()
            return

        if isinstance(out, BaseException):
            self._mark_closed(out)
            self._finish_driver()
            return

        self._handle_event(out)

    def _pump_until(self, pred: ta.Callable[[], bool]) -> None:
        while not pred():
            if self._driver_done:
                return
            self._step()

    ##
    # sending

    def _send(self, cmd: Jpm.Command) -> None:
        """Hand a send command to the driver and pump until the session reports it Sent, for backpressure."""

        if self._closed:
            raise self._closed_error()

        if not self._enqueue(cmd):
            raise self._closed_error()

        key = id(cmd)
        try:
            self._pump_until(lambda: key in self._sent or self._closed)
        finally:
            self._sent.discard(key)

    def _on_sent(self, cmd: Jpm.Command) -> None:
        self._sent.add(id(cmd))

    def send_request(
            self,
            req: Request,
            *,
            timeout_s: float | None | type[NotSpecified] = NotSpecified,
    ) -> Response:
        """Send a prepared request (with id) and pump until its raw response arrives."""

        check.arg(not req.is_notification, 'request must have an id')

        with self._owned():
            if self._closed:
                raise self._closed_error()

            waiter = _SyncWaiter()
            self._add_waiter(req, waiter)
            try:
                self._send(Jpm.SendRequest(req, timeout_s=timeout_s))
                self._pump_until(lambda: waiter.done)
                if not waiter.done:
                    raise self._closed_error()
                return waiter.result()

            finally:
                if self._pop_waiter(req.id_value()) is not None and not waiter.done:
                    self._enqueue(Jpm.CancelRequest(req.id_value()))

    def request(
            self,
            method: str,
            params: Params | None = None,
            *,
            timeout_s: float | None | type[NotSpecified] = NotSpecified,
    ) -> ta.Any:
        return self._result_of(self.send_request(self._new_request(method, params), timeout_s=timeout_s))

    def notify(self, method: str, params: Params | None = None) -> None:
        with self._owned():
            self._send(Jpm.SendNotification(self._new_notification(method, params)))

    def send_batch(
            self,
            reqs: ta.Sequence[Request],
            *,
            timeout_s: float | None | type[NotSpecified] = NotSpecified,
    ) -> list[Response | None]:
        """
        Send prepared requests and notifications as one batch, returning responses in order (None for notifications).
        """  # noqa

        with self._owned():
            if self._closed:
                raise self._closed_error()

            waiters: list[_SyncWaiter | None] = []
            for req in reqs:
                if req.is_notification:
                    waiters.append(None)
                    continue
                nw = _SyncWaiter()
                self._add_waiter(req, nw)
                waiters.append(nw)

            try:
                self._send(Jpm.SendBatch(Batch(reqs), timeout_s=timeout_s))
                self._pump_until(lambda: all(ww is None or ww.done for ww in waiters))
                out: list[Response | None] = []
                for ow in waiters:
                    if ow is None:
                        out.append(None)
                    elif not ow.done:
                        raise self._closed_error()
                    else:
                        out.append(ow.result())
                return out

            finally:
                for req, fw in zip(reqs, waiters):
                    if fw is not None and self._pop_waiter(req.id_value()) is not None and not fw.done:
                        self._enqueue(Jpm.CancelRequest(req.id_value()))

    ##
    # receiving

    def _on_request_received(self, req: Request) -> None:
        response: Response
        try:
            if (d := self._dispatcher) is None:
                raise JsonrpcMethodError(KnownErrors.METHOD_NOT_FOUND, data=req.method)

            result = d.dispatch(self, req)
            response = Response(req.id_value(), result=result)

        except JsonrpcMethodError as e:
            response = Response(req.id_value(), error=e.error)

        except Exception as e:  # noqa
            log.exception('Unhandled error handling request %r', req.method)
            response = self._error_response(req, e)

        self._enqueue(Jpm.SendResponse(response))

    def _on_request_handling_aborted(self, req: Request, exc: BaseException) -> None:
        # Handlers run to completion inline, so there is nothing to cancel.
        pass

    def _on_notification_received(self, note: Request) -> None:
        if (h := self._notification_handler) is None:
            log.debug('Dropping notification with no handler: %r', note.method)
            return

        try:
            h(self, note)
        except Exception:  # noqa
            log.exception('Unhandled error handling notification %r', note.method)


##
# construction helpers


def _try_set_nodelay(sock: socket.socket) -> None:
    try:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError as e:
        if e.errno != errno.ENOPROTOOPT:
            raise


class SyncJsonrpcConnections(lang.Namespace):
    """
    Factories taping the connection onto sockets, file descriptor pairs, a subprocess's stdio, or our own.

    Sockets are left with no timeout: every timeout is enforced by the session, and a socket timeout would surface as a
    spurious TimeoutError from the pump.
    """

    @staticmethod
    def of_driver(
            driver: ipl.SyncDriver,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            **kwargs: ta.Any,
    ) -> SyncJsonrpcConnection:
        return SyncJsonrpcConnection(driver, config, **kwargs)

    @classmethod
    def of_socket(
            cls,
            sock: socket.socket,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            close_socket: bool = True,
            driver_config: ipl.SyncDriver.Config | None = None,
            ssl_kwargs: ta.Mapping[str, ta.Any] | None = None,
            spec_kwargs: ta.Mapping[str, ta.Any] | None = None,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
            **kwargs: ta.Any,
    ) -> SyncJsonrpcConnection:
        """The socket is closed when the connection closes unless `close_socket` is false."""

        spec = build_jsonrpc_pipeline_spec(
            config,
            ssl_kwargs=ssl_kwargs,
            **(spec_kwargs or {}),
        )
        return cls.of_driver(
            ipl.SocketSyncDriver(spec, sock, driver_config),
            config,
            closers=[*([sock.close] if close_socket else []), *closers],
            **kwargs,
        )

    @classmethod
    def of_fds(
            cls,
            read_fd: int,
            write_fd: int,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            close_fds: bool = False,
            driver_config: ipl.SyncDriver.Config | None = None,
            spec_kwargs: ta.Mapping[str, ta.Any] | None = None,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
            **kwargs: ta.Any,
    ) -> SyncJsonrpcConnection:
        """The descriptors are left open when the connection closes unless `close_fds` is true."""

        spec = build_jsonrpc_pipeline_spec(
            config,
            **(spec_kwargs or {}),
        )

        def close_fds_() -> None:
            for fd in {read_fd, write_fd}:
                try:
                    os.close(fd)
                except OSError:
                    pass

        return cls.of_driver(
            ipl.FdSyncDriver(spec, read_fd, write_fd, driver_config),
            config,
            closers=[*([close_fds_] if close_fds else []), *closers],
            **kwargs,
        )

    @classmethod
    def connect_tcp(
            cls,
            host: str,
            port: int,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            connect_timeout_s: float | None = 10.,
            ssl: bool | ta.Mapping[str, ta.Any] = False,
            **kwargs: ta.Any,
    ) -> SyncJsonrpcConnection:
        sock = socket.create_connection((host, port), timeout=connect_timeout_s)
        try:
            sock.settimeout(None)
            _try_set_nodelay(sock)

            ssl_kwargs: ta.Mapping[str, ta.Any] | None
            if ssl is True:
                ssl_kwargs = dict(server_side=False, server_hostname=host)
            elif ssl is False:
                ssl_kwargs = None
            else:
                ssl_kwargs = ssl

            return cls.of_socket(sock, config, ssl_kwargs=ssl_kwargs, **kwargs)

        except BaseException:
            sock.close()
            raise

    @classmethod
    def connect_unix(
            cls,
            path: str,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            connect_timeout_s: float | None = 10.,
            **kwargs: ta.Any,
    ) -> SyncJsonrpcConnection:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.settimeout(connect_timeout_s)
            sock.connect(path)
            sock.settimeout(None)
            return cls.of_socket(sock, config, **kwargs)

        except BaseException:
            sock.close()
            raise

    @classmethod
    def of_subprocess(
            cls,
            proc: subprocess.Popen,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            closers: ta.Sequence[ta.Callable[[], None]] = (),
            **kwargs: ta.Any,
    ) -> SyncJsonrpcConnection:
        """
        Talk to a child process over its stdio. The process must have been created with piped stdin and stdout. Its
        stdin is closed when the connection closes so it sees EOF.
        """

        stdin = check.not_none(proc.stdin)
        return cls.of_fds(
            check.not_none(proc.stdout).fileno(),
            stdin.fileno(),
            config,
            closers=[stdin.close, *closers],
            **kwargs,
        )

    @classmethod
    def of_stdio(
            cls,
            config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
            *,
            stdin: ta.IO | None = None,
            stdout: ta.IO | None = None,
            **kwargs: ta.Any,
    ) -> SyncJsonrpcConnection:
        """Serve or talk over this process's own stdio."""

        return cls.of_fds(
            (stdin if stdin is not None else sys.stdin).fileno(),
            (stdout if stdout is not None else sys.stdout).fileno(),
            config,
            **kwargs,
        )
