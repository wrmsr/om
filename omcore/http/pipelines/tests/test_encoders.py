# ruff: noqa: UP006 UP007 UP045
# @om-lite
import unittest

from ....io.pipelines.core import IoPipeline
from ....io.pipelines.handlers.feedback import FeedbackInboundIoPipelineHandler
from ....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ....io.streambufs.utils import ByteStreamBuffers
from ...headers import HttpHeaders
from ...versions import HttpVersion
from ..clients.requests import IoPipelineHttpRequestEncoder
from ..requests import FullIoPipelineHttpRequest
from ..requests import IoPipelineHttpRequestChunkedTrailers
from ..requests import IoPipelineHttpRequestHead
from ..responses import FullIoPipelineHttpResponse
from ..responses import IoPipelineHttpResponseBodyData
from ..responses import IoPipelineHttpResponseChunk
from ..responses import IoPipelineHttpResponseChunkedTrailers
from ..responses import IoPipelineHttpResponseEnd
from ..responses import IoPipelineHttpResponseEndChunk
from ..responses import IoPipelineHttpResponseHead
from ..responses import IoPipelineHttpResponseLastChunk
from ..servers.requests import IoPipelineHttpRequestDecoder
from ..servers.responses import IoPipelineHttpResponseEncoder


##


def _new_response_encoder_pipeline() -> IoPipeline:
    return IoPipeline.new([
        IoPipelineHttpResponseEncoder(),
        FeedbackInboundIoPipelineHandler(),
    ])


def _full_response(body: bytes) -> FullIoPipelineHttpResponse:
    return FullIoPipelineHttpResponse(
        head=IoPipelineHttpResponseHead(
            version=HttpVersion(1, 1),
            status=200,
            reason='OK',
            headers=HttpHeaders([('Content-Length', str(len(body)))]),
        ),
        body=body,
    )


##


class TestBodyData(unittest.TestCase):
    def test_non_streaming_body_data_is_passed_through_once(self) -> None:
        channel = IoPipeline.new([
            IoPipelineHttpResponseEncoder(),
            fbi := FeedbackInboundIoPipelineHandler(),
        ])

        channel.feed_in(fbi.wrap(_full_response(b'hello')))
        channel.output.drain()

        channel.feed_in(fbi.wrap(IoPipelineHttpResponseBodyData(b'world')))

        out = channel.output.drain()
        self.assertEqual(len(out), 1)
        self.assertIsInstance(out[0], IoPipelineHttpResponseBodyData)

    def test_streaming_body_data_is_encoded_once(self) -> None:
        channel = IoPipeline.new([
            IoPipelineHttpResponseEncoder(),
            fbi := FeedbackInboundIoPipelineHandler(),
        ])

        channel.feed_in(fbi.wrap(IoPipelineHttpResponseHead(
            version=HttpVersion(1, 1),
            status=200,
            reason='OK',
            headers=HttpHeaders([('Content-Length', '5')]),
        )))
        channel.output.drain()

        channel.feed_in(fbi.wrap(IoPipelineHttpResponseBodyData(b'world')))
        channel.feed_in(fbi.wrap(IoPipelineHttpResponseEnd()))

        out = channel.output.drain()
        self.assertEqual(out, [b'world'])


##


class TestObsTextEncoding(unittest.TestCase):
    def test_obs_text_header_value(self) -> None:
        channel = IoPipeline.new([
            IoPipelineHttpResponseEncoder(),
            fbi := FeedbackInboundIoPipelineHandler(),
        ])

        channel.feed_in(fbi.wrap(FullIoPipelineHttpResponse(
            head=IoPipelineHttpResponseHead(
                version=HttpVersion(1, 1),
                status=200,
                reason='OK',
                headers=HttpHeaders([('X-Y', 'caf\xe9')]),
            ),
            body=b'',
        )))

        out = channel.output.drain()
        self.assertEqual(out, [b'HTTP/1.1 200 OK\r\nX-Y: caf\xe9\r\n\r\n'])

    def test_obs_text_reason_phrase(self) -> None:
        channel = IoPipeline.new([
            IoPipelineHttpResponseEncoder(),
            fbi := FeedbackInboundIoPipelineHandler(),
        ])

        channel.feed_in(fbi.wrap(FullIoPipelineHttpResponse(
            head=IoPipelineHttpResponseHead(
                version=HttpVersion(1, 1),
                status=200,
                reason='caf\xe9',
                headers=HttpHeaders([]),
            ),
            body=b'',
        )))

        out = channel.output.drain()
        self.assertEqual(out, [b'HTTP/1.1 200 caf\xe9\r\n\r\n'])

    def test_decoded_request_round_trips(self) -> None:
        raw = b'GET /caf\xe9 HTTP/1.1\r\nHost: t\r\nX-Y: caf\xe9\r\n\r\n'

        dec_channel = IoPipeline.new([
            IoPipelineHttpRequestDecoder(),
            ibq := InboundQueueIoPipelineHandler(),
        ])
        dec_channel.feed_in(raw)

        head = ibq.drain()[0]
        self.assertIsInstance(head, IoPipelineHttpRequestHead)

        enc_channel = IoPipeline.new([
            IoPipelineHttpRequestEncoder(),
            fbi := FeedbackInboundIoPipelineHandler(),
        ])
        enc_channel.feed_in(fbi.wrap(FullIoPipelineHttpRequest(head=head, body=b'')))

        # Note: the parsed head's field names are normalized to lowercase.
        self.assertEqual(
            b''.join(enc_channel.output.drain()),
            b'GET /caf\xe9 HTTP/1.1\r\nhost: t\r\nx-y: caf\xe9\r\n\r\n',
        )


##


class TestChunkedTrailersEncoding(unittest.TestCase):
    def _encode(self, trailers: HttpHeaders) -> bytes:
        channel = IoPipeline.new([
            IoPipelineHttpResponseEncoder(),
            fbi := FeedbackInboundIoPipelineHandler(),
        ])

        channel.feed_in(fbi.wrap(
            IoPipelineHttpResponseHead(
                version=HttpVersion(1, 1),
                status=200,
                reason='OK',
                headers=HttpHeaders([('Transfer-Encoding', 'chunked')]),
            ),
            IoPipelineHttpResponseChunk(5),
            IoPipelineHttpResponseBodyData(b'hello'),
            IoPipelineHttpResponseEndChunk(),
            IoPipelineHttpResponseLastChunk(),
            IoPipelineHttpResponseChunkedTrailers(trailers),
            IoPipelineHttpResponseEnd(),
        ))

        return b''.join(
            ByteStreamBuffers.to_bytes(msg, strict=True)
            for msg in channel.output.drain()
            if ByteStreamBuffers.can_bytes(msg)
        )

    def test_empty_trailers_write_only_the_terminator(self) -> None:
        self.assertEqual(
            self._encode(HttpHeaders([])),
            b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n',
        )

    def test_trailer_fields_are_written(self) -> None:
        self.assertEqual(
            self._encode(HttpHeaders([('X-Sig', 'abc'), ('Expires', 'x')])),
            b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n'
            b'5\r\nhello\r\n0\r\nX-Sig: abc\r\nExpires: x\r\n\r\n',
        )

    def test_decoded_trailers_round_trip(self) -> None:
        decode_channel = IoPipeline.new([
            IoPipelineHttpRequestDecoder(),
            ibq := InboundQueueIoPipelineHandler(),
        ])
        decode_channel.feed_in(
            b'POST / HTTP/1.1\r\nHost: t\r\nTransfer-Encoding: chunked\r\n\r\n'
            b'5\r\nhello\r\n0\r\nX-Sig: abc\r\n\r\n',
        )

        [trailers] = [m for m in ibq.drain() if isinstance(m, IoPipelineHttpRequestChunkedTrailers)]

        # Note: as with parsed heads, the parsed field names are normalized to lowercase.
        self.assertEqual(self._encode(trailers.trailers).split(b'0\r\n')[-1], b'x-sig: abc\r\n\r\n')
