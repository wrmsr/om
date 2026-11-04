# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
Typed calls and typed handlers, over a pluggable serde.

The connection speaks wire values - whatever the envelope codec's value codec carries. This layer converts between those
and typed objects, so concern code neither marshals by hand nor knows which marshaler is in use. The core knows no
marshaler at all: `RpcSerde` is two methods, with an identity implementation, an adapter over the lite marshaler here,
and an adapter over the standard `omcore.marshal` in `marshal.py` for standard code.

 - `rpc_typed_method` turns an async function of one typed argument into a method table entry.
 - `RpcTypedCaller` makes typed calls and notifications over a connection, optionally translating remote errors.

A sync function is made async with `omcore.lite.asyncs.as_async` before wrapping.
"""
import abc
import functools
import typing as ta

from ..lite.abstract import Abstract
from ..lite.marshal import OBJ_MARSHALER_MANAGER
from ..lite.marshal import ObjMarshalerManager
from .connection import RpcConnection
from .connection import RpcTimeoutArg
from .dispatch import RpcMethodFn
from .errors import RpcRemoteError
from .messages import RpcUnspecified


RpcErrorTranslator = ta.Callable[['RpcRemoteError'], BaseException]  # ta.TypeAlias


##


class RpcSerde(Abstract):
    @abc.abstractmethod
    def marshal(self, obj: ta.Any, ty: ta.Any = None) -> ta.Any:
        """An object to a wire value. A `ty` of None means the object's own type."""

        raise NotImplementedError

    @abc.abstractmethod
    def unmarshal(self, value: ta.Any, ty: ta.Any) -> ta.Any:
        raise NotImplementedError


class IdentityRpcSerde(RpcSerde):
    """Wire values are the objects: for concerns which already deal in plain values."""

    def marshal(self, obj: ta.Any, ty: ta.Any = None) -> ta.Any:
        return obj

    def unmarshal(self, value: ta.Any, ty: ta.Any) -> ta.Any:
        return value


class LiteMarshalRpcSerde(RpcSerde):
    """Over `omcore.lite.marshal`: the global manager by default, or a given one."""

    def __init__(self, manager: ta.Optional[ObjMarshalerManager] = None) -> None:
        super().__init__()

        self._manager = manager if manager is not None else OBJ_MARSHALER_MANAGER

    def marshal(self, obj: ta.Any, ty: ta.Any = None) -> ta.Any:
        return self._manager.marshal_obj(obj, ty)

    def unmarshal(self, value: ta.Any, ty: ta.Any) -> ta.Any:
        return self._manager.unmarshal_obj(value, ty)


##


def rpc_typed_method(
        fn: ta.Callable[..., ta.Awaitable[ta.Any]],
        params_type: ta.Any = None,
        result_type: ta.Any = None,
        *,
        serde: RpcSerde,
) -> RpcMethodFn:
    """
    A method table entry calling `fn` with its params unmarshaled as `params_type` and marshaling its result as
    `result_type`. With no `params_type`, `fn` takes no argument and any params sent are ignored. With no `result_type`
    the result is marshaled by its own type, and None goes out as None.
    """

    @functools.wraps(fn)
    async def inner(params: ta.Any) -> ta.Any:
        if params_type is None:
            result = await fn()
        else:
            result = await fn(serde.unmarshal(params, params_type))

        if result is None and result_type is None:
            return None
        return serde.marshal(result, result_type)

    return inner


class RpcTypedCaller:
    """
    Typed calls over a connection. `translate_error`, if given, maps each remote error to the exception actually raised
    - `translate_rpc_remote_builtin_error` from `translate.py`, say, or a concern's own.
    """

    def __init__(
            self,
            connection: RpcConnection,
            serde: RpcSerde,
            *,
            translate_error: ta.Optional[RpcErrorTranslator] = None,
    ) -> None:
        super().__init__()

        self._connection = connection
        self._serde = serde
        self._translate_error = translate_error

    @property
    def connection(self) -> RpcConnection:
        return self._connection

    @property
    def serde(self) -> RpcSerde:
        return self._serde

    def _marshal_params(self, params: ta.Any, params_type: ta.Any) -> ta.Any:
        if params is None:
            return None
        return self._serde.marshal(params, params_type)

    async def call(
            self,
            method: str,
            params: ta.Any = None,
            result_type: ta.Any = None,
            *,
            params_type: ta.Any = None,
            timeout_s: RpcTimeoutArg = RpcUnspecified,
    ) -> ta.Any:
        """Calls `method`, returning its result unmarshaled as `result_type`, or the raw wire value without one."""

        value = self._marshal_params(params, params_type)

        try:
            result = await self._connection.request(method, value, timeout_s=timeout_s)

        except RpcRemoteError as e:
            if (te := self._translate_error) is None:
                raise
            translated = te(e)
            if translated is e:
                raise
            raise translated from e

        if result_type is None or result is None:
            return result
        return self._serde.unmarshal(result, result_type)

    async def notify(
            self,
            method: str,
            params: ta.Any = None,
            *,
            params_type: ta.Any = None,
    ) -> None:
        await self._connection.notify(method, self._marshal_params(params, params_type))
