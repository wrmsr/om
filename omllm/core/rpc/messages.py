# ruff: noqa: UP006 UP007 UP045
import abc
import dataclasses as dc
import json
import typing as ta

from omcore.lite.abstract import Abstract
from omcore.lite.check import check
from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj

from .errors import RpcProtocolError
from .errors import RpcRemoteErrorData


##


@dc.dataclass(frozen=True)
class RpcRequestMessage:
    id: int
    method: str
    params: ta.Any = None

    def __post_init__(self) -> None:
        check.arg(self.id > 0, RpcProtocolError)
        check.non_empty_str(self.method, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcResultMessage:
    id: int
    result: ta.Any = None

    def __post_init__(self) -> None:
        check.arg(self.id > 0, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcErrorMessage:
    id: int
    error: RpcRemoteErrorData

    def __post_init__(self) -> None:
        check.arg(self.id > 0, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcCancelMessage:
    id: int

    def __post_init__(self) -> None:
        check.arg(self.id > 0, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcNotificationMessage:
    method: str
    params: ta.Any = None

    def __post_init__(self) -> None:
        check.non_empty_str(self.method, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcPingMessage:
    id: int

    def __post_init__(self) -> None:
        check.arg(self.id > 0, RpcProtocolError)


@dc.dataclass(frozen=True)
class RpcPongMessage:
    id: int

    def __post_init__(self) -> None:
        check.arg(self.id > 0, RpcProtocolError)


RpcMessage = ta.Union[  # ta.TypeAlias  # om-amalg-typing-no-move
    RpcRequestMessage,
    RpcResultMessage,
    RpcErrorMessage,
    RpcCancelMessage,
    RpcNotificationMessage,
    RpcPingMessage,
    RpcPongMessage,
]


##


class RpcMessageCodec(Abstract):
    @abc.abstractmethod
    def encode(self, message: RpcMessage) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    def decode(self, data: bytes) -> RpcMessage:
        raise NotImplementedError


# The wire is a `{"type": <tag>, **fields}` object: the discriminator tag selects the message dataclass, whose fields
# marshal/unmarshal directly. There is no field/discriminator-tagged union in the lite marshaler, so the tag is managed
# here while the per-message field mapping (including the nested error's `remote_type` -> `type`) is the marshaler's.
_RPC_MESSAGE_TAGS: ta.Mapping[type, str] = {
    RpcRequestMessage: 'request',
    RpcResultMessage: 'result',
    RpcErrorMessage: 'error',
    RpcCancelMessage: 'cancel',
    RpcNotificationMessage: 'notification',
    RpcPingMessage: 'ping',
    RpcPongMessage: 'pong',
}

_RPC_MESSAGE_TYPES: ta.Mapping[str, type] = {tag: ty for ty, tag in _RPC_MESSAGE_TAGS.items()}


class JsonRpcMessageCodec(RpcMessageCodec):
    @staticmethod
    def _reject_json_constant(value: str) -> ta.NoReturn:
        raise ValueError(f'Invalid JSON constant: {value}')

    def encode(self, message: RpcMessage) -> bytes:
        try:
            tag = _RPC_MESSAGE_TAGS[type(message)]
        except KeyError:
            raise TypeError(message) from None
        try:
            obj = {'type': tag, **marshal_obj(message)}
            return json.dumps(
                obj,
                allow_nan=False,
                separators=(',', ':'),
            ).encode('utf-8')
        except (RecursionError, TypeError, ValueError) as e:
            raise RpcProtocolError(f'RPC message is not JSON-compatible: {e}') from e

    def decode(self, data: bytes) -> RpcMessage:
        try:
            obj = json.loads(data.decode('utf-8'), parse_constant=self._reject_json_constant)
        except (RecursionError, UnicodeDecodeError, ValueError) as e:
            raise RpcProtocolError(f'Invalid RPC JSON: {e}') from e

        if not isinstance(obj, dict):
            raise RpcProtocolError(f'RPC message must be an object, got {type(obj).__name__}')
        try:
            tag = obj.pop('type')
        except KeyError:
            raise RpcProtocolError('RPC message is missing its type') from None
        try:
            ty = _RPC_MESSAGE_TYPES[tag]
        except KeyError:
            raise RpcProtocolError(f'Invalid RPC message type: {tag!r}') from None

        try:
            return unmarshal_obj(obj, ty)
        except RpcProtocolError:
            raise
        except Exception as e:  # noqa
            # Any failure to build the message from its wire fields - an unknown or missing field, a bad nested shape -
            # is a protocol error.
            raise RpcProtocolError(f'Invalid RPC {tag} message: {e}') from e
