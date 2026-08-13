import math
import struct
import typing as ta
import uuid

from ....formats.json import all as json
from ....io.pipelines.bytes.decoders import BufferedBytesToMessageDecoderIoPipelineHandler
from ....io.pipelines.core import IoPipelineHandler
from ....io.pipelines.core import IoPipelineHandlerContext
from ....io.streambufs.types import ByteStreamBuffer
from ....io.streambufs.utils import ByteStreamBuffers
from ..protocol import RPC_PROTOCOL_NAME
from ..protocol import RpcProtocolError
from ..protocol import RpcRequest
from .messages import RpcClientHello
from .messages import RpcFrame
from .messages import RpcPipelineFailure
from .messages import RpcServerHello
from .messages import RpcWireError
from .messages import RpcWireMessage
from .messages import RpcWireRequest
from .messages import RpcWireResult


##


_FRAME_HEADER = struct.Struct('!I')


class RpcFrameCodecIoPipelineHandler(BufferedBytesToMessageDecoderIoPipelineHandler):
    """Decode and encode bounded length-prefixed RPC frames."""

    def __init__(self, max_frame_bytes: int) -> None:
        super().__init__()

        if max_frame_bytes < 1:
            raise ValueError(max_frame_bytes)
        self._max_frame_bytes = max_frame_bytes
        self._frame_size: int | None = None

    def _decode_buffer(
            self,
            ctx: IoPipelineHandlerContext,
            buf: ByteStreamBuffer,
            out: list[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        while True:
            if self._frame_size is None:
                if len(buf) < _FRAME_HEADER.size:
                    break
                self._frame_size = size = _FRAME_HEADER.unpack(buf.coalesce(_FRAME_HEADER.size))[0]
                buf.advance(_FRAME_HEADER.size)
                if size > self._max_frame_bytes:
                    raise RpcProtocolError(
                        f'RPC frame is {size} bytes, exceeding limit {self._max_frame_bytes}',
                    )

            size = self._frame_size
            if len(buf) < size:
                break

            out.append(RpcFrame(ByteStreamBuffers.to_bytes(buf.split_to(size), strict=True)))
            self._frame_size = None

        if final and (self._frame_size is not None or len(buf)):
            self._frame_size = None
            buf.advance(len(buf))
            out.append(RpcPipelineFailure(
                exc=RpcProtocolError('RPC connection closed within a frame'),
            ))

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, RpcFrame):
            size = len(msg.data)
            if size > self._max_frame_bytes:
                raise RpcProtocolError(
                    f'RPC frame is {size} bytes, exceeding limit {self._max_frame_bytes}',
                )
            msg = _FRAME_HEADER.pack(size) + msg.data

        ctx.feed_out(msg)


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


def rpc_wire_message_from_obj(obj: ta.Any) -> RpcWireMessage:
    if not isinstance(obj, dict):
        raise RpcProtocolError(f'RPC message must be an object, got {type(obj).__name__}')

    message_type = obj.get('type')
    if message_type == 'hello':
        if obj.get('protocol') != RPC_PROTOCOL_NAME:
            raise RpcProtocolError(f'Unexpected RPC protocol: {obj.get("protocol")!r}')
        version = obj.get('version')
        if not isinstance(version, int):
            raise RpcProtocolError(f'Invalid RPC protocol version: {version!r}')

        if 'instance_id' not in obj:
            return RpcClientHello(version=version)

        raw_instance_id = _required_str(obj, 'instance_id')
        try:
            instance_id = uuid.UUID(raw_instance_id)
        except ValueError as exc:
            raise RpcProtocolError(f'Invalid RPC service instance id: {raw_instance_id!r}') from exc
        return RpcServerHello(
            version=version,
            instance_id=instance_id,
        )

    if message_type == 'request':
        try:
            request = RpcRequest(
                client_id=_required_str(obj, 'client_id'),
                request_id=_required_str(obj, 'request_id'),
                method=_required_str(obj, 'method'),
                params=obj.get('params'),
            )
        except (TypeError, ValueError) as exc:
            raise RpcProtocolError(f'Invalid RPC request: {exc}') from exc
        return RpcWireRequest(request=request)

    client_id = _required_str(obj, 'client_id')
    request_id = _required_str(obj, 'request_id')
    if message_type == 'result':
        if 'result' not in obj:
            raise RpcProtocolError('Missing RPC result')
        return RpcWireResult(
            client_id=client_id,
            request_id=request_id,
            result=obj['result'],
        )

    if message_type == 'error':
        error = obj.get('error')
        if not isinstance(error, dict):
            raise RpcProtocolError(f'Invalid RPC error: {error!r}')
        return RpcWireError(
            client_id=client_id,
            request_id=request_id,
            code=_required_str(error, 'code'),
            remote_type=_required_str(error, 'type'),
            message=_required_str(error, 'message', allow_empty=True),
        )

    raise RpcProtocolError(f'Unknown RPC message type: {message_type!r}')


def rpc_wire_message_to_obj(msg: RpcWireMessage) -> ta.Mapping[str, ta.Any]:
    if isinstance(msg, RpcClientHello):
        return {
            'type': 'hello',
            'protocol': RPC_PROTOCOL_NAME,
            'version': msg.version,
        }

    if isinstance(msg, RpcServerHello):
        return {
            'type': 'hello',
            'protocol': RPC_PROTOCOL_NAME,
            'version': msg.version,
            'instance_id': str(msg.instance_id),
        }

    if isinstance(msg, RpcWireRequest):
        return {
            'type': 'request',
            'client_id': msg.request.client_id,
            'request_id': msg.request.request_id,
            'method': msg.request.method,
            'params': msg.request.params,
        }

    if isinstance(msg, RpcWireResult):
        return {
            'type': 'result',
            'client_id': msg.client_id,
            'request_id': msg.request_id,
            'result': msg.result,
        }

    if isinstance(msg, RpcWireError):
        return {
            'type': 'error',
            'client_id': msg.client_id,
            'request_id': msg.request_id,
            'error': {
                'code': msg.code,
                'type': msg.remote_type,
                'message': msg.message,
            },
        }

    raise TypeError(msg)


def _validate_json_numbers(obj: ta.Any, seen: set[int]) -> None:
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError(f'Out of range float values are not JSON compliant: {obj!r}')
        return

    if isinstance(obj, dict):
        if id(obj) in seen:
            return
        seen.add(id(obj))
        for key, value in obj.items():
            _validate_json_numbers(key, seen)
            _validate_json_numbers(value, seen)
        return

    if isinstance(obj, (list, tuple)):
        if id(obj) in seen:
            return
        seen.add(id(obj))
        for value in obj:
            _validate_json_numbers(value, seen)


def encode_rpc_wire_message_payload(msg: RpcWireMessage) -> bytes:
    obj = rpc_wire_message_to_obj(msg)
    try:
        _validate_json_numbers(obj, set())
        return json.dumps_compact(obj).encode('utf-8')
    except (TypeError, ValueError) as exc:
        raise RpcProtocolError(f'RPC message is not JSON-compatible: {exc}') from exc


class RpcJsonCodecIoPipelineHandler(IoPipelineHandler):
    """Translate JSON RPC frames to and from typed wire messages."""

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, RpcFrame):
            try:
                obj = json.loads(msg.data.decode('utf-8'))
            except ValueError as exc:
                raise RpcProtocolError(f'Invalid RPC JSON: {exc}') from exc
            msg = rpc_wire_message_from_obj(obj)

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, (RpcClientHello, RpcServerHello, RpcWireRequest, RpcWireResult, RpcWireError)):
            msg = RpcFrame(encode_rpc_wire_message_payload(msg))

        ctx.feed_out(msg)
