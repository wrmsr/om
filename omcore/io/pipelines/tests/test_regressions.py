# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
Regression tests for defects found reviewing the half-close and multiplexing work. The ids in the comments (F1-F4,
O1-O31, T1-T4) are those of the review findings recorded in FINDINGS.md at commit 323de87b3; each comment describes the
defect as it was found.
"""
import gc
import typing as ta
import unittest
import weakref

from ...streambufs.utils import ByteStreamBuffers
from ..bytes.decoders import DelimiterFrameDecoderIoPipelineHandler
from ..core import IoPipeline
from ..core import IoPipelineHandler
from ..core import IoPipelineHandlerContext
from ..core import IoPipelineHandlerNotifications
from ..core import IoPipelineMessages
from ..drivers.pure import PureIoPipelineDriver
from ..drivers.types import IoPipelineDriverState
from ..errors import SawFinalOutputIoPipelineError
from ..flow.stub import StubIoPipelineFlowService
from ..flow.types import IoPipelineFlowMessages
from ..handlers.feedback import FeedbackInboundIoPipelineHandler


##


class _ClosesTwice(IoPipelineHandler):
    """Sends two FinalOutputs on InitialInput, recording what comes back."""

    def __init__(self) -> None:
        super().__init__()

        self.first = IoPipelineMessages.FinalOutput()
        self.second = IoPipelineMessages.FinalOutput()
        self.errors: ta.List[IoPipelineMessages.Error] = []

        # Outcomes are only observable from listeners (DESIGN 5).
        self.second_exc: ta.Optional[BaseException] = None
        self.second.add_listener(self._on_second_done)

    def _on_second_done(self, msg: IoPipelineMessages.Completable) -> None:
        if msg.is_failed():
            self.second_exc = msg.get_exception()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(self.first)
            ctx.feed_out(self.second)
            return

        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg)
            return

        ctx.feed_in(msg)


class TestSecondFinalOutput(unittest.TestCase):
    # DESIGN 4: "Once it reaches the outbound terminal, no further outbound message may reach that terminal." A second
    # FinalOutput is such a message, and must be rejected like anything else - not appended to the output queue, where
    # every driver then fails on it.

    def test_second_final_output_is_rejected_at_the_terminal(self) -> None:
        h = _ClosesTwice()
        p = IoPipeline.new([h])
        p.feed_initial_input()

        out = p.output.drain()
        self.assertEqual(out, [h.first])
        self.assertFalse(h.first.is_done())

        self.assertTrue(h.second.is_failed())
        self.assertIsInstance(h.second_exc, SawFinalOutputIoPipelineError)
        (err,) = h.errors
        self.assertIsInstance(err.exc, SawFinalOutputIoPipelineError)
        self.assertEqual(err.direction, 'outbound')

    def test_driver_closes_gracefully_after_a_second_final_output(self) -> None:
        h = _ClosesTwice()
        d = PureIoPipelineDriver(IoPipeline.Spec([h]))
        try:
            self.assertIsNone(d.next(read=True, raise_on_stall=False))
            self.assertIs(d.state, IoPipelineDriverState.DRAINING)
            d.drain_output()
            self.assertIs(d.state, IoPipelineDriverState.CLOSED)
            self.assertTrue(h.first.is_succeeded())
            self.assertTrue(h.second.is_failed())
        finally:
            d.close()


##


class _Command(IoPipelineMessages.AfterFinalInput):
    """An out-of-band request injected at a handler's position, as `MultiplexMessages.OpenStream` is."""


class _Recorder(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.seen: ta.List[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        self.seen.append(msg)
        if isinstance(msg, IoPipelineMessages.MustPropagate):
            ctx.feed_in(msg)


class TestInjectedInputBeforeInitialInput(unittest.TestCase):
    # O6. `IoPipeline.feed_in_to` injects a message at a handler's position - the multiplexing README documents it as
    # the way to open a stream from outside the pipeline. Doing so before the driver has fed InitialInput (which every
    # driver does on its first step, after the pipeline exists) counts as "input", so the InitialInput which follows
    # is rejected and the driver fails. An injected request is not transport input and should not begin the input
    # lifetime.

    def test_injected_request_then_initial_input(self) -> None:
        rec = _Recorder()
        p = IoPipeline.new([rec])
        ref = p.handlers()[0]

        p.feed_in_to(ref, _Command())
        p.feed_initial_input()

        self.assertEqual([type(m) for m in rec.seen], [_Command, IoPipelineMessages.InitialInput])
        self.assertTrue(p.saw_initial_input)


class _ReadFrames(IoPipelineHandler):
    """Requests one frame at a time and records the frames it gets."""

    def __init__(self) -> None:
        super().__init__()

        self.frames: ta.List[ta.Any] = []

    def inbound(self, ctx, msg):
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())
        elif ByteStreamBuffers.can_bytes(msg):
            self.frames.append(ByteStreamBuffers.to_bytes(msg))
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())
            return
        ctx.feed_in(msg)


class TestDelimiterDecoderManualRead(unittest.TestCase):
    # O28 (reviewer 2's CORE-01; pre-existing, noted in the decoder's own TODO). With manual reads, the delimiter
    # decoder buffers a partial frame without producing output and without requesting more transport input, so the
    # application's outstanding read is never satisfied.

    def test_delimiter_decoder_rearms_manual_read_for_incomplete_frame(self) -> None:
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


class _RemovalHandler(IoPipelineHandler):
    """Records its removal, optionally failing it."""

    def __init__(self, *, fail: bool = False) -> None:
        super().__init__()

        self.fail = fail
        self.removed = False

    def notify(self, ctx, no):
        if isinstance(no, IoPipelineHandlerNotifications.Removed):
            self.removed = True
            if self.fail:
                raise RuntimeError('removal failed')


class _Payload:
    pass


class TestDestroyCleanup(unittest.TestCase):
    # O29 (reviewer 2's CORE-02). `destroy()` removes handlers in one loop: one Removed callback raising stops the
    # loop, leaves the other handlers in place, and still marks the pipeline DESTROYED, so a second destroy cannot
    # complete the cleanup.

    def test_destroy_finishes_cleanup_when_one_removed_callback_raises(self) -> None:
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

    # O30 (reviewer 2's CORE-03). Output which reached the terminal queue but was never consumed stays referenced by
    # the destroyed pipeline, so retaining the pipeline object retains payloads nothing can use.

    def test_destroy_releases_undrained_output(self) -> None:
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
