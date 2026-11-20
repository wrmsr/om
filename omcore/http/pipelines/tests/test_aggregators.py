# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta
import unittest

from ....io.pipelines.core import IoPipeline
from ....io.pipelines.core import IoPipelineMessages
from ....io.pipelines.handlers.feedback import FeedbackInboundIoPipelineHandler
from ....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ....io.streambufs.errors import FrameTooLargeByteStreamBufferError
from ....io.streambufs.utils import ByteStreamBuffers
from ..aggregators import IoPipelineHttpAggregationConfig
from ..clients.requests import IoPipelineHttpRequestEncoder
from ..clients.responses import IoPipelineHttpClientResponseDecoder
from ..clients.responses import IoPipelineHttpResponseAggregatorDecoder
from ..requests import FullIoPipelineHttpRequest
from ..requests import IoPipelineHttpRequestAborted
from ..responses import FullIoPipelineHttpResponse
from ..responses import IoPipelineHttpResponseAborted
from ..servers.requests import IoPipelineHttpRequestAggregatorDecoder
from ..servers.requests import IoPipelineHttpRequestDecoder


##


def _new_aggregating_pipeline(
        config: IoPipelineHttpAggregationConfig = IoPipelineHttpAggregationConfig.DEFAULT,
) -> ta.Tuple[IoPipeline, InboundQueueIoPipelineHandler]:
    return (
        IoPipeline.new([
            IoPipelineHttpRequestDecoder(),
            IoPipelineHttpRequestAggregatorDecoder(config=config),
            ibq := InboundQueueIoPipelineHandler(),
        ]),
        ibq,
    )


def _chunked_request(body: bytes) -> bytes:
    return (
        b'POST / HTTP/1.1\r\n'
        b'Host: t\r\n'
        b'Transfer-Encoding: chunked\r\n'
        b'\r\n' +
        f'{len(body):x}'.encode('ascii') + b'\r\n' + body + b'\r\n'
        b'0\r\n\r\n'
    )


##


class TestOversizedBodies(unittest.TestCase):
    def test_oversized_chunked_body_aborts_without_truncated_full(self) -> None:
        channel, ibq = _new_aggregating_pipeline(IoPipelineHttpAggregationConfig(
            body_buffer=IoPipelineHttpAggregationConfig.BufferConfig(max_size=4096, chunk_size=4096),
        ))

        channel.feed_in(_chunked_request(b'a' * 100000))

        out = ibq.drain()
        self.assertEqual(len(out), 1)
        self.assertIsInstance(out[0], IoPipelineHttpRequestAborted)

    def test_oversized_chunked_body_across_many_chunks_aborts(self) -> None:
        channel, ibq = _new_aggregating_pipeline(IoPipelineHttpAggregationConfig(
            body_buffer=IoPipelineHttpAggregationConfig.BufferConfig(max_size=16, chunk_size=16),
        ))

        channel.feed_in(
            b'POST / HTTP/1.1\r\nHost: t\r\nTransfer-Encoding: chunked\r\n\r\n' +
            b''.join(b'8\r\n' + b'a' * 8 + b'\r\n' for _ in range(4)) +
            b'0\r\n\r\n',
        )

        out = ibq.drain()
        self.assertEqual(len(out), 1)
        self.assertIsInstance(out[0], IoPipelineHttpRequestAborted)

    def test_chunked_body_within_max_is_aggregated(self) -> None:
        channel, ibq = _new_aggregating_pipeline(IoPipelineHttpAggregationConfig(
            body_buffer=IoPipelineHttpAggregationConfig.BufferConfig(max_size=4096, chunk_size=4096),
        ))

        channel.feed_in(_chunked_request(b'a' * 4096))

        out = ibq.drain()
        self.assertEqual(len(out), 1)
        self.assertIsInstance(out[0], FullIoPipelineHttpRequest)
        self.assertEqual(ByteStreamBuffers.to_bytes(out[0].body), b'a' * 4096)

    def test_oversized_content_length_body_aborts(self) -> None:
        channel, ibq = _new_aggregating_pipeline(IoPipelineHttpAggregationConfig(
            body_buffer=IoPipelineHttpAggregationConfig.BufferConfig(max_size=16, chunk_size=16),
        ))

        channel.feed_in(
            b'POST / HTTP/1.1\r\nHost: t\r\nContent-Length: 100\r\n\r\n' +
            b'a' * 100,
        )

        out = ibq.drain()
        self.assertEqual(len(out), 1)
        self.assertIsInstance(out[0], IoPipelineHttpRequestAborted)


##


class TestAbortedState(unittest.TestCase):
    def test_streamed_remainder_after_abort_is_discarded(self) -> None:
        channel, ibq = _new_aggregating_pipeline(IoPipelineHttpAggregationConfig(
            body_buffer=IoPipelineHttpAggregationConfig.BufferConfig(max_size=16, chunk_size=16),
        ))

        # The decoder keeps streaming BodyData / End from the same read after the aggregator has aborted.
        channel.feed_in(
            b'POST / HTTP/1.1\r\nHost: t\r\nContent-Length: 100\r\n\r\n' +
            b'a' * 100,
        )
        channel.feed_final_input()

        out = ibq.drain()
        self.assertEqual(len(out), 2)
        self.assertIsInstance(out[0], IoPipelineHttpRequestAborted)
        self.assertIsInstance(out[1], IoPipelineMessages.FinalInput)


##


class TestAggregatedTrailers(unittest.TestCase):
    def test_trailers_are_carried_onto_the_full_message(self) -> None:
        channel, ibq = _new_aggregating_pipeline()

        channel.feed_in(
            b'POST / HTTP/1.1\r\nHost: t\r\nTransfer-Encoding: chunked\r\n\r\n'
            b'5\r\nhello\r\n'
            b'0\r\nExpires: x\r\nX-Y: z\r\n\r\n',
        )

        [full] = [m for m in ibq.drain() if isinstance(m, FullIoPipelineHttpRequest)]
        self.assertEqual(ByteStreamBuffers.to_bytes(full.body, strict=True), b'hello')
        self.assertEqual(full.trailers.single['expires'], 'x')
        self.assertEqual(full.trailers.single['x-y'], 'z')

        # Never merged - see IoPipelineHttpMessageChunkedTrailers.
        self.assertNotIn('x-y', dict(full.head.headers.items()))

    def test_no_trailers_yields_empty(self) -> None:
        channel, ibq = _new_aggregating_pipeline()

        channel.feed_in(
            b'POST / HTTP/1.1\r\nHost: t\r\nTransfer-Encoding: chunked\r\n\r\n'
            b'5\r\nhello\r\n0\r\n\r\n',
        )

        [full] = [m for m in ibq.drain() if isinstance(m, FullIoPipelineHttpRequest)]
        self.assertEqual(len(full.trailers), 0)

    def test_content_length_body_has_empty_trailers(self) -> None:
        channel, ibq = _new_aggregating_pipeline()

        channel.feed_in(b'POST / HTTP/1.1\r\nHost: t\r\nContent-Length: 5\r\n\r\nhello')

        [full] = [m for m in ibq.drain() if isinstance(m, FullIoPipelineHttpRequest)]
        self.assertEqual(ByteStreamBuffers.to_bytes(full.body, strict=True), b'hello')
        self.assertEqual(len(full.trailers), 0)

    def test_trailers_do_not_leak_across_pipelined_messages(self) -> None:
        channel, ibq = _new_aggregating_pipeline()

        channel.feed_in(
            b'POST / HTTP/1.1\r\nHost: t\r\nTransfer-Encoding: chunked\r\n\r\n'
            b'5\r\nhello\r\n0\r\nX-Y: z\r\n\r\n'
            b'POST / HTTP/1.1\r\nHost: t\r\nTransfer-Encoding: chunked\r\n\r\n'
            b'5\r\nworld\r\n0\r\n\r\n',
        )

        first, second = [m for m in ibq.drain() if isinstance(m, FullIoPipelineHttpRequest)]
        self.assertEqual(first.trailers.single['x-y'], 'z')
        self.assertEqual(len(second.trailers), 0)


##


class TestResponseAggregatorBodylessAndHeadRegressions(unittest.TestCase):
    @staticmethod
    def _new_client_response_pipeline(
            max_size: int = 16,
    ) -> ta.Tuple[IoPipeline, FeedbackInboundIoPipelineHandler, InboundQueueIoPipelineHandler]:
        fbi = FeedbackInboundIoPipelineHandler()
        ibq = InboundQueueIoPipelineHandler()
        channel = IoPipeline.new([
            IoPipelineHttpRequestEncoder(),
            IoPipelineHttpClientResponseDecoder(),
            IoPipelineHttpResponseAggregatorDecoder(config=IoPipelineHttpAggregationConfig(
                body_buffer=IoPipelineHttpAggregationConfig.BufferConfig(max_size=max_size, chunk_size=max_size),
            )),
            fbi,
            ibq,
        ])
        return channel, fbi, ibq

    def test_head_response_with_large_content_length_is_not_aborted(self) -> None:
        # Regression: IoPipelineHttpResponseAggregatorDecoder previously checked Content-Length > max_size eagerly in
        # _HeadState. Because a HEAD response legally carries the target resource's Content-Length (e.g. 100000) while
        # sending 0 body bytes (Head + End), any HEAD response whose Content-Length exceeded max_size was wrongly
        # aborted with FrameTooLargeByteStreamBufferError.
        channel, fbi, ibq = self._new_client_response_pipeline(max_size=16)

        channel.feed_in(fbi.wrap(FullIoPipelineHttpRequest.simple('example.com', '/big', method='HEAD')))
        channel.output.drain()

        channel.feed_in(b'HTTP/1.1 200 OK\r\nContent-Length: 100000\r\n\r\n')

        [resp] = ibq.drain()
        self.assertIsInstance(resp, FullIoPipelineHttpResponse)
        self.assertEqual(resp.head.status, 200)
        self.assertEqual(resp.head.headers.single['content-length'], '100000')
        self.assertEqual(ByteStreamBuffers.to_bytes(resp.body, strict=True), b'')

    def test_bodyless_status_responses_with_large_content_length_are_not_aborted(self) -> None:
        # Regression: 304 Not Modified, 204 No Content, and 1xx responses never carry a body regardless of
        # Content-Length (304 routinely carries the cached representation's Content-Length). Previously the response
        # aggregator used generic IoPipelineHttpBodyMode.select and aborted them when Content-Length exceeded max_size.
        channel, fbi, ibq = self._new_client_response_pipeline(max_size=16)

        for status_line in (
                b'HTTP/1.1 304 Not Modified\r\nContent-Length: 100000\r\n\r\n',
                b'HTTP/1.1 204 No Content\r\nContent-Length: 100000\r\n\r\n',
        ):
            channel.feed_in(fbi.wrap(FullIoPipelineHttpRequest.simple('example.com', '/cached', method='GET')))
            channel.output.drain()
            channel.feed_in(status_line)

            [resp] = ibq.drain()
            self.assertIsInstance(resp, FullIoPipelineHttpResponse)
            self.assertEqual(ByteStreamBuffers.to_bytes(resp.body, strict=True), b'')

        # 100 Continue followed by 200 OK on the same request.
        channel.feed_in(fbi.wrap(FullIoPipelineHttpRequest.simple('example.com', '/upload', method='POST')))
        channel.output.drain()
        channel.feed_in(
            b'HTTP/1.1 100 Continue\r\nContent-Length: 100000\r\n\r\n'
            b'HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok',
        )
        interim, final = ibq.drain()
        self.assertIsInstance(interim, FullIoPipelineHttpResponse)
        self.assertEqual(interim.head.status, 100)
        self.assertIsInstance(final, FullIoPipelineHttpResponse)
        self.assertEqual(final.head.status, 200)
        self.assertEqual(ByteStreamBuffers.to_bytes(final.body, strict=True), b'ok')

    def test_get_response_with_oversized_content_length_aborts_on_first_body_data(self) -> None:
        # Deferring the Content-Length check until BodyData must still reject an oversized GET response immediately on
        # its very first body byte (even when that single chunk is smaller than max_size), without buffering up to
        # max_size first.
        channel, fbi, ibq = self._new_client_response_pipeline(max_size=16)

        channel.feed_in(fbi.wrap(FullIoPipelineHttpRequest.simple('example.com', '/big', method='GET')))
        channel.output.drain()

        channel.feed_in(b'HTTP/1.1 200 OK\r\nContent-Length: 100000\r\n\r\nx')

        [aborted] = ibq.drain()
        self.assertIsInstance(aborted, IoPipelineHttpResponseAborted)
        self.assertIsInstance(aborted.reason, FrameTooLargeByteStreamBufferError)
