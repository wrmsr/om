# ruff: noqa: SLF001 UP006 UP037 UP045
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
from ..types import IoPipelineDriverState


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


_CLOSE = object()
_EOF_SEEN = object()


class GracefulCloseIoPipelineHandler(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _CLOSE:
            ctx.feed_out(b'payload')
            ctx.feed_final_output()
        else:
            ctx.feed_in(msg)


class CaptureFinalInputIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.saw_final_input = False

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self.saw_final_input = True
            ctx.feed_out(b'after-eof')
            ctx.feed_out(_EOF_SEEN)
        ctx.feed_in(msg)


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


class LifecycleStreamWriter:
    class Transport:
        def __init__(self, owner: 'LifecycleStreamWriter') -> None:
            self._owner = owner
            self._size = 0

        def set_write_buffer_limits(self, *, high: int, low: int) -> None:
            pass

        def get_write_buffer_size(self) -> int:
            return self._size

        def abort(self) -> None:
            self._owner.events.append('abort')
            self._owner.closed = True

    def __init__(self, wait_closed_exc: ta.Optional[BaseException] = None) -> None:
        self.transport = self.Transport(self)
        self.events: ta.List[ta.Any] = []
        self.closed = False
        self._wait_closed_exc = wait_closed_exc

    def write(self, data: ta.Any) -> None:
        self.transport._size += len(data)
        self.events.append(('write', bytes(data)))

    def close(self) -> None:
        self.events.append('close')
        self.closed = True

    async def wait_closed(self) -> None:
        self.events.append('wait_closed')
        if self._wait_closed_exc is not None:
            raise self._wait_closed_exc


class BlockingCloseStreamWriter(LifecycleStreamWriter):
    def __init__(self) -> None:
        super().__init__()

        self.wait_closed_started = asyncio.Event()
        self.allow_wait_closed = asyncio.Event()

    async def wait_closed(self) -> None:
        self.events.append('wait_closed')
        self.wait_closed_started.set()
        await self.allow_wait_closed.wait()


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


class TestPollAsyncioStreamIoPipelineDriverLifecycle(AsyncioIsolatedAsyncTestCase):
    async def test_final_output_gracefully_drains_preceding_bytes(self) -> None:
        writer = LifecycleStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [GracefulCloseIoPipelineHandler()],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
            drv.enqueue(_CLOSE)

            self.assertIsNone(await drv.next(read=False))

            self.assertEqual(writer.events, [('write', b'payload'), 'close', 'wait_closed'])
            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            self.assertFalse(drv.pipeline.is_ready)
            self.assertTrue(ta.cast(asyncio.Task, drv._read_task).done())
        finally:
            await drv.close()

    async def test_final_input_does_not_close_output(self) -> None:
        reader = asyncio.StreamReader()
        reader.feed_eof()
        writer = LifecycleStreamWriter()
        capture = CaptureFinalInputIoPipelineHandler()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec([capture]),
            reader,
            ta.cast(asyncio.StreamWriter, writer),
        )
        try:
            self.assertIs(await drv.next(), _EOF_SEEN)

            self.assertTrue(capture.saw_final_input)
            self.assertEqual(writer.events, [('write', b'after-eof')])
            self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
            self.assertTrue(drv.pipeline.is_ready)
            self.assertFalse(drv.pipeline.saw_final_output)
        finally:
            await drv.close()

    async def test_close_is_abortive(self) -> None:
        writer = LifecycleStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
        )
        self.assertIsNone(await drv.next(read=False))

        await drv.close()

        self.assertEqual(writer.events, ['abort', 'wait_closed'])
        self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
        self.assertFalse(drv.pipeline.is_ready)

    async def test_draining_state_is_observable(self) -> None:
        writer = BlockingCloseStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [GracefulCloseIoPipelineHandler()],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
        )
        task: ta.Optional[asyncio.Task] = None
        try:
            self.assertIsNone(await drv.next(read=False))
            drv.enqueue(_CLOSE)
            task = asyncio.create_task(drv.next(read=False))

            await writer.wait_closed_started.wait()

            self.assertIs(drv.state, IoPipelineDriverState.DRAINING)
            self.assertTrue(drv.pipeline.is_ready)

            writer.allow_wait_closed.set()
            self.assertIsNone(await task)

            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            self.assertFalse(drv.pipeline.is_ready)
        finally:
            writer.allow_wait_closed.set()
            if task is not None:
                await asyncio.gather(task, return_exceptions=True)
            await drv.close()

    async def test_graceful_drain_failure_is_reported(self) -> None:
        error = BrokenPipeError('broken')
        writer = LifecycleStreamWriter(error)
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [GracefulCloseIoPipelineHandler()],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            drv.enqueue(_CLOSE)

            with self.assertRaises(BrokenPipeError) as raised:
                await drv.next(read=False)

            self.assertIs(raised.exception, error)
            self.assertEqual(writer.events, [('write', b'payload'), 'close', 'wait_closed'])
            self.assertIs(drv.state, IoPipelineDriverState.FAILED)
            self.assertFalse(drv.pipeline.is_ready)
        finally:
            await drv.close()

        self.assertIs(drv.state, IoPipelineDriverState.FAILED)
