"""
A client for the line protocol, for when `nc -U` or `socat` are not to hand: stdin to the socket, the socket to stdout,
until either end closes. Plain blocking sockets and `selectors`; no loop.
"""
import os
import selectors
import socket
import sys
import typing as ta

from .base import Address
from .base import TcpAddress
from .base import UnixAddress


##


def connect(address: Address) -> socket.socket:
    if isinstance(address, UnixAddress):
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(address.path)
        return sock
    if isinstance(address, TcpAddress):
        return socket.create_connection((address.host, address.port))
    raise TypeError(address)


def run_client(
        address: Address,
        *,
        stdin_fd: int | None = None,
        stdout: ta.BinaryIO | None = None,
) -> None:
    """Relay until the server closes, or until stdin ends and the server has said its last."""

    in_fd = sys.stdin.fileno() if stdin_fd is None else stdin_fd
    out = sys.stdout.buffer if stdout is None else stdout

    sock = connect(address)
    try:
        with selectors.DefaultSelector() as sel:
            sel.register(sock, selectors.EVENT_READ)
            sel.register(in_fd, selectors.EVENT_READ)
            stdin_open = True

            while True:
                for key, _ in sel.select():
                    if key.fileobj is sock:
                        data = sock.recv(65536)
                        if not data:
                            return
                        out.write(data)
                        out.flush()

                    elif stdin_open:
                        data = os.read(in_fd, 65536)
                        if not data:
                            # Our side is done talking; the server sees the end of input and closes in turn.
                            stdin_open = False
                            sel.unregister(in_fd)
                            sock.shutdown(socket.SHUT_WR)
                        else:
                            sock.sendall(data)
    finally:
        sock.close()
