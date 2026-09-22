# ruff: noqa: UP006 UP007 UP045
import abc
import dataclasses as dc
import json
import typing as ta

from omcore.lite.abstract import Abstract

from .errors import RpcProtocolError
from .errors import RpcRemoteErrorData


##


@dc.dataclass(frozen=True)
class RpcRequestMessage:
    id: int
    method: str
    params: ta.Any = None


@dc.dataclass(frozen=True)
class RpcResultMessage:
    id: int
    result: ta.Any = None


@dc.dataclass(frozen=True)
class RpcErrorMessage:
    id: int
    error: RpcRemoteErrorData


@dc.dataclass(frozen=True)
class RpcCancelMessage:
    id: int


@dc.dataclass(frozen=True)
class RpcNotificationMessage:
    method: str
    params: ta.Any = None


@dc.dataclass(frozen=True)
class RpcPingMessage:
    id: int


@dc.dataclass(frozen=True)
class RpcPongMessage:
    id: int


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


class JsonRpcMessageCodec(RpcMessageCodec):
    @classmethod
    def _to_obj(cls, message: RpcMessage) -> ta.Mapping[str, ta.Any]:
        if isinstance(message, RpcRequestMessage):
            return {'type': 'request', 'id': message.id, 'method': message.method, 'params': message.params}
        if isinstance(message, RpcResultMessage):
            return {'type': 'result', 'id': message.id, 'result': message.result}
        if isinstance(message, RpcErrorMessage):
            return {
                'type': 'error',
                'id': message.id,
                'error': {
                    'code': message.error.code,
                    'type': message.error.remote_type,
                    'message': message.error.message,
                    'traceback': message.error.traceback,
                },
            }
        if isinstance(message, RpcCancelMessage):
            return {'type': 'cancel', 'id': message.id}
        if isinstance(message, RpcNotificationMessage):
            return {'type': 'notification', 'method': message.method, 'params': message.params}
        if isinstance(message, RpcPingMessage):
            return {'type': 'ping', 'id': message.id}
        if isinstance(message, RpcPongMessage):
            return {'type': 'pong', 'id': message.id}
        raise TypeError(message)

    @staticmethod
    def _check_keys(dct: ta.Mapping[str, ta.Any], keys: ta.AbstractSet[str]) -> None:
        actual = set(dct)
        if actual != keys:
            raise RpcProtocolError(f'Invalid RPC message fields: expected {sorted(keys)!r}, got {sorted(actual)!r}')

    @staticmethod
    def _decode_id(value: ta.Any) -> int:
        if type(value) is not int or value <= 0:
            raise RpcProtocolError(f'Invalid RPC message id: {value!r}')
        return value

    @staticmethod
    def _decode_method(value: ta.Any) -> str:
        if not isinstance(value, str) or not value:
            raise RpcProtocolError(f'Invalid RPC method: {value!r}')
        return value

    @classmethod
    def _from_obj(cls, obj: ta.Any) -> RpcMessage:
        if not isinstance(obj, dict):
            raise RpcProtocolError(f'RPC message must be an object, got {type(obj).__name__}')

        message_type = obj.get('type')
        if message_type == 'request':
            cls._check_keys(obj, {'type', 'id', 'method', 'params'})
            return RpcRequestMessage(
                cls._decode_id(obj['id']),
                cls._decode_method(obj['method']),
                obj['params'],
            )
        if message_type == 'result':
            cls._check_keys(obj, {'type', 'id', 'result'})
            return RpcResultMessage(cls._decode_id(obj['id']), obj['result'])
        if message_type == 'error':
            cls._check_keys(obj, {'type', 'id', 'error'})
            error = obj['error']
            if not isinstance(error, dict):
                raise RpcProtocolError(f'RPC error must be an object, got {type(error).__name__}')
            cls._check_keys(error, {'code', 'type', 'message', 'traceback'})
            if not isinstance(error['code'], str) or not error['code']:
                raise RpcProtocolError(f'Invalid RPC error code: {error["code"]!r}')
            if not isinstance(error['type'], str) or not error['type']:
                raise RpcProtocolError(f'Invalid RPC error type: {error["type"]!r}')
            if not isinstance(error['message'], str):
                raise RpcProtocolError(f'Invalid RPC error message: {error["message"]!r}')
            if error['traceback'] is not None and not isinstance(error['traceback'], str):
                raise RpcProtocolError(f'Invalid RPC error traceback: {error["traceback"]!r}')
            return RpcErrorMessage(
                cls._decode_id(obj['id']),
                RpcRemoteErrorData(
                    code=error['code'],
                    remote_type=error['type'],
                    message=error['message'],
                    traceback=error['traceback'],
                ),
            )
        if message_type == 'cancel':
            cls._check_keys(obj, {'type', 'id'})
            return RpcCancelMessage(cls._decode_id(obj['id']))
        if message_type == 'notification':
            cls._check_keys(obj, {'type', 'method', 'params'})
            return RpcNotificationMessage(cls._decode_method(obj['method']), obj['params'])
        if message_type == 'ping':
            cls._check_keys(obj, {'type', 'id'})
            return RpcPingMessage(cls._decode_id(obj['id']))
        if message_type == 'pong':
            cls._check_keys(obj, {'type', 'id'})
            return RpcPongMessage(cls._decode_id(obj['id']))
        raise RpcProtocolError(f'Invalid RPC message type: {message_type!r}')

    def encode(self, message: RpcMessage) -> bytes:
        try:
            obj = self._to_obj(message)
            self._from_obj(obj)
            return json.dumps(
                obj,
                allow_nan=False,
                separators=(',', ':'),
            ).encode('utf-8')
        except (RecursionError, TypeError, ValueError) as e:
            raise RpcProtocolError(f'RPC message is not JSON-compatible: {e}') from e

    @staticmethod
    def _reject_json_constant(value: str) -> ta.NoReturn:
        raise ValueError(f'Invalid JSON constant: {value}')

    def decode(self, data: bytes) -> RpcMessage:
        try:
            obj = json.loads(data.decode('utf-8'), parse_constant=self._reject_json_constant)
        except (RecursionError, UnicodeDecodeError, ValueError) as e:
            raise RpcProtocolError(f'Invalid RPC JSON: {e}') from e
        return self._from_obj(obj)
