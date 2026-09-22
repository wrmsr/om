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
