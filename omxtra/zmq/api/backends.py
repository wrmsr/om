import abc
import types
import typing as ta

from omcore import lang

from .configs import SocketConfig
from .sockets import Dealer
from .sockets import Publisher
from .sockets import Router
from .sockets import Subscriber


##


class Backend(lang.Abstract):
    """
    Creates sockets and owns them: closing the backend closes every socket it created. Sockets are bound to the event
    loop they were created on and are not thread-safe.
    """

    @abc.abstractmethod
    def create_publisher(self, config: SocketConfig | None = None) -> Publisher:
        raise NotImplementedError

    @abc.abstractmethod
    def create_subscriber(self, config: SocketConfig | None = None) -> Subscriber:
        raise NotImplementedError

    @abc.abstractmethod
    def create_dealer(
            self,
            config: SocketConfig | None = None,
            *,
            routing_id: bytes | None = None,
    ) -> Dealer:
        raise NotImplementedError

    @abc.abstractmethod
    def create_router(
            self,
            config: SocketConfig | None = None,
            *,
            routing_id: bytes | None = None,
    ) -> Router:
        raise NotImplementedError

    @abc.abstractmethod
    def aclose(self) -> ta.Awaitable[None]:
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
