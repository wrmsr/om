# ruff: noqa: UP006 UP045
# @om-lite
"""
Connecting to and listening on unix and tcp socket endpoints, synchronously.

The asyncio transport binds via the sync transport and adopts the already-bound socket, so unix socket mode, backlog,
and stale-socket replacement policy are shared between the two.

TODO:
 - merge / dedupe with ./bind
"""
import os
import socket as socket_
import typing as ta

from ...lite.check import check
from ..endpoints import SocketEndpoint
from ..endpoints import TcpSocketEndpoint
from ..endpoints import UnixSocketEndpoint
from ..io import close_socket_immediately
from .base import OwnedSocketListener
from .base import _bind_unix_socket
from .base import _unlink_unix_socket


##


class SyncSocketListener(ta.Protocol):
    @property
    def bound_endpoint(self) -> SocketEndpoint:
        raise NotImplementedError

    @property
    def socket(self) -> socket_.socket:
        raise NotImplementedError

    def accept(self) -> ta.Tuple[socket_.socket, ta.Any]:
        raise NotImplementedError

    def close(self) -> bool:
        raise NotImplementedError


class SyncSocketTransport(ta.Protocol):
    def connect(
            self,
            endpoint: SocketEndpoint,
            *,
            timeout_s: ta.Optional[float],
    ) -> socket_.socket:
        raise NotImplementedError

    def listen(
            self,
            endpoint: SocketEndpoint,
            *,
            backlog: int,
            unix_socket_mode: int,
    ) -> SyncSocketListener:
        raise NotImplementedError


##


@ta.final
class DefaultSyncSocketTransport:
    """Default Unix-domain and plaintext TCP synchronous socket transport."""

    def connect(
            self,
            endpoint: SocketEndpoint,
            *,
            timeout_s: ta.Optional[float],
    ) -> socket_.socket:
        if isinstance(endpoint, UnixSocketEndpoint):
            sock = socket_.socket(socket_.AF_UNIX, socket_.SOCK_STREAM)
            try:
                sock.settimeout(timeout_s)
                sock.connect(endpoint.path)
            except BaseException:
                close_socket_immediately(sock)
                raise
            return sock

        if isinstance(endpoint, TcpSocketEndpoint):
            check.arg(endpoint.port > 0, 'Cannot connect to TCP port zero')
            return socket_.create_connection(
                (endpoint.host, endpoint.port),
                timeout=timeout_s,
            )

        raise TypeError(endpoint)

    def listen(
            self,
            endpoint: SocketEndpoint,
            *,
            backlog: int,
            unix_socket_mode: int,
    ) -> SyncSocketListener:
        check.arg(backlog > 0)
        check.arg(0 <= unix_socket_mode <= 0o777)

        if isinstance(endpoint, UnixSocketEndpoint):
            sock = socket_.socket(socket_.AF_UNIX, socket_.SOCK_STREAM)
            identity: ta.Optional[ta.Tuple[int, int]] = None
            try:
                identity = _bind_unix_socket(sock, endpoint)
                os.chmod(endpoint.path, unix_socket_mode)
                sock.listen(backlog)
            except BaseException:
                close_socket_immediately(sock)
                _unlink_unix_socket(endpoint.path, identity)
                raise
            return OwnedSocketListener(
                sock,
                endpoint,
                unix_socket_identity=identity,
            )

        if isinstance(endpoint, TcpSocketEndpoint):
            addr_info = socket_.getaddrinfo(
                endpoint.host,
                endpoint.port,
                family=socket_.AF_UNSPEC,
                type=socket_.SOCK_STREAM,
                flags=socket_.AI_PASSIVE,
            )
            errors: list[OSError] = []
            for family, sock_type, proto, _, address in addr_info:
                sock = socket_.socket(family, sock_type, proto)
                try:
                    sock.setsockopt(socket_.SOL_SOCKET, socket_.SO_REUSEADDR, 1)
                    sock.bind(address)
                    sock.listen(backlog)
                except OSError as exc:
                    errors.append(exc)
                    close_socket_immediately(sock)
                    continue

                raw_bound_address = sock.getsockname()
                bound_endpoint = TcpSocketEndpoint(
                    host=check.isinstance(raw_bound_address[0], str),
                    port=check.isinstance(raw_bound_address[1], int),
                )
                return OwnedSocketListener(sock, bound_endpoint)

            if errors:
                raise errors[-1]
            raise OSError(f'No TCP addresses resolved for {endpoint!r}')

        raise TypeError(endpoint)


DEFAULT_SYNC_SOCKET_TRANSPORT: SyncSocketTransport = DefaultSyncSocketTransport()
