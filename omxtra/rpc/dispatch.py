# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
What a connection dispatches inbound requests and notifications to.

Handlers are async-colored like everything above the pipeline: a sync runtime drives them with `sync_await`, so a
handler used under one must never actually suspend. `rpc_async_method` wraps a plain callable for use in a method
table.

The table handler is deliberately a plain mapping from method name to callable - no reflection, no signature binding,
no object facades. Concerns compose by merging their tables, with duplicate names rejected at composition time.
"""
import abc
import functools
import typing as ta

from omcore.lite.abstract import Abstract
from omcore.logs.modules import get_module_logger

from .errors import RpcMethodNotFoundError


T = ta.TypeVar('T')

RpcMethodFn = ta.Callable[[ta.Any], ta.Awaitable[ta.Any]]  # ta.TypeAlias  # params -> result
RpcInlineNotificationFn = ta.Callable[[ta.Any], None]  # ta.TypeAlias  # params -> None


log = get_module_logger(globals())  # noqa


##


class RpcHandler(Abstract):
    """
    Requests are answered by `handle_request`; its result is sent back as-is and any exception it raises is sent back
    as an error. Raise `RpcMethodNotFoundError` for an unknown method.

    Notifications are first offered to `handle_notification_inline`, which runs synchronously on the connection's pump
    in wire order: anything the peer sent after the notification, such as the reply to a later request, is seen only
    once it has been applied. This is how ordered streams are pushed. Returning False hands the notification to
    `handle_notification`, which the connection runs however it runs request handlers.
    """

    @abc.abstractmethod
    async def handle_request(self, method: str, params: ta.Any) -> ta.Any:
        raise NotImplementedError

    def handle_notification_inline(self, method: str, params: ta.Any) -> bool:
        return False

    async def handle_notification(self, method: str, params: ta.Any) -> None:
        log.debug('Dropping unhandled notification: %r', method)


##


def rpc_merge_method_tables(*tables: ta.Mapping[str, T]) -> ta.Dict[str, T]:
    """Merges method tables, rejecting a name present in more than one."""

    out: ta.Dict[str, T] = {}
    for table in tables:
        for name, fn in table.items():
            if name in out:
                raise ValueError(f'duplicate rpc method: {name!r}')
            out[name] = fn
    return out


def rpc_async_method(fn: ta.Callable[[ta.Any], ta.Any]) -> RpcMethodFn:
    """Wraps a plain callable as an async method table entry."""

    @functools.wraps(fn)
    async def inner(params: ta.Any) -> ta.Any:
        return fn(params)

    return inner


class RpcMethodTableHandler(RpcHandler):
    def __init__(
            self,
            methods: ta.Optional[ta.Mapping[str, RpcMethodFn]] = None,
            *,
            notifications: ta.Optional[ta.Mapping[str, RpcMethodFn]] = None,
            inline_notifications: ta.Optional[ta.Mapping[str, RpcInlineNotificationFn]] = None,
    ) -> None:
        super().__init__()

        self._methods: ta.Dict[str, RpcMethodFn] = dict(methods or {})
        self._notifications: ta.Dict[str, RpcMethodFn] = dict(notifications or {})
        self._inline_notifications: ta.Dict[str, RpcInlineNotificationFn] = dict(inline_notifications or {})

        if dup := set(self._notifications) & set(self._inline_notifications):
            raise ValueError(f'notification methods both inline and not: {sorted(dup)!r}')

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{len(self._methods)} methods>'

    @property
    def methods(self) -> ta.Mapping[str, RpcMethodFn]:
        return self._methods

    @property
    def notifications(self) -> ta.Mapping[str, RpcMethodFn]:
        return self._notifications

    @property
    def inline_notifications(self) -> ta.Mapping[str, RpcInlineNotificationFn]:
        return self._inline_notifications

    #

    def add_methods(self, methods: ta.Mapping[str, RpcMethodFn]) -> None:
        self._methods = rpc_merge_method_tables(self._methods, methods)

    def add_notifications(self, notifications: ta.Mapping[str, RpcMethodFn]) -> None:
        if dup := set(notifications) & set(self._inline_notifications):
            raise ValueError(f'notification methods both inline and not: {sorted(dup)!r}')
        self._notifications = rpc_merge_method_tables(self._notifications, notifications)

    def add_inline_notifications(self, notifications: ta.Mapping[str, RpcInlineNotificationFn]) -> None:
        if dup := set(notifications) & set(self._notifications):
            raise ValueError(f'notification methods both inline and not: {sorted(dup)!r}')
        self._inline_notifications = rpc_merge_method_tables(self._inline_notifications, notifications)

    #

    async def handle_request(self, method: str, params: ta.Any) -> ta.Any:
        try:
            fn = self._methods[method]
        except KeyError:
            raise RpcMethodNotFoundError(method) from None

        return await fn(params)

    def handle_notification_inline(self, method: str, params: ta.Any) -> bool:
        if (fn := self._inline_notifications.get(method)) is None:
            return False

        fn(params)
        return True

    async def handle_notification(self, method: str, params: ta.Any) -> None:
        if (fn := self._notifications.get(method)) is None:
            log.debug('Dropping unhandled notification: %r', method)
            return

        await fn(params)
