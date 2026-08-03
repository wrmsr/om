# ruff: noqa: SLF001 UP006
# @om-lite
import dataclasses as dc
import typing as ta
import unittest

from .....lite.bytes import Bytes
from .....lite.check import check
from ....streambufs.direct import DirectByteStreamBuffer
from ....streambufs.segmented import SegmentedByteStreamBuffer
from ....streambufs.types import ByteStreamBuffer
from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineMessages
from ...core import IoPipelineService
from ...flow.types import IoPipelineFlow
from ...flow.types import IoPipelineFlowMessages
from ...handlers.queues import InboundQueueIoPipelineHandler
from ..decoders import BufferedBytesToMessageDecoderIoPipelineHandler
from ..decoders import DelimiterFrameDecoderIoPipelineHandler
from ..decoders import IoPipelineHandlerContext
from ..decoders import UnicodeDecoderIoPipelineHandler


##


class TestDecoders(unittest.TestCase):
    def test_decoders(self):
        ch = IoPipeline.new([
            UnicodeDecoderIoPipelineHandler(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        ch.feed_in(b'abcd')
        assert ibq.drain() == ['abcd']

        ch.feed_in(b'hi \xe2\x98\x83 there')
        assert ibq.drain() == ['hi ☃ there']

    def test_delim(self):
        ch = IoPipeline.new([
            DelimiterFrameDecoderIoPipelineHandler([b'\n']),
            UnicodeDecoderIoPipelineHandler(),
            ibq := InboundQueueIoPipelineHandler(),
        ])

        ch.feed_in(b'abc')
        assert ibq.drain() == []
        ch.feed_in(b'de\nf')
        assert ibq.drain() == ['abcde']
        ch.feed_in(b'g\nh\nij\n')
        assert ibq.drain() == ['fg', 'h', 'ij']
        ch.feed_in(b'\nk')
        assert ibq.drain() == ['']
        ch.feed_final_input()
        om, eof = ibq.drain()
        assert om == 'k'
        assert isinstance(eof, IoPipelineMessages.FinalInput)


##


class MyFlow(IoPipelineFlow, IoPipelineService):
    def __init__(self, *, auto_read: bool) -> None:
        super().__init__()

        self._auto_read = auto_read

    def is_auto_read(self) -> bool:
        return self._auto_read

    def set_auto_read(self, auto_read: bool) -> None:
        self._auto_read = auto_read


@dc.dataclass()
class DumbBytesMessage:
    b: Bytes


class ByteTripletsToMessageDecoder(BufferedBytesToMessageDecoderIoPipelineHandler):
    def __init__(self, **kwargs: ta.Any) -> None:
        super().__init__(**kwargs)

        self.final_remainders: ta.List[ta.Any] = []

    def _decode_buffer(
            self,
            ctx: IoPipelineHandlerContext,
            inb: ByteStreamBuffer,
            out: ta.List[ta.Any],
            *,
            final: bool = False,
    ) -> None:
        if final:
            # A trailing partial triplet is truncation - record it rather than emitting it.
            if len(inb):
                self.final_remainders.append(inb.split_to(len(inb)).tobytes())
            return

        check.state(len(inb) > 0)
        while len(inb) >= 3:
            out.append(DumbBytesMessage(inb.split_to(3).tobytes()))


def test_b2md_ar():
    ch = IoPipeline.new(
        [
            ByteTripletsToMessageDecoder(),
            ibq := InboundQueueIoPipelineHandler(),
        ],
        services=[mf := MyFlow(auto_read=True)],  # noqa
    )

    print()

    ch.feed_in(b'abcd', IoPipelineFlowMessages.FlushInput())
    print(f'{ch.output.drain()=} {ibq.drain()=}')

    ch.feed_in(IoPipelineMessages.FinalInput())
    print(f'{ch.output.drain()=} {ibq.drain()=}')


def test_b2md_nar():
    ch = IoPipeline.new(
        [
            ByteTripletsToMessageDecoder(),
            ibq := InboundQueueIoPipelineHandler(),
        ],
        services=[mf := MyFlow(auto_read=False)],  # noqa
    )

    print()

    ch.feed_in(b'abcd', IoPipelineFlowMessages.FlushInput())
    print(f'{ch.output.drain()=} {ibq.drain()=}')

    ch.feed_in(IoPipelineMessages.FinalInput())
    print(f'{ch.output.drain()=} {ibq.drain()=}')


class TestBufferedBytesToMessageDecoderIoPipelineHandler(unittest.TestCase):
    def test_adopts_mutable_input_buffer_and_retains_remainder(self) -> None:
        decoder = ByteTripletsToMessageDecoder()
        ch = IoPipeline.new([
            decoder,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        buf = SegmentedByteStreamBuffer(chunk_size=2)
        buf.write(b'ab')
        buf.write(b'cd')
        ch.feed_in(buf)

        self.assertIs(decoder._buf, buf)
        self.assertEqual(len(buf), 1)
        self.assertEqual(ibq.drain(), [DumbBytesMessage(b'abc')])

        ch.feed_in(DirectByteStreamBuffer(b'ef'))

        self.assertIsNone(decoder._buf)
        self.assertEqual(ibq.drain(), [DumbBytesMessage(b'def')])

    def test_consumes_read_only_input_without_cumulation_copy(self) -> None:
        decoder = ByteTripletsToMessageDecoder()
        ch = IoPipeline.new([
            decoder,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        buf = DirectByteStreamBuffer(b'abc')
        ch.feed_in(buf)

        self.assertEqual(len(buf), 0)
        self.assertIsNone(decoder._buf)
        self.assertEqual(ibq.drain(), [DumbBytesMessage(b'abc')])

    def test_copies_only_read_only_input_remainder(self) -> None:
        decoder = ByteTripletsToMessageDecoder()
        ch = IoPipeline.new([
            decoder,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        buf = DirectByteStreamBuffer(b'abcd')
        ch.feed_in(buf)

        self.assertEqual(len(buf), 1)
        self.assertIsNotNone(decoder._buf)
        self.assertIsNot(decoder._buf, buf)
        self.assertEqual(ByteStreamBuffers.to_bytes(check.not_none(decoder._buf)), b'd')
        self.assertEqual(ibq.drain(), [DumbBytesMessage(b'abc')])

    def test_final_input_presents_the_cumulation(self) -> None:
        # Without the cumulation a subclass cannot flush or even detect a truncated trailing frame.

        decoder = ByteTripletsToMessageDecoder()
        ch = IoPipeline.new([
            decoder,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        ch.feed_in(b'abcd')
        self.assertEqual(ibq.drain(), [DumbBytesMessage(b'abc')])
        self.assertEqual(decoder.inbound_buffered_bytes(), 1)

        ch.feed_final_input()

        self.assertEqual(decoder.final_remainders, [b'd'])
        self.assertEqual(decoder.inbound_buffered_bytes(), 0)
        self.assertEqual([type(m) for m in ibq.drain()], [IoPipelineMessages.FinalInput])

    def test_final_input_with_no_cumulation(self) -> None:
        decoder = ByteTripletsToMessageDecoder()
        ch = IoPipeline.new([
            decoder,
            ibq := InboundQueueIoPipelineHandler(),
        ])

        ch.feed_in(b'abc')
        self.assertEqual(ibq.drain(), [DumbBytesMessage(b'abc')])

        ch.feed_final_input()

        self.assertEqual(decoder.final_remainders, [])
        self.assertEqual(decoder.inbound_buffered_bytes(), 0)
        self.assertEqual([type(m) for m in ibq.drain()], [IoPipelineMessages.FinalInput])
