# ruff: noqa: UP006 UP007 UP045
import abc
import typing as ta

from omcore.lite.abstract import Abstract

from .errors import RpcMethodNotFoundError


if ta.TYPE_CHECKING:
    from .messages import RpcNotificationMessage


RpcMethod = ta.Callable[[ta.Any], ta.Awaitable[ta.Any]]  # ta.TypeAlias
RpcNotificationErrorHandler = ta.Callable[['RpcNotificationMessage', BaseException], None]  # ta.TypeAlias
RpcInlineNotificationHandler = ta.Callable[[str, ta.Any], None]  # ta.TypeAlias


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


class RpcNotificationRouter(RpcHandler):
    """
    The handler for an endpoint which only ever receives notifications: each is applied inline, in wire order, by the
    callback routed for its method, and anything unrouted, calls included, is rejected as not found. Routes may be
    added after the peer is built, so whatever applies a method can itself be built on that peer.
    """

    def __init__(self) -> None:
        super().__init__()

        self._routes: ta.Dict[str, RpcInlineNotificationHandler] = {}

    def add_routes(self, methods: ta.Iterable[str], handler: RpcInlineNotificationHandler) -> None:
        for method in methods:
            if method in self._routes:
                raise ValueError(f'RPC notification method is already routed: {method!r}')
            self._routes[method] = handler

    def handle_notification_inline(self, method: str, params: ta.Any) -> bool:
        if (handler := self._routes.get(method)) is None:
            return False
        handler(method, params)
        return True

    async def handle(self, method: str, params: ta.Any) -> ta.Any:
        raise RpcMethodNotFoundError(method)
