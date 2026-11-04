# ruff: noqa: PT009 PT027 UP006 UP007 UP045
# @om-lite
import ast
import math
import typing as ta
import unittest

from ...io.pipelines.core import IoPipeline
from ...io.pipelines.core import IoPipelineHandler
from ...io.pipelines.core import IoPipelineMessages
from ...io.pipelines.handlers.feedback import FeedbackInboundIoPipelineHandler
from ...io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ..codecs import JsonRpcValueCodec
from ..codecs import RpcEnvelopeCodecIoPipelineHandler
from ..codecs import RpcValueCodec
from ..codecs import RpcValueEnvelopeCodec
from ..errors import RpcMessageTooLargeError
from ..errors import RpcProtocolError
from ..errors import RpcRemoteErrorData
from ..framing import RpcFrame
from ..framing import RpcLengthPrefixedFramingIoPipelineHandler
from ..messages import RpcCancelMessage
from ..messages import RpcEnvelope
from ..messages import RpcErrorMessage
from ..messages import RpcNotificationMessage
from ..messages import RpcPingMessage
from ..messages import RpcPongMessage
from ..messages import RpcRequestMessage
from ..messages import RpcResultMessage
from ..messages import RpcSessionMessages as Rsm


##


ALL_ENVELOPES: ta.Sequence[RpcEnvelope] = [
    RpcRequestMessage(1, 'fs.read', {'path': '/x', 'n': [1, 2.5, None, True]}),
    RpcRequestMessage('uuid-ish', 'noparams'),
    RpcResultMessage(1, {'ok': 'yes'}),
    RpcResultMessage(2),
    RpcErrorMessage(3, RpcRemoteErrorData('remote', 'builtins.ValueError', 'bad', 'Traceback...')),
    RpcErrorMessage(4, RpcRemoteErrorData('busy', 'x.Busy', 'busy')),
    RpcCancelMessage(5),
    RpcNotificationMessage('process.output', {'data': 'abc'}),
    RpcNotificationMessage('bare'),
    RpcPingMessage(6),
    RpcPongMessage('rpc-keepalive:1'),
]


class LiteralRpcValueCodec(RpcValueCodec):
    """A deliberately non-JSON value codec: python literals, which carry bytes and tuples JSON cannot."""

    def encode(self, value: ta.Any) -> bytes:
        return repr(value).encode('utf-8')

    def decode(self, data: bytes) -> ta.Any:
        return ast.literal_eval(data.decode('utf-8'))


class TestValueCodecs(unittest.TestCase):
    def test_json_compact(self):
        c = JsonRpcValueCodec()
        self.assertEqual(c.encode({'a': [1, 'b']}), b'{"a":[1,"b"]}')
        self.assertEqual(c.decode(b'{"a":[1,"b"]}'), {'a': [1, 'b']})

    def test_json_unicode(self):
        c = JsonRpcValueCodec()
        self.assertEqual(c.decode(c.encode('snow ☃')), 'snow ☃')
        self.assertIn('☃'.encode(), c.encode('☃'))
        self.assertEqual(JsonRpcValueCodec(ensure_ascii=True).encode('☃'), b'"\\u2603"')

    def test_json_rejects_nan(self):
        c = JsonRpcValueCodec()
        for v in (math.nan, math.inf, -math.inf):
            with self.assertRaises(ValueError):
                c.encode(v)

    def test_json_rejects_unencodable(self):
        with self.assertRaises(TypeError):
            JsonRpcValueCodec().encode(object())


class TestEnvelopeCodec(unittest.TestCase):
    def test_roundtrip_all(self):
        c = RpcValueEnvelopeCodec()
        for env in ALL_ENVELOPES:
            with self.subTest(env=env):
                self.assertEqual(c.decode(c.encode(env)), env)

    def test_wire_shape(self):
        c = RpcValueEnvelopeCodec()
        self.assertEqual(
            c.envelope_to_value(RpcRequestMessage(1, 'm', [1])),
            {'type': 'request', 'id': 1, 'method': 'm', 'params': [1]},
        )
        self.assertEqual(
            c.envelope_to_value(RpcErrorMessage(2, RpcRemoteErrorData('c', 't', 'm'))),
            {'type': 'error', 'id': 2, 'error': {'code': 'c', 'type': 't', 'message': 'm'}},
        )

    def test_alternate_value_codec(self):
        c = RpcValueEnvelopeCodec(LiteralRpcValueCodec())
        env = RpcRequestMessage(1, 'm', {'blob': b'\x00\xff', 'pair': (1, 2)})
        data = c.encode(env)
        self.assertFalse(data.startswith(b'{"'))
        self.assertEqual(c.decode(data), env)

    def test_unknown_keys_ignored(self):
        c = RpcValueEnvelopeCodec()
        self.assertEqual(
            c.decode(b'{"type":"cancel","id":3,"future":"thing"}'),
            RpcCancelMessage(3),
        )

    def test_malformed(self):
        c = RpcValueEnvelopeCodec()
        for data in [
            b'not json',
            b'\xff\xfe',
            b'[1, 2]',
            b'{"id": 1}',
            b'{"type": 1}',
            b'{"type": "nope"}',
            b'{"type": "request", "method": "m"}',
            b'{"type": "request", "id": null, "method": "m"}',
            b'{"type": "request", "id": 1, "method": 2}',
            b'{"type": "request", "id": 1, "method": ""}',
            b'{"type": "result"}',
            b'{"type": "error", "id": 1, "error": "x"}',
            b'{"type": "error", "id": 1, "error": {"code": "c", "type": "t"}}',
            b'{"type": "error", "id": 1, "error": {"code": "c", "type": "t", "message": "m", "traceback": 1}}',
            b'{"type": "notification"}',
            b'{"type": "ping"}',
            b'{"type": "request", "id": [1], "method": "m"}',
            b'{"type": "result", "id": {"a": 1}}',
            b'{"type": "cancel", "id": []}',
        ]:
            with self.subTest(data=data):
                with self.assertRaises(RpcProtocolError):
                    c.decode(data)


##


class _Rig:
    """A pipeline of the handlers under test, with a queue capturing inbound and a feedback handler for outbound."""

    def __init__(self, *handlers: IoPipelineHandler, raise_immediately: bool = False) -> None:
        self.q = InboundQueueIoPipelineHandler()
        self.fb = FeedbackInboundIoPipelineHandler()
        self.p = IoPipeline.new(
            [*handlers, self.fb, self.q],
            IoPipeline.Config.DEFAULT.update(raise_immediately=raise_immediately),
        )

    def feed_in(self, *msgs: ta.Any) -> None:
        self.p.feed_in(*msgs)

    def feed_out(self, *msgs: ta.Any) -> None:
        self.p.feed_in(self.fb.wrap(*msgs))

    def drain_in(self) -> ta.List[ta.Any]:
        return self.q.drain()

    def drain_out(self) -> ta.List[ta.Any]:
        return self.p.output.drain()


class TestEnvelopeCodecHandler(unittest.TestCase):
    def test_inbound_outbound(self):
        r = _Rig(RpcEnvelopeCodecIoPipelineHandler(max_frame_bytes=1024))

        c = RpcValueEnvelopeCodec()
        env = RpcRequestMessage(1, 'm', {'a': 1})
        r.feed_in(RpcFrame(c.encode(env)))
        self.assertEqual(r.drain_in(), [env])

        r.feed_out(env)
        self.assertEqual(r.drain_out(), [RpcFrame(c.encode(env))])

    def test_malformed_inbound_raises(self):
        r = _Rig(RpcEnvelopeCodecIoPipelineHandler(max_frame_bytes=1024), raise_immediately=True)

        with self.assertRaises(RpcProtocolError):
            r.feed_in(RpcFrame(b'garbage'))
        self.assertEqual(r.drain_in(), [])

    def test_unencodable_outbound_reported_inward(self):
        r = _Rig(RpcEnvelopeCodecIoPipelineHandler(max_frame_bytes=1024))

        env = RpcResultMessage(1, object())
        r.feed_out(env)
        self.assertEqual(r.drain_out(), [])
        [msg] = r.drain_in()
        self.assertIsInstance(msg, Rsm.OutboundEncodeFailed)
        self.assertIs(msg.envelope, env)
        self.assertIsInstance(msg.exc, TypeError)

    def test_oversized_outbound_reported_inward(self):
        r = _Rig(RpcEnvelopeCodecIoPipelineHandler(max_frame_bytes=64))

        r.feed_out(RpcResultMessage(1, 'x' * 100))
        self.assertEqual(r.drain_out(), [])
        [msg] = r.drain_in()
        self.assertIsInstance(msg, Rsm.OutboundEncodeFailed)
        self.assertIsInstance(msg.exc, RpcMessageTooLargeError)

    def test_passthrough(self):
        r = _Rig(RpcEnvelopeCodecIoPipelineHandler(max_frame_bytes=64))
        r.feed_in('other')
        self.assertEqual(r.drain_in(), ['other'])
        r.feed_out('other')
        self.assertEqual(r.drain_out(), ['other'])


##


class TestFraming(unittest.TestCase):
    def test_encode(self):
        r = _Rig(RpcLengthPrefixedFramingIoPipelineHandler(max_frame_bytes=1024))
        r.feed_out(RpcFrame(b'abc'))
        self.assertEqual(r.drain_out(), [b'\x00\x00\x00\x03abc'])

    def test_encode_variants(self):
        r = _Rig(RpcLengthPrefixedFramingIoPipelineHandler(
            max_frame_bytes=1024,
            length_field_length=2,
            byteorder='little',
        ))
        r.feed_out(RpcFrame(b'abc'))
        self.assertEqual(r.drain_out(), [b'\x03\x00abc'])

    def test_decode_whole_and_split(self):
        r = _Rig(RpcLengthPrefixedFramingIoPipelineHandler(max_frame_bytes=1024))
        r.feed_in(b'\x00\x00\x00\x03abc\x00\x00\x00\x00\x00\x00\x00\x02xy')
        self.assertEqual(r.drain_in(), [RpcFrame(b'abc'), RpcFrame(b''), RpcFrame(b'xy')])

        data = b'\x00\x00\x00\x05hello\x00\x00\x00\x02hi'
        for b in data:
            r.feed_in(bytes([b]))
        self.assertEqual(r.drain_in(), [RpcFrame(b'hello'), RpcFrame(b'hi')])

    def test_decode_variants(self):
        r = _Rig(RpcLengthPrefixedFramingIoPipelineHandler(
            max_frame_bytes=1024,
            length_field_length=2,
            byteorder='little',
        ))
        r.feed_in(b'\x03\x00abc')
        self.assertEqual(r.drain_in(), [RpcFrame(b'abc')])

    def test_limits(self):
        r = _Rig(RpcLengthPrefixedFramingIoPipelineHandler(max_frame_bytes=4), raise_immediately=True)
        r.feed_in(b'\x00\x00\x00\x04abcd')
        self.assertEqual(r.drain_in(), [RpcFrame(b'abcd')])

        with self.assertRaises(RpcMessageTooLargeError):
            r.feed_out(RpcFrame(b'abcde'))

    def test_oversized_inbound_fatal(self):
        r = _Rig(RpcLengthPrefixedFramingIoPipelineHandler(max_frame_bytes=4), raise_immediately=True)
        with self.assertRaises(RpcMessageTooLargeError):
            r.feed_in(b'\x00\x00\x00\x05abcde')

    def test_truncated_at_eof(self):
        r = _Rig(RpcLengthPrefixedFramingIoPipelineHandler(max_frame_bytes=1024))
        r.feed_in(IoPipelineMessages.InitialInput())
        r.feed_in(b'\x00\x00\x00\x05ab')
        r.feed_in(IoPipelineMessages.FinalInput())
        msgs = r.drain_in()
        errs = [m for m in msgs if isinstance(m, IoPipelineMessages.Error)]
        self.assertEqual(len(errs), 1)
        self.assertIsInstance(errs[0].exc, RpcProtocolError)
        self.assertIsInstance(msgs[-1], IoPipelineMessages.FinalInput)

    def test_constructor_validation(self):
        with self.assertRaises(ValueError):
            RpcLengthPrefixedFramingIoPipelineHandler(max_frame_bytes=0)
        with self.assertRaises(ValueError):
            RpcLengthPrefixedFramingIoPipelineHandler(max_frame_bytes=10, length_field_length=3)
        with self.assertRaises(ValueError):
            RpcLengthPrefixedFramingIoPipelineHandler(max_frame_bytes=1 << 16, length_field_length=2)
        RpcLengthPrefixedFramingIoPipelineHandler(max_frame_bytes=(1 << 16) - 1, length_field_length=2)


##


class TestEnvelopeValidation(unittest.TestCase):
    def test_validation(self):
        with self.assertRaises(RpcProtocolError):
            RpcRequestMessage(None, 'm')
        with self.assertRaises(RpcProtocolError):
            RpcRequestMessage(1, '')
        with self.assertRaises(RpcProtocolError):
            RpcErrorMessage(1, 'not error data')  # type: ignore[arg-type]
        with self.assertRaises(RpcProtocolError):
            RpcPongMessage(None)
