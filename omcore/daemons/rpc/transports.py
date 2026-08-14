import asyncio
import errno
import os
import socket
import stat
import typing as ta

from ... import check
from ... import lang
from ...sockets.io import close_socket_immediately
from .endpoints import RpcEndpoint
from .endpoints import TcpRpcEndpoint
from .endpoints import UnixRpcEndpoint


Socket: ta.TypeAlias = socket.socket


##


class SyncRpcListener(ta.Protocol):
    @property
    def bound_endpoint(self) -> RpcEndpoint:
        raise NotImplementedError

    @property
    def socket(self) -> socket.socket:
        raise NotImplementedError

    def accept(self) -> tuple[Socket, ta.Any]:
        raise NotImplementedError

    def close(self) -> bool:
        raise NotImplementedError


class SyncRpcTransport(ta.Protocol):
    def connect(
            self,
            endpoint: RpcEndpoint,
            *,
            timeout_s: float | None,
    ) -> socket.socket:
        raise NotImplementedError

    def listen(
            self,
            endpoint: RpcEndpoint,
            *,
            backlog: int,
            unix_socket_mode: int,
    ) -> SyncRpcListener:
        raise NotImplementedError


class AsyncioRpcListener(ta.Protocol):
    @property
    def bound_endpoint(self) -> RpcEndpoint:
        raise NotImplementedError

    async def serve_forever(self) -> ta.NoReturn:
        raise NotImplementedError

    async def close(self) -> bool:
        raise NotImplementedError


AsyncioRpcConnectionHandler: ta.TypeAlias = ta.Callable[
    [asyncio.StreamReader, asyncio.StreamWriter],
    None,
]


class AsyncioRpcTransport(ta.Protocol):
    async def connect(
            self,
            endpoint: RpcEndpoint,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        raise NotImplementedError

    async def listen(
            self,
            endpoint: RpcEndpoint,
            handler: AsyncioRpcConnectionHandler,
            *,
            backlog: int,
            unix_socket_mode: int,
    ) -> AsyncioRpcListener:
        raise NotImplementedError


##


def _unlink_unix_socket(path: str, identity: tuple[int, int] | None) -> None:
    if identity is None:
        return
    try:
        stat_result = os.lstat(path)
    except FileNotFoundError:
        return
    if (stat_result.st_dev, stat_result.st_ino) == identity:
        os.unlink(path)


def _bind_unix_socket(sock: socket.socket, endpoint: UnixRpcEndpoint) -> tuple[int, int]:
    try:
        sock.bind(endpoint.path)
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE:
            raise

        try:
            socket_stat = os.lstat(endpoint.path)
        except FileNotFoundError:
            sock.bind(endpoint.path)
        else:
            if not stat.S_ISSOCK(socket_stat.st_mode):
                raise RuntimeError(f'Refusing to replace non-socket path: {endpoint.path!r}')

            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as probe:
                try:
                    probe.connect(endpoint.path)
                except (ConnectionRefusedError, FileNotFoundError):
                    pass
                else:
                    raise RuntimeError(f'RPC socket is already active: {endpoint.path!r}')

            try:
                os.unlink(endpoint.path)
            except FileNotFoundError:
                pass
            sock.bind(endpoint.path)

    stat_result = os.lstat(endpoint.path)
    return stat_result.st_dev, stat_result.st_ino


class SocketRpcListener(lang.Final):
    """Own a listening socket and any endpoint-specific cleanup."""

    def __init__(
            self,
            sock: socket.socket,
            bound_endpoint: RpcEndpoint,
            *,
            unix_socket_identity: tuple[int, int] | None = None,
    ) -> None:
        super().__init__()

        self._socket: socket.socket | None = sock
        self._bound_endpoint = bound_endpoint
        self._unix_socket_identity = unix_socket_identity

    @property
    def bound_endpoint(self) -> RpcEndpoint:
        return self._bound_endpoint

    @property
    def socket(self) -> socket.socket:
        return check.not_none(self._socket)

    def accept(self) -> tuple[Socket, ta.Any]:
        return self.socket.accept()

    def close(self) -> bool:
        if (sock := self._socket) is None:
            return False
        self._socket = None

        close_socket_immediately(sock)
        if isinstance(endpoint := self._bound_endpoint, UnixRpcEndpoint):
            _unlink_unix_socket(endpoint.path, self._unix_socket_identity)
        return True


class DefaultSyncRpcTransport(lang.Final):
    """Default Unix-domain and plaintext TCP synchronous socket transport."""

    def connect(
            self,
            endpoint: RpcEndpoint,
            *,
            timeout_s: float | None,
    ) -> socket.socket:
        if isinstance(endpoint, UnixRpcEndpoint):
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                sock.settimeout(timeout_s)
                sock.connect(endpoint.path)
            except BaseException:
                close_socket_immediately(sock)
                raise
            return sock

        if isinstance(endpoint, TcpRpcEndpoint):
            check.arg(endpoint.port > 0, 'Cannot connect to TCP port zero')
            return socket.create_connection(
                (endpoint.host, endpoint.port),
                timeout=timeout_s,
            )

        raise TypeError(endpoint)

    def listen(
            self,
            endpoint: RpcEndpoint,
            *,
            backlog: int,
            unix_socket_mode: int,
    ) -> SyncRpcListener:
        check.arg(backlog > 0)
        check.arg(0 <= unix_socket_mode <= 0o777)

        if isinstance(endpoint, UnixRpcEndpoint):
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            identity: tuple[int, int] | None = None
            try:
                identity = _bind_unix_socket(sock, endpoint)
                os.chmod(endpoint.path, unix_socket_mode)
                sock.listen(backlog)
            except BaseException:
                close_socket_immediately(sock)
                _unlink_unix_socket(endpoint.path, identity)
                raise
            return SocketRpcListener(
                sock,
                endpoint,
                unix_socket_identity=identity,
            )

        if isinstance(endpoint, TcpRpcEndpoint):
            addr_info = socket.getaddrinfo(
                endpoint.host,
                endpoint.port,
                family=socket.AF_UNSPEC,
                type=socket.SOCK_STREAM,
                flags=socket.AI_PASSIVE,
            )
            errors: list[OSError] = []
            for family, sock_type, proto, _, address in addr_info:
                sock = socket.socket(family, sock_type, proto)
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind(address)
                    sock.listen(backlog)
                except OSError as exc:
                    errors.append(exc)
                    close_socket_immediately(sock)
                    continue

                raw_bound_address = sock.getsockname()
                bound_endpoint = TcpRpcEndpoint(
                    host=check.isinstance(raw_bound_address[0], str),
                    port=check.isinstance(raw_bound_address[1], int),
                )
                return SocketRpcListener(sock, bound_endpoint)

            if errors:
                raise errors[-1]
            raise OSError(f'No TCP addresses resolved for {endpoint!r}')

        raise TypeError(endpoint)


DEFAULT_SYNC_RPC_TRANSPORT: SyncRpcTransport = DefaultSyncRpcTransport()


##


class AsyncioServerRpcListener(lang.Final):
    """Own an asyncio server and its underlying endpoint cleanup."""

    def __init__(
            self,
            server: asyncio.Server,
            socket_listener: SyncRpcListener,
    ) -> None:
        super().__init__()

        self._server: asyncio.Server | None = server
        self._socket_listener = socket_listener

    @property
    def bound_endpoint(self) -> RpcEndpoint:
        return self._socket_listener.bound_endpoint

    async def serve_forever(self) -> ta.NoReturn:
        await check.not_none(self._server).serve_forever()
        raise RuntimeError('Asyncio RPC listener stopped serving')

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


class DefaultAsyncioRpcTransport(lang.Final):
    """Default Unix-domain and plaintext TCP asyncio stream transport."""

    def __init__(
            self,
            sync_transport: SyncRpcTransport = DEFAULT_SYNC_RPC_TRANSPORT,
    ) -> None:
        super().__init__()

        self._sync_transport = sync_transport

    async def connect(
            self,
            endpoint: RpcEndpoint,
    ) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
        if isinstance(endpoint, UnixRpcEndpoint):
            return await asyncio.open_unix_connection(endpoint.path)
        if isinstance(endpoint, TcpRpcEndpoint):
            check.arg(endpoint.port > 0, 'Cannot connect to TCP port zero')
            return await asyncio.open_connection(endpoint.host, endpoint.port)
        raise TypeError(endpoint)

    async def listen(
            self,
            endpoint: RpcEndpoint,
            handler: AsyncioRpcConnectionHandler,
            *,
            backlog: int,
            unix_socket_mode: int,
    ) -> AsyncioRpcListener:
        socket_listener = self._sync_transport.listen(
            endpoint,
            backlog=backlog,
            unix_socket_mode=unix_socket_mode,
        )
        try:
            sock = socket_listener.socket
            sock.setblocking(False)
            if isinstance(endpoint, UnixRpcEndpoint):
                server = await asyncio.start_unix_server(handler, sock=sock)
            elif isinstance(endpoint, TcpRpcEndpoint):
                server = await asyncio.start_server(handler, sock=sock)
            else:
                raise TypeError(endpoint)
        except BaseException:
            socket_listener.close()
            raise
        return AsyncioServerRpcListener(server, socket_listener)


DEFAULT_ASYNCIO_RPC_TRANSPORT: AsyncioRpcTransport = DefaultAsyncioRpcTransport()
