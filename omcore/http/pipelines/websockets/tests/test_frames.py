# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta
import unittest

from .....io.pipelines.core import IoPipeline
from .....io.pipelines.core import IoPipelineMessages
from .....io.pipelines.handlers.queues import InboundQueueIoPipelineHandler
from .....io.streambufs.utils import ByteStreamBuffers
from ..frames import IoPipelineWebsocketFrameDecoder
from ..objects import IoPipelineWebsocketFrame
from ..objects import IoPipelineWebsocketOpcode


def _run(data: bytes, **kwargs: ta.Any):
    dec = IoPipelineWebsocketFrameDecoder(expect_masked=False, **kwargs)
    pipeline = IoPipeline.new([
        dec,
        ibq := InboundQueueIoPipelineHandler(),
    ])
    pipeline.feed_in(data)
    return dec, ibq.drain()


def _single_error(msgs):
    [err] = [m for m in msgs if isinstance(m, IoPipelineMessages.Error)]
    return err.exc


class TestFrameDecoderLimits(unittest.TestCase):
    def test_rejects_msb_set_extended_length(self) -> None:
        # RFC 6455 §5.2: the most significant bit of a 64 bit length MUST be 0.
        dec, msgs = _run(b'\x82\x7f' + (1 << 63).to_bytes(8, 'big'))

        exc = _single_error(msgs)
        assert isinstance(exc, ValueError)
        assert 'invalid websocket frame length' in str(exc)
        # Only the header itself was ever buffered.
        assert dec.inbound_buffered_bytes() <= IoPipelineWebsocketFrameDecoder.MAX_FRAME_HEADER_SIZE

    def test_rejects_absurd_extended_length_without_buffering(self) -> None:
        # A 10 byte header claiming 2**62 bytes must not park the rest of the connection in the buffer.
        dec, msgs = _run(b'\x82\x7f' + (1 << 62).to_bytes(8, 'big'))

        exc = _single_error(msgs)
        assert isinstance(exc, ValueError)
        assert 'exceeds limit' in str(exc)
        # Only the header itself was ever buffered.
        assert dec.inbound_buffered_bytes() <= IoPipelineWebsocketFrameDecoder.MAX_FRAME_HEADER_SIZE

    def test_rejects_oversized_control_frame_from_header(self) -> None:
        # Only the 4 byte header is fed - the 200 byte payload it claims must never be waited for.
        dec, msgs = _run(b'\x89\x7e' + (200).to_bytes(2, 'big'))

        exc = _single_error(msgs)
        assert isinstance(exc, ValueError)
        assert 'invalid control frame' in str(exc)
        # Only the header itself was ever buffered.
        assert dec.inbound_buffered_bytes() <= IoPipelineWebsocketFrameDecoder.MAX_FRAME_HEADER_SIZE

    def test_rejects_fragmented_control_frame_from_header(self) -> None:
        dec, msgs = _run(b'\x09\x00')

        exc = _single_error(msgs)
        assert isinstance(exc, ValueError)
        assert 'invalid control frame' in str(exc)

    def test_max_frame_size(self) -> None:
        dec, msgs = _run(b'\x82\x10' + b'x' * 16, max_frame_size=8)

        exc = _single_error(msgs)
        assert isinstance(exc, ValueError)
        assert 'exceeds limit' in str(exc)

    def test_max_frame_size_allows_smaller_frames(self) -> None:
        dec, msgs = _run(b'\x82\x04' + b'abcd', max_frame_size=8)

        [frm] = [m for m in msgs if isinstance(m, IoPipelineWebsocketFrame)]
        assert frm.opcode == IoPipelineWebsocketOpcode.BINARY
        assert ByteStreamBuffers.to_bytes(frm.payload) == b'abcd'

    def test_rejects_non_positive_max_frame_size(self) -> None:
        with self.assertRaises(ValueError):
            IoPipelineWebsocketFrameDecoder(expect_masked=False, max_frame_size=0)

    def test_control_frame_at_limit_still_decodes(self) -> None:
        dec, msgs = _run(b'\x89\x7d' + b'p' * 125)

        [frm] = [m for m in msgs if isinstance(m, IoPipelineWebsocketFrame)]
        assert frm.opcode == IoPipelineWebsocketOpcode.PING
        assert ByteStreamBuffers.to_bytes(frm.payload) == b'p' * 125
