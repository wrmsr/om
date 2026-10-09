# ruff: noqa: SLF001 UP006 UP037 UP045
# @om-lite
import dataclasses as dc
import typing as ta
import unittest

from ....streambufs.types import ByteStreamBuffer
from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...errors import AbortedIoPipelineError
from ...errors import SawShutdownOutputIoPipelineError
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ...sched.types import IoPipelineScheduling
from ..pure import PureIoPipelineDriver
from ..types import IoPipelineDriverState


##


@dc.dataclass(frozen=True)
class Observed(IoPipelineMessages.AfterShutdownOutput):
    """Echoed back to the driver's caller as unhandled output; remains deliverable after an output shutdown."""

    msg: ta.Any


@dc.dataclass(frozen=True)
class Emit:
    msgs: ta.Sequence[ta.Any]


@dc.dataclass(frozen=True)
class Schedule:
    delay_s: float
    output: ta.Any


class CaptureIoPipelineHandler(IoPipelineHandler):
    def __init__(self, *, output_after_final_input: ta.Optional[bytes] = None) -> None:
        super().__init__()

        self.inputs: ta.List[ta.Any] = []
        self.output_writability: ta.List[ta.Any] = []
        self._output_after_final_input = output_after_final_input

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, Emit):
            for out_msg in msg.msgs:
                ctx.feed_out(out_msg)
            return

        if isinstance(msg, IoPipelineMessages.FinalInput) and self._output_after_final_input is not None:
            ctx.feed_out(self._output_after_final_input)

        if isinstance(msg, Schedule):
            ctx.services[IoPipelineScheduling].schedule_context(
                ctx.ref,
                msg.delay_s,
                lambda ctx2: ctx2.feed_out(msg.output),
            )
            return

        self.inputs.append(msg)
        if isinstance(msg, (IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput)):
            self.output_writability.append(msg)
        elif ByteStreamBuffers.can_bytes(msg):
            ctx.feed_out(Observed(ByteStreamBuffers.to_bytes(msg, strict=True)))
            return
        ctx.feed_in(msg)


##


class TestPureIoPipelineDriver(unittest.TestCase):
    def test_invalid_config(self) -> None:
        with self.assertRaises(ValueError):
            PureIoPipelineDriver.Config(read_chunk_size=0)
        with self.assertRaises(ValueError):
            PureIoPipelineDriver.Config(read_batch_max_bytes=0)
        with self.assertRaises(ValueError):
            PureIoPipelineDriver.Config(read_batch_max_reads=0)
        with self.assertRaises(ValueError):
            PureIoPipelineDriver.Config(write_chunk_max=0)
        with self.assertRaises(ValueError):
            PureIoPipelineDriver.Config(write_high_watermark=1, write_low_watermark=2)

    def test_transport_input_is_explicit_and_chunked(self) -> None:
        capture = CaptureIoPipelineHandler()
        driver = PureIoPipelineDriver(
            IoPipeline.Spec([capture]),
            PureIoPipelineDriver.Config(read_chunk_size=2),
        )
        try:
            self.assertIsNone(driver.next(read=False))
            driver.feed_input(b'abcd')

            self.assertIsNone(driver.next(read=False))
            self.assertEqual(driver.next(read=True, raise_on_stall=False), Observed(b'abcd'))
            self.assertIsNone(driver.next(read=False))

            self.assertIsInstance(capture.inputs[0], IoPipelineMessages.InitialInput)
            input_buffers = [msg for msg in capture.inputs if ByteStreamBuffers.can_bytes(msg)]
            self.assertEqual(len(input_buffers), 1)
            self.assertTrue(all(isinstance(msg, ByteStreamBuffer) for msg in input_buffers))
            self.assertEqual(
                [bytes(mv) for mv in input_buffers[0].segments()],
                [b'ab', b'cd'],
            )
        finally:
            driver.close()

    def test_read_batch_honors_byte_and_read_limits(self) -> None:
        for config, expected in [
            (
                PureIoPipelineDriver.Config(
                    read_chunk_size=3,
                    read_batch_max_bytes=4,
                    read_batch_max_reads=3,
                ),
                [b'abc', b'd'],
            ),
            (
                PureIoPipelineDriver.Config(
                    read_chunk_size=2,
                    read_batch_max_bytes=10,
                    read_batch_max_reads=2,
                ),
                [b'ab', b'cd'],
            ),
        ]:
            with self.subTest(config=config):
                driver = PureIoPipelineDriver(
                    IoPipeline.Spec(services=[StubIoPipelineFlowService(auto_read=False)]),
                    config,
                )
                try:
                    self.assertIsNone(driver.next(read=False))
                    driver.feed_input(b'abcdef')
                    driver._want_read = True

                    messages = driver._do_read()

                    self.assertEqual(len(messages), 2)
                    self.assertIsInstance(messages[0], ByteStreamBuffer)
                    self.assertEqual(
                        [bytes(mv) for mv in messages[0].segments()],
                        expected,
                    )
                    self.assertIsInstance(messages[-1], IoPipelineFlowMessages.FlushInput)
                    self.assertFalse(driver.wants_input)
                finally:
                    driver.close()

    def test_read_batch_flushes_before_eof(self) -> None:
        driver = PureIoPipelineDriver(
            IoPipeline.Spec(services=[StubIoPipelineFlowService(auto_read=False)]),
            PureIoPipelineDriver.Config(
                read_chunk_size=2,
                read_batch_max_bytes=10,
                read_batch_max_reads=4,
            ),
        )
        try:
            self.assertIsNone(driver.next(read=False))
            driver.feed_input(b'abc')
            driver.feed_eof()
            driver._want_read = True

            messages = driver._do_read()

            self.assertIsInstance(messages[0], ByteStreamBuffer)
            self.assertEqual([bytes(mv) for mv in messages[0].segments()], [b'ab', b'c'])
            self.assertIsInstance(messages[1], IoPipelineFlowMessages.FlushInput)
            self.assertIsInstance(messages[2], IoPipelineMessages.FinalInput)
            self.assertFalse(driver.wants_input)
        finally:
            driver.close()

    def test_partial_output_acceptance_and_flush_completion(self) -> None:
        capture = CaptureIoPipelineHandler()
        flush_output = IoPipelineFlowMessages.FlushOutput()
        driver = PureIoPipelineDriver(
            IoPipeline.Spec(
                [capture],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            PureIoPipelineDriver.Config(
                write_high_watermark=4,
                write_low_watermark=2,
            ),
        )
        try:
            self.assertIsNone(driver.next(read=False))
            driver.enqueue(Emit([b'abcdef', flush_output]))
            self.assertIsNone(driver.next(read=False))

            self.assertEqual(driver.pending_output_bytes, 6)
            self.assertFalse(flush_output.is_done())
            self.assertEqual(
                [type(msg) for msg in capture.output_writability],
                [IoPipelineFlowMessages.PauseOutput],
            )

            self.assertEqual(driver.drain_output(2), b'ab')
            self.assertEqual(driver.pending_output_bytes, 4)
            self.assertFalse(flush_output.is_done())

            self.assertEqual(driver.drain_output(2), b'cd')
            self.assertEqual(driver.pending_output_bytes, 2)
            self.assertFalse(flush_output.is_done())
            self.assertEqual(
                [type(msg) for msg in capture.output_writability],
                [IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput],
            )

            self.assertEqual(driver.drain_output(), b'ef')
            self.assertTrue(flush_output.is_succeeded())
            self.assertEqual(driver.pending_output_bytes, 0)
        finally:
            driver.close()

    def test_manual_clock_and_tickless_scheduling(self) -> None:
        capture = CaptureIoPipelineHandler()
        marker = object()
        driver = PureIoPipelineDriver(IoPipeline.Spec([capture]))
        try:
            self.assertIsNone(driver.next(read=False))
            self.assertIsNone(driver.next_deadline())

            driver.enqueue(Schedule(3., marker))
            self.assertIsNone(driver.next(read=False))
            self.assertEqual(driver.next_deadline(), 3.)

            driver.advance_time(2.)
            self.assertIsNone(driver.next(read=False))
            self.assertEqual(driver.next_deadline(), 3.)

            driver.advance_time(1.)
            self.assertIs(driver.next(read=False), marker)
            self.assertIsNone(driver.next_deadline())

            with self.assertRaises(ValueError):
                driver.advance_time(-1.)
        finally:
            driver.close()

    def test_write_chunk_max_bounds_each_acceptance_step(self) -> None:
        flush_output = IoPipelineFlowMessages.FlushOutput()
        driver = PureIoPipelineDriver(
            IoPipeline.Spec([CaptureIoPipelineHandler()]),
            PureIoPipelineDriver.Config(write_chunk_max=2),
        )
        try:
            self.assertIsNone(driver.next(read=False))
            driver.enqueue(Emit([b'abc', flush_output]))
            self.assertIsNone(driver.next(read=False))

            self.assertEqual(driver.drain_output(), b'ab')
            self.assertFalse(flush_output.is_done())
            self.assertEqual(driver.drain_output(), b'c')
            self.assertTrue(flush_output.is_succeeded())
        finally:
            driver.close()

    def test_stall_does_not_fail_driver(self) -> None:
        driver = PureIoPipelineDriver(IoPipeline.Spec())
        try:
            self.assertIsNone(driver.next(read=False))
            with self.assertRaisesRegex(RuntimeError, 'stalled'):
                driver.next()
            self.assertIs(driver.state, IoPipelineDriverState.RUNNING)
            self.assertTrue(driver.pipeline.is_ready)
        finally:
            driver.close()

    def test_loop_until_done_returns_transport_output(self) -> None:
        final_output = IoPipelineMessages.FinalOutput()
        driver = PureIoPipelineDriver(IoPipeline.Spec([CaptureIoPipelineHandler()]))
        driver.enqueue(Emit([b'one', b'two', final_output]))

        self.assertEqual(driver.loop_until_done(), b'onetwo')
        self.assertTrue(final_output.is_succeeded())
        self.assertIs(driver.state, IoPipelineDriverState.CLOSED)
        self.assertFalse(driver.pipeline.is_ready)

    def test_watermarks_after_final_input(self) -> None:
        # A half-closed peer (request sent, write side shut down) followed by a response large enough to cross the
        # high watermark. Writability concerns output, which outlives input completion, so these must still be
        # deliverable inbound after FinalInput.

        capture = CaptureIoPipelineHandler(output_after_final_input=b'abcdef')
        driver = PureIoPipelineDriver(
            IoPipeline.Spec(
                [capture],
                services=[StubIoPipelineFlowService()],
            ),
            PureIoPipelineDriver.Config(
                write_high_watermark=4,
                write_low_watermark=2,
            ),
        )
        try:
            self.assertIsNone(driver.next(read=False))
            driver.feed_eof()
            self.assertIsNone(driver.next(read=True, raise_on_stall=False))

            self.assertEqual(
                [type(msg) for msg in capture.output_writability],
                [IoPipelineFlowMessages.PauseOutput],
            )

            self.assertEqual(driver.drain_output(), b'abcdef')
            self.assertEqual(
                [type(msg) for msg in capture.output_writability],
                [IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput],
            )
        finally:
            driver.close()


class TestPureIoPipelineDriverOutputShutdown(unittest.TestCase):
    def _driver(
            self,
            capture: CaptureIoPipelineHandler,
            *,
            manual_input: bool = False,
            pipeline_config: IoPipeline.Config = IoPipeline.Config.DEFAULT,
            **kwargs: ta.Any,
    ) -> PureIoPipelineDriver:
        return PureIoPipelineDriver(
            IoPipeline.Spec(
                [capture],
                pipeline_config,
                services=[StubIoPipelineFlowService(auto_read=not manual_input)],
            ),
            PureIoPipelineDriver.Config(**kwargs),
        )

    def test_shutdown_follows_preceding_bytes_across_partial_drains(self) -> None:
        capture = CaptureIoPipelineHandler()
        so = IoPipelineMessages.ShutdownOutput()
        driver = self._driver(capture)
        try:
            self.assertIsNone(driver.next(read=False))
            driver.enqueue(Emit([b'abc', so]))
            self.assertIsNone(driver.next(read=False))
            self.assertTrue(driver.has_pending_output)

            self.assertEqual(driver.drain_output(2), b'ab')
            self.assertFalse(driver.output_shutdown)
            self.assertFalse(so.is_done())

            self.assertEqual(driver.drain_output(1), b'c')
            self.assertTrue(driver.output_shutdown)
            self.assertTrue(so.is_succeeded())
            self.assertFalse(driver.has_pending_output)
            self.assertIs(driver.state, IoPipelineDriverState.RUNNING)
            self.assertTrue(driver.pipeline.saw_shutdown_output)
        finally:
            driver.close()

    def test_zero_byte_shutdown_completes_on_a_zero_byte_drain(self) -> None:
        so = IoPipelineMessages.ShutdownOutput()
        driver = self._driver(CaptureIoPipelineHandler())
        try:
            self.assertIsNone(driver.next(read=False))
            driver.enqueue(Emit([so]))
            self.assertIsNone(driver.next(read=False))

            self.assertEqual(driver.drain_output(0), b'')
            self.assertTrue(so.is_succeeded())
            self.assertTrue(driver.output_shutdown)
        finally:
            driver.close()

    def test_input_continues_after_shutdown_until_final_output(self) -> None:
        fo = IoPipelineMessages.FinalOutput()

        class CloseOnFinalInputHandler(CaptureIoPipelineHandler):
            def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
                super().inbound(ctx, msg)
                if isinstance(msg, IoPipelineMessages.FinalInput):
                    ctx.feed_out(fo)

        capture = CloseOnFinalInputHandler()
        so = IoPipelineMessages.ShutdownOutput()
        driver = self._driver(capture)
        try:
            self.assertIsNone(driver.next(read=False))
            driver.enqueue(Emit([b'request', so]))
            self.assertIsNone(driver.next(read=False))
            self.assertEqual(driver.drain_output(), b'request')
            self.assertTrue(driver.output_shutdown)

            driver.feed_input(b'response')
            self.assertEqual(driver.next(), Observed(b'response'))
            driver.feed_eof()
            self.assertIsNone(driver.next(raise_on_stall=False))
            self.assertTrue(driver.pipeline.saw_final_input)

            # The application policy closes once both directions have ended.
            self.assertIs(driver.state, IoPipelineDriverState.DRAINING)
            self.assertEqual(driver.drain_output(), b'')
            self.assertTrue(fo.is_succeeded())
            self.assertIs(driver.state, IoPipelineDriverState.CLOSED)
        finally:
            driver.close()

    def test_final_output_queued_behind_shutdown(self) -> None:
        so = IoPipelineMessages.ShutdownOutput()
        fo = IoPipelineMessages.FinalOutput()
        driver = self._driver(CaptureIoPipelineHandler())
        try:
            self.assertIsNone(driver.next(read=False))
            driver.enqueue(Emit([b'xy', so, fo]))
            self.assertIsNone(driver.next(read=False))

            self.assertEqual(driver.drain_output(1), b'x')
            self.assertFalse(so.is_done())
            self.assertFalse(fo.is_done())

            self.assertEqual(driver.drain_output(), b'y')
            self.assertTrue(so.is_succeeded())
            self.assertTrue(fo.is_succeeded())
            self.assertIs(driver.state, IoPipelineDriverState.CLOSED)
        finally:
            driver.close()

    def test_writability_is_not_announced_after_shutdown(self) -> None:
        capture = CaptureIoPipelineHandler()
        so = IoPipelineMessages.ShutdownOutput()
        driver = self._driver(capture, write_high_watermark=4, write_low_watermark=2)
        try:
            self.assertIsNone(driver.next(read=False))
            driver.enqueue(Emit([b'abcdef', so]))
            self.assertIsNone(driver.next(read=False))
            self.assertEqual(
                [type(msg) for msg in capture.output_writability],
                [IoPipelineFlowMessages.PauseOutput],
            )

            self.assertEqual(driver.drain_output(), b'abcdef')
            self.assertTrue(driver.output_shutdown)

            # Draining below the low watermark would ordinarily announce ReadyForOutput, but nothing may produce
            # ordinary output any more.
            self.assertEqual(
                [type(msg) for msg in capture.output_writability],
                [IoPipelineFlowMessages.PauseOutput],
            )
        finally:
            driver.close()

    def test_output_after_shutdown_is_an_inbound_error(self) -> None:
        capture = CaptureIoPipelineHandler()
        driver = self._driver(capture, pipeline_config=IoPipeline.Config(inbound_terminal='drop'))
        try:
            self.assertIsNone(driver.next(read=False))
            driver.enqueue(Emit([IoPipelineMessages.ShutdownOutput()]))
            driver.enqueue(Emit([b'late']))
            self.assertIsNone(driver.next(read=False))

            errors = [m for m in capture.inputs if isinstance(m, IoPipelineMessages.Error)]
            self.assertEqual(len(errors), 1)
            self.assertIsInstance(errors[0].exc, SawShutdownOutputIoPipelineError)
            self.assertEqual(driver.pending_output_bytes, 0)
            self.assertIs(driver.state, IoPipelineDriverState.RUNNING)
        finally:
            driver.close()

    def test_manual_read_tokens_are_honored_after_shutdown(self) -> None:
        capture = CaptureIoPipelineHandler()
        driver = self._driver(capture, manual_input=True)
        try:
            self.assertIsNone(driver.next(read=False))
            driver.enqueue(Emit([IoPipelineMessages.ShutdownOutput(), IoPipelineFlowMessages.ReadyForInput()]))
            self.assertIsNone(driver.next(read=False))
            driver.drain_output()
            self.assertTrue(driver.output_shutdown)

            driver.feed_input(b'more')
            self.assertTrue(driver.wants_input)
            self.assertEqual(driver.next(), Observed(b'more'))
            self.assertFalse(driver.wants_input)
        finally:
            driver.close()

    def test_close_fails_pending_shutdown(self) -> None:
        so = IoPipelineMessages.ShutdownOutput()
        excs: ta.List[ta.Optional[BaseException]] = []
        so.add_listener(lambda m: excs.append(m.get_exception()))
        driver = self._driver(CaptureIoPipelineHandler())
        self.assertIsNone(driver.next(read=False))
        driver.enqueue(Emit([b'unsent', so]))
        self.assertIsNone(driver.next(read=False))

        driver.close()

        self.assertTrue(so.is_failed())
        self.assertEqual(len(excs), 1)
        self.assertIsInstance(excs[0], AbortedIoPipelineError)
        self.assertFalse(driver.output_shutdown)

    def test_half_closed_lifecycle_releases_without_cyclic_gc(self) -> None:
        import gc
        import weakref

        def run() -> ta.Tuple[weakref.ReferenceType, ...]:
            capture = CaptureIoPipelineHandler()
            so = IoPipelineMessages.ShutdownOutput()
            fo = IoPipelineMessages.FinalOutput()
            driver = self._driver(capture)
            self.assertIsNone(driver.next(read=False))
            driver.enqueue(Emit([b'request', so]))
            self.assertIsNone(driver.next(read=False))
            driver.drain_output()
            driver.feed_input(b'response')
            self.assertEqual(driver.next(), Observed(b'response'))
            driver.enqueue(Emit([fo]))
            self.assertIsNone(driver.next(read=False))
            driver.drain_output()
            self.assertIs(driver.state, IoPipelineDriverState.CLOSED)
            return (weakref.ref(driver), weakref.ref(driver.pipeline), weakref.ref(capture), weakref.ref(so))

        was_enabled = gc.isenabled()
        gc.disable()
        try:
            refs = run()
            self.assertEqual([r() for r in refs], [None] * len(refs))
        finally:
            if was_enabled:
                gc.enable()
