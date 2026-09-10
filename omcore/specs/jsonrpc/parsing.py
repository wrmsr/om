"""
Strict, marshal-free conversion between JSON values and JSON-RPC message objects.

The lenient `parse_payload` / `loads_payload` functions never raise on bad input: anything which is not a valid message
comes back as an `InvalidMessage` carrying the error response the spec says it must be answered with. This is what a
connection wants, as a malformed message from a peer is a protocol event rather than a local bug. The strict
`parse_message` function raises instead, for callers which know their input is supposed to be well-formed.

Numbers: JSON has no integer/float distinction but python does, and `bool` is a subclass of `int`. Ids and error codes
reject bools explicitly, and ids accept floats as the spec allows (while discouraging) them.
"""
import math
import typing as ta

from ... import dataclasses as dc
from ... import lang
from ...formats.json import all as json
from .errors import JsonrpcInvalidMessageError
from .errors import KnownErrors
from .types import VERSION
from .types import Batch
from .types import Error
from .types import Id
from .types import InvalidMessage
from .types import Message
from .types import NotSpecified
from .types import Payload
from .types import Request
from .types import Response


##


@dc.dataclass(frozen=True, kw_only=True)
class ParseOptions:
    """
    Knobs for how strictly received messages are validated.

    `require_version` demands the `jsonrpc: "2.0"` member. Some dialects omit it, though all of the ones currently in
    use include it. `allow_null_request_id` accepts a request whose id is JSON null, which the spec permits but which is
    indistinguishable in its response from an error answering an unparseable message, so peers are within their rights
    to refuse it.
    """

    require_version: bool = True
    allow_null_request_id: bool = True

    DEFAULT: ta.ClassVar[ParseOptions]


ParseOptions.DEFAULT = ParseOptions()


##


def _is_valid_id(v: ta.Any) -> bool:
    # bool is an int subclass and must be excluded explicitly.
    return v is None or (isinstance(v, (str, int, float)) and not isinstance(v, bool))


def _detect_id(obj: ta.Mapping[str, ta.Any]) -> Id:
    """Best-effort id extraction for error responses: the id if present and valid, else null."""

    try:
        v = obj['id']
    except KeyError:
        return None
    if not _is_valid_id(v):
        return None
    return v


def _parse_error(v: ta.Any) -> Error:
    if not isinstance(v, dict):
        raise JsonrpcInvalidMessageError('error must be an object', looks_like_response=True)

    try:
        code = v['code']
    except KeyError:
        raise JsonrpcInvalidMessageError('error is missing code', looks_like_response=True) from None
    if not isinstance(code, int) or isinstance(code, bool):
        raise JsonrpcInvalidMessageError('error code must be an integer', looks_like_response=True)

    try:
        message = v['message']
    except KeyError:
        raise JsonrpcInvalidMessageError('error is missing message', looks_like_response=True) from None
    if not isinstance(message, str):
        raise JsonrpcInvalidMessageError('error message must be a string', looks_like_response=True)

    data: ta.Any = v.get('data', NotSpecified)

    return Error(code, message, data)


def parse_message(
        obj: ta.Any,
        opts: ParseOptions = ParseOptions.DEFAULT,
) -> Message:
    """Parse a single JSON object as a Request or Response, raising JsonrpcInvalidMessageError if it is neither."""

    if not isinstance(obj, dict):
        raise JsonrpcInvalidMessageError(f'message must be an object, not {type(obj).__name__}')

    if opts.require_version:
        version = obj.get('jsonrpc')
        if version != VERSION:
            raise JsonrpcInvalidMessageError(
                f'unsupported jsonrpc version: {version!r}',
                id=_detect_id(obj),
                looks_like_response='method' not in obj and ('result' in obj or 'error' in obj),
            )

    if 'method' in obj:
        method = obj['method']
        if not isinstance(method, str):
            raise JsonrpcInvalidMessageError('method must be a string', id=_detect_id(obj))

        params: ta.Any = obj.get('params')
        if params is not None and not isinstance(params, (dict, list)):
            raise JsonrpcInvalidMessageError('params must be an object or an array', id=_detect_id(obj))

        id: ta.Any  # noqa
        if 'id' in obj:
            id = obj['id']  # noqa
            if not _is_valid_id(id):
                raise JsonrpcInvalidMessageError('id must be a string, number, or null')
            if id is None and not opts.allow_null_request_id:
                raise JsonrpcInvalidMessageError('null request ids are not accepted')
        else:
            id = NotSpecified  # noqa

        return Request(id, method, params)

    #

    has_result = 'result' in obj
    has_error = 'error' in obj

    if not (has_result or has_error):
        # Neither a request nor a response - most likely a request which lost its method.
        raise JsonrpcInvalidMessageError('message has no method, result, or error', id=_detect_id(obj))

    if has_result and has_error:
        raise JsonrpcInvalidMessageError(
            'response has both result and error',
            id=_detect_id(obj),
            looks_like_response=True,
        )

    try:
        id = obj['id']  # noqa
    except KeyError:
        raise JsonrpcInvalidMessageError('response is missing id', looks_like_response=True) from None
    if not _is_valid_id(id):
        raise JsonrpcInvalidMessageError('id must be a string, number, or null', looks_like_response=True)

    if has_error:
        error = _parse_error(obj['error'])
        return Response(id, error=error)

    return Response(id, result=obj['result'])


##


def _invalid_message(obj: ta.Any, exc: JsonrpcInvalidMessageError) -> InvalidMessage:
    return InvalidMessage(
        KnownErrors.INVALID_REQUEST.to_error(),
        id=exc.id,
        raw=obj,
        exc=exc,
        looks_like_response=exc.looks_like_response,
    )


def parse_item(
        obj: ta.Any,
        opts: ParseOptions = ParseOptions.DEFAULT,
) -> Message | InvalidMessage:
    """Parse one message leniently, returning an InvalidMessage rather than raising."""

    try:
        return parse_message(obj, opts)
    except JsonrpcInvalidMessageError as e:
        return _invalid_message(obj, e)


def parse_payload(
        obj: ta.Any,
        opts: ParseOptions = ParseOptions.DEFAULT,
) -> Payload:
    """
    Parse a decoded JSON value as a message or a batch, leniently.

    Per the spec an empty array is answered with a single Invalid Request response rather than an empty batch, and each
    non-object element of a non-empty array is answered with its own Invalid Request response within the batch.
    """

    if isinstance(obj, list):
        if not obj:
            return InvalidMessage(
                KnownErrors.INVALID_REQUEST.to_error(),
                raw=obj,
                exc=JsonrpcInvalidMessageError('empty batch'),
            )

        return Batch([parse_item(item, opts) for item in obj])

    return parse_item(obj, opts)


def loads_payload(
        s: str | bytes | bytearray | memoryview,
        opts: ParseOptions = ParseOptions.DEFAULT,
) -> Payload:
    """Decode JSON text and parse it leniently, mapping decoding failures to a Parse Error InvalidMessage."""

    if isinstance(s, memoryview):
        s = s.tobytes()

    try:
        obj = json.loads(s)
    except (ValueError, UnicodeDecodeError) as e:
        return InvalidMessage(
            KnownErrors.PARSE_ERROR.to_error(),
            raw=s,
            exc=e,
        )

    return parse_payload(obj, opts)


##


def dump_error(error: Error) -> dict[str, ta.Any]:
    dct: dict[str, ta.Any] = {
        'code': error.code,
        'message': error.message,
    }
    if error.data is not NotSpecified:
        dct['data'] = error.data
    return dct


def dump_message(msg: Message | InvalidMessage) -> dict[str, ta.Any]:
    """Render a message as a JSON-compatible dict. An InvalidMessage renders as the error response answering it."""

    if isinstance(msg, Request):
        dct: dict[str, ta.Any] = {
            'jsonrpc': VERSION,
            'method': msg.method,
        }
        if (params := msg.params) is not None:
            # Backends differ on which abstract containers they accept, so normalize the top level.
            if isinstance(params, ta.Mapping):
                params = dict(params)
            elif isinstance(params, (str, bytes)):
                raise TypeError('params must be an object or an array')
            else:
                params = list(params)
            dct['params'] = params
        if not msg.is_notification:
            dct['id'] = msg.id
        return dct

    elif isinstance(msg, InvalidMessage):
        msg = msg.to_response()

    if isinstance(msg, Response):
        dct = {
            'jsonrpc': VERSION,
        }
        if msg.is_error:
            dct['error'] = dump_error(ta.cast(Error, msg.error))
        else:
            dct['result'] = msg.result
        dct['id'] = msg.id
        return dct

    raise TypeError(msg)


def dump_payload(payload: Payload) -> dict[str, ta.Any] | list[dict[str, ta.Any]]:
    if isinstance(payload, Batch):
        return [dump_message(m) for m in payload.items]
    return dump_message(payload)


def _check_json_value(obj: ta.Any, seen: set[int]) -> None:
    """
    Reject values which are not representable in standard JSON.

    Non-finite floats have no JSON representation and the available backends disagree on what to do with them, so they
    are refused up front, as are circular references. Leaf types are otherwise left to the backend to accept or reject.
    """

    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError(f'non-finite float is not JSON representable: {obj!r}')

    elif isinstance(obj, (str, bytes, bytearray)):
        pass

    elif isinstance(obj, ta.Mapping):
        if id(obj) in seen:
            raise ValueError('circular reference')
        seen.add(id(obj))
        for k, v in obj.items():
            if not isinstance(k, str):
                raise TypeError(f'JSON object keys must be strings, not {type(k).__name__}')
            _check_json_value(v, seen)
        seen.discard(id(obj))

    elif isinstance(obj, ta.Sequence):
        if id(obj) in seen:
            raise ValueError('circular reference')
        seen.add(id(obj))
        for v in obj:
            _check_json_value(v, seen)
        seen.discard(id(obj))


def dumps_payload(payload: Payload) -> str:
    """
    Render a payload as compact JSON text, which is guaranteed to contain no raw newlines.

    Raises TypeError or ValueError if the payload contains values which cannot be represented in JSON.
    """

    obj = dump_payload(payload)
    _check_json_value(obj, set())
    return json.dumps_compact(obj)


##


class Payloads(lang.Namespace):
    """Small helpers over the parse / dump functions."""

    @staticmethod
    def is_notification_only(payload: Payload) -> bool:
        """True if nothing in the payload calls for a response: a lone notification, or a batch of nothing but."""

        if isinstance(payload, Batch):
            return all(isinstance(m, Request) and m.is_notification for m in payload.items)
        return isinstance(payload, Request) and payload.is_notification
