# ruff: noqa: UP006 UP007 UP045
import abc
import typing as ta

from omcore.lite.abstract import Abstract

from .errors import RpcMethodNotFoundError


if ta.TYPE_CHECKING:
    from .messages import RpcNotificationMessage


RpcMethod = ta.Callable[[ta.Any], ta.Awaitable[ta.Any]]  # ta.TypeAlias
RpcNotificationErrorHandler = ta.Callable[['RpcNotificationMessage', BaseException], None]  # ta.TypeAlias


##


class RpcHandler(Abstract):
    @abc.abstractmethod
    def handle(self, method: str, params: ta.Any) -> ta.Awaitable[ta.Any]:
        raise NotImplementedError

    def handle_notification_inline(self, method: str, params: ta.Any) -> bool:
        """
        Offers a notification to the handler synchronously, on the receive loop, in wire order - returning False to have
        it dispatched to `handle` in its own task instead. Handling inline is what makes the stream's order the delivery
        order: a notification handled here is fully applied before anything the other side sent after it is seen. An
        implementation must not block or suspend here, and an exception it raises is reported to the peer's notification
        error handler.
        """

        return False


class RpcMethodHandler(RpcHandler):
    def __init__(self, methods: ta.Mapping[str, RpcMethod]) -> None:
        super().__init__()

        self._methods = dict(methods)

    async def handle(self, method: str, params: ta.Any) -> ta.Any:
        try:
            fn = self._methods[method]
        except KeyError:
            raise RpcMethodNotFoundError(method) from None
        return await fn(params)
