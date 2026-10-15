# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
The asyncio transport host: each hosted pipeline is driven by `PollAsyncioStreamIoPipelineDriver` in one task of its
own, which for a connection also performs the connect, so that nothing finer-grained than a pipeline is a task. Name
resolution is asyncio's by default - the loop resolves off its thread - and a sync `IoPipelineHostResolver` may be
injected instead. Listening binds through the sync socket transport and accepts from a reader callback on the loop.
"""
import abc
import asyncio
import fcntl
import os
import socket
import typing as ta

from .....lite.abstract import Abstract
from .....lite.check import check
from .....sockets.endpoints import SocketEndpoint
from .....sockets.endpoints import TcpSocketEndpoint
from .....sockets.transports.sync import DEFAULT_SYNC_SOCKET_TRANSPORT
from .....sockets.transports.sync import SyncSocketListener
from .....sockets.transports.sync import SyncSocketTransport
from ...core import IoPipeline
from ...core import IoPipelineHandlerRef
from ...errors import StateIoPipelineError
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
from ...hosts.types import ResolveIoPipelineHostError
from ...posting.types import IoPipelinePosting
from ..types import IoPipelineDriverState
from .streams import PollAsyncioStreamIoPipelineDriver


##


class AsyncioIoPipelineHostResolver(Abstract):
    """An asyncio-native resolver: awaited by the connecting task."""

    @abc.abstractmethod
    async def resolve(self, host: str, port: int) -> IoPipelineHostResolveResult:
        raise NotImplementedError


class LoopAsyncioIoPipelineHostResolver(AsyncioIoPipelineHostResolver):
    """Resolves with the loop's `getaddrinfo`, which runs off the loop's thread. The default."""

    def __repr__(self) -> str:
        return f'{type(self).__name__}()'

    async def resolve(self, host: str, port: int) -> IoPipelineHostResolveResult:
        loop = asyncio.get_running_loop()
        try:
            infos = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except OSError as e:
            raise ResolveIoPipelineHostError(TcpSocketEndpoint(host, port), [e]) from e
        return [(family, type_, proto, sockaddr) for family, type_, proto, _, sockaddr in infos]


class SyncAsyncioIoPipelineHostResolver(AsyncioIoPipelineHostResolver):
    """Adapts a callback-style `IoPipelineHostResolver`, awaiting its callback."""

    def __init__(self, resolver: IoPipelineHostResolver) -> None:
        super().__init__()

        self._resolver = resolver

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._resolver!r})'

    async def resolve(self, host: str, port: int) -> IoPipelineHostResolveResult:
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()

        def on_done(result: ta.Union[IoPipelineHostResolveResult, BaseException]) -> None:
            if fut.done():
                return
            if isinstance(result, BaseException):
                fut.set_exception(result)
            else:
                fut.set_result(result)

        self._resolver.resolve(host, port, on_done)
        return await fut


##


class ProxyAsyncioStreamWriter:
    """A stream writer standing in for another, for the pipe transports' differences from the socket ones."""

    def __init__(self, writer: asyncio.StreamWriter) -> None:
        super().__init__()

        self._writer = writer

    def __getattr__(self, name: str) -> ta.Any:
        return getattr(self._writer, name)

    @property
    def transport(self) -> asyncio.BaseTransport:
        return self._writer.transport


class NoEofAsyncioStreamWriter(ProxyAsyncioStreamWriter):
    """
    For a pipe transport which could write EOF, but must not: the descriptor it would close is a duplicate of the
    caller's, whose own keeps the pipe open, or is the one it also reads from. The driver sees a writer which cannot
    write EOF and fails ShutdownOutput as the descriptor drivers do.
    """

    def can_write_eof(self) -> bool:
        return False

    def write_eof(self) -> None:
        raise NotImplementedError('cannot write eof')


class EofClosesAsyncioStreamWriter(ProxyAsyncioStreamWriter):
    """
    For an owned pipe write descriptor: EOF on a pipe transport is the descriptor's close, after which the transport
    reports its connection lost. A drain after the EOF was asked for, finding the connection lost, is the EOF having
    gone out, not a failure; before it, a lost connection is the failure it always was.
    """

    def __init__(self, writer: asyncio.StreamWriter) -> None:
        super().__init__(writer)

        self._eof_written = False

    def write_eof(self) -> None:
        self._eof_written = True
        self._writer.write_eof()

    async def drain(self) -> None:
        try:
            await self._writer.drain()
        except ConnectionResetError:
            if not self._eof_written:
                raise


class AsyncioHostedIoPipelineDriver(BaseIoPipelineHostHandle, IoPipelineHostedDriver):
    """
    Driven in a task of its own, created by the host; the task starts the driver, delivers the start outcome, drives
    until done, and closes the driver. Closing the handle cancels the task.
    """

    _closes_first = False

    def __init__(
            self,
            host: 'AsyncioIoPipelineHost',
            owner: ta.Optional[IoPipelineHandlerRef],
            info: IoPipelineHostTransportInfo,
    ) -> None:
        self._info = info
        self._driver: ta.Optional[PollAsyncioStreamIoPipelineDriver] = None
        self._task: ta.Optional[asyncio.Task] = None
        self._started: asyncio.Future = host.loop.create_future()
        self._cancelled = False
        self.unhandled: ta.List[ta.Any] = []

        super().__init__(host, owner)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self.state.name}>'

    @property
    def driver(self) -> ta.Optional[PollAsyncioStreamIoPipelineDriver]:
        return self._driver

    @property
    def task(self) -> ta.Optional[asyncio.Task]:
        return self._task

    @property
    def info(self) -> IoPipelineHostTransportInfo:
        return self._info

    @property
    def state(self) -> IoPipelineDriverState:
        if (d := self._driver) is None:
            if self._cancelled or (self._task is not None and self._task.done()):
                return IoPipelineDriverState.CLOSED
            return IoPipelineDriverState.NEW
        return d.state

    @property
    def pipeline(self) -> ta.Optional[IoPipeline]:
        if (d := self._driver) is None or not self._started.done():
            return None
        return d.pipeline

    @property
    def posting(self) -> IoPipelinePosting:
        if (d := self._driver) is None:
            raise StateIoPipelineError('hosted driver has not started')
        return d.posting

    @property
    def closed(self) -> bool:
        return self.state in (IoPipelineDriverState.CLOSED, IoPipelineDriverState.FAILED)

    def close(self) -> None:
        self._cancelled = True
        if (t := self._task) is not None and not t.done():
            t.cancel()
        self._unregister()

    async def wait_started(self) -> None:
        """Returns once the driver has started, or raises what stopped it from starting."""

        await asyncio.shield(self._started)

    async def wait_closed(self) -> None:
        if (t := self._task) is not None:
            try:
                await asyncio.shield(t)
            except (asyncio.CancelledError, Exception):  # noqa
                pass

    #

    def _fail_start(self, exc: BaseException) -> None:
        if not self._started.done():
            self._started.set_exception(exc)
            self._started.exception()  # Retrieved: no "exception was never retrieved" warning.

    async def _drive(
            self,
            driver: PollAsyncioStreamIoPipelineDriver,
            on_started: ta.Optional[ta.Callable[[], None]] = None,
            cleanup: ta.Optional[ta.Callable[[], None]] = None,
    ) -> None:
        """The driving task's body: start, report, drive to the end, close."""

        self._driver = driver
        try:
            try:
                check.none(await driver.next(read=False))
            except BaseException as e:  # noqa
                self._fail_start(e)
                raise
            if not self._started.done():
                self._started.set_result(None)
            if on_started is not None:
                on_started()

            while driver.is_running:
                if (out := await driver.next(raise_on_stall=False)) is not None:
                    self.unhandled.append(out)

        except asyncio.CancelledError:
            pass

        finally:
            try:
                await driver.close()
            finally:
                if cleanup is not None:
                    cleanup()
                self._fail_start(ClosedIoPipelineHostError('hosted driver closed before starting'))
                self._unregister()


class AsyncioHostedIoPipelineConnect(BaseIoPipelineHostHandle, IoPipelineHostedConnect):
    _closes_first = False

    def __init__(
            self,
            host: 'AsyncioIoPipelineHost',
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

        self._task: ta.Optional[asyncio.Task] = None
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
        self._unregister()

    def close(self) -> None:
        if self._done:
            return
        self._finish()
        if (t := self._task) is not None and not t.done():
            t.cancel()
        self._deliver(self._on_failed, ClosedIoPipelineHostError('connect closed'))

    async def _connect(self, host: 'AsyncioIoPipelineHost') -> ta.Optional[socket.socket]:
        """Resolves and connects, returning the socket, or None having delivered the failure."""

        if (addresses := host.literal_addresses(self._endpoint)) is None:
            tcp = check.isinstance(self._endpoint, TcpSocketEndpoint)
            try:
                addresses = await host.resolver.resolve(tcp.host, tcp.port)
            except ConnectIoPipelineHostError as e:
                self._deliver(self._on_failed, e)
                return None
            except Exception as e:  # noqa
                self._deliver(self._on_failed, ConnectIoPipelineHostError(self._endpoint, [e]))
                return None

        loop = asyncio.get_running_loop()
        errors: ta.List[BaseException] = []
        for family, type_, proto, sockaddr in addresses:
            try:
                sock = socket.socket(family, type_, proto)
            except OSError as e:
                errors.append(e)
                continue
            sock.setblocking(False)
            try:
                await asyncio.wait_for(loop.sock_connect(sock, sockaddr), self._timeout_s)
            except asyncio.TimeoutError:  # noqa: UP041  # Distinct from the builtin before 3.11.
                sock.close()
                errors.append(TimeoutError(f'connect timed out after {self._timeout_s}s'))
                continue
            except OSError as e:
                sock.close()
                errors.append(e)
                continue
            except BaseException:
                sock.close()
                raise
            return sock

        if errors and isinstance(errors[-1], TimeoutError):
            self._deliver(self._on_failed, ConnectTimeoutIoPipelineHostError(self._endpoint, errors))
        else:
            self._deliver(self._on_failed, ConnectIoPipelineHostError(self._endpoint, errors))
        return None

    async def _main(self, host: 'AsyncioIoPipelineHost') -> None:
        """The task: connect, then become the connection's driving task."""

        try:
            sock = await self._connect(host)
        except asyncio.CancelledError:
            return
        if sock is None:
            self._finish()
            return

        if self._done or host.closed:
            sock.close()
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
        except Exception as e:  # noqa
            sock.close()
            self._finish()
            self._deliver(self._on_failed, ConnectIoPipelineHostError(self._endpoint, [e]))
            return

        hosted = AsyncioHostedIoPipelineDriver(host, self.owner, info)
        hosted._task = asyncio.current_task()  # noqa
        self._finish()

        on_connected = self._on_connected
        await host._serve_socket(  # noqa
            hosted,
            sock,
            spec,
            owned=True,
            on_started=lambda: hosted._deliver(on_connected, hosted),  # noqa
        )


class AsyncioHostedIoPipelineListener(BaseIoPipelineHostHandle, IoPipelineHostedListener):
    _closes_first = True

    def __init__(
            self,
            host: 'AsyncioIoPipelineHost',
            owner: ta.Optional[IoPipelineHandlerRef],
            socket_listener: SyncSocketListener,
            spec_factory: IoPipelineHostSpecFactory,
            on_accepted: ta.Optional[IoPipelineHostCallback[IoPipelineHostedDriver]],
    ) -> None:
        self._socket_listener: ta.Optional[SyncSocketListener] = socket_listener
        self._bound_endpoint = socket_listener.bound_endpoint
        self._spec_factory = spec_factory
        self._on_accepted = on_accepted
        self._fd = socket_listener.socket.fileno()

        super().__init__(host, owner)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._bound_endpoint!r}>'

    @property
    def bound_endpoint(self) -> SocketEndpoint:
        return self._bound_endpoint

    @property
    def closed(self) -> bool:
        return self._socket_listener is None

    def close(self) -> None:
        if (socket_listener := self._socket_listener) is None:
            return
        self._socket_listener = None
        if (host := self._host) is not None:
            try:
                ta.cast('AsyncioIoPipelineHost', host).loop.remove_reader(self._fd)
            except (ValueError, OSError, RuntimeError):
                pass
        try:
            socket_listener.close()
        finally:
            self._unregister()

    def _on_readable(self) -> None:
        if (socket_listener := self._socket_listener) is None:
            return
        if (host := self._host) is None or host.closed:
            self.close()
            return
        ahost = ta.cast('AsyncioIoPipelineHost', host)

        for _ in range(64):
            try:
                conn, addr = socket_listener.socket.accept()
            except BlockingIOError:
                return
            except OSError:
                return

            conn.setblocking(False)
            try:
                local = conn.getsockname()
            except OSError:
                local = None
            info = IoPipelineHostTransportInfo(endpoint=self._bound_endpoint, local_address=local, peer_address=addr)

            try:
                spec = self._spec_factory(info)
            except Exception:  # noqa
                conn.close()
                continue

            hosted = AsyncioHostedIoPipelineDriver(ahost, self.owner, info)
            on_accepted = self._on_accepted
            ahost._start_task(hosted, ahost._serve_socket(  # noqa
                hosted,
                conn,
                spec,
                owned=True,
                on_started=(lambda: hosted._deliver(on_accepted, hosted)) if on_accepted is not None else None,  # noqa
            ))


##


class AsyncioIoPipelineHost(BaseIoPipelineHost):
    """
    Hosts transports on one asyncio loop. A transport it adopts is one of: a connected `socket.socket`, which it
    drives over a duplicate unless `owned`, so that the caller's socket is restored and never closed; a duplex
    descriptor such as a terminal master, read and written through two pipe transports; or a `(read_fd, write_fd)`
    pair. A caller-owned non-socket write descriptor, and a duplex descriptor, cannot be half-closed, so ShutdownOutput
    fails on them as it does on the fdio forms; an owned pipe write descriptor is closed by it.
    """

    def __init__(
            self,
            *,
            loop: ta.Optional[asyncio.AbstractEventLoop] = None,
            resolver: ta.Union[AsyncioIoPipelineHostResolver, IoPipelineHostResolver, None] = None,
            driver_config: ta.Optional[PollAsyncioStreamIoPipelineDriver.Config] = None,
            socket_transport: SyncSocketTransport = DEFAULT_SYNC_SOCKET_TRANSPORT,
    ) -> None:
        super().__init__()

        self._loop = loop
        self._async_resolver: AsyncioIoPipelineHostResolver
        if resolver is None:
            self._async_resolver = LoopAsyncioIoPipelineHostResolver()
        elif isinstance(resolver, AsyncioIoPipelineHostResolver):
            self._async_resolver = resolver
        else:
            self._async_resolver = SyncAsyncioIoPipelineHostResolver(resolver)
        self._driver_config = driver_config
        self._socket_transport = socket_transport

        self._tasks: ta.Set[asyncio.Task] = set()

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}'

    @property
    def loop(self) -> asyncio.AbstractEventLoop:
        if (loop := self._loop) is None:
            self._loop = loop = asyncio.get_running_loop()
        return loop

    @property
    def resolver(self) -> AsyncioIoPipelineHostResolver:  # type: ignore[override]
        return self._async_resolver

    #

    def _start_task(
            self,
            hosted: AsyncioHostedIoPipelineDriver,
            coro: ta.Coroutine[ta.Any, ta.Any, None],
    ) -> asyncio.Task:
        task: asyncio.Task = self.loop.create_task(coro)
        hosted._task = task  # noqa
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def _serve_socket(
            self,
            hosted: AsyncioHostedIoPipelineDriver,
            sock: socket.socket,
            spec: IoPipeline.Spec,
            *,
            owned: bool,
            on_started: ta.Optional[ta.Callable[[], None]] = None,
    ) -> None:
        restore: ta.Optional[ta.Callable[[], None]] = None
        if not owned:
            # The transport closes what it is given: a duplicate, so the caller's socket survives. Nonblocking mode
            # lives on the shared description, so the caller's is restored afterwards.
            original_timeout = sock.gettimeout()
            served = sock.dup()

            def restore_caller_socket(caller_sock: socket.socket = sock) -> None:
                try:
                    caller_sock.settimeout(original_timeout)
                except OSError:
                    pass

            restore = restore_caller_socket
        else:
            served = sock

        try:
            reader, writer = await asyncio.open_connection(sock=served)
        except BaseException as e:  # noqa
            served.close()
            if restore is not None:
                restore()
            hosted._fail_start(e)  # noqa
            hosted._unregister()  # noqa
            raise

        driver = PollAsyncioStreamIoPipelineDriver(self._hosted_spec(spec), reader, writer, self._driver_config)
        await hosted._drive(driver, on_started, restore)  # noqa

    async def _serve_fds(
            self,
            hosted: AsyncioHostedIoPipelineDriver,
            read_fd: int,
            write_fd: int,
            spec: IoPipeline.Spec,
            *,
            owned: bool,
    ) -> None:
        loop = self.loop
        fds = {read_fd, write_fd}
        original_flags = {fd: fcntl.fcntl(fd, fcntl.F_GETFL) for fd in fds}
        # A caller-owned descriptor is served through a duplicate, which the transports own and close; an owned one is
        # handed over as is. Either way nonblocking mode lands on the shared description, restored afterwards.
        # One owned descriptor serving both ways gets a duplicate for its second transport, so each closes its own.
        served_read = read_fd if owned else os.dup(read_fd)
        served_write = write_fd if owned and write_fd != read_fd else os.dup(write_fd)

        def restore() -> None:
            if owned:
                return
            for fd, flags in original_flags.items():
                try:
                    fcntl.fcntl(fd, fcntl.F_SETFL, flags)
                except OSError:
                    pass

        read_transport: ta.Optional[asyncio.BaseTransport] = None
        try:
            reader = asyncio.StreamReader(loop=loop)
            read_protocol = asyncio.StreamReaderProtocol(reader, loop=loop)
            read_transport, _ = await loop.connect_read_pipe(lambda: read_protocol, os.fdopen(served_read, 'rb', 0))
            write_protocol = asyncio.streams.FlowControlMixin(loop=loop)
            write_transport, _ = await loop.connect_write_pipe(
                lambda: write_protocol,
                os.fdopen(served_write, 'wb', 0),
            )
            writer: ta.Any = asyncio.StreamWriter(write_transport, write_protocol, None, loop)
        except BaseException as e:  # noqa
            if read_transport is not None:
                read_transport.close()
            for fd in (served_read, served_write):
                if fd not in fds:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
            restore()
            hosted._fail_start(e)  # noqa
            hosted._unregister()  # noqa
            raise

        # EOF on a pipe transport closes its descriptor: a half-close only for an owned write descriptor of its own.
        if owned and write_fd != read_fd:
            writer = EofClosesAsyncioStreamWriter(writer)
        else:
            writer = NoEofAsyncioStreamWriter(writer)

        def cleanup() -> None:
            check.not_none(read_transport).close()
            restore()

        driver = PollAsyncioStreamIoPipelineDriver(self._hosted_spec(spec), reader, writer, self._driver_config)
        await hosted._drive(driver, None, cleanup)  # noqa

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

        handle = AsyncioHostedIoPipelineConnect(
            self,
            owner,
            endpoint,
            spec_factory,
            on_connected,
            on_failed,
            timeout_s,
        )
        task = self.loop.create_task(handle._main(self))  # noqa
        handle._task = task  # noqa
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
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

        socket_listener.socket.setblocking(False)
        listener = AsyncioHostedIoPipelineListener(self, owner, socket_listener, spec_factory, on_accepted)
        self.loop.add_reader(socket_listener.socket.fileno(), listener._on_readable)  # noqa
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
            hosted = AsyncioHostedIoPipelineDriver(self, owner, info)
            self._start_task(hosted, self._serve_socket(hosted, transport, spec, owned=owned))
            return hosted

        if isinstance(transport, int):
            if info is None:
                info = IoPipelineHostTransportInfo()
            hosted = AsyncioHostedIoPipelineDriver(self, owner, info)
            self._start_task(hosted, self._serve_fds(hosted, transport, transport, spec, owned=owned))
            return hosted

        if isinstance(transport, tuple) and len(transport) == 2:
            read_fd, write_fd = transport
            if info is None:
                info = IoPipelineHostTransportInfo()
            hosted = AsyncioHostedIoPipelineDriver(self, owner, info)
            self._start_task(hosted, self._serve_fds(
                hosted,
                check.isinstance(read_fd, int),
                check.isinstance(write_fd, int),
                spec,
                owned=owned,
            ))
            return hosted

        raise TypeError(transport)

    #

    async def wait_closed(self) -> None:
        """Waits for the tasks of everything closed to finish; for a host which was closed, for all of them."""

        tasks = [t for t in self._tasks if not t.done()]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
