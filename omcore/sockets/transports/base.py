# ruff: noqa: UP006 UP045
# @om-lite
"""
Connecting to and listening on unix and tcp socket endpoints.

TODO:
 - merge / dedupe with ./bind
"""
import errno
import os
import socket as socket_
import stat
import typing as ta

from ...lite.check import check
from ..endpoints import SocketEndpoint
from ..endpoints import UnixSocketEndpoint
from ..io import close_socket_immediately


##


def _unlink_unix_socket(path: str, identity: ta.Optional[ta.Tuple[int, int]]) -> None:
    if identity is None:
        return
    try:
        stat_result = os.lstat(path)
    except FileNotFoundError:
        return
    if (stat_result.st_dev, stat_result.st_ino) == identity:
        os.unlink(path)


def _bind_unix_socket(sock: socket_.socket, endpoint: UnixSocketEndpoint) -> ta.Tuple[int, int]:
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

            with socket_.socket(socket_.AF_UNIX, socket_.SOCK_STREAM) as probe:
                try:
                    probe.connect(endpoint.path)
                except (ConnectionRefusedError, FileNotFoundError):
                    pass
                else:
                    raise RuntimeError(f'Socket is already active: {endpoint.path!r}')

            try:
                os.unlink(endpoint.path)
            except FileNotFoundError:
                pass
            sock.bind(endpoint.path)

    stat_result = os.lstat(endpoint.path)
    return stat_result.st_dev, stat_result.st_ino


@ta.final
class OwnedSocketListener:
    """Own a listening socket and any endpoint-specific cleanup."""

    def __init__(
            self,
            sock: socket_.socket,
            bound_endpoint: SocketEndpoint,
            *,
            unix_socket_identity: ta.Optional[ta.Tuple[int, int]] = None,
    ) -> None:
        super().__init__()

        self._socket: ta.Optional[socket_.socket] = sock
        self._bound_endpoint = bound_endpoint
        self._unix_socket_identity = unix_socket_identity

    @property
    def bound_endpoint(self) -> SocketEndpoint:
        return self._bound_endpoint

    @property
    def socket(self) -> socket_.socket:
        return check.not_none(self._socket)

    def accept(self) -> ta.Tuple[socket_.socket, ta.Any]:
        return self.socket.accept()

    def close(self) -> bool:
        if (sock := self._socket) is None:
            return False
        self._socket = None

        close_socket_immediately(sock)
        if isinstance(endpoint := self._bound_endpoint, UnixSocketEndpoint):
            _unlink_unix_socket(endpoint.path, self._unix_socket_identity)
        return True
