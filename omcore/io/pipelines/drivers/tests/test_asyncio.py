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
        self.assertIsNone(await drv.next(read=False, raise_on_stall=False))
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

            self.assertIsNone(await drv.next(read=False, raise_on_stall=False))
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

            self.assertIsNone(await drv.next(read=False, raise_on_stall=False))
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
