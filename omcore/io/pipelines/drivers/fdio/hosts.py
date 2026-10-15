# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
The fdio transport host: connects through `ConnectingSocketFdioHandler`, listens through a handler of its own, and
drives each connection with the fdio driver forms, all registered with one `FdioManager`. Name resolution blocks the
manager's thread by default; `ThreadedFdioIoPipelineHostResolver` may be injected instead.
"""
import errno
import functools
import socket
import typing as ta
import weakref

from .....lite.abstract import Abstract
from .....lite.check import check
from .....sockets.endpoints import SocketEndpoint
from .....sockets.transports.sync import DEFAULT_SYNC_SOCKET_TRANSPORT
from .....sockets.transports.sync import SyncSocketListener
from .....sockets.transports.sync import SyncSocketTransport
from ....fdio.connecting import ConnectingSocketFdioHandler
from ....fdio.connecting import FdioConnectClosedError
from ....fdio.connecting import FdioConnectError
from ....fdio.connecting import FdioConnectTimeoutError
from ....fdio.handlers import FdioHandler
from ....fdio.manager import FdioManager
from ...core import IoPipeline
from ...core import IoPipelineHandlerRef
from ...hosts.base import BaseIoPipelineHost
from ...hosts.base import BaseIoPipelineHostHandle
from ...hosts.types import ClosedIoPipelineHostError
from ...hosts.types import ConnectIoPipelineHostError
from ...hosts.types import ConnectTimeoutIoPipelineHostError
from ...hosts.types import IoPipelineHostCallback
from ...hosts.types import IoPipelineHostedConnect
from ...hosts.types import IoPipelineHostedDriver
from ...hosts.types import IoPipelineHostedListener
from ...hosts.types import IoPipelineHostError
from ...hosts.types import IoPipelineHostResolver
from ...hosts.types import IoPipelineHostResolveResult
from ...hosts.types import IoPipelineHostSpecFactory
from ...hosts.types import IoPipelineHostTransportInfo
from ...hosts.types import ListenIoPipelineHostError
from ...posting.types import IoPipelinePosting
from ..types import IoPipelineDriverState
from .core import IoPipelineFdioDriver
from .duplex import IoPipelineDriverDuplexFdioHandler
from .pairs import IoPipelineDriverFdPairFdioHandlers
from .sockets import IoPipelineDriverSocketFdioHandler


FdioHostedForm = ta.Union[  # ta.TypeAlias  # noqa
    IoPipelineDriverSocketFdioHandler,
    IoPipelineDriverDuplexFdioHandler,
    IoPipelineDriverFdPairFdioHandlers,
]


##


class FdioHostedIoPipelineHandle(BaseIoPipelineHostHandle, Abstract):
    def _fdio_host(self) -> ta.Optional['FdioIoPipelineHost']:
        if (host := self._host) is None or host.closed:
            return None
        return ta.cast('FdioIoPipelineHost', host)


class FdioHostedIoPipelineDriver(FdioHostedIoPipelineHandle, IoPipelineHostedDriver):
    _closes_first = False

    def __init__(
            self,
            host: 'FdioIoPipelineHost',
            owner: ta.Optional[IoPipelineHandlerRef],
            form: FdioHostedForm,
            info: IoPipelineHostTransportInfo,
    ) -> None:
        self._form = form
        self._info = info

        super().__init__(host, owner)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._form.state.name}>'

    @property
    def form(self) -> FdioHostedForm:
        return self._form

    @property
    def info(self) -> IoPipelineHostTransportInfo:
        return self._info

    @property
    def state(self) -> IoPipelineDriverState:
        return self._form.state

    @property
    def pipeline(self) -> ta.Optional[IoPipeline]:
        return self._form.pipeline

    @property
    def posting(self) -> IoPipelinePosting:
        return self._form.posting

    @property
    def closed(self) -> bool:
        return self._form.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)

    def close(self) -> None:
        try:
            self._form.close()
        finally:
            self._unregister()


class FdioHostedIoPipelineConnect(FdioHostedIoPipelineHandle, IoPipelineHostedConnect):
    _closes_first = False

    def __init__(
            self,
            host: 'FdioIoPipelineHost',
            owner: ta.Optional[IoPipelineHandlerRef],
            endpoint: SocketEndpoint,
            spec_factory: IoPipelineHostSpecFactory,
            on_connected: IoPipelineHostCallback[IoPipelineHostedDriver],
            on_failed: IoPipelineHostCallback[IoPipelineHostError],
            timeout_s: ta.Optional[float],
    ) -> None:
        self._endpoint = endpoint
        self._spec_factory = spec_factory
        self._on_connected = on_connected
        self._on_failed = on_failed
        self._timeout_s = timeout_s

        self._connecting: ta.Optional[ConnectingSocketFdioHandler] = None
        self._done = False

        super().__init__(host, owner)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._endpoint!r}>'

    @property
    def endpoint(self) -> SocketEndpoint:
        return self._endpoint

    @property
    def closed(self) -> bool:
        return self._done

    def _finish(self) -> None:
        self._done = True
        self._connecting = None
        self._unregister()

    def close(self) -> None:
        if self._done:
            return
        connecting = self._connecting
        self._finish()
        if connecting is not None:
            connecting.cancel()  # This handle reports, not the attempt.
        self._deliver(self._on_failed, ClosedIoPipelineHostError('connect closed'))

    #

    def _on_resolved(self, result: ta.Union[IoPipelineHostResolveResult, BaseException]) -> None:
        if self._done:
            return
        if (host := self._fdio_host()) is None:
            self._finish()
            self._deliver(self._on_failed, ClosedIoPipelineHostError('host closed'))
            return

        if isinstance(result, BaseException):
            self._finish()
            if isinstance(result, ConnectIoPipelineHostError):
                exc: IoPipelineHostError = result
            else:
                exc = ConnectIoPipelineHostError(self._endpoint, [result])
            self._deliver(self._on_failed, exc)
            return

        if not result:
            self._finish()
            self._deliver(self._on_failed, ConnectIoPipelineHostError(self._endpoint, []))
            return

        self._connecting = connecting = ConnectingSocketFdioHandler(
            result,
            self._on_socket,
            self._on_connect_failed,
            timeout_s=self._timeout_s,
        )
        if not connecting.closed:
            host.manager.register(connecting)

    def _on_socket(self, sock: socket.socket) -> None:
        if self._done:
            sock.close()
            return
        if (host := self._fdio_host()) is None:
            sock.close()
            self._finish()
            self._deliver(self._on_failed, ClosedIoPipelineHostError('host closed'))
            return

        try:
            peer = sock.getpeername()
        except OSError:
            peer = None
        try:
            local = sock.getsockname()
        except OSError:
            local = None
        info = IoPipelineHostTransportInfo(endpoint=self._endpoint, local_address=local, peer_address=peer)

        try:
            spec = self._spec_factory(info)
            hosted = host._host_socket(sock, peer, spec, info, self.owner)  # noqa
        except Exception as e:  # noqa
            sock.close()
            self._finish()
            self._deliver(self._on_failed, ConnectIoPipelineHostError(self._endpoint, [e]))
            return

        self._finish()
        self._deliver(self._on_connected, hosted)

    def _on_connect_failed(self, exc: FdioConnectError) -> None:
        if self._done:
            return
        self._finish()
        host_exc: IoPipelineHostError
        if isinstance(exc, FdioConnectClosedError):
            host_exc = ClosedIoPipelineHostError('connect closed')
        elif isinstance(exc, FdioConnectTimeoutError):
            host_exc = ConnectTimeoutIoPipelineHostError(self._endpoint, exc.errors)
        else:
            host_exc = ConnectIoPipelineHostError(self._endpoint, exc.errors)
        self._deliver(self._on_failed, host_exc)


##


class FdioHostListenerFdioHandler(FdioHandler):
    """Accepts for a hosted listener. Holds the listener handle only weakly: the handle owns the socket."""

    _EXHAUSTION_ERRNOS: ta.ClassVar[ta.FrozenSet[int]] = frozenset([
        errno.EMFILE,
        errno.ENFILE,
        errno.ENOBUFS,
        errno.ENOMEM,
    ])

    def __init__(self, sock: socket.socket, listener: 'FdioHostedIoPipelineListener') -> None:
        super().__init__()

        self._sock: ta.Optional[socket.socket] = sock
        self.__listener_ref = weakref.ref(listener)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    def fd(self) -> int:
        return check.not_none(self._sock).fileno()

    @property
    def closed(self) -> bool:
        return self._sock is None

    def close(self) -> None:
        # The socket itself is the listener handle's to close.
        self._sock = None

    def readable(self) -> bool:
        return self._sock is not None

    def on_readable(self) -> None:
        if (sock := self._sock) is None:
            return
        if (listener := self.__listener_ref()) is None or listener.closed:
            self._sock = None
            return

        for _ in range(64):
            try:
                conn, addr = sock.accept()
            except BlockingIOError:
                return
            except OSError as e:
                if e.errno in (errno.ECONNABORTED, errno.EINTR):
                    continue
                # Exhaustion, or the socket going away: nothing to do but wait for the next readiness.
                return

            listener._accepted(conn, addr)  # noqa


class FdioHostedIoPipelineListener(FdioHostedIoPipelineHandle, IoPipelineHostedListener):
    _closes_first = True

    def __init__(
            self,
            host: 'FdioIoPipelineHost',
            owner: ta.Optional[IoPipelineHandlerRef],
            socket_listener: SyncSocketListener,
            spec_factory: IoPipelineHostSpecFactory,
            on_accepted: ta.Optional[IoPipelineHostCallback[IoPipelineHostedDriver]],
    ) -> None:
        self._socket_listener: ta.Optional[SyncSocketListener] = socket_listener
        self._bound_endpoint = socket_listener.bound_endpoint
        self._spec_factory = spec_factory
        self._on_accepted = on_accepted

        sock = socket_listener.socket
        sock.setblocking(False)
        self._handler = FdioHostListenerFdioHandler(sock, self)

        super().__init__(host, owner)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._bound_endpoint!r}>'

    @property
    def bound_endpoint(self) -> SocketEndpoint:
        return self._bound_endpoint

    @property
    def handler(self) -> FdioHandler:
        return self._handler

    @property
    def closed(self) -> bool:
        return self._socket_listener is None

    def close(self) -> None:
        if (socket_listener := self._socket_listener) is None:
            return
        self._socket_listener = None
        self._handler.close()
        try:
            socket_listener.close()
        finally:
            self._unregister()

    def _accepted(self, conn: socket.socket, addr: ta.Any) -> None:
        if (host := self._fdio_host()) is None or self.closed:
            conn.close()
            return

        conn.setblocking(False)
        try:
            local = conn.getsockname()
        except OSError:
            local = None
        info = IoPipelineHostTransportInfo(endpoint=self._bound_endpoint, local_address=local, peer_address=addr)

        try:
            spec = self._spec_factory(info)
            hosted = host._host_socket(conn, addr, spec, info, self.owner)  # noqa
        except Exception:  # noqa
            # The factory refused the connection, or the pipeline could not be built: the connection is closed.
            conn.close()
            return

        if (on_accepted := self._on_accepted) is not None:
            self._deliver(on_accepted, hosted)


##


class FdioIoPipelineHost(BaseIoPipelineHost):
    """
    Hosts transports on one `FdioManager`. A transport it adopts is one of: a connected `socket.socket`, which it
    drives through the socket form if `owned` and otherwise through the duplex form over the socket's descriptor, so
    that the caller's socket is restored and never closed; a duplex descriptor; or a `(read_fd, write_fd)` pair.
    """

    def __init__(
            self,
            manager: FdioManager,
            *,
            resolver: ta.Optional[IoPipelineHostResolver] = None,
            driver_config: ta.Optional[IoPipelineFdioDriver.Config] = None,
            socket_transport: SyncSocketTransport = DEFAULT_SYNC_SOCKET_TRANSPORT,
    ) -> None:
        super().__init__(resolver=resolver)

        self._manager = manager
        self._driver_config = driver_config
        self._socket_transport = socket_transport

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @property
    def manager(self) -> FdioManager:
        return self._manager

    #

    def _host_form(
            self,
            form: FdioHostedForm,
            info: IoPipelineHostTransportInfo,
            owner: ta.Optional[IoPipelineHandlerRef],
    ) -> FdioHostedIoPipelineDriver:
        check.none(form.next(read=False))
        if form.is_active:
            if isinstance(form, IoPipelineDriverFdPairFdioHandlers):
                form.register(self._manager)
            else:
                self._manager.register(form)
        return FdioHostedIoPipelineDriver(self, owner, form, info)

    def _host_socket(
            self,
            sock: socket.socket,
            addr: ta.Any,
            spec: IoPipeline.Spec,
            info: IoPipelineHostTransportInfo,
            owner: ta.Optional[IoPipelineHandlerRef],
    ) -> FdioHostedIoPipelineDriver:
        form = IoPipelineDriverSocketFdioHandler(sock, addr, self._hosted_spec(spec), self._driver_config)
        return self._host_form(form, info, owner)

    #

    def connect(
            self,
            endpoint: SocketEndpoint,
            spec_factory: IoPipelineHostSpecFactory,
            *,
            on_connected: IoPipelineHostCallback[IoPipelineHostedDriver],
            on_failed: IoPipelineHostCallback[IoPipelineHostError],
            timeout_s: ta.Optional[float] = None,
            owner: ta.Optional[IoPipelineHandlerRef] = None,
    ) -> IoPipelineHostedConnect:
        self._check_open()
        check.isinstance(endpoint, SocketEndpoint)
        if timeout_s is not None and timeout_s < 0.:
            raise ValueError(timeout_s)

        handle = FdioHostedIoPipelineConnect(
            self,
            owner,
            endpoint,
            spec_factory,
            on_connected,
            on_failed,
            timeout_s,
        )
        # Resolution may complete at once or later; either way the handle takes it from there.
        self._resolve(endpoint, functools.partial(FdioHostedIoPipelineConnect._on_resolved, handle))  # noqa
        return handle

    def listen(
            self,
            endpoint: SocketEndpoint,
            spec_factory: IoPipelineHostSpecFactory,
            *,
            on_accepted: ta.Optional[IoPipelineHostCallback[IoPipelineHostedDriver]] = None,
            backlog: int = 128,
            unix_socket_mode: int = 0o600,
            owner: ta.Optional[IoPipelineHandlerRef] = None,
    ) -> IoPipelineHostedListener:
        self._check_open()
        check.isinstance(endpoint, SocketEndpoint)

        try:
            socket_listener = self._socket_transport.listen(
                endpoint,
                backlog=backlog,
                unix_socket_mode=unix_socket_mode,
            )
        except OSError as e:
            raise ListenIoPipelineHostError(endpoint, e) from e

        listener = FdioHostedIoPipelineListener(self, owner, socket_listener, spec_factory, on_accepted)
        self._manager.register(listener.handler)
        return listener

    def adopt(
            self,
            transport: ta.Any,
            spec: IoPipeline.Spec,
            *,
            info: ta.Optional[IoPipelineHostTransportInfo] = None,
            owned: bool = False,
            owner: ta.Optional[IoPipelineHandlerRef] = None,
    ) -> IoPipelineHostedDriver:
        self._check_open()
        hosted_spec = self._hosted_spec(spec)

        form: FdioHostedForm
        if isinstance(transport, socket.socket):
            try:
                peer = transport.getpeername()
            except OSError:
                peer = None
            try:
                local = transport.getsockname()
            except OSError:
                local = None
            if info is None:
                info = IoPipelineHostTransportInfo(local_address=local, peer_address=peer)
            if owned:
                form = IoPipelineDriverSocketFdioHandler(transport, peer, hosted_spec, self._driver_config)
            else:
                form = IoPipelineDriverDuplexFdioHandler(transport.fileno(), hosted_spec, self._driver_config)

        elif isinstance(transport, int):
            if info is None:
                info = IoPipelineHostTransportInfo()
            form = IoPipelineDriverDuplexFdioHandler(transport, hosted_spec, self._driver_config, owned=owned)

        elif isinstance(transport, tuple) and len(transport) == 2:
            read_fd, write_fd = transport
            if info is None:
                info = IoPipelineHostTransportInfo()
            form = IoPipelineDriverFdPairFdioHandlers(
                check.isinstance(read_fd, int),
                check.isinstance(write_fd, int),
                hosted_spec,
                self._driver_config,
                owned=owned,
            )

        else:
            raise TypeError(transport)

        return self._host_form(form, info, owner)
