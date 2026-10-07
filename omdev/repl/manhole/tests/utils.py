"""A blocking socket client with deadlines, for talking to a running manhole from a test."""
import socket
import time

from ..base import Address
from ..base import TcpAddress
from ..base import UnixAddress


##


class Client:
    def __init__(self, address: Address | None, *, timeout_s: float = 10.) -> None:
        super().__init__()

        if address is None:
            raise ValueError('Not listening')
        self.timeout_s = timeout_s
        if isinstance(address, UnixAddress):
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(address.path)
        elif isinstance(address, TcpAddress):
            self.sock = socket.create_connection((address.host, address.port))
        else:
            raise TypeError(address)
        self.sock.settimeout(.2)
        self.buf = b''

    def close(self) -> None:
        self.sock.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def send(self, data: str | bytes) -> None:
        self.sock.sendall(data.encode('utf-8') if isinstance(data, str) else data)

    def read_until(self, marker: bytes, *, timeout_s: float | None = None) -> bytes:
        """Everything received up to and including the next `marker`."""

        deadline = time.monotonic() + (self.timeout_s if timeout_s is None else timeout_s)
        while True:
            if (i := self.buf.find(marker)) >= 0:
                out, self.buf = self.buf[:i + len(marker)], self.buf[i + len(marker):]
                return out
            if time.monotonic() >= deadline:
                raise TimeoutError(f'waiting for {marker!r}; have {self.buf!r}')
            try:
                data = self.sock.recv(65536)
            except TimeoutError:
                continue
            if not data:
                raise EOFError(f'closed while waiting for {marker!r}; have {self.buf!r}')
            self.buf += data

    def read_eof(self, *, timeout_s: float | None = None) -> bytes:
        deadline = time.monotonic() + (self.timeout_s if timeout_s is None else timeout_s)
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError(f'waiting for eof; have {self.buf!r}')
            try:
                data = self.sock.recv(65536)
            except TimeoutError:
                continue
            if not data:
                out, self.buf = self.buf, b''
                return out
            self.buf += data

    def prompt(self) -> bytes:
        return self.read_until(b'>>> ')

    def ask(self, line: str) -> str:
        """Send a line and return what came back before the next python prompt."""

        self.send(line + '\n')
        return self.prompt()[:-len(b'>>> ')].decode('utf-8')
