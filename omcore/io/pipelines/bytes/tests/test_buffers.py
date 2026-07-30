# ruff: noqa: UP006
# @om-lite
import typing as ta
import unittest

from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ...handlers.feedback import FeedbackInboundIoPipelineHandler
from ..buffers import OutboundBytesBufferIoPipelineHandler


class CaptureOutputWritabilityIoPipelineHandler(IoPipelineHandler):
    def __init__(self):
        super().__init__()

        self.events = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, (IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput)):
            self.events.append(msg)
        ctx.feed_in(msg)


class PauseOutputOnBytesIoPipelineHandler(IoPipelineHandler):
    def __init__(self):
        super().__init__()

        self._paused = False

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if ByteStreamBuffers.can_bytes(msg) and not self._paused:
            self._paused = True
            ctx.feed_in(IoPipelineFlowMessages.PauseOutput())
        ctx.feed_out(msg)


class TestOutboundBytesBuffer(unittest.TestCase):
    def test_invalid_watermarks(self):
        with self.assertRaises(ValueError):
            OutboundBytesBufferIoPipelineHandler.Config(
                write_high_watermark=1,
                write_low_watermark=2,
            )

    def test_basic_buffering(self):
        """Test that bytes are buffered until flush."""

        ch = IoPipeline.new(
            [
                OutboundBytesBufferIoPipelineHandler(
                    OutboundBytesBufferIoPipelineHandler.Config(
                        flush_threshold=None,  # Only flush on explicit flush
                    ),
                ),
                fbi := FeedbackInboundIoPipelineHandler(),
            ],
            services=[StubIoPipelineFlowService()],
        )

        # Send some bytes outbound via feedback
        ch.feed_in(fbi.wrap(b'abc'))
        ch.feed_in(fbi.wrap(b'def'))

        # Should be buffered, not yet in output
        assert ch.output.drain() == []

        # Now flush
        flush_output = IoPipelineFlowMessages.FlushOutput()
        ch.feed_in(fbi.wrap(flush_output))

        # Should now see the buffered bytes
        drained = ch.output.drain()
        # Buffer coalesces the segments, so we get 1 byte segment + FlushOutput
        assert len(drained) == 2
        assert drained[0].tobytes() == b'abcdef'
        assert drained[1] is flush_output

    def test_threshold_flush(self):
        """Test that buffering flushes when threshold is reached."""

        ch = IoPipeline.new(
            [
                OutboundBytesBufferIoPipelineHandler(
                    OutboundBytesBufferIoPipelineHandler.Config(
                        flush_threshold=10,
                    ),
                ),
                fbi := FeedbackInboundIoPipelineHandler(),
            ],
            services=[StubIoPipelineFlowService()],
        )

        # Send small chunks
        ch.feed_in(fbi.wrap(b'abc'))
        assert ch.output.drain() == []

        ch.feed_in(fbi.wrap(b'def'))
        assert ch.output.drain() == []

        # This should cross the threshold (total: 12 bytes)
        ch.feed_in(fbi.wrap(b'ghijkl'))

        # Should have flushed - buffer coalesces into single segment
        drained = ch.output.drain()
        assert len(drained) == 1
        assert drained[0].tobytes() == b'abcdefghijkl'

    def test_final_output_flush(self):
        """Test that FinalOutput flushes buffered bytes."""

        ch = IoPipeline.new(
            [
                OutboundBytesBufferIoPipelineHandler(
                    OutboundBytesBufferIoPipelineHandler.Config(
                        flush_threshold=None,
                    ),
                ),
                fbi := FeedbackInboundIoPipelineHandler(),
            ],
            services=[StubIoPipelineFlowService()],
        )

        # Send bytes
        ch.feed_in(fbi.wrap(b'hello'))
        ch.feed_in(fbi.wrap(b'world'))

        # Not flushed yet
        assert ch.output.drain() == []

        # Send FinalOutput
        ch.feed_in(fbi.wrap(IoPipelineMessages.FinalOutput()))

        # Should flush and include FinalOutput - buffer coalesces into single segment
        drained = ch.output.drain()
        assert len(drained) == 2
        assert drained[0].tobytes() == b'helloworld'
        assert isinstance(drained[1], IoPipelineMessages.FinalOutput)

    def test_non_bytes_passthrough(self):
        """Test that non-bytes messages pass through unchanged."""

        ch = IoPipeline.new(
            [
                OutboundBytesBufferIoPipelineHandler(),
                fbi := FeedbackInboundIoPipelineHandler(),
            ],
            services=[StubIoPipelineFlowService()],
        )

        # Send a non-bytes message
        class CustomMessage:
            pass

        msg = CustomMessage()
        ch.feed_in(fbi.wrap(msg))

        # Should pass through immediately
        drained = ch.output.drain()
        assert len(drained) == 1
        assert drained[0] is msg

    def test_buffered_bytes_reporting(self):
        """Test that outbound_buffered_bytes returns correct size."""

        handler = OutboundBytesBufferIoPipelineHandler(
            OutboundBytesBufferIoPipelineHandler.Config(
                flush_threshold=None,
            ),
        )

        ch = IoPipeline.new(
            [
                handler,
                fbi := FeedbackInboundIoPipelineHandler(),
            ],
            services=[StubIoPipelineFlowService()],
        )

        # Initially empty
        assert handler.outbound_buffered_bytes() == 0

        ch.feed_in(fbi.wrap(b'abc'))
        assert handler.outbound_buffered_bytes() == 3

        ch.feed_in(fbi.wrap(b'defgh'))
        assert handler.outbound_buffered_bytes() == 8

        # Flush
        ch.feed_in(fbi.wrap(IoPipelineFlowMessages.FlushOutput()))
        assert handler.outbound_buffered_bytes() == 0

    def test_downstream_writability_edges_are_combined(self):
        capture = CaptureOutputWritabilityIoPipelineHandler()
        ch = IoPipeline.new(
            [
                OutboundBytesBufferIoPipelineHandler(),
                capture,
            ],
            services=[StubIoPipelineFlowService()],
        )

        ch.feed_in(IoPipelineFlowMessages.PauseOutput())
        ch.feed_in(IoPipelineFlowMessages.PauseOutput())
        ch.feed_in(IoPipelineFlowMessages.ReadyForOutput())
        ch.feed_in(IoPipelineFlowMessages.ReadyForOutput())

        assert [type(event) for event in capture.events] == [
            IoPipelineFlowMessages.PauseOutput,
            IoPipelineFlowMessages.ReadyForOutput,
        ]

    def test_local_and_downstream_writability_are_combined(self):
        capture = CaptureOutputWritabilityIoPipelineHandler()
        ch = IoPipeline.new(
            [
                OutboundBytesBufferIoPipelineHandler(
                    OutboundBytesBufferIoPipelineHandler.Config(
                        flush_threshold=None,
                        write_high_watermark=4,
                        write_low_watermark=2,
                    ),
                ),
                capture,
                fbi := FeedbackInboundIoPipelineHandler(),
            ],
            services=[StubIoPipelineFlowService()],
        )

        ch.feed_in(fbi.wrap(b'abcde'))
        ch.feed_in(fbi.wrap(b'f'))
        assert [type(event) for event in capture.events] == [
            IoPipelineFlowMessages.PauseOutput,
        ]

        ch.feed_in(IoPipelineFlowMessages.PauseOutput())
        ch.feed_in(IoPipelineFlowMessages.ReadyForOutput())
        assert [type(event) for event in capture.events] == [
            IoPipelineFlowMessages.PauseOutput,
        ]

        ch.feed_in(fbi.wrap(IoPipelineFlowMessages.FlushOutput()))
        assert [type(event) for event in capture.events] == [
            IoPipelineFlowMessages.PauseOutput,
            IoPipelineFlowMessages.ReadyForOutput,
        ]

    def test_reentrant_downstream_pause_during_flush(self):
        capture = CaptureOutputWritabilityIoPipelineHandler()
        ch = IoPipeline.new(
            [
                PauseOutputOnBytesIoPipelineHandler(),
                OutboundBytesBufferIoPipelineHandler(
                    OutboundBytesBufferIoPipelineHandler.Config(
                        flush_threshold=None,
                        write_high_watermark=4,
                        write_low_watermark=2,
                    ),
                ),
                capture,
                fbi := FeedbackInboundIoPipelineHandler(),
            ],
            services=[StubIoPipelineFlowService()],
        )

        ch.feed_in(fbi.wrap(b'abcde'))
        ch.feed_in(fbi.wrap(IoPipelineFlowMessages.FlushOutput()))
        assert [type(event) for event in capture.events] == [
            IoPipelineFlowMessages.PauseOutput,
        ]

        ch.feed_in(IoPipelineFlowMessages.ReadyForOutput())
        assert [type(event) for event in capture.events] == [
            IoPipelineFlowMessages.PauseOutput,
            IoPipelineFlowMessages.ReadyForOutput,
        ]
