# ruff: noqa: SLF001
# @om-lite
import asyncio
import typing as ta

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineHandlerRef
from ...core import IoPipelineMessages
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ...sched.types import IoPipelineScheduling
from ..asyncio import PollAsyncioStreamIoPipelineDriver


class TimerOutputIoPipelineHandler(IoPipelineHandler):
    def __init__(self, delay_s, output):
        super().__init__()

        self._delay_s = delay_s
        self._output = output

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.services[IoPipelineScheduling].schedule(
                ctx.ref,
                self._delay_s,
                lambda: ctx.feed_out(self._output),
            )

        ctx.feed_in(msg)


class NopIoPipelineHandler(IoPipelineHandler):
    pass


class CaptureOutputWritabilityIoPipelineHandler(IoPipelineHandler):
    def __init__(self):
        super().__init__()

        self.events = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, (IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput)):
            self.events.append(msg)
        ctx.feed_in(msg)


class BufferedStreamWriter:
    class Transport:
        def __init__(self):
            self.size = 0
            self.limits = None

        def set_write_buffer_limits(self, *, high, low):
            self.limits = (low, high)

        def get_write_buffer_size(self):
            return self.size

    def __init__(self):
        self.transport = self.Transport()
        self.closed = False

    def write(self, data):
        self.transport.size += len(data)

    async def drain(self):
        self.transport.size = 0

    def close(self):
        self.closed = True

    async def wait_closed(self):
        pass


class TestPollAsyncioStreamIoPipelineDriverScheduling(AsyncioIsolatedAsyncTestCase):
    async def make_driver(self, *handlers: IoPipelineHandler) -> PollAsyncioStreamIoPipelineDriver:
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                handlers,
                services=[
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
            asyncio.StreamReader(),
        )
        self.assertIsNone(await drv.next(read=False))
        return drv

    def find_handler_ref(
            self,
            drv: PollAsyncioStreamIoPipelineDriver,
            handler: IoPipelineHandler,
    ) -> IoPipelineHandlerRef:
        ref = drv.pipeline.find_handler(handler)
        if ref is None:
            self.fail('Expected handler in pipeline')
        return ref

    async def test_timer_runs_in_pipeline(self):
        drv = await self.make_driver(TimerOutputIoPipelineHandler(.01, 'timer'))
        try:
            self.assertEqual(await drv.next(), 'timer')
        finally:
            await drv.close()

    async def test_handle_and_owner_cancellation(self):
        ah = NopIoPipelineHandler()
        bh = NopIoPipelineHandler()
        drv = await self.make_driver(ah, bh)
        try:
            ar = self.find_handler_ref(drv, ah)
            br = self.find_handler_ref(drv, bh)

            events = []

            cancelled_handle = drv._sched.schedule(ar, 0., lambda: events.append('handle'))
            cancelled_handle.cancel()
            cancelled_handle.cancel()

            drv._sched.schedule(ar, 0., lambda: events.append('owner'))
            drv._sched.cancel_all(ar)

            drv._sched.schedule(br, 0., lambda: events.append('live'))
            await drv._sched._flush_pending()
            await asyncio.gather(*tuple(drv._sched._tasks))

            self.assertIsNone(await drv.next(read=False))
            self.assertEqual(events, ['live'])
        finally:
            await drv.close()

    async def test_removal_cancels_already_queued_timer(self):
        removing_handler = NopIoPipelineHandler()
        removed_handler = NopIoPipelineHandler()
        drv = await self.make_driver(removing_handler, removed_handler)
        try:
            removing_ref = self.find_handler_ref(drv, removing_handler)
            removed_ref = self.find_handler_ref(drv, removed_handler)

            events = []
            drv._sched.schedule(
                removing_ref,
                0.,
                lambda: drv.pipeline.remove(removed_ref),
            )
            drv._sched.schedule(
                removed_ref,
                0.,
                lambda: events.append('removed'),
            )
            await drv._sched._flush_pending()
            await asyncio.gather(*tuple(drv._sched._tasks))

            self.assertIsNone(await drv.next(read=False))
            self.assertEqual(events, [])
            self.assertTrue(removed_ref.invalidated)
            with self.assertRaises(RuntimeError):
                drv._sched.schedule(removed_ref, 0., lambda: events.append('orphan'))
        finally:
            await drv.close()

    async def test_destroy_cancels_all_timers(self):
        handler = NopIoPipelineHandler()
        drv = await self.make_driver(handler)
        ref = self.find_handler_ref(drv, handler)

        events = []
        drv._sched.schedule(ref, 60., lambda: events.append('timer'))
        await drv._sched._flush_pending()
        tasks = tuple(drv._sched._tasks)

        await drv.close()

        self.assertEqual(drv._sched._live, set())
        self.assertTrue(all(t.done() for t in tasks))
        self.assertEqual(events, [])

    async def test_due_timer_runs_with_read_false(self):
        drv = await self.make_driver(TimerOutputIoPipelineHandler(0., 'timer'))
        try:
            self.assertEqual(await drv.next(read=False), 'timer')
        finally:
            await drv.close()

    async def test_future_timer_does_not_block_read_false(self):
        drv = await self.make_driver(TimerOutputIoPipelineHandler(60., 'timer'))
        try:
            self.assertIsNone(await drv.next(read=False))
        finally:
            await drv.close()


class TestPollAsyncioStreamIoPipelineDriverOutputWritability(AsyncioIsolatedAsyncTestCase):
    def test_invalid_watermarks(self):
        with self.assertRaises(ValueError):
            PollAsyncioStreamIoPipelineDriver.Config(
                write_high_watermark=1,
                write_low_watermark=2,
            )

    async def test_no_flow_preserves_transport_limits(self):
        writer = BufferedStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            self.assertIsNone(writer.transport.limits)
        finally:
            await drv.close()

    async def test_watermark_transitions(self):
        capture = CaptureOutputWritabilityIoPipelineHandler()
        writer = BufferedStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [capture],
                services=[
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
            config=PollAsyncioStreamIoPipelineDriver.Config(
                write_high_watermark=4,
                write_low_watermark=2,
            ),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            self.assertEqual(writer.transport.limits, (2, 4))

            self.assertEqual(await drv._handle_output(b'abcde'), 'handled')
            self.assertEqual(
                [type(event) for event in capture.events],
                [IoPipelineFlowMessages.PauseOutput],
            )

            self.assertEqual(
                await drv._handle_output(IoPipelineFlowMessages.FlushOutput()),
                'handled',
            )
            self.assertEqual(
                [type(event) for event in capture.events],
                [
                    IoPipelineFlowMessages.PauseOutput,
                    IoPipelineFlowMessages.ReadyForOutput,
                ],
            )
        finally:
            await drv.close()
