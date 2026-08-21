import socket
import ssl
import typing as ta

from ..exceptions import InterfaceError


SslContextArg: ta.TypeAlias = ssl.SSLContext | bool | None


##


def make_ssl_context(arg: SslContextArg) -> ssl.SSLContext:
    if isinstance(arg, ssl.SSLContext):
        return arg
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def connect_socket(
        *,
        unix_sock: str | None = None,
        sock: socket.socket | None = None,
        host: str | None = None,
        port: int = 5432,
        timeout: float | None = None,
        source_address: tuple[str, int] | None = None,
        tcp_keepalive: bool = True,
) -> socket.socket:
    if unix_sock is not None:
        if sock is not None:
            raise InterfaceError('If unix_sock is provided, sock must be None')

        if not hasattr(socket, 'AF_UNIX'):
            raise InterfaceError('attempt to connect to unix socket on unsupported platform')

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            sock.settimeout(timeout)
            sock.connect(unix_sock)
            if tcp_keepalive:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except OSError as e:
            sock.close()
            raise InterfaceError('communication error') from e
        return sock

    elif sock is not None:
        return sock

    elif host is not None:
        try:
            sock = socket.create_connection((host, port), timeout, source_address)
        except OSError as e:
            raise InterfaceError(
                f"Can't create a connection to host {host} and port {port} "
                f"(timeout is {timeout} and source_address is {source_address}).",
            ) from e

        if tcp_keepalive:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        return sock

    else:
        raise InterfaceError('one of host, sock or unix_sock must be provided')
