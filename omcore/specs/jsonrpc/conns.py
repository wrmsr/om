"""
The connection interfaces: what a host sees of a JSON-RPC peer regardless of which transport or driver powers it.

Both interfaces are symmetric, as the protocol is: a connection sends requests and notifications and, if a dispatcher
is installed, answers the peer's. The client / server distinction is only in who connected to whom.
"""
import abc
import typing as ta

from ... import lang
from .types import NotSpecified
from .types import Params


##


class JsonrpcConnection(lang.Abstract):
    @abc.abstractmethod
    def request(
            self,
            method: str,
            params: Params | None = None,
            *,
            timeout_s: float | None | type[NotSpecified] = NotSpecified,
    ) -> ta.Any:
        """
        Send a request and return its result, raising JsonrpcRemoteError if the peer answers with an error and
        JsonrpcTimeoutError or JsonrpcConnectionClosedError if it never answers.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def notify(self, method: str, params: Params | None = None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def close(self, *, graceful: bool = True) -> None:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_closed(self) -> bool:
        raise NotImplementedError


class AsyncJsonrpcConnection(lang.Abstract):
    @abc.abstractmethod
    def request(
            self,
            method: str,
            params: Params | None = None,
            *,
            timeout_s: float | None | type[NotSpecified] = NotSpecified,
    ) -> ta.Awaitable[ta.Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def notify(self, method: str, params: Params | None = None) -> ta.Awaitable[None]:
        raise NotImplementedError

    @abc.abstractmethod
    def close(self, *, graceful: bool = True) -> ta.Awaitable[None]:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_closed(self) -> bool:
        raise NotImplementedError
