# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta
import unittest

from ....io.pipelines.core import IoPipeline
from ....io.pipelines.core import IoPipelineMessages
from ....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ....io.streambufs.utils import ByteStreamBuffers
from ..aggregators import IoPipelineHttpAggregationConfig
from ..requests import FullIoPipelineHttpRequest
from ..requests import IoPipelineHttpRequestAborted
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
