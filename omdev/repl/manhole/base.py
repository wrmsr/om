"""
The manhole's loop-neutral interfaces: where it listens, what a connection is, and what a server does. The protocol
(`protocol.py`) and the manhole proper (`server.py`) are written against these alone; `asyncio.py` implements them over
asyncio streams, `sync.py` over blocking sockets.
"""
import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


##


@dc.dataclass(frozen=True)
class UnixAddress(lang.Final):
    path: str

    _: dc.KW_ONLY

    mode: int = 0o600  # the socket file's permissions - who may connect, so by default only the owning user
    unlink_existing: bool = True

    def __str__(self) -> str:
        return self.path


@dc.dataclass(frozen=True)
class TcpAddress(lang.Final):
    host: str = '127.0.0.1'  # loopback unless told otherwise: there is no authentication
    port: int = 0            # 0 binds an ephemeral port; the bound address reports which

    def __str__(self) -> str:
        return f'{self.host}:{self.port}'


Address: ta.TypeAlias = UnixAddress | TcpAddress


def parse_address(s: str) -> Address:
    """`host:port` or `:port` for tcp; anything else is a unix socket path."""

    if s.startswith(':') and s[1:].isdigit():
        return TcpAddress(port=int(s[1:]))
    host, sep, port = s.rpartition(':')
    if sep and port.isdigit() and '/' not in host:
        return TcpAddress(host=host or '127.0.0.1', port=int(port))
    return UnixAddress(s)


##


class Connection(lang.Abstract):
    @property
    @abc.abstractmethod
    def peer(self) -> str:
        """A description of the other end, for logs."""

        raise NotImplementedError

    @abc.abstractmethod
    def read_line(self) -> ta.Awaitable[str | None]:
        """The next line without its line ending, or None at the end of input."""

        raise NotImplementedError

    @abc.abstractmethod
    def post(self, text: str) -> None:
        """
        Queue text to send, in order, without waiting. Thread-safe: the one way output reaches a connection from
        wherever the code producing it happens to run.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def drain(self) -> ta.Awaitable[None]:
        """Wait for what was posted to have been sent, as far as the transport will say."""

        raise NotImplementedError

    async def write(self, text: str) -> None:
        self.post(text)
        await self.drain()

    @abc.abstractmethod
    def aclose(self) -> ta.Awaitable[None]:
        """Send what was posted and close. Idempotent."""

        raise NotImplementedError


ConnectionHandler: ta.TypeAlias = ta.Callable[[Connection], ta.Awaitable[None]]


##


class ManholeServer(lang.Abstract):
    """Listens at an address and runs the handler once per connection, each in its own context."""

    @property
    @abc.abstractmethod
    def address(self) -> Address | None:
        """The bound address once started - a tcp one with its actual port - else None."""

        raise NotImplementedError

    @property
    @abc.abstractmethod
    def num_connections(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def start(self) -> ta.Awaitable[None]:
        """Bind, listen, and begin accepting; returns once listening."""

        raise NotImplementedError

    @abc.abstractmethod
    def stop(self) -> ta.Awaitable[None]:
        """Stop accepting, close every connection, and wait for their handlers. Idempotent."""

        raise NotImplementedError

    async def __aenter__(self) -> ta.Self:
        await self.start()
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.stop()
