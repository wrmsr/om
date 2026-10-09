# ruff: noqa: UP006 UP007 UP045
# @om-lite
import gc
import unittest
import weakref

from ...streambufs.utils import ByteStreamBuffers
from ..bytes.decoders import DelimiterFrameDecoderIoPipelineHandler
from ..core import IoPipeline
from ..core import IoPipelineHandler
from ..core import IoPipelineHandlerNotifications
from ..core import IoPipelineMessages
from ..drivers.pure import PureIoPipelineDriver
from ..flow.stub import StubIoPipelineFlowService
from ..flow.types import IoPipelineFlowMessages
from ..handlers.feedback import FeedbackInboundIoPipelineHandler


##


class _ReadFrames(IoPipelineHandler):
    def __init__(self):
        super().__init__()

        self.frames = []

    def inbound(self, ctx, msg):
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())
        elif ByteStreamBuffers.can_bytes(msg):
            self.frames.append(ByteStreamBuffers.to_bytes(msg))
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())
        ctx.feed_in(msg)


class _Payload:
    pass


class _RemovalHandler(IoPipelineHandler):
    def __init__(self, *, fail=False):
        super().__init__()

        self.fail = fail
        self.removed = False

    def notify(self, ctx, no):
        if isinstance(no, IoPipelineHandlerNotifications.Removed):
            self.removed = True
            if self.fail:
                raise RuntimeError('removal failed')


class TestPipelineAdversarial(unittest.TestCase):
    def test_destroy_finishes_cleanup_when_one_removed_callback_raises(self):
        outer = _RemovalHandler()
        inner = _RemovalHandler(fail=True)
        pipeline = IoPipeline.new([outer, inner])
        try:
            with self.assertRaisesRegex(RuntimeError, 'removal failed'):
                pipeline.destroy()
            self.assertTrue(inner.removed)
            self.assertTrue(outer.removed, 'one failed callback stranded the remaining handlers during destruction')
            self.assertEqual(pipeline.handlers(), [])
        finally:
            pipeline.destroy()

    def test_delimiter_decoder_rearms_manual_read_for_incomplete_frame(self):
        app = _ReadFrames()
        driver = PureIoPipelineDriver(IoPipeline.Spec(
            [DelimiterFrameDecoderIoPipelineHandler([b'\n']), app],
            services=[StubIoPipelineFlowService(auto_read=False)],
        ))
        try:
            driver.feed_input(b'hel')
            driver.next(read=True, raise_on_stall=False)
            self.assertEqual(app.frames, [])
            driver.feed_input(b'lo\n')
            driver.next(read=True, raise_on_stall=False)
            self.assertEqual(app.frames, [b'hello'])
        finally:
            driver.close()

    def test_destroy_releases_undrained_output(self):
        feedback = FeedbackInboundIoPipelineHandler()
        pipeline = IoPipeline.new([feedback])
        payload = _Payload()
        ref = weakref.ref(payload)
        pipeline.feed_in(feedback.wrap(payload))
        del payload
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            pipeline.destroy()
            self.assertIsNone(ref())
            self.assertIsNone(pipeline.output.peek())
        finally:
            pipeline.destroy()
            if gc_was_enabled:
                gc.enable()
