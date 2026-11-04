"""
The synchronous connection: the JSON-RPC connection (`base.py`) on an `omcore.rpc` sync runtime over a
SyncIoPipelineDriver (socket or file descriptor pair), driven from this thread with `sync_await`.

There is no pump task: the calling thread pumps the driver while it waits for what it asked for. Inbound requests are
dispatched inline as they arrive, so a handler may itself call back into the peer. Dispatchers and notification
handlers here are sync, and are handed this connection. One thread at a time may use the connection; a nested use from
a handler on that same thread is fine.
"""
import errno
import os
import socket
import subprocess
import sys
import typing as ta

from .... import check
from .... import lang
from ....io.pipelines import all as ipl
from ....rpc.connection import BaseSyncRpcConnection
from ....rpc.syncs import SyncRpcRuntime
from ..conns import JsonrpcConnection
from ..dispatch import AsyncJsonrpcDispatcher
from ..dispatch import JsonrpcDispatcher
from ..ids import JsonrpcIdCreatorLike
from ..types import NotSpecified
from ..types import Params
from ..types import Request
from ..types import Response
from .base import BaseJsonrpcConnection
from .base import TimeoutArg
from .configs import JsonrpcPipelineConfig
from .specs import build_jsonrpc_pipeline_spec


type SyncJsonrpcNotificationHandler = ta.Callable[
    [SyncJsonrpcConnection, Request],
    None,
]


##


class _SyncJsonrpcDispatcherAdapter(AsyncJsonrpcDispatcher):
    """Runs a sync dispatcher inline, handing it the sync connection so its handlers can call back synchronously."""

    def __init__(self, dispatcher: JsonrpcDispatcher, connection: SyncJsonrpcConnection) -> None:
        super().__init__()

        self._dispatcher = dispatcher
        self._connection = connection

    @property
    def dispatcher(self) -> JsonrpcDispatcher:
        return self._dispatcher

    async def dispatch(self, connection: ta.Any, request: Request) -> ta.Any:
        return self._dispatcher.dispatch(self._connection, request)


class SyncJsonrpcConnection(BaseSyncRpcConnection, JsonrpcConnection):
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

        self._driver = driver

        jc = BaseJsonrpcConnection(
            SyncRpcRuntime(driver, closers=closers),
            config,
            id_creator=id_creator,
            include_error_details=include_error_details,
        )

        super().__init__(jc)

        self._jc = jc
        self.set_dispatcher(dispatcher)
        self.set_notification_handler(notification_handler)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._driver!r}>'

    @property
    def connection(self) -> BaseJsonrpcConnection:
        return self._jc

    @property
    def driver(self) -> ipl.SyncDriver:
        return self._driver

    @property
    def config(self) -> JsonrpcPipelineConfig:
        return self._jc.config

    @property
    def dispatcher(self) -> JsonrpcDispatcher | None:
        if isinstance(d := self._jc.dispatcher, _SyncJsonrpcDispatcherAdapter):
            return d.dispatcher
        return None

    def set_dispatcher(self, dispatcher: JsonrpcDispatcher | None) -> None:
        """May be called at any time; requests already being handled keep the dispatcher they started with."""

        self._jc.set_dispatcher(_SyncJsonrpcDispatcherAdapter(dispatcher, self) if dispatcher is not None else None)

    def set_notification_handler(self, handler: SyncJsonrpcNotificationHandler | None) -> None:
        if handler is None:
            self._jc.set_notification_handler(None)
            return

        async def handle(connection: ta.Any, note: Request) -> None:
            handler(self, note)

        self._jc.set_notification_handler(handle)

    ##
    # lifecycle

    def run(self, aw: ta.Awaitable[ta.Any]) -> ta.Any:
        # Starting is optional for a sync connection: the first operation does it.
        if not self._jc.is_started and not self._jc.is_closed:
            super().run(self._jc.start())
        return super().run(aw)

    def start(self) -> None:
        """Bring the connection up without touching the transport. Optional: the first operation does this too."""

        if not self._jc.is_started:
            super().run(self._jc.start())

    def close(  # type: ignore[override]
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

        self.run(self._jc.close(graceful=graceful, timeout_s=timeout_s))

    def serve(self) -> None:
        """
        Pump the connection until it closes, dispatching whatever the peer sends: the server side's main loop.

        Raises nothing for a peer which simply goes away; the reason, if any, is left in `close_exception`.
        """

        self.run(self._jc.serve())

    ##
    # sending

    def send_request(
            self,
            req: Request,
            *,
            timeout_s: TimeoutArg = NotSpecified,
    ) -> Response:
        """Send a prepared request (with id) and pump until its raw response arrives."""

        return self.run(self._jc.send_request(req, timeout_s=timeout_s))

    def request(
            self,
            method: str,
            params: Params | None = None,
            *,
            timeout_s: TimeoutArg = NotSpecified,
    ) -> ta.Any:
        return self.run(self._jc.request(method, params, timeout_s=timeout_s))

    def notify(self, method: str, params: Params | None = None) -> None:
        self.run(self._jc.notify(method, params))

    def send_batch(
            self,
            reqs: ta.Sequence[Request],
            *,
            timeout_s: TimeoutArg = NotSpecified,
    ) -> list[Response | None]:
        """
        Send prepared requests and notifications as one batch, returning responses in order (None for notifications).
        """

        return self.run(self._jc.send_batch(reqs, timeout_s=timeout_s))


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
