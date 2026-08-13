from __future__ import annotations

import json
import socket
import struct
import typing as ta
import uuid

from ... import check
from ... import dataclasses as dc


##


RPC_PROTOCOL_NAME = 'omcore.daemons.rpc'
RPC_PROTOCOL_VERSION = 1
RPC_DEFAULT_MAX_FRAME_BYTES = 16 * 1024 * 1024


class RpcError(Exception):
    """Base exception for the local RPC protocol."""


class RpcProtocolError(RpcError):
    """Indicates an invalid or incompatible RPC exchange."""


class RpcUnavailableError(RpcError):
    """Indicates that an RPC request is known not to have executed and may be retried safely."""


class RpcRemoteError(RpcError):
    """Reports an exception raised while executing an RPC request."""

    def __init__(
            self,
            *,
            remote_type: str,
            message: str,
    ) -> None:
        super().__init__(f'{remote_type}: {message}')

        self._remote_type = remote_type
        self._message = message

    @property
    def remote_type(self) -> str:
        return self._remote_type

    @property
    def message(self) -> str:
        return self._message


class RpcCallIndeterminateError(RpcError):
    """Indicates that a request may have executed but no authoritative response was received."""

    def __init__(
            self,
            request: RpcRequest,
            *,
            instance_id: uuid.UUID,
            actual_instance_id: uuid.UUID | None = None,
    ) -> None:
        if actual_instance_id is None:
            detail = f'response from service instance {instance_id!r} was lost'
        else:
            detail = (
                f'service instance changed from {instance_id!r} '
                f'to {actual_instance_id!r}'
            )
        super().__init__(f'Outcome of RPC request {request.request_id!r} is indeterminate: {detail}')

        self._request = request
        self._instance_id = instance_id
        self._actual_instance_id = actual_instance_id

    @property
    def request(self) -> RpcRequest:
        return self._request

    @property
    def instance_id(self) -> uuid.UUID:
        return self._instance_id

    @property
    def actual_instance_id(self) -> uuid.UUID | None:
        return self._actual_instance_id


##


@dc.dataclass(frozen=True, kw_only=True)
class RpcRequest:
    """A stable request identity and its JSON-compatible invocation data."""

    client_id: str
    request_id: str
    method: str
    params: ta.Any = None

    def __post_init__(self) -> None:
        check.non_empty_str(self.client_id)
        check.non_empty_str(self.request_id)
        check.non_empty_str(self.method)


class RpcHandler(ta.Protocol):
    def __call__(self, request: RpcRequest) -> ta.Any:
        raise NotImplementedError


##


_FRAME_HEADER = struct.Struct('!I')


def encode_rpc_message(obj: ta.Mapping[str, ta.Any], max_frame_bytes: int) -> bytes:
    try:
        payload = json.dumps(
            obj,
            allow_nan=False,
            separators=(',', ':'),
        ).encode('utf-8')
    except (TypeError, ValueError) as exc:
        raise RpcProtocolError(f'RPC message is not JSON-compatible: {exc}') from exc

    if len(payload) > max_frame_bytes:
        raise RpcProtocolError(f'RPC frame is {len(payload)} bytes, exceeding limit {max_frame_bytes}')

    return _FRAME_HEADER.pack(len(payload)) + payload


def send_rpc_message(
        sock: socket.socket,
        obj: ta.Mapping[str, ta.Any],
        max_frame_bytes: int,
) -> None:
    sock.sendall(encode_rpc_message(obj, max_frame_bytes))


def _recv_exact(sock: socket.socket, size: int) -> bytes:
    buf = bytearray()
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            if not buf:
                raise EOFError('RPC connection closed')
            raise RpcProtocolError('RPC connection closed within a frame')
        buf.extend(chunk)
    return bytes(buf)


def recv_rpc_message(sock: socket.socket, max_frame_bytes: int) -> ta.Mapping[str, ta.Any]:
    header = _recv_exact(sock, _FRAME_HEADER.size)
    size = _FRAME_HEADER.unpack(header)[0]
    if size > max_frame_bytes:
        raise RpcProtocolError(f'RPC frame is {size} bytes, exceeding limit {max_frame_bytes}')

    payload = _recv_exact(sock, size)
    try:
        obj = json.loads(payload.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RpcProtocolError(f'Invalid RPC JSON: {exc}') from exc
    if not isinstance(obj, dict):
        raise RpcProtocolError(f'RPC message must be an object, got {type(obj).__name__}')
    return obj


def exception_type_name(exc: BaseException) -> str:
    cls = type(exc)
    return f'{cls.__module__}.{cls.__qualname__}'


def hello_message(*, version: int, instance_id: uuid.UUID | None = None) -> ta.Mapping[str, ta.Any]:
    return {
        'type': 'hello',
        'protocol': RPC_PROTOCOL_NAME,
        'version': version,
        **({'instance_id': str(instance_id)} if instance_id is not None else {}),
    }


def request_message(request: RpcRequest) -> ta.Mapping[str, ta.Any]:
    return {
        'type': 'request',
        'client_id': request.client_id,
        'request_id': request.request_id,
        'method': request.method,
        'params': request.params,
    }


def result_message(request: RpcRequest, result: ta.Any) -> ta.Mapping[str, ta.Any]:
    return {
        'type': 'result',
        'client_id': request.client_id,
        'request_id': request.request_id,
        'result': result,
    }


def error_message(
        request: RpcRequest,
        *,
        code: str,
        remote_type: str,
        message: str,
) -> ta.Mapping[str, ta.Any]:
    return {
        'type': 'error',
        'client_id': request.client_id,
        'request_id': request.request_id,
        'error': {
            'code': code,
            'type': remote_type,
            'message': message,
        },
    }
