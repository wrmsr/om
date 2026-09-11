"""
Answering the peer's requests: a dispatcher maps a request to a result or an exception.

A handler signals a specific error response by raising JsonrpcMethodError. Any other exception is answered with a
generic Internal Error so that no details leak to the peer; the connection logs it.

The dict-based dispatchers bind params to the callable's signature: an object binds by name, an array by position, and
a binding failure is answered with Invalid Params rather than being mistaken for an error inside the handler.
"""
import abc
import inspect
import typing as ta

from ... import dataclasses as dc
from ... import lang
from .errors import JsonrpcErrorResponseError
from .errors import JsonrpcMethodError
from .errors import KnownErrors
from .types import Error
from .types import NotSpecified
from .types import Request


##


@dc.dataclass(frozen=True)
class JsonrpcDispatchContext:
    """Handed to handlers registered with `with_context`, giving them the connection to notify or call back on."""

    connection: ta.Any
    request: Request


class JsonrpcDispatcher(lang.Abstract):
    @abc.abstractmethod
    def dispatch(self, connection: ta.Any, request: Request) -> ta.Any:
        raise NotImplementedError


class AsyncJsonrpcDispatcher(lang.Abstract):
    @abc.abstractmethod
    def dispatch(self, connection: ta.Any, request: Request) -> ta.Awaitable[ta.Any]:
        raise NotImplementedError


##


@dc.dataclass(frozen=True)
class JsonrpcMethod:
    fn: ta.Callable[..., ta.Any]

    _: dc.KW_ONLY

    # Whether fn receives a JsonrpcDispatchContext as its first positional argument.
    with_context: bool = False

    @lang.cached_function
    def signature(self) -> inspect.Signature:
        return inspect.signature(self.fn)


JsonrpcMethodLike: ta.TypeAlias = JsonrpcMethod | ta.Callable[..., ta.Any]


def jsonrpc_method_of(obj: JsonrpcMethodLike) -> JsonrpcMethod:
    if isinstance(obj, JsonrpcMethod):
        return obj
    if callable(obj):
        return JsonrpcMethod(obj)
    raise TypeError(obj)


class BaseDictJsonrpcDispatcher(lang.Abstract):
    def __init__(self, methods: ta.Mapping[str, JsonrpcMethodLike] | None = None) -> None:
        super().__init__()

        self._methods: dict[str, JsonrpcMethod] = {}
        if methods:
            for name, m in methods.items():
                self.add(name, m)

    @property
    def methods(self) -> ta.Mapping[str, JsonrpcMethod]:
        return self._methods

    def add(self, name: str, method: JsonrpcMethodLike) -> None:
        if name in self._methods:
            raise KeyError(f'method already registered: {name!r}')
        self._methods[name] = jsonrpc_method_of(method)

    #

    def _bind(
            self,
            connection: ta.Any,
            request: Request,
    ) -> tuple[JsonrpcMethod, tuple[ta.Any, ...], dict[str, ta.Any]]:
        try:
            m = self._methods[request.method]
        except KeyError:
            raise JsonrpcMethodError(KnownErrors.METHOD_NOT_FOUND, data=request.method) from None

        args: tuple[ta.Any, ...] = ()
        kwargs: dict[str, ta.Any] = {}
        if m.with_context:
            args = (JsonrpcDispatchContext(connection, request),)

        params = request.params
        if params is None:
            pass
        elif isinstance(params, ta.Mapping):
            kwargs = dict(params)
        else:
            args = (*args, *params)

        try:
            m.signature().bind(*args, **kwargs)
        except TypeError as e:
            raise JsonrpcMethodError(KnownErrors.INVALID_PARAMS, data=str(e)) from e

        return m, args, kwargs


class DictJsonrpcDispatcher(BaseDictJsonrpcDispatcher, JsonrpcDispatcher):
    def dispatch(self, connection: ta.Any, request: Request) -> ta.Any:
        m, args, kwargs = self._bind(connection, request)
        return m.fn(*args, **kwargs)


class AsyncDictJsonrpcDispatcher(BaseDictJsonrpcDispatcher, AsyncJsonrpcDispatcher):
    """Methods may be coroutine functions or plain functions; a plain function's result is returned as-is."""

    async def dispatch(self, connection: ta.Any, request: Request) -> ta.Any:
        m, args, kwargs = self._bind(connection, request)
        ret = m.fn(*args, **kwargs)
        if inspect.isawaitable(ret):
            ret = await ret
        return ret


##


def jsonrpc_error_for_exception(exc: BaseException, *, include_details: bool = False) -> Error:
    """
    The error object answering a request whose handler raised.

    Handlers raise JsonrpcErrorResponseError subclasses to control the response; anything else is an internal error
    whose details are withheld unless explicitly asked for.
    """

    if isinstance(exc, JsonrpcErrorResponseError):
        return exc.error

    return KnownErrors.INTERNAL_ERROR.to_error(
        data=repr(exc) if include_details else NotSpecified,
    )
