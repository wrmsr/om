"""
The daemons wire dialect, as an `omcore.rpc` envelope codec.

The wire is unchanged: four-byte big-endian length frames of compact JSON objects, a `hello` greeting each way, then
`request`, `result`, and `error` objects carrying a `client_id` and `request_id` in place of an envelope id. The codec
maps that pair onto the envelope id, a `(client_id, request_id)` tuple, so the session correlates responses as with any
other id, and the replay registry sees the identity a client chose. Envelope kinds the dialect lacks - cancels,
notifications, pings - cannot be sent, and arriving are protocol errors.
"""
import typing as ta
import uuid

from omcore.rpc.codecs import JsonRpcValueCodec
from omcore.rpc.codecs import RpcValueEnvelopeCodec
from omcore.rpc.errors import RpcRemoteErrorData
from omcore.rpc.messages import RpcEnvelope
from omcore.rpc.messages import RpcErrorMessage
from omcore.rpc.messages import RpcHelloMessage
from omcore.rpc.messages import RpcRequestMessage
from omcore.rpc.messages import RpcResultMessage

from ..protocol import RPC_PROTOCOL_NAME
from ..protocol import RpcProtocolError
from ..protocol import RpcRequest
from .messages import RpcWireError
from .messages import RpcWireRequest
from .messages import RpcWireResult


RpcWireMessage: ta.TypeAlias = ta.Union[  # noqa: UP007
    RpcWireRequest,
    RpcWireResult,
    RpcWireError,
]


##


def _required_str(
        obj: ta.Mapping[str, ta.Any],
        key: str,
        *,
        allow_empty: bool = False,
) -> str:
    try:
        value = obj[key]
    except KeyError as exc:
        raise RpcProtocolError(f'Missing RPC message field: {key!r}') from exc
    if not isinstance(value, str) or (not value and not allow_empty):
        raise RpcProtocolError(f'Invalid RPC message field {key!r}: {value!r}')
    return value


def rpc_request_id(client_id: str, request_id: str) -> tuple[str, str]:
    return (client_id, request_id)


def rpc_request_of_message(msg: RpcRequestMessage) -> RpcRequest:
    client_id, request_id = msg.id
    return RpcRequest(
        client_id=client_id,
        request_id=request_id,
        method=msg.method,
        params=msg.params,
    )


def rpc_message_of_request(request: RpcRequest) -> RpcRequestMessage:
    return RpcRequestMessage(
        rpc_request_id(request.client_id, request.request_id),
        request.method,
        request.params,
    )


##


class DaemonsRpcEnvelopeCodec(RpcValueEnvelopeCodec):
    def __init__(self) -> None:
        # Escaped like the blocking wire helpers in `..protocol`, so both spell a message the same way.
        super().__init__(JsonRpcValueCodec(ensure_ascii=True))

    def envelope_to_value(self, envelope: RpcEnvelope) -> ta.Any:
        if isinstance(envelope, RpcRequestMessage):
            client_id, request_id = envelope.id
            return {
                'type': 'request',
                'client_id': client_id,
                'request_id': request_id,
                'method': envelope.method,
                'params': envelope.params,
            }

        if isinstance(envelope, RpcResultMessage):
            client_id, request_id = envelope.id
            return {
                'type': 'result',
                'client_id': client_id,
                'request_id': request_id,
                'result': envelope.result,
            }

        if isinstance(envelope, RpcErrorMessage):
            client_id, request_id = envelope.id
            return {
                'type': 'error',
                'client_id': client_id,
                'request_id': request_id,
                'error': {
                    'code': envelope.error.code,
                    'type': envelope.error.remote_type,
                    'message': envelope.error.message,
                },
            }

        if isinstance(envelope, RpcHelloMessage):
            return super().envelope_to_value(envelope)

        raise TypeError(f'not part of the daemons rpc dialect: {envelope!r}')

    def envelope_from_value(self, value: ta.Any) -> RpcEnvelope:
        if not isinstance(value, dict):
            raise RpcProtocolError(f'RPC message must be an object, got {type(value).__name__}')

        message_type = value.get('type')

        if message_type == 'hello':
            return super().envelope_from_value(value)

        if message_type == 'request':
            try:
                return rpc_message_of_request(RpcRequest(
                    client_id=_required_str(value, 'client_id'),
                    request_id=_required_str(value, 'request_id'),
                    method=_required_str(value, 'method'),
                    params=value.get('params'),
                ))
            except RpcProtocolError:
                raise
            except (TypeError, ValueError) as exc:
                raise RpcProtocolError(f'Invalid RPC request: {exc}') from exc

        rid = rpc_request_id(_required_str(value, 'client_id'), _required_str(value, 'request_id'))

        if message_type == 'result':
            if 'result' not in value:
                raise RpcProtocolError('Missing RPC result')
            return RpcResultMessage(rid, value['result'])

        if message_type == 'error':
            error = value.get('error')
            if not isinstance(error, dict):
                raise RpcProtocolError(f'Invalid RPC error: {error!r}')
            return RpcErrorMessage(rid, RpcRemoteErrorData(
                code=_required_str(error, 'code'),
                remote_type=_required_str(error, 'type'),
                message=_required_str(error, 'message', allow_empty=True),
            ))

        raise RpcProtocolError(f'Unknown RPC message type: {message_type!r}')

    def decode(self, data: bytes) -> RpcEnvelope:
        try:
            value = self.value_codec.decode(data)
        except Exception as exc:  # noqa
            raise RpcProtocolError(f'Invalid RPC JSON: {exc}') from exc
        return self.envelope_from_value(value)


DAEMONS_RPC_ENVELOPE_CODEC = DaemonsRpcEnvelopeCodec()


##
# hellos


def rpc_client_hello(protocol_version: int) -> ta.Mapping[str, ta.Any]:
    return {
        'protocol': RPC_PROTOCOL_NAME,
        'version': protocol_version,
    }


def rpc_server_hello(protocol_version: int, instance_id: uuid.UUID) -> ta.Mapping[str, ta.Any]:
    return {
        'protocol': RPC_PROTOCOL_NAME,
        'version': protocol_version,
        'instance_id': str(instance_id),
    }


def rpc_hello_version(hello: ta.Mapping[str, ta.Any]) -> int:
    if hello.get('protocol') != RPC_PROTOCOL_NAME:
        raise RpcProtocolError(f'Unexpected RPC protocol: {hello.get("protocol")!r}')
    version = hello.get('version')
    if not isinstance(version, int) or isinstance(version, bool):
        raise RpcProtocolError(f'Invalid RPC protocol version: {version!r}')
    return version


def rpc_hello_instance_id(hello: ta.Mapping[str, ta.Any]) -> uuid.UUID:
    raw = _required_str(hello, 'instance_id')
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise RpcProtocolError(f'Invalid RPC service instance id: {raw!r}') from exc


##
# payloads, for size checks ahead of sending


def _wire_message_envelope(msg: RpcWireMessage) -> RpcEnvelope:
    if isinstance(msg, RpcWireRequest):
        return rpc_message_of_request(msg.request)
    if isinstance(msg, RpcWireResult):
        return RpcResultMessage(rpc_request_id(msg.client_id, msg.request_id), msg.result)
    if isinstance(msg, RpcWireError):
        return RpcErrorMessage(rpc_request_id(msg.client_id, msg.request_id), RpcRemoteErrorData(
            code=msg.code,
            remote_type=msg.remote_type,
            message=msg.message,
        ))
    raise TypeError(msg)


def encode_rpc_wire_message_payload(msg: RpcWireMessage) -> bytes:
    try:
        return DAEMONS_RPC_ENVELOPE_CODEC.encode(_wire_message_envelope(msg))
    except (TypeError, ValueError) as exc:
        raise RpcProtocolError(f'RPC message is not JSON-compatible: {exc}') from exc
