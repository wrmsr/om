# ruff: noqa: SLF001 UP006 UP037 UP045
# @om-lite
import dataclasses as dc
import typing as ta
import unittest

from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ...sched.types import IoPipelineScheduling
from ..pure import PureIoPipelineDriver
from ..types import IoPipelineDriverState


##


@dc.dataclass(frozen=True)
class Observed:
    msg: ta.Any


@dc.dataclass(frozen=True)
class Emit:
    msgs: ta.Sequence[ta.Any]


@dc.dataclass(frozen=True)
class Schedule:
    delay_s: float
    output: ta.Any


class CaptureIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.inputs: ta.List[ta.Any] = []
        self.output_writability: ta.List[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, Emit):
            for out_msg in msg.msgs:
                ctx.feed_out(out_msg)
            return

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
        elif isinstance(msg, (bytes, bytearray, memoryview)):
            ctx.feed_out(Observed(bytes(msg)))
            return
        ctx.feed_in(msg)


##


class TestPureIoPipelineDriver(unittest.TestCase):
    def test_invalid_config(self) -> None:
        with self.assertRaises(ValueError):
            PureIoPipelineDriver.Config(read_chunk_size=0)
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
            self.assertEqual(driver.next(read=True, raise_on_stall=False), Observed(b'ab'))
            self.assertEqual(driver.next(read=True, raise_on_stall=False), Observed(b'cd'))
            self.assertIsNone(driver.next(read=False))

            self.assertIsInstance(capture.inputs[0], IoPipelineMessages.InitialInput)
            self.assertEqual(capture.inputs[1:], [b'ab', b'cd'])
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
