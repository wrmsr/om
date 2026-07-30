# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta
import unittest

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineHandler
from .....io.pipelines.core import IoPipelineHandlerContext
from .....io.pipelines.handlers.feedback import FeedbackInboundIoPipelineHandler
from .....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from .....io.streambufs.utils import ByteStreamBuffers
from ....headers import HttpHeaders
from ...requests import IoPipelineHttpRequestHead
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ..frames import IoPipelineWebsocketFrameDecoder
from ..frames import IoPipelineWebsocketFrameEncoder
from ..handshakes import IoPipelineWebsocketClientUpgradeHandler
from ..handshakes import IoPipelineWebsocketHandshakes
from ..objects import IoPipelineWebsocketFrame
from ..objects import IoPipelineWebsocketOpcode
from ..objects import IoPipelineWebsocketOpen
from ..objects import IoPipelineWebsocketText


class OutboundAdapter(IoPipelineHandler):
    """Converts inbound into outbound to exercise encoders in tests."""

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        ctx.feed_out(msg)


class TestBasic(unittest.TestCase):
    def test_ws_accept_computation(self):
        # From RFC 6455 example
        key = 'dGhlIHNhbXBsZSBub25jZQ=='
        expected_accept = 's3pPLMBiTxaQ9kYGzzhZRbK+xOo='
        assert IoPipelineWebsocketHandshakes.compute_accept_for_key(key) == expected_accept

    def test_text_roundtrip_encode_decode(self):
        # Encode as a client (masking enabled)
        enc = IoPipelineWebsocketFrameEncoder(mask=True)
        p_enc = IoPipeline.new([enc, OutboundAdapter()])

        p_enc.feed_in(IoPipelineWebsocketText('hi'))
        data = p_enc.output.drain()
        assert all(ByteStreamBuffers.can_bytes(part) for part in data)
        assert sum(ByteStreamBuffers.bytes_len(part) for part in data) >= 6  # header + mask + payload

        # Decode as a server (expects masked inbound)
        dec = IoPipelineWebsocketFrameDecoder(expect_masked=True)
        p_dec = IoPipeline(IoPipeline.Spec([dec, ibq := InboundQueueIoPipelineHandler()]))

        p_dec.feed_in(*data)

        # Find the decoded frame in the tap
        got = [m for m in ibq.drain() if isinstance(m, IoPipelineWebsocketFrame)]
        assert len(got) >= 1
        f = got[-1]
        assert f.opcode == IoPipelineWebsocketOpcode.TEXT
        assert ByteStreamBuffers.to_bytes(f.payload) == b'hi'

    def test_client_upgrade_consumes_response_end(self) -> None:
        handler = IoPipelineWebsocketClientUpgradeHandler(host='localhost')
        pipeline = IoPipeline.new([
            handler,
            fbi := FeedbackInboundIoPipelineHandler(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        request = IoPipelineHttpRequestHead(
            method='GET',
            target='/',
            headers=HttpHeaders([]),
        )
        pipeline.feed_in(fbi.wrap(request))
        upgraded_request = pipeline.output.poll()
        assert isinstance(upgraded_request, IoPipelineHttpRequestHead)
        key = upgraded_request.headers.single['Sec-Websocket-Key']

        pipeline.feed_in(
            IoPipelineHttpResponseHead(
                status=101,
                reason='Switching Protocols',
                headers=HttpHeaders([
                    (
                        'Sec-Websocket-Accept',
                        IoPipelineWebsocketHandshakes.compute_accept_for_key(key),
                    ),
                ]),
            ),
            IoPipelineHttpResponseEnd(),
            IoPipelineWebsocketText('ready'),
        )

        opened, text = ibq.drain()
        self.assertIsInstance(opened, IoPipelineWebsocketOpen)
        self.assertEqual(text, IoPipelineWebsocketText('ready'))
