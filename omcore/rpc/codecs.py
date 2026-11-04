# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
RpcFrame <-> RpcEnvelope, in two pluggable halves.

A value codec turns bytes into an opaque value tree and back - JSON by default, but nothing in the toolbox depends on
JSON: anything which can carry string-keyed mappings, strings, and whatever the serde above the connection produces as
params and results (CBOR, say) plugs in here. An envelope codec maps the seven envelope kinds onto such a tree; the
default spells each as a mapping tagged by kind. This is the one place a differently-shaped wire dialect differs.

Decoding failures are protocol errors and fatal to the connection. Encoding never raises: an envelope which cannot be
encoded, or which encodes larger than the frame limit, is dropped and reported inward as an OutboundEncodeFailed so the
session can fail just that message rather than the connection.
"""
import abc
import json
import typing as ta

from ..io.pipelines.core import IoPipelineHandler
from ..io.pipelines.core import IoPipelineHandlerContext
from ..lite.abstract import Abstract
from .errors import RpcMessageTooLargeError
from .errors import RpcProtocolError
from .errors import RpcRemoteErrorData
from .framing import RpcFrame
from .messages import RpcCancelMessage
from .messages import RpcEnvelope
from .messages import RpcErrorMessage
from .messages import RpcHelloMessage
from .messages import RpcNotificationMessage
from .messages import RpcPingMessage
from .messages import RpcPongMessage
from .messages import RpcRequestMessage
from .messages import RpcResultMessage
from .messages import RpcSessionMessages


##


class RpcValueCodec(Abstract):
    """bytes <-> an opaque value tree. Both methods raise on input they cannot handle."""

    @abc.abstractmethod
    def encode(self, value: ta.Any) -> bytes:
        raise NotImplementedError

    @abc.abstractmethod
    def decode(self, data: bytes) -> ta.Any:
        raise NotImplementedError


class JsonRpcValueCodec(RpcValueCodec):
    """
    Compact UTF-8 JSON. NaN and infinities are rejected rather than emitted as the non-standard tokens json allows.
    """  # noqa

    def __init__(
            self,
            *,
            ensure_ascii: bool = False,
            sort_keys: bool = False,
    ) -> None:
        super().__init__()

        self._ensure_ascii = ensure_ascii
        self._sort_keys = sort_keys

    def encode(self, value: ta.Any) -> bytes:
        return json.dumps(
            value,
            separators=(',', ':'),
            ensure_ascii=self._ensure_ascii,
            sort_keys=self._sort_keys,
            allow_nan=False,
        ).encode('utf-8')

    def decode(self, data: bytes) -> ta.Any:
        return json.loads(data.decode('utf-8'))


##


class RpcEnvelopeCodec(Abstract):
    @abc.abstractmethod
    def encode(self, envelope: RpcEnvelope) -> bytes:
        """Raises on an unencodable envelope; the pipeline handler reports that inward as an OutboundEncodeFailed."""

        raise NotImplementedError

    @abc.abstractmethod
    def decode(self, data: bytes) -> RpcEnvelope:
        """Raises RpcProtocolError on data which is not a well-formed envelope."""

        raise NotImplementedError


class RpcValueEnvelopeCodec(RpcEnvelopeCodec):
    """
    Envelopes as tagged mappings over a value codec: `{"type": <kind>, ...fields}`. Error data is spelled
    `{"code", "type", "message", "traceback"?}`. Unknown keys are ignored on decode, for forward compatibility.
    """

    TYPE_KEY: ta.ClassVar[str] = 'type'

    REQUEST_TYPE: ta.ClassVar[str] = 'request'
    RESULT_TYPE: ta.ClassVar[str] = 'result'
    ERROR_TYPE: ta.ClassVar[str] = 'error'
    CANCEL_TYPE: ta.ClassVar[str] = 'cancel'
    NOTIFICATION_TYPE: ta.ClassVar[str] = 'notification'
    PING_TYPE: ta.ClassVar[str] = 'ping'
    PONG_TYPE: ta.ClassVar[str] = 'pong'
    HELLO_TYPE: ta.ClassVar[str] = 'hello'

    def __init__(
            self,
            value_codec: ta.Optional[RpcValueCodec] = None,
    ) -> None:
        super().__init__()

        if value_codec is None:
            value_codec = JsonRpcValueCodec()
        self._value_codec = value_codec

    @property
    def value_codec(self) -> RpcValueCodec:
        return self._value_codec

    #

    def _error_data_to_value(self, e: RpcRemoteErrorData) -> ta.Any:
        dct: ta.Dict[str, ta.Any] = {
            'code': e.code,
            'type': e.remote_type,
            'message': e.message,
        }
        if e.traceback is not None:
            dct['traceback'] = e.traceback
        return dct

    def envelope_to_value(self, envelope: RpcEnvelope) -> ta.Any:
        tk = self.TYPE_KEY

        if isinstance(envelope, RpcRequestMessage):
            return {tk: self.REQUEST_TYPE, 'id': envelope.id, 'method': envelope.method, 'params': envelope.params}

        elif isinstance(envelope, RpcResultMessage):
            return {tk: self.RESULT_TYPE, 'id': envelope.id, 'result': envelope.result}

        elif isinstance(envelope, RpcErrorMessage):
            return {tk: self.ERROR_TYPE, 'id': envelope.id, 'error': self._error_data_to_value(envelope.error)}

        elif isinstance(envelope, RpcCancelMessage):
            return {tk: self.CANCEL_TYPE, 'id': envelope.id}

        elif isinstance(envelope, RpcNotificationMessage):
            return {tk: self.NOTIFICATION_TYPE, 'method': envelope.method, 'params': envelope.params}

        elif isinstance(envelope, RpcPingMessage):
            return {tk: self.PING_TYPE, 'id': envelope.id}

        elif isinstance(envelope, RpcPongMessage):
            return {tk: self.PONG_TYPE, 'id': envelope.id}

        elif isinstance(envelope, RpcHelloMessage):
            if tk in envelope.fields:
                raise ValueError(f'hello fields may not use the {tk!r} key')
            return {tk: self.HELLO_TYPE, **envelope.fields}

        else:
            raise TypeError(envelope)

    #

    @staticmethod
    def _require(dct: ta.Mapping[str, ta.Any], key: str) -> ta.Any:
        try:
            return dct[key]
        except KeyError:
            raise RpcProtocolError(f'envelope missing {key!r}') from None

    @staticmethod
    def _require_str(dct: ta.Mapping[str, ta.Any], key: str) -> str:
        v = RpcValueEnvelopeCodec._require(dct, key)
        if not isinstance(v, str):
            raise RpcProtocolError(f'envelope {key!r} is not a string: {v!r}')
        return v

    def _error_data_from_value(self, v: ta.Any) -> RpcRemoteErrorData:
        if not isinstance(v, ta.Mapping):
            raise RpcProtocolError(f'error is not a mapping: {v!r}')

        tb = v.get('traceback')
        if tb is not None and not isinstance(tb, str):
            raise RpcProtocolError(f'error traceback is not a string: {tb!r}')

        return RpcRemoteErrorData(
            code=self._require_str(v, 'code'),
            remote_type=self._require_str(v, 'type'),
            message=self._require_str(v, 'message'),
            traceback=tb,
        )

    def envelope_from_value(self, value: ta.Any) -> RpcEnvelope:
        if not isinstance(value, ta.Mapping):
            raise RpcProtocolError(f'envelope is not a mapping: {type(value).__name__}')

        ty = self._require_str(value, self.TYPE_KEY)

        try:
            if ty == self.REQUEST_TYPE:
                return RpcRequestMessage(
                    self._require(value, 'id'),
                    self._require_str(value, 'method'),
                    value.get('params'),
                )

            elif ty == self.RESULT_TYPE:
                return RpcResultMessage(self._require(value, 'id'), value.get('result'))

            elif ty == self.ERROR_TYPE:
                return RpcErrorMessage(
                    self._require(value, 'id'),
                    self._error_data_from_value(self._require(value, 'error')),
                )

            elif ty == self.CANCEL_TYPE:
                return RpcCancelMessage(self._require(value, 'id'))

            elif ty == self.NOTIFICATION_TYPE:
                return RpcNotificationMessage(self._require_str(value, 'method'), value.get('params'))

            elif ty == self.PING_TYPE:
                return RpcPingMessage(self._require(value, 'id'))

            elif ty == self.PONG_TYPE:
                return RpcPongMessage(self._require(value, 'id'))

            elif ty == self.HELLO_TYPE:
                return RpcHelloMessage({k: v for k, v in value.items() if k != self.TYPE_KEY})

            else:
                raise RpcProtocolError(f'unknown envelope type: {ty!r}')

        except RpcProtocolError:
            raise

        except (TypeError, ValueError) as e:
            raise RpcProtocolError(f'malformed {ty} envelope: {e}') from e

    #

    def encode(self, envelope: RpcEnvelope) -> bytes:
        return self._value_codec.encode(self.envelope_to_value(envelope))

    def decode(self, data: bytes) -> RpcEnvelope:
        try:
            value = self._value_codec.decode(data)
        except RpcProtocolError:
            raise
        except Exception as e:  # noqa
            raise RpcProtocolError(f'undecodable envelope: {e}') from e

        return self.envelope_from_value(value)


##


class RpcEnvelopeCodecIoPipelineHandler(IoPipelineHandler):
    """RpcFrame <-> RpcEnvelope. Sits between the framing handler and the session (or any handlers between them)."""

    def __init__(
            self,
            codec: ta.Optional[RpcEnvelopeCodec] = None,
            *,
            max_frame_bytes: int,
    ) -> None:
        super().__init__()

        if codec is None:
            codec = RpcValueEnvelopeCodec()
        self._codec = codec

        if max_frame_bytes < 1:
            raise ValueError(max_frame_bytes)
        self._max_frame_bytes = max_frame_bytes

    @property
    def codec(self) -> RpcEnvelopeCodec:
        return self._codec

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, RpcFrame):
            msg = self._codec.decode(msg.data)

        ctx.feed_in(msg)

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, RpcEnvelope):
            try:
                data = self._codec.encode(msg)
            except Exception as e:  # noqa
                ctx.feed_in(RpcSessionMessages.OutboundEncodeFailed(msg, e))
                return

            if len(data) > self._max_frame_bytes:
                ctx.feed_in(RpcSessionMessages.OutboundEncodeFailed(msg, RpcMessageTooLargeError(
                    f'outbound envelope is {len(data)} bytes, exceeding limit {self._max_frame_bytes}',
                )))
                return

            msg = RpcFrame(data)

        ctx.feed_out(msg)
