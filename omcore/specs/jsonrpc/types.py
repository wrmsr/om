"""
https://www.jsonrpc.org/specification

TODO:
 - drop NotSpecified, use lang.Maybe, make marshal do that

See:
 - https://github.com/python-lsp/python-lsp-jsonrpc
"""
import operator
import types
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang
from ... import marshal as msh


T = ta.TypeVar('T')

NUMBER_TYPES: tuple[type, ...] = (int, float)
Number: ta.TypeAlias = int | float

Object: ta.TypeAlias = ta.Mapping[str, ta.Any]

# Params may be by-name (an object) or by-position (an array).
Params: ta.TypeAlias = Object | ta.Sequence[ta.Any]

ID_TYPES: tuple[type, ...] = (str, *NUMBER_TYPES, types.NoneType)
Id: ta.TypeAlias = str | Number | None


##


VERSION = '2.0'


##


class NotSpecified(lang.Marker):
    pass


def is_not_specified(v: ta.Any) -> bool:
    return v is NotSpecified


def check_not_not_specified(v: T | type[NotSpecified]) -> T:
    check.arg(not is_not_specified(v))
    return ta.cast(T, v)


##


@dc.dataclass(frozen=True)
@msh.update_field_options('id', omit_if=is_not_specified, default=lang.just(NotSpecified))
@msh.update_field_options(
    'params',
    omit_if=operator.not_,
    # Params are raw JSON values (an object or an array) and are passed through marshaling untouched.
    marshal_via=msh.MarshalVia(ta.Any),
    unmarshal_via=msh.UnmarshalVia(ta.Any),
)
class Request(lang.Final):
    id: Id | type[NotSpecified]

    @property
    def is_notification(self) -> bool:
        return self.id is NotSpecified

    def id_value(self) -> Id:
        return check.isinstance(self.id, ID_TYPES)

    method: str
    params: Params | None = None

    jsonrpc: str = dc.field(default=VERSION, kw_only=True)
    dc.validate(lambda self: self.jsonrpc == VERSION)


def request(id: Id, method: str, params: Params | None = None) -> Request:  # noqa
    return Request(id, method, params)


def notification(method: str, params: Params | None = None) -> Request:
    return Request(NotSpecified, method, params)


##


@dc.dataclass(frozen=True)
@msh.update_field_options(['result', 'error'], omit_if=is_not_specified)
class Response(lang.Final):
    id: Id
    dc.validate(lambda self: self.id is not NotSpecified)

    _: dc.KW_ONLY

    #

    result: ta.Any = dc.field(default=NotSpecified)
    error: Error | type[NotSpecified] = dc.field(default=NotSpecified)
    dc.validate(lambda self: is_not_specified(self.result) ^ is_not_specified(self.error))

    @property
    def is_result(self) -> bool:
        return not is_not_specified(self.result)

    @property
    def is_error(self) -> bool:
        return not is_not_specified(self.error)

    #

    jsonrpc: str = dc.field(default=VERSION)
    dc.validate(lambda self: self.jsonrpc == VERSION)


def result(id: Id, result: ta.Any) -> Response:  # noqa
    return Response(id, result=result)


##


@dc.dataclass(frozen=True)
@msh.update_field_options('data', omit_if=is_not_specified)
class Error(lang.Final):
    code: int
    message: str
    data: ta.Any = NotSpecified


def error(id: Id, error: Error) -> Response:  # noqa
    return Response(id, error=error)


##


Message: ta.TypeAlias = Request | Response


def detect_message_type(dct: ta.Mapping[str, ta.Any]) -> type[Message]:
    if 'method' in dct:
        return Request
    else:
        return Response


##


@dc.dataclass(frozen=True)
class InvalidMessage(lang.Final):
    """
    A received value which could not be parsed as a message, along with the error to answer it with.

    Per the spec, an unparseable or malformed request is answered with a Parse Error or Invalid Request response whose
    id is that of the offending request if it could be determined and null otherwise. Values which look like malformed
    responses rather than requests are flagged as such so peers do not answer responses with responses.
    """

    error: Error

    _: dc.KW_ONLY

    id: Id = None

    raw: ta.Any = dc.field(default=None, repr=False)
    exc: Exception | None = dc.field(default=None, repr=False)

    looks_like_response: bool = False

    def to_response(self) -> Response:
        return Response(self.id, error=self.error)


@dc.dataclass(frozen=True)
class Batch(lang.Final):
    """A JSON-RPC batch: an array of messages sent or received as one payload."""

    items: ta.Sequence[Message | InvalidMessage]
    dc.validate(lambda self: all(isinstance(i, (Request, Response, InvalidMessage)) for i in self.items))

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self) -> ta.Iterator[Message | InvalidMessage]:
        return iter(self.items)


# Everything a single wire frame may decode to, and everything which may be encoded to a single wire frame.
Payload: ta.TypeAlias = Message | InvalidMessage | Batch
