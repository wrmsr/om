# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta
import unittest

from ....io.pipelines.core import IoPipeline
from ....io.pipelines.handlers.feedback import FeedbackInboundIoPipelineHandler
from ....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ...headers import HttpHeaders
from ..bodymodes import IoPipelineHttpBodyMode
from ..bodymodes import is_chunked_transfer_encoding
from ..clients.requests import IoPipelineHttpRequestChunker
from ..requests import IoPipelineHttpRequestBodyData
from ..requests import IoPipelineHttpRequestChunk
from ..requests import IoPipelineHttpRequestChunkedTrailers
from ..requests import IoPipelineHttpRequestEnd
from ..requests import IoPipelineHttpRequestEndChunk
from ..requests import IoPipelineHttpRequestHead
from ..requests import IoPipelineHttpRequestLastChunk
from ..servers.requests import IoPipelineHttpRequestDechunker
from ..servers.requests import IoPipelineHttpRequestDecoder


##


class TestIsChunkedTransferEncoding(unittest.TestCase):
    def test_list_values(self) -> None:
        for value, expected in [
            ('chunked', True),
            ('Chunked', True),
            ('gzip, chunked', True),
            ('gzip,chunked', True),
            ('gzip , Chunked ', True),
            ('gzip', False),
            ('chunked, gzip', False),  # RFC 9112 requires chunked to be the last coding
            ('chunkedy', False),
            ('xchunked', False),
        ]:
            with self.subTest(value=value):
                self.assertEqual(
                    is_chunked_transfer_encoding(HttpHeaders([('Transfer-Encoding', value)])),
                    expected,
                )

    def test_repeated_header_lines(self) -> None:
        self.assertTrue(is_chunked_transfer_encoding(HttpHeaders([
            ('Transfer-Encoding', 'gzip'),
            ('Transfer-Encoding', 'chunked'),
        ])))

        self.assertFalse(is_chunked_transfer_encoding(HttpHeaders([
            ('Transfer-Encoding', 'chunked'),
            ('Transfer-Encoding', 'gzip'),
        ])))

    def test_missing(self) -> None:
        self.assertFalse(is_chunked_transfer_encoding(HttpHeaders([('Host', 't')])))


class TestBodyModeSelect(unittest.TestCase):
    def test_multi_coding_transfer_encoding_is_chunked(self) -> None:
        te = IoPipelineHttpBodyMode.select(
            HttpHeaders([('Transfer-Encoding', 'gzip, chunked')]),
            if_length_missing='empty',
        )
        self.assertEqual(te.mode, 'chunked')


##


class TestMultiCodingFraming(unittest.TestCase):
    _RAW = (
        b'POST / HTTP/1.1\r\n'
        b'Host: t\r\n'
        b'Transfer-Encoding: gzip, chunked\r\n'
        b'\r\n'
        b'5\r\nhello\r\n'
        b'0\r\n\r\n'
    )

    def test_decoder_frames_multi_coding_body(self) -> None:
        channel = IoPipeline.new([
            IoPipelineHttpRequestDecoder(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        # Without chunked framing the body's framing bytes would themselves be parsed as the next request head, and the
        # pipelined request below would be swallowed as its body - request smuggling.
        channel.feed_in(self._RAW + b'GET /next HTTP/1.1\r\nHost: t\r\n\r\n')

        out = ibq.drain()
        self.assertEqual(
            [type(m) for m in out],
            [
                IoPipelineHttpRequestHead,
                IoPipelineHttpRequestChunk,
                IoPipelineHttpRequestBodyData,
                IoPipelineHttpRequestEndChunk,
                IoPipelineHttpRequestLastChunk,
                IoPipelineHttpRequestChunkedTrailers,
                IoPipelineHttpRequestEnd,
                IoPipelineHttpRequestHead,
                IoPipelineHttpRequestEnd,
            ],
        )
        self.assertEqual(out[7].target, '/next')

    def test_dechunker_strips_multi_coding_framing(self) -> None:
        channel = IoPipeline.new([
            IoPipelineHttpRequestDecoder(),
            IoPipelineHttpRequestDechunker(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        channel.feed_in(self._RAW)

        out = ibq.drain()
        self.assertEqual(
            [type(m) for m in out],
            [
                IoPipelineHttpRequestHead,
                IoPipelineHttpRequestBodyData,
                IoPipelineHttpRequestEnd,
            ],
        )

    def test_chunker_frames_multi_coding_body(self) -> None:
        channel = IoPipeline.new([
            IoPipelineHttpRequestChunker(),
            fbi := FeedbackInboundIoPipelineHandler(),
        ])

        head = IoPipelineHttpRequestHead(
            method='POST',
            target='/',
            headers=HttpHeaders([('Transfer-Encoding', 'gzip, chunked')]),
        )
        channel.feed_in(fbi.wrap(head))
        channel.feed_in(fbi.wrap(IoPipelineHttpRequestBodyData(b'hello')))
        channel.feed_in(fbi.wrap(IoPipelineHttpRequestEnd()))

        out = channel.output.drain()
        self.assertEqual(
            [type(m) for m in out],
            [
                IoPipelineHttpRequestHead,
                IoPipelineHttpRequestChunk,
                IoPipelineHttpRequestBodyData,
                IoPipelineHttpRequestEndChunk,
                IoPipelineHttpRequestLastChunk,
                IoPipelineHttpRequestChunkedTrailers,
                IoPipelineHttpRequestEnd,
            ],
        )


##


class TestDechunkerTrailers(unittest.TestCase):
    _RAW: ta.ClassVar[bytes] = (
        b'POST / HTTP/1.1\r\n'
        b'Host: t\r\n'
        b'Transfer-Encoding: chunked\r\n'
        b'\r\n'
        b'5\r\nhello\r\n'
        b'0\r\nX-Sig: abc\r\n\r\n'
    )

    def _run(self, **kwargs: ta.Any) -> ta.List[ta.Any]:
        channel = IoPipeline.new([
            IoPipelineHttpRequestDecoder(),
            IoPipelineHttpRequestDechunker(**kwargs),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        channel.feed_in(self._RAW)

        return ibq.drain()

    def test_trailers_are_stripped_by_default(self) -> None:
        # Downstream readers are written against the stripped Head + BodyData* + End stream.
        self.assertEqual(
            [type(m) for m in self._run()],
            [
                IoPipelineHttpRequestHead,
                IoPipelineHttpRequestBodyData,
                IoPipelineHttpRequestEnd,
            ],
        )

    def test_keep_trailers_forwards_them(self) -> None:
        out = self._run(keep_trailers=True)

        self.assertEqual(
            [type(m) for m in out],
            [
                IoPipelineHttpRequestHead,
                IoPipelineHttpRequestBodyData,
                IoPipelineHttpRequestChunkedTrailers,
                IoPipelineHttpRequestEnd,
            ],
        )
        self.assertEqual(out[2].trailers.single['x-sig'], 'abc')
