"""
The application-facing socket capabilities. Each pattern is a separate interface, so no socket offers an operation it
cannot perform.

A successful send means local acceptance under the operation's policy - not transmission, receipt, or processing.
Receives deliver whole messages; a receive cancelled before it returns leaves its message available. Only one receive
may be outstanding per socket.

Timeouts are in seconds: `None` uses the socket's configured default, and `math.inf` waits without a deadline.
"""
import abc
import types
import typing as ta

from omcore import lang

from .addresses import Address
from .addresses import AnyAddress
from .messages import Message
from .messages import RoutedMessage


##


class Attachment(lang.Abstract):
    """A bind or connect on a socket. Closing it stops listening or reconnecting; it is not a delivery barrier."""

    @property
    @abc.abstractmethod
    def address(self) -> Address:
        """The bound address, with any ephemeral port resolved, or the address connected to."""

        raise NotImplementedError

    @abc.abstractmethod
    def aclose(self) -> ta.Awaitable[None]:
        raise NotImplementedError


class Socket(lang.Abstract):
    @abc.abstractmethod
    def bind(self, address: AnyAddress) -> ta.Awaitable[Attachment]:
        """Completes when the listener exists."""

        raise NotImplementedError

    @abc.abstractmethod
    def connect(self, address: AnyAddress) -> ta.Awaitable[Attachment]:
        """Completes when the connection intent is registered, not when a peer is connected or ready."""

        raise NotImplementedError

    @abc.abstractmethod
    def aclose(self) -> ta.Awaitable[None]:
        """Abortively close the socket: fail waiters, stop attachments, and discard unsent and unreceived messages."""

        raise NotImplementedError

    async def __aenter__(self) -> ta.Self:
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_val: BaseException | None,
            exc_tb: types.TracebackType | None,
    ) -> None:
        await self.aclose()


class Publisher(Socket, lang.Abstract):
    @abc.abstractmethod
    def send(self, message: Message) -> ta.Awaitable[None]:
        """Publish to matching subscribers without waiting for any: a subscriber without capacity misses it."""

        raise NotImplementedError


class Subscriber(Socket, lang.Abstract):
    @abc.abstractmethod
    def subscribe(self, prefix: bytes) -> ta.Awaitable[None]:
        """Add a reference to a first-frame prefix subscription. The empty prefix matches everything."""

        raise NotImplementedError

    @abc.abstractmethod
    def unsubscribe(self, prefix: bytes) -> ta.Awaitable[None]:
        """Remove a reference added by subscribe; unsubscribing an absent prefix does nothing."""

        raise NotImplementedError

    @abc.abstractmethod
    def recv(self, *, timeout: float | None = None) -> ta.Awaitable[Message]:
        raise NotImplementedError


class Dealer(Socket, lang.Abstract):
    @abc.abstractmethod
    def send(self, message: Message, *, timeout: float | None = None) -> ta.Awaitable[None]:
        """Wait for a ready peer with capacity, chosen round robin, and queue the message to it."""

        raise NotImplementedError

    @abc.abstractmethod
    def recv(self, *, timeout: float | None = None) -> ta.Awaitable[Message]:
        raise NotImplementedError


class Router(Socket, lang.Abstract):
    @abc.abstractmethod
    def send(self, route: bytes, message: Message) -> ta.Awaitable[None]:
        """
        Queue a message to the peer with the given route without waiting. Raises UnroutableError for an unknown route
        and WouldBlockError for a known route without capacity.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def recv(self, *, timeout: float | None = None) -> ta.Awaitable[RoutedMessage]:
        raise NotImplementedError
