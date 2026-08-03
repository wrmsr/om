# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta
import unittest

from ....io.pipelines.core import IoPipeline
from ....io.pipelines.core import IoPipelineMessages
from ....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ....io.streambufs.utils import ByteStreamBuffers
from ....lite.check import check
from ..decoders import IoPipelineHttpDecodingConfig
from ..requests import IoPipelineHttpRequestAborted
from ..requests import IoPipelineHttpRequestBodyData
from ..requests import IoPipelineHttpRequestChunk
from ..requests import IoPipelineHttpRequestChunkedTrailers
from ..requests import IoPipelineHttpRequestEnd
from ..requests import IoPipelineHttpRequestEndChunk
from ..requests import IoPipelineHttpRequestHead
from ..requests import IoPipelineHttpRequestLastChunk
from ..servers.requests import IoPipelineHttpRequestDecoder


##


def _new_decoder_pipeline(
        config: IoPipelineHttpDecodingConfig = IoPipelineHttpDecodingConfig.DEFAULT,
) -> ta.Tuple[IoPipeline, InboundQueueIoPipelineHandler]:
    return (
        IoPipeline.new([
            IoPipelineHttpRequestDecoder(config=config),
            ibq := InboundQueueIoPipelineHandler(),
        ]),
        ibq,
    )


def _chunked_head(*extra: bytes) -> bytes:
    return (
        b'POST / HTTP/1.1\r\n'
        b'Host: t\r\n'
        b'Transfer-Encoding: chunked\r\n'
        b'\r\n' +
        b''.join(extra)
    )


##


class TestHeadParseErrors(unittest.TestCase):
    def test_bad_head_aborts_instead_of_raising(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(b'BAD REQUEST LINE\r\nHost: t\r\n\r\n')

        out = ibq.drain()
        self.assertEqual(len(out), 1)
        self.assertIsInstance(out[0], IoPipelineHttpRequestAborted)

    def test_bad_head_does_not_discard_earlier_message_from_same_read(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(
            b'GET /good HTTP/1.1\r\nHost: t\r\n\r\n'
            b'BAD REQUEST LINE\r\nHost: t\r\n\r\n',
        )

        out = ibq.drain()
        self.assertEqual(len(out), 3)
        self.assertIsInstance(out[0], IoPipelineHttpRequestHead)
        self.assertEqual(out[0].target, '/good')
        self.assertIsInstance(out[1], IoPipelineHttpRequestEnd)
        self.assertIsInstance(out[2], IoPipelineHttpRequestAborted)

    def test_non_ascii_request_target(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(b'GET /caf\xe9 HTTP/1.1\r\nHost: t\r\n\r\n')

        out = ibq.drain()
        self.assertEqual(len(out), 2)
        self.assertIsInstance(out[0], IoPipelineHttpRequestHead)
        self.assertEqual(out[0].target.encode('latin-1'), b'/caf\xe9')
        self.assertIsInstance(out[1], IoPipelineHttpRequestEnd)


##


class TestChunkSizeLines(unittest.TestCase):
    def test_chunk_extensions_are_ignored(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(_chunked_head(b'5;foo=bar\r\nhello\r\n0\r\n\r\n'))

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
            ],
        )
        self.assertEqual(out[1].size, 5)
        self.assertEqual(ByteStreamBuffers.to_bytes(out[2].data), b'hello')

    def test_last_chunk_extensions_are_ignored(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(_chunked_head(b'0;foo=bar\r\n\r\n'))

        out = ibq.drain()
        self.assertEqual(
            [type(m) for m in out],
            [
                IoPipelineHttpRequestHead,
                IoPipelineHttpRequestLastChunk,
                IoPipelineHttpRequestChunkedTrailers,
                IoPipelineHttpRequestEnd,
            ],
        )

    def test_non_hex_chunk_sizes_abort(self) -> None:
        for size_line in [
            b'0x5',
            b'1_0',
            b'+5',
            b'-5',
            b'',
            b' 5',
            b'5 ',
        ]:
            with self.subTest(size_line=size_line):
                channel, ibq = _new_decoder_pipeline()

                channel.feed_in(_chunked_head(size_line + b'\r\nhello\r\n'))

                out = ibq.drain()
                self.assertEqual(len(out), 2)
                self.assertIsInstance(out[0], IoPipelineHttpRequestHead)
                self.assertIsInstance(out[1], IoPipelineHttpRequestAborted)
                self.assertNotIsInstance(out[1].reason, BaseException)

    def test_hex_chunk_sizes_are_accepted(self) -> None:
        for size_line, size in [
            (b'5', 5),
            (b'A', 10),
            (b'a', 10),
            (b'00000005', 5),
        ]:
            with self.subTest(size_line=size_line):
                channel, ibq = _new_decoder_pipeline()

                channel.feed_in(_chunked_head(size_line + b'\r\n'))

                out = ibq.drain()
                self.assertEqual(len(out), 2)
                self.assertIsInstance(out[1], IoPipelineHttpRequestChunk)
                self.assertEqual(out[1].size, size)


##


class TestUnboundedBuffers(unittest.TestCase):
    def test_unbounded_head_buffer(self) -> None:
        channel, ibq = _new_decoder_pipeline(IoPipelineHttpDecodingConfig(
            head_buffer=IoPipelineHttpDecodingConfig.BufferConfig(max_size=None, chunk_size=4096),
        ))

        for b in [
            b'GET / HTTP/1.1\r\n',
            b'Host: t\r\n',
            b'\r\n',
        ]:
            channel.feed_in(b)

        out = ibq.drain()
        self.assertEqual(len(out), 2)
        self.assertIsInstance(out[0], IoPipelineHttpRequestHead)
        self.assertIsInstance(out[1], IoPipelineHttpRequestEnd)

    def test_unbounded_chunk_header_buffer(self) -> None:
        channel, ibq = _new_decoder_pipeline(IoPipelineHttpDecodingConfig(
            chunk_header_buffer=IoPipelineHttpDecodingConfig.BufferConfig(max_size=None, chunk_size=1024),
        ))

        channel.feed_in(_chunked_head(b'5\r\nhello\r\n0\r\n\r\n'))

        out = ibq.drain()
        self.assertEqual(len(out), 7)
        self.assertIsInstance(out[-1], IoPipelineHttpRequestEnd)
        self.assertEqual(ByteStreamBuffers.to_bytes(out[2].data), b'hello')

    def test_unbounded_trailer_buffer(self) -> None:
        channel, ibq = _new_decoder_pipeline(IoPipelineHttpDecodingConfig(
            trailer_buffer=IoPipelineHttpDecodingConfig.BufferConfig(max_size=None, chunk_size=1024),
        ))

        channel.feed_in(_chunked_head(b'0\r\nExpires: x\r\n\r\n'))

        out = ibq.drain()
        self.assertEqual(len(out), 4)
        self.assertIsInstance(out[-1], IoPipelineHttpRequestEnd)


##


class TestEofHandling(unittest.TestCase):
    def test_clean_eof_on_idle_connection_does_not_abort(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_final_input()

        out = ibq.drain()
        self.assertEqual(len(out), 1)
        self.assertIsInstance(out[0], IoPipelineMessages.FinalInput)

    def test_clean_eof_between_keepalive_messages_does_not_abort(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(b'GET / HTTP/1.1\r\nHost: t\r\n\r\n')
        channel.feed_final_input()

        out = ibq.drain()
        self.assertEqual(len(out), 3)
        self.assertIsInstance(out[0], IoPipelineHttpRequestHead)
        self.assertIsInstance(out[1], IoPipelineHttpRequestEnd)
        self.assertIsInstance(out[2], IoPipelineMessages.FinalInput)

    def test_eof_mid_head_aborts(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(b'GET / HTTP/1.1\r\nHost: t\r\n')
        channel.feed_final_input()

        out = ibq.drain()
        self.assertEqual(len(out), 2)
        self.assertIsInstance(out[0], IoPipelineHttpRequestAborted)
        self.assertIsInstance(out[1], IoPipelineMessages.FinalInput)


##


class TestAbortedState(unittest.TestCase):
    def test_input_after_abort_is_discarded(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(b'BAD REQUEST LINE\r\nHost: t\r\n\r\n')
        self.assertEqual(len(ibq.drain()), 1)

        channel.feed_in(b'GET / HTTP/1.1\r\nHost: t\r\n\r\n')
        channel.feed_final_input()

        out = ibq.drain()
        self.assertEqual(len(out), 1)
        self.assertIsInstance(out[0], IoPipelineMessages.FinalInput)

    def test_abort_mid_read_discards_remainder_without_error(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(_chunked_head(b'zz\r\nhello\r\n0\r\n\r\n') + b'GET / HTTP/1.1\r\nHost: t\r\n\r\n')

        out = ibq.drain()
        self.assertEqual(len(out), 2)
        self.assertIsInstance(out[0], IoPipelineHttpRequestHead)
        self.assertIsInstance(out[1], IoPipelineHttpRequestAborted)


##


class TestTrailers(unittest.TestCase):
    def test_empty_trailer_section(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(_chunked_head(b'5\r\nhello\r\n0\r\n\r\n'))

        out = ibq.drain()
        self.assertEqual(len(out), 7)
        trailers = check.isinstance(out[5], IoPipelineHttpRequestChunkedTrailers)
        self.assertIsInstance(out[6], IoPipelineHttpRequestEnd)

        self.assertEqual(len(trailers.trailers), 0)
        self.assertIsNone(trailers.parsed_trailers)

    def test_trailer_fields_are_carried(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(_chunked_head(b'5\r\nhello\r\n0\r\nExpires: x\r\nX-Y: z\r\n\r\n'))

        out = ibq.drain()
        self.assertEqual(len(out), 7)
        trailers = check.isinstance(out[5], IoPipelineHttpRequestChunkedTrailers)
        self.assertIsInstance(out[6], IoPipelineHttpRequestEnd)

        self.assertEqual(trailers.trailers.single['expires'], 'x')
        self.assertEqual(trailers.trailers.single['x-y'], 'z')
        self.assertIsNotNone(trailers.parsed_trailers)

    def test_trailer_fields_are_not_merged_into_the_head(self) -> None:
        # RFC 9110 §6.5.1 only permits merging for fields a recipient understands, so the pipeline never merges.
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(_chunked_head(b'5\r\nhello\r\n0\r\nX-Y: z\r\n\r\n'))

        out = ibq.drain()
        head = check.isinstance(out[0], IoPipelineHttpRequestHead)
        self.assertNotIn('x-y', dict(head.headers.items()))

    def test_trailers_split_across_reads(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        for b in [
            _chunked_head(b'0\r\n'),
            b'Expi',
            b'res: x\r',
            b'\n',
            b'\r\n',
        ]:
            channel.feed_in(b)

        out = ibq.drain()
        self.assertEqual(
            [type(m) for m in out],
            [
                IoPipelineHttpRequestHead,
                IoPipelineHttpRequestLastChunk,
                IoPipelineHttpRequestChunkedTrailers,
                IoPipelineHttpRequestEnd,
            ],
        )

    def test_message_after_trailers_is_decoded(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(
            _chunked_head(b'0\r\nExpires: x\r\n\r\n') +
            b'GET /next HTTP/1.1\r\nHost: t\r\n\r\n',
        )

        out = ibq.drain()
        self.assertEqual(len(out), 6)
        self.assertIsInstance(out[4], IoPipelineHttpRequestHead)
        self.assertEqual(out[4].target, '/next')
        self.assertIsInstance(out[5], IoPipelineHttpRequestEnd)

    def test_forbidden_trailer_field_aborts(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(_chunked_head(b'0\r\nContent-Length: 5\r\n\r\n'))

        out = ibq.drain()
        self.assertEqual(len(out), 3)
        self.assertIsInstance(out[1], IoPipelineHttpRequestLastChunk)
        self.assertIsInstance(out[2], IoPipelineHttpRequestAborted)

    def test_oversized_trailers_abort(self) -> None:
        channel, ibq = _new_decoder_pipeline(IoPipelineHttpDecodingConfig(
            trailer_buffer=IoPipelineHttpDecodingConfig.BufferConfig(max_size=64, chunk_size=64),
        ))

        channel.feed_in(_chunked_head(b'0\r\nX-Y: ' + b'z' * 128 + b'\r\n\r\n'))

        out = ibq.drain()
        self.assertEqual(len(out), 3)
        self.assertIsInstance(out[2], IoPipelineHttpRequestAborted)

    def test_eof_mid_trailers_aborts(self) -> None:
        channel, ibq = _new_decoder_pipeline()

        channel.feed_in(_chunked_head(b'0\r\nExpires: x\r\n'))
        channel.feed_final_input()

        out = ibq.drain()
        self.assertEqual(len(out), 4)
        self.assertIsInstance(out[1], IoPipelineHttpRequestLastChunk)
        self.assertIsInstance(out[2], IoPipelineHttpRequestAborted)
        self.assertIsInstance(out[3], IoPipelineMessages.FinalInput)
