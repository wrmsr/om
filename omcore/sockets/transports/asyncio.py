# ruff: noqa: UP006 UP045
# @om-lite
"""
Connecting to and listening on unix and tcp socket endpoints, under asyncio.

TODO:
 - merge / dedupe with ./bind
"""
import asyncio
import typing as ta

from ...lite.check import check
from ..endpoints import SocketEndpoint
from ..endpoints import TcpSocketEndpoint
from ..endpoints import UnixSocketEndpoint
from .sync import DEFAULT_SYNC_SOCKET_TRANSPORT
from .sync import SyncSocketListener
from .sync import SyncSocketTransport


AsyncioSocketConnectionHandler = ta.Callable[[asyncio.StreamReader, asyncio.StreamWriter], None]  # ta.TypeAlias


##


class AsyncioSocketListener(ta.Protocol):
    @property
    def bound_endpoint(self) -> SocketEndpoint:
        raise NotImplementedError

    async def serve_forever(self) -> ta.NoReturn:
        raise NotImplementedError

    async def close(self) -> bool:
        raise NotImplementedError


class AsyncioSocketTransport(ta.Protocol):
    async def connect(
            self,
            endpoint: SocketEndpoint,
    ) -> ta.Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        raise NotImplementedError

    async def listen(
            self,
            endpoint: SocketEndpoint,
            handler: AsyncioSocketConnectionHandler,
            *,
            backlog: int,
            unix_socket_mode: int,
    ) -> AsyncioSocketListener:
        raise NotImplementedError


##


@ta.final
class AsyncioServerSocketListener:
    """Own an asyncio server and its underlying endpoint cleanup."""

    def __init__(
            self,
            server: asyncio.base_events.Server,  # Note: not available as `asyncio.Server` until 3.9
            socket_listener: SyncSocketListener,
    ) -> None:
        super().__init__()

        self._server: ta.Optional[asyncio.base_events.Server] = server
        self._socket_listener = socket_listener

    @property
    def bound_endpoint(self) -> SocketEndpoint:
        return self._socket_listener.bound_endpoint

    async def serve_forever(self) -> ta.NoReturn:
        await check.not_none(self._server).serve_forever()
        raise RuntimeError('Asyncio listener stopped serving')

    async def close(self) -> bool:
        if (server := self._server) is None:
            return False
        self._server = None

        try:
            server.close()
            await server.wait_closed()
        finally:
            self._socket_listener.close()
        return True


@ta.final
class DefaultAsyncioSocketTransport:
    """Default Unix-domain and plaintext TCP asyncio stream transport."""

    def __init__(
            self,
            sync_transport: SyncSocketTransport = DEFAULT_SYNC_SOCKET_TRANSPORT,
    ) -> None:
        super().__init__()

        self._sync_transport = sync_transport

    async def connect(
            self,
            endpoint: SocketEndpoint,
    ) -> ta.Tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        if isinstance(endpoint, UnixSocketEndpoint):
            return await asyncio.open_unix_connection(endpoint.path)
        if isinstance(endpoint, TcpSocketEndpoint):
            check.arg(endpoint.port > 0, 'Cannot connect to TCP port zero')
            return await asyncio.open_connection(endpoint.host, endpoint.port)
        raise TypeError(endpoint)

    async def listen(
            self,
            endpoint: SocketEndpoint,
            handler: AsyncioSocketConnectionHandler,
            *,
            backlog: int,
            unix_socket_mode: int,
    ) -> AsyncioSocketListener:
        socket_listener = self._sync_transport.listen(
            endpoint,
            backlog=backlog,
            unix_socket_mode=unix_socket_mode,
        )
        try:
            sock = socket_listener.socket
            sock.setblocking(False)
            if isinstance(endpoint, UnixSocketEndpoint):
                server = await asyncio.start_unix_server(handler, sock=sock)
            elif isinstance(endpoint, TcpSocketEndpoint):
                server = await asyncio.start_server(handler, sock=sock)
            else:
                raise TypeError(endpoint)
        except BaseException:
            socket_listener.close()
            raise
        return AsyncioServerSocketListener(server, socket_listener)


DEFAULT_ASYNCIO_SOCKET_TRANSPORT: AsyncioSocketTransport = DefaultAsyncioSocketTransport()
