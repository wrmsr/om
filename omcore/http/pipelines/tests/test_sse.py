# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta
import unittest

from ....io.pipelines.bytes.decoders import DelimiterFrameDecoderIoPipelineHandler
from ....io.pipelines.bytes.decoders import UnicodeDecoderIoPipelineHandler
from ....io.pipelines.core import IoPipeline
from ....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from ..sse import IoPipelineSseDecoder
from ..sse import IoPipelineSseEvent


##


def _new_sse_pipeline() -> ta.Tuple[IoPipeline, InboundQueueIoPipelineHandler]:
    return (
        IoPipeline.new([
            DelimiterFrameDecoderIoPipelineHandler([b'\r\n', b'\n'], keep_ends=True),
            UnicodeDecoderIoPipelineHandler(),
            IoPipelineSseDecoder(),
            ibq := InboundQueueIoPipelineHandler(),
        ]),
        ibq,
    )


def _events(msgs: ta.Sequence[ta.Any]) -> ta.List[IoPipelineSseEvent]:
    return [m for m in msgs if isinstance(m, IoPipelineSseEvent)]


##


class TestSseDecoder(unittest.TestCase):
    def test_kept_line_ends_are_stripped(self) -> None:
        channel, ibq = _new_sse_pipeline()

        channel.feed_in(
            b'event: message\n'
            b'data: hello\n'
            b'data: world\n'
            b'\n'
            b'data: lone\n'
            b'\n',
        )

        self.assertEqual(
            _events(ibq.drain()),
            [
                IoPipelineSseEvent(event='message', data='hello\nworld'),
                IoPipelineSseEvent(event=None, data='lone'),
            ],
        )

    def test_crlf_line_ends(self) -> None:
        channel, ibq = _new_sse_pipeline()

        channel.feed_in(
            b'data: hello\r\n'
            b'\r\n',
        )

        self.assertEqual(_events(ibq.drain()), [IoPipelineSseEvent(data='hello')])

    def test_comments_are_ignored(self) -> None:
        channel, ibq = _new_sse_pipeline()

        channel.feed_in(
            b': keepalive\n'
            b'\n'
            b'data: hello\n'
            b'\n',
        )

        self.assertEqual(_events(ibq.drain()), [IoPipelineSseEvent(data='hello')])

    def test_incomplete_event_is_discarded_at_eof(self) -> None:
        channel, ibq = _new_sse_pipeline()

        channel.feed_in(
            b'data: hello\n'
            b'\n'
            b'data: incomplete\n',
        )
        channel.feed_final_input()

        self.assertEqual(_events(ibq.drain()), [IoPipelineSseEvent(data='hello')])

    def test_last_event_id_persists(self) -> None:
        channel, ibq = _new_sse_pipeline()

        channel.feed_in(
            b'id: 1\n'
            b'data: a\n'
            b'\n'
            b'data: b\n'
            b'\n'
            b'id: 2\n'
            b'data: c\n'
            b'\n',
        )

        self.assertEqual(
            _events(ibq.drain()),
            [
                IoPipelineSseEvent(data='a', id='1'),
                IoPipelineSseEvent(data='b', id='1'),
                IoPipelineSseEvent(data='c', id='2'),
            ],
        )

    def test_retry(self) -> None:
        channel, ibq = _new_sse_pipeline()

        channel.feed_in(
            b'retry: 100\n'
            b'data: a\n'
            b'\n'
            b'retry: nope\n'
            b'data: b\n'
            b'\n',
        )

        self.assertEqual(
            _events(ibq.drain()),
            [
                IoPipelineSseEvent(data='a', retry=100),
                IoPipelineSseEvent(data='b'),
            ],
        )

    def test_blank_lines_alone_emit_nothing(self) -> None:
        channel, ibq = _new_sse_pipeline()

        channel.feed_in(b'\n\n\n')

        self.assertEqual(_events(ibq.drain()), [])

    def test_lines_split_across_reads(self) -> None:
        channel, ibq = _new_sse_pipeline()

        for b in [b'data: hel', b'lo\n', b'\n']:
            channel.feed_in(b)

        self.assertEqual(_events(ibq.drain()), [IoPipelineSseEvent(data='hello')])


##


class TestSseDecodeDemo(unittest.TestCase):
    def test_demo_produces_events(self) -> None:
        # The demo wires the decoder behind a real HTTP response decoder, whose framed body objects have to be
        # unwrapped before the line framer can see any bytes.

        from .demos.sse_decode import demo_sync_http_sse  # noqa

        self.assertEqual(
            demo_sync_http_sse(),
            [
                IoPipelineSseEvent(event='message', data='hello\nworld'),
                IoPipelineSseEvent(data='lone'),
            ],
        )
