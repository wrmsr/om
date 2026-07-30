# ruff: noqa: UP006 UP007 UP045
# @om-lite
import unittest

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.handlers.feedback import FeedbackInboundIoPipelineHandler
from .....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from .....io.streambufs.utils import ByteStreamBuffers
from ....headers import HttpHeaders
from ...bodymodes import IoPipelineHttpBodyMode
from ...bodymodes import IoPipelineHttpBodyModeError
from ...requests import FullIoPipelineHttpRequest
from ...responses import IoPipelineHttpResponseAborted
from ...responses import IoPipelineHttpResponseBodyData
from ...responses import IoPipelineHttpResponseEnd
from ...responses import IoPipelineHttpResponseHead
from ..requests import IoPipelineHttpRequestEncoder
from ..responses import IoPipelineHttpClientResponseDecoder
from ..responses import IoPipelineHttpResponseDecoder


class TestPipelineHttpResponseDecoder(unittest.TestCase):
    def test_basic_response_head(self) -> None:
        """Test basic HTTP response head parsing."""

        decoder = IoPipelineHttpResponseDecoder()
        channel = IoPipeline.new([
            decoder,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        response = b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\n'
        channel.feed_in(response)

        out = ibq.drain()
        self.assertEqual(len(out), 1)

        head = out[0]
        self.assertEqual(head.status, 200)
        self.assertEqual(head.reason, 'OK')
        self.assertEqual(head.headers.single.get('content-length'), '5')

    def test_response_with_body_in_same_chunk(self) -> None:
        """Test response head + body bytes received together."""

        decoder = IoPipelineHttpResponseDecoder()
        channel = IoPipeline.new([
            decoder,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        response = b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello'
        channel.feed_in(response)

        head, body, end = ibq.drain()

        # First: head
        self.assertEqual(head.status, 200)

        # Second: body bytes
        self.assertIsInstance(body, IoPipelineHttpResponseBodyData)
        self.assertEqual(ByteStreamBuffers.to_bytes(body.data), b'hello')

        self.assertIsInstance(end, IoPipelineHttpResponseEnd)

    def test_response_incremental_head(self) -> None:
        """Test response head received incrementally."""

        decoder = IoPipelineHttpResponseDecoder()
        channel = IoPipeline.new([
            decoder,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        # Send head in parts
        channel.feed_in(b'HTTP/1.1 200 OK\r\n')
        out = ibq.drain()
        self.assertEqual(len(out), 0)  # Not complete yet

        channel.feed_in(b'Content-Type: text/plain\r\n\r\n')
        out = ibq.drain()
        self.assertEqual(len(out), 1)

        head = out[0]
        self.assertEqual(head.status, 200)
        self.assertEqual(head.headers.single.get('content-type'), 'text/plain')

    def test_eof_before_head_complete(self) -> None:
        """Test EOF arriving before head is complete raises ValueError."""

        decoder = IoPipelineHttpResponseDecoder()
        channel = IoPipeline.new([
            decoder,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        # Send partial head
        channel.feed_in(b'HTTP/1.1 200 OK\r\n')

        # Send EOF
        channel.feed_final_input()

        out = ibq.drain()

        # Should get an aborted message
        aborted, eof = out
        self.assertIsInstance(aborted, IoPipelineHttpResponseAborted)
        self.assertIsInstance(eof, IoPipelineMessages.FinalInput)

    def test_status_derived_empty_responses_are_request_agnostic(self) -> None:
        channel = IoPipeline.new([
            IoPipelineHttpResponseDecoder(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        channel.feed_in(
            b'HTTP/1.1 100 Continue\r\nContent-Length: 99\r\n\r\n'
            b'HTTP/1.1 204 No Content\r\nContent-Length: 99\r\n\r\n'
            b'HTTP/1.1 304 Not Modified\r\nTransfer-Encoding: chunked\r\n\r\n'
            b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello',
        )

        out = ibq.drain()
        self.assertEqual(
            [msg.status for msg in out if isinstance(msg, IoPipelineHttpResponseHead)],
            [100, 204, 304, 200],
        )
        self.assertEqual(sum(isinstance(msg, IoPipelineHttpResponseEnd) for msg in out), 4)
        self.assertEqual(
            [ByteStreamBuffers.to_bytes(msg.data) for msg in out if isinstance(msg, IoPipelineHttpResponseBodyData)],
            [b'hello'],
        )

    def test_switching_protocols_passes_through_coalesced_bytes(self) -> None:
        channel = IoPipeline.new([
            IoPipelineHttpResponseDecoder(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        channel.feed_in(
            b'HTTP/1.1 101 Switching Protocols\r\nConnection: upgrade\r\nUpgrade: example\r\n\r\n'
            b'opaque upgraded bytes',
        )

        head, end, opaque = ibq.drain()
        self.assertIsInstance(head, IoPipelineHttpResponseHead)
        self.assertIsInstance(end, IoPipelineHttpResponseEnd)
        self.assertEqual(ByteStreamBuffers.to_bytes(opaque), b'opaque upgraded bytes')

    def test_transfer_encoding_with_content_length_is_rejected(self) -> None:
        with self.assertRaisesRegex(IoPipelineHttpBodyModeError, 'both Transfer-Encoding and Content-Length'):
            IoPipelineHttpBodyMode.select(
                HttpHeaders([
                    ('Transfer-Encoding', 'chunked'),
                    ('Content-Length', '5'),
                ]),
                if_length_missing='eof',
            )


class TestPipelineHttpClientResponseDecoder(unittest.TestCase):
    @staticmethod
    def _make_channel():
        channel = IoPipeline.new([
            IoPipelineHttpRequestEncoder(),
            IoPipelineHttpClientResponseDecoder(),
            fbi := FeedbackInboundIoPipelineHandler(),
            ibq := InboundQueueIoPipelineHandler(),
        ])
        return channel, fbi, ibq

    def test_rejects_response_without_request(self) -> None:
        channel = IoPipeline.new(
            [IoPipelineHttpClientResponseDecoder()],
            IoPipeline.Config(raise_immediately=True, inbound_terminal='drop'),
        )

        with self.assertRaisesRegex(RuntimeError, 'without a corresponding request'):
            channel.feed_in(b'HTTP/1.1 204 No Content\r\n\r\n')

    def test_head_does_not_consume_the_next_response(self) -> None:
        channel, fbi, ibq = self._make_channel()

        channel.feed_in(fbi.wrap(
            FullIoPipelineHttpRequest.simple('test', '/head', method='HEAD'),
            FullIoPipelineHttpRequest.simple('test', '/get'),
        ))
        channel.output.drain()

        channel.feed_in(
            b'HTTP/1.1 200 OK\r\nContent-Length: 999\r\nContent-Encoding: gzip\r\n\r\n'
            b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello',
        )

        out = ibq.drain()
        self.assertEqual(
            [msg.status for msg in out if isinstance(msg, IoPipelineHttpResponseHead)],
            [200, 200],
        )
        self.assertEqual(sum(isinstance(msg, IoPipelineHttpResponseEnd) for msg in out), 2)
        self.assertEqual(
            [ByteStreamBuffers.to_bytes(msg.data) for msg in out if isinstance(msg, IoPipelineHttpResponseBodyData)],
            [b'hello'],
        )

    def test_interim_response_does_not_consume_request_method(self) -> None:
        channel, fbi, ibq = self._make_channel()

        channel.feed_in(fbi.wrap(
            FullIoPipelineHttpRequest.simple('test', '/head', method='HEAD'),
            FullIoPipelineHttpRequest.simple('test', '/get'),
        ))
        channel.output.drain()

        channel.feed_in(
            b'HTTP/1.1 100 Continue\r\n\r\n'
            b'HTTP/1.1 200 OK\r\nContent-Length: 999\r\n\r\n'
            b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok',
        )

        out = ibq.drain()
        self.assertEqual(
            [msg.status for msg in out if isinstance(msg, IoPipelineHttpResponseHead)],
            [100, 200, 200],
        )
        self.assertEqual(sum(isinstance(msg, IoPipelineHttpResponseEnd) for msg in out), 3)
        self.assertEqual(
            [ByteStreamBuffers.to_bytes(msg.data) for msg in out if isinstance(msg, IoPipelineHttpResponseBodyData)],
            [b'ok'],
        )

    def test_successful_connect_enters_tunnel_mode(self) -> None:
        channel, fbi, ibq = self._make_channel()

        channel.feed_in(fbi.wrap(FullIoPipelineHttpRequest.simple(
            'example.com',
            'example.com:443',
            method='CONNECT',
        )))
        channel.output.drain()

        channel.feed_in(
            b'HTTP/1.1 200 Connection Established\r\nContent-Length: 999\r\n\r\n'
            b'opaque tunnel bytes',
        )

        head, end, opaque = ibq.drain()
        self.assertIsInstance(head, IoPipelineHttpResponseHead)
        self.assertIsInstance(end, IoPipelineHttpResponseEnd)
        self.assertEqual(ByteStreamBuffers.to_bytes(opaque), b'opaque tunnel bytes')

    def test_switching_protocols_enters_tunnel_mode(self) -> None:
        channel, fbi, ibq = self._make_channel()

        channel.feed_in(fbi.wrap(FullIoPipelineHttpRequest.simple('test', '/upgrade')))
        channel.output.drain()

        channel.feed_in(
            b'HTTP/1.1 101 Switching Protocols\r\nConnection: upgrade\r\nUpgrade: example\r\n\r\n'
            b'opaque upgraded bytes',
        )

        head, end, opaque = ibq.drain()
        self.assertIsInstance(head, IoPipelineHttpResponseHead)
        self.assertIsInstance(end, IoPipelineHttpResponseEnd)
        self.assertEqual(ByteStreamBuffers.to_bytes(opaque), b'opaque upgraded bytes')
