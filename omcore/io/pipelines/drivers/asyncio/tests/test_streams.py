# ruff: noqa: SLF001 UP006 UP037 UP045
# @om-lite
import asyncio
import typing as ta

from ......testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from .....streambufs.types import ByteStreamBuffer
from .....streambufs.utils import ByteStreamBuffers
from ....asyncs import AsyncIoPipelineMessages
from ....core import IoPipeline
from ....core import IoPipelineHandler
from ....core import IoPipelineHandlerContext
from ....core import IoPipelineHandlerRef
from ....core import IoPipelineMessages
from ....core import IoPipelineService
from ....core import IoPipelineUpdate
from ....flow.stub import StubIoPipelineFlowService
from ....flow.types import IoPipelineFlowMessages
from ....sched.types import IoPipelineScheduling
from ...types import IoPipelineDriverState
from ..streams import PollAsyncioStreamIoPipelineDriver


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


class TimerCallbackIoPipelineHandler(IoPipelineHandler):
    def __init__(self, delay_s, fn, output):
        super().__init__()

        self._delay_s = delay_s
        self._fn = fn
        self._output = output

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            def run() -> None:
                self._fn()
                ctx.feed_out(self._output)

            ctx.services[IoPipelineScheduling].schedule(
                ctx.ref,
                self._delay_s,
                run,
            )

        ctx.feed_in(msg)


class DeferredTimerIoPipelineHandler(IoPipelineHandler):
    def __init__(self, delay_s, output):
        super().__init__()

        self._delay_s = delay_s
        self._output = output

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            def deferred(ctx2: IoPipelineHandlerContext) -> None:
                ctx2.services[IoPipelineScheduling].schedule(
                    ctx2.ref,
                    self._delay_s,
                    lambda: ctx.feed_out(self._output),
                )

            ctx.defer(deferred)

        ctx.feed_in(msg)


class NopIoPipelineHandler(IoPipelineHandler):
    pass


_CLOSE = object()
_EOF_SEEN = object()


class GracefulCloseIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.final_output = IoPipelineMessages.FinalOutput()

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _CLOSE:
            ctx.feed_out(b'payload')
            ctx.feed_out(self.final_output)
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


class CaptureInputIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.inputs: ta.List[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        self.inputs.append(msg)
        if not ByteStreamBuffers.can_bytes(msg):
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

    async def drain(self) -> None:
        self.events.append('drain')
        self.transport._size = 0

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


class AbortableBlockingCloseStreamWriter(BlockingCloseStreamWriter):
    class Transport(LifecycleStreamWriter.Transport):
        def abort(self) -> None:
            super().abort()
            ta.cast('AbortableBlockingCloseStreamWriter', self._owner).allow_wait_closed.set()

    def __init__(self) -> None:
        super().__init__()

        self.transport = self.Transport(self)


class BlockingDrainStreamWriter(LifecycleStreamWriter):
    def __init__(self, drain_exc: ta.Optional[BaseException] = None) -> None:
        super().__init__()

        self.drain_started = asyncio.Event()
        self.drain_cancelled = asyncio.Event()
        self.allow_drain = asyncio.Event()

        self.drain_calls = 0
        self.active_drains = 0
        self.max_active_drains = 0

        self._drain_exc = drain_exc

    async def drain(self) -> None:
        self.events.append('drain')
        self.drain_calls += 1
        self.active_drains += 1
        self.max_active_drains = max(self.max_active_drains, self.active_drains)
        self.drain_started.set()
        try:
            await self.allow_drain.wait()
            if self._drain_exc is not None:
                raise self._drain_exc
            self.transport._size = 0
        except asyncio.CancelledError:
            self.drain_cancelled.set()
            raise
        finally:
            self.active_drains -= 1


class FailingWriteStreamWriter(LifecycleStreamWriter):
    def __init__(self, exc: BaseException) -> None:
        super().__init__()

        self._exc = exc

    def write(self, data: ta.Any) -> None:
        self.events.append(('write', bytes(data)))
        raise self._exc


class FailingStreamReader:
    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    async def read(self, size: int) -> bytes:
        raise self._exc


class LifecycleIoPipelineService(IoPipelineService):
    def __init__(self, removal_exc: ta.Optional[BaseException] = None) -> None:
        super().__init__()

        self.removed = 0
        self._removal_exc = removal_exc

    def pipeline_update(self, pipeline: IoPipeline, kind: IoPipelineUpdate) -> None:
        if kind == 'removed':
            self.removed += 1
            if self._removal_exc is not None:
                raise self._removal_exc


_ERROR = object()


async def _wait_drained(drv: PollAsyncioStreamIoPipelineDriver) -> None:
    """Lets the driver's drainer task run until it has no drain pending."""

    await asyncio.wait_for(drv._drain_idle_event.wait(), 1.)


class OutputErrorIoPipelineHandler(IoPipelineHandler):
    def __init__(self, error: BaseException) -> None:
        super().__init__()

        self._error = error

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _ERROR:
            ctx.feed_out(self._error)
        else:
            ctx.feed_in(msg)


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
        self.assertIsNotNone(drv._timer_handle)

        await drv.close()

        self.assertEqual(drv._sched._live, set())
        self.assertIsNone(drv._timer_handle)
        self.assertEqual(events, [])

    async def test_timers_create_no_tasks(self):
        handler = NopIoPipelineHandler()
        drv = await self.make_driver(handler)
        try:
            ref = self.find_handler_ref(drv, handler)
            tasks_before = len(asyncio.all_tasks())

            handles = [drv._sched.schedule(ref, 60. + i, lambda: None) for i in range(100)]

            self.assertEqual(len(asyncio.all_tasks()), tasks_before)
            self.assertIsNotNone(drv._timer_handle)
            for h in handles:
                h.cancel()
            self.assertIsNone(await drv.next(read=False))
            self.assertEqual(drv._sched._live, set())
        finally:
            await drv.close()

    async def test_earlier_timer_rearms_the_wake(self):
        # The outer handler's far timer is armed first; the inner handler's near one must replace it.
        drv = await self.make_driver(
            TimerOutputIoPipelineHandler(60., 'late'),
            TimerOutputIoPipelineHandler(.01, 'soon'),
        )
        try:
            self.assertEqual(await asyncio.wait_for(drv.next(), .5), 'soon')
        finally:
            await drv.close()

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

    async def test_timer_scheduled_from_deferred_runs(self):
        # A Defer is drained from pipeline output rather than the command queue, so the loop timer must be armed for
        # the timers it schedules before waiting. A due-on-arrival deadline is rescued by run_due at the top of next();
        # only a future one exercises the arming.

        drv = await self.make_driver(DeferredTimerIoPipelineHandler(.01, 'timer'))
        try:
            self.assertEqual(await asyncio.wait_for(drv.next(), .5), 'timer')
        except TimeoutError:
            self.fail('timer scheduled from a deferred callback never ran')
        finally:
            await drv.close()


class TestPollAsyncioStreamIoPipelineDriverOutputWritability(AsyncioIsolatedAsyncTestCase):
    def test_invalid_chunk_sizes(self):
        with self.assertRaises(ValueError):
            PollAsyncioStreamIoPipelineDriver.Config(read_chunk_size=0)
        with self.assertRaises(ValueError):
            PollAsyncioStreamIoPipelineDriver.Config(read_batch_max_bytes=0)
        with self.assertRaises(ValueError):
            PollAsyncioStreamIoPipelineDriver.Config(read_batch_max_reads=0)
        with self.assertRaises(ValueError):
            PollAsyncioStreamIoPipelineDriver.Config(write_chunk_max=0)

    def test_invalid_watermarks(self):
        with self.assertRaises(ValueError):
            PollAsyncioStreamIoPipelineDriver.Config(
                write_high_watermark=1,
                write_low_watermark=2,
            )

    async def test_read_batch_flushes_before_eof(self) -> None:
        capture = CaptureInputIoPipelineHandler()
        driver = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [capture],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            asyncio.StreamReader(),
        )
        try:
            self.assertIsNone(await driver.next(read=False))

            await driver._handle_command_read_completed(
                PollAsyncioStreamIoPipelineDriver._ReadCompletedCommand([b'ab', b'c', b'']),
            )

            self.assertIsInstance(capture.inputs[1], ByteStreamBuffer)
            self.assertEqual([bytes(mv) for mv in capture.inputs[1].segments()], [b'ab', b'c'])
            self.assertEqual(ByteStreamBuffers.to_bytes(capture.inputs[1], strict=True), b'abc')
            self.assertIsInstance(capture.inputs[2], IoPipelineFlowMessages.FlushInput)
            self.assertIsInstance(capture.inputs[3], IoPipelineMessages.FinalInput)
            self.assertFalse(driver._want_read)
        finally:
            await driver.close()

    async def test_flush_without_writer_completes_immediately(self) -> None:
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            asyncio.StreamReader(),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            flush_output = IoPipelineFlowMessages.FlushOutput()

            self.assertEqual(await drv._handle_output(flush_output), 'handled')

            self.assertTrue(flush_output.is_succeeded())
            self.assertFalse(drv._drain_pending)
        finally:
            await drv.close()

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

    async def test_write_chunk_max_bounds_each_write(self):
        writer = LifecycleStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
            config=PollAsyncioStreamIoPipelineDriver.Config(write_chunk_max=2),
        )
        try:
            self.assertIsNone(await drv.next(read=False))

            self.assertEqual(await drv._handle_output(b'abcde'), 'handled')
            self.assertEqual(
                writer.events,
                [
                    ('write', b'ab'),
                    ('write', b'cd'),
                    ('write', b'e'),
                ],
            )
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
            await _wait_drained(drv)
            self.assertIsNone(await drv.next(read=False))
            self.assertEqual(
                [type(event) for event in capture.events],
                [
                    IoPipelineFlowMessages.PauseOutput,
                    IoPipelineFlowMessages.ReadyForOutput,
                ],
            )
        finally:
            await drv.close()

    async def test_blocked_drain_does_not_block_read_false_or_timer(self):
        timer_fired = asyncio.Event()
        timer_error = TimeoutError('timer')
        capture = CaptureOutputWritabilityIoPipelineHandler()
        writer = BlockingDrainStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [
                    TimerCallbackIoPipelineHandler(
                        .01,
                        timer_fired.set,
                        timer_error,
                    ),
                    capture,
                ],
                services=[StubIoPipelineFlowService(auto_read=False)],
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
            self.assertEqual(await drv._handle_output(b'payload'), 'handled')
            self.assertEqual(
                await drv._handle_output(IoPipelineFlowMessages.FlushOutput()),
                'handled',
            )
            await writer.drain_started.wait()

            self.assertIsNone(await asyncio.wait_for(drv.next(read=False), .1))
            next_task = asyncio.create_task(drv.next())
            await asyncio.wait_for(timer_fired.wait(), .5)

            self.assertIs(await asyncio.wait_for(next_task, .5), timer_error)
            self.assertTrue(drv._drain_pending)

            self.assertEqual(
                [type(event) for event in capture.events],
                [IoPipelineFlowMessages.PauseOutput],
            )
        finally:
            await drv.close()

        self.assertTrue(writer.drain_cancelled.is_set())

    async def test_flushes_coalesce_without_concurrent_drains(self):
        capture = CaptureOutputWritabilityIoPipelineHandler()
        writer = BlockingDrainStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [capture],
                services=[StubIoPipelineFlowService(auto_read=False)],
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
            tasks_before = len(asyncio.all_tasks())
            self.assertEqual(await drv._handle_output(b'abcde'), 'handled')
            first_flush_output = IoPipelineFlowMessages.FlushOutput()
            self.assertEqual(
                await drv._handle_output(first_flush_output),
                'handled',
            )
            await writer.drain_started.wait()
            self.assertFalse(first_flush_output.is_done())
            self.assertTrue(drv._drain_pending)

            # Handled directly, bypassing the command loop's hold behind the pending drain: it joins the next one.
            second_flush_output = IoPipelineFlowMessages.FlushOutput()
            self.assertEqual(
                await drv._handle_output(second_flush_output),
                'handled',
            )
            self.assertTrue(drv._drain_requested)
            self.assertFalse(second_flush_output.is_done())

            writer.allow_drain.set()
            await _wait_drained(drv)
            self.assertIsNone(await drv.next(read=False))
            self.assertTrue(first_flush_output.is_succeeded())
            self.assertTrue(second_flush_output.is_succeeded())

            # Two drains, one after the other, on the one drainer task.
            self.assertEqual(writer.drain_calls, 2)
            self.assertEqual(writer.max_active_drains, 1)
            self.assertEqual(len(asyncio.all_tasks()), tasks_before)
            self.assertFalse(drv._drain_pending)
            self.assertEqual(
                [type(event) for event in capture.events],
                [
                    IoPipelineFlowMessages.PauseOutput,
                    IoPipelineFlowMessages.ReadyForOutput,
                ],
            )
        finally:
            writer.allow_drain.set()
            await drv.close()

    async def test_drain_failure_fails_driver(self):
        error = BrokenPipeError('broken')
        writer = BlockingDrainStreamWriter(error)
        writer.allow_drain.set()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            flush_output = IoPipelineFlowMessages.FlushOutput()
            self.assertEqual(
                await drv._handle_output(flush_output),
                'handled',
            )
            self.assertFalse(flush_output.is_done())

            with self.assertRaises(BrokenPipeError) as driver_raised:
                await asyncio.wait_for(drv.next(), .5)
            self.assertIs(driver_raised.exception, error)

            self.assertTrue(flush_output.is_failed())
            self.assertIs(drv.state, IoPipelineDriverState.FAILED)
            self.assertFalse(drv.pipeline.is_ready)
            self.assertTrue(writer.closed)
            self.assertEqual(writer.events, ['drain', 'abort', 'wait_closed'])
        finally:
            await drv.close()

        self.assertIs(drv.state, IoPipelineDriverState.FAILED)


class TestPollAsyncioStreamIoPipelineDriverLifecycle(AsyncioIsolatedAsyncTestCase):
    async def test_driver_owned_await_can_close_its_driver(self) -> None:
        done = asyncio.Event()
        errors: ta.List[BaseException] = []

        class CloseFromAwait(IoPipelineHandler):
            def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
                if msg == 'close':
                    ctx.feed_out(AsyncIoPipelineMessages.Await(close_driver()))
                else:
                    ctx.feed_in(msg)

        drv = PollAsyncioStreamIoPipelineDriver(IoPipeline.Spec([CloseFromAwait()]), asyncio.StreamReader())

        async def close_driver() -> None:
            try:
                await drv.close()
            except BaseException as e:  # noqa
                errors.append(e)
            finally:
                done.set()

        try:
            self.assertIsNone(await drv.next(read=False))
            drv.enqueue('close')
            self.assertIsNone(await drv.next(read=False))
            await asyncio.wait_for(done.wait(), 1.)

            self.assertEqual(errors, [])
            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            self.assertFalse(drv.pipeline.is_ready)
        finally:
            await drv.close()

    async def test_close_before_pipeline_initialization(self) -> None:
        writer = LifecycleStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
        )

        await drv.close()
        await drv.close()

        self.assertEqual(writer.events, ['abort', 'wait_closed'])
        self.assertIs(drv.state, IoPipelineDriverState.CLOSED)

    async def test_repeated_close_destroys_pipeline_once(self) -> None:
        lifecycle = LifecycleIoPipelineService()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                services=[
                    lifecycle,
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
            asyncio.StreamReader(),
        )
        self.assertIsNone(await drv.next(read=False))

        await drv.close()
        await drv.close()

        self.assertEqual(lifecycle.removed, 1)
        self.assertIs(drv.state, IoPipelineDriverState.CLOSED)

    async def test_pipeline_output_error_is_non_terminal(self) -> None:
        error = RuntimeError('pipeline')
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [OutputErrorIoPipelineHandler(error)],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            asyncio.StreamReader(),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            drv.enqueue(_ERROR)

            self.assertIs(await drv.next(read=False), error)
            self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
            self.assertTrue(drv.pipeline.is_ready)
        finally:
            await drv.close()

    async def test_transport_read_failure_fails_driver(self) -> None:
        error = ConnectionResetError('reset')
        writer = LifecycleStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(),
            ta.cast(asyncio.StreamReader, FailingStreamReader(error)),
            ta.cast(asyncio.StreamWriter, writer),
        )

        with self.assertRaises(ConnectionResetError) as raised:
            await drv.next()

        self.assertIs(raised.exception, error)
        self.assertIs(drv.state, IoPipelineDriverState.FAILED)
        self.assertFalse(drv.pipeline.is_ready)
        self.assertEqual(writer.events, ['abort', 'wait_closed'])

        await drv.close()
        self.assertIs(drv.state, IoPipelineDriverState.FAILED)

    async def test_transport_write_failure_fails_driver(self) -> None:
        error = BrokenPipeError('broken')
        writer = FailingWriteStreamWriter(error)
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [GracefulCloseIoPipelineHandler()],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
        )
        self.assertIsNone(await drv.next(read=False))
        drv.enqueue(_CLOSE)

        with self.assertRaises(BrokenPipeError) as raised:
            await drv.next(read=False)

        self.assertIs(raised.exception, error)
        self.assertIs(drv.state, IoPipelineDriverState.FAILED)
        self.assertFalse(drv.pipeline.is_ready)
        self.assertEqual(writer.events, [('write', b'payload'), 'abort', 'wait_closed'])

        await drv.close()
        self.assertIs(drv.state, IoPipelineDriverState.FAILED)

    async def test_pipeline_removal_failure_fails_close(self) -> None:
        error = RuntimeError('remove')
        lifecycle = LifecycleIoPipelineService(error)
        writer = LifecycleStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                services=[
                    lifecycle,
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
        )
        self.assertIsNone(await drv.next(read=False))

        with self.assertRaises(RuntimeError) as raised:
            await drv.close()

        self.assertIs(raised.exception, error)
        self.assertEqual(lifecycle.removed, 1)
        self.assertIs(drv.state, IoPipelineDriverState.FAILED)
        self.assertFalse(drv.pipeline.is_ready)
        self.assertEqual(writer.events, ['abort', 'wait_closed'])

        await drv.close()
        self.assertEqual(lifecycle.removed, 1)

    async def test_post_listener_failure_in_close_still_releases_transport(self) -> None:
        """
        A post still queued when the driver closes is failed, and its listener may raise: the close raises, as it does
        when a handler's removal fails, but it is still the close of the transport and of the pipeline.
        """

        error = RuntimeError('listener')
        writer = LifecycleStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(services=[StubIoPipelineFlowService(auto_read=False)]),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
        )
        self.assertIsNone(await drv.next(read=False))

        def raise_on_done(post):
            raise error

        post = drv.posting.post(lambda: None)
        post.add_listener(raise_on_done)

        with self.assertRaises(RuntimeError) as raised:
            await drv.close()

        self.assertIs(raised.exception, error)
        self.assertTrue(post.is_failed())
        self.assertIs(drv.state, IoPipelineDriverState.FAILED)
        self.assertFalse(drv.pipeline.is_ready)
        self.assertEqual(writer.events, ['abort', 'wait_closed'])

        await drv.close()
        self.assertEqual(writer.events, ['abort', 'wait_closed'])

    async def test_close_runs_every_release_and_raises_the_first_failure(self) -> None:
        """
        A handler's removal and a failed post's listener both raise: both ran, the removal's error is the one raised.
        """

        removal_error = RuntimeError('remove')
        listener_error = RuntimeError('listener')
        lifecycle = LifecycleIoPipelineService(removal_error)
        writer = LifecycleStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                services=[
                    lifecycle,
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
        )
        self.assertIsNone(await drv.next(read=False))

        def raise_on_done(post):
            raise listener_error

        post = drv.posting.post(lambda: None)
        post.add_listener(raise_on_done)

        with self.assertRaises(RuntimeError) as raised:
            await drv.close()

        self.assertIs(raised.exception, removal_error)
        self.assertEqual(lifecycle.removed, 1)
        self.assertTrue(post.is_failed())
        self.assertIs(drv.state, IoPipelineDriverState.FAILED)
        self.assertFalse(drv.pipeline.is_ready)
        self.assertEqual(writer.events, ['abort', 'wait_closed'])

    async def test_close_interrupted_by_cancellation_still_releases_transport(self) -> None:
        """
        The task closing the driver may be cancelled while the close waits for the tasks it cancelled - a connection
        ending on its own just as its owner closes it, say. The transport has been aborted regardless.
        """

        writer = LifecycleStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(services=[StubIoPipelineFlowService(auto_read=False)]),
            asyncio.StreamReader(),
            ta.cast(asyncio.StreamWriter, writer),
        )
        self.assertIsNone(await drv.next(read=False))

        close_task = asyncio.ensure_future(drv.close())
        await asyncio.sleep(0)  # The close has released everything, and now waits for the tasks it cancelled.
        close_task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await close_task

        self.assertEqual(writer.events, ['abort'])
        self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
        self.assertFalse(drv.pipeline.is_ready)

        await drv.close()
        self.assertEqual(writer.events, ['abort'])

    async def test_final_output_gracefully_drains_preceding_bytes(self) -> None:
        writer = LifecycleStreamWriter()
        graceful_close = GracefulCloseIoPipelineHandler()
        completion_writer_events = []
        graceful_close.final_output.add_listener(
            lambda msg: completion_writer_events.append((msg.is_succeeded(), list(writer.events))),
        )
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [graceful_close],
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

            self.assertEqual(writer.events, [('write', b'payload'), 'drain', 'close', 'wait_closed'])
            self.assertTrue(graceful_close.final_output.is_succeeded())
            self.assertEqual(
                completion_writer_events,
                [(True, [('write', b'payload'), 'drain', 'close', 'wait_closed'])],
            )
            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            self.assertFalse(drv.pipeline.is_ready)
            self.assertTrue(ta.cast(asyncio.Task, drv._read_task).done())
        finally:
            await drv.close()

    async def test_final_output_waits_for_pending_drain(self) -> None:
        capture = CaptureOutputWritabilityIoPipelineHandler()
        writer = BlockingDrainStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [
                    capture,
                    GracefulCloseIoPipelineHandler(),
                ],
                services=[StubIoPipelineFlowService(auto_read=False)],
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
            self.assertEqual(await drv._handle_output(b'abcde'), 'handled')
            self.assertEqual(
                await drv._handle_output(IoPipelineFlowMessages.FlushOutput()),
                'handled',
            )
            await writer.drain_started.wait()

            drv.enqueue(_CLOSE)
            self.assertIsNone(await drv.next(read=False))

            self.assertFalse(writer.drain_cancelled.is_set())
            self.assertTrue(drv._drain_pending)
            self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
            self.assertEqual(
                [type(event) for event in capture.events],
                [IoPipelineFlowMessages.PauseOutput],
            )

            writer.allow_drain.set()
            await _wait_drained(drv)
            self.assertIsNone(await drv.next(read=False))

            self.assertFalse(drv._drain_pending)
            # The payload was held behind the drain and counted, so queued output never fell to the low watermark: the
            # pause is never lifted.
            self.assertEqual(
                [type(event) for event in capture.events],
                [IoPipelineFlowMessages.PauseOutput],
            )
            self.assertEqual(
                writer.events,
                [
                    ('write', b'abcde'),
                    'drain',
                    ('write', b'payload'),
                    'drain',
                    'close',
                    'wait_closed',
                ],
            )
            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            self.assertFalse(drv.pipeline.is_ready)
        finally:
            writer.allow_drain.set()
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
        graceful_close = GracefulCloseIoPipelineHandler()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [graceful_close],
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
            self.assertFalse(graceful_close.final_output.is_done())

            writer.allow_wait_closed.set()
            self.assertIsNone(await task)

            self.assertTrue(graceful_close.final_output.is_succeeded())
            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            self.assertFalse(drv.pipeline.is_ready)
        finally:
            writer.allow_wait_closed.set()
            if task is not None:
                await asyncio.gather(task, return_exceptions=True)
            await drv.close()

    async def test_close_while_draining_is_abortive(self) -> None:
        lifecycle = LifecycleIoPipelineService()
        writer = AbortableBlockingCloseStreamWriter()
        graceful_close = GracefulCloseIoPipelineHandler()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [graceful_close],
                services=[
                    lifecycle,
                    StubIoPipelineFlowService(auto_read=False),
                ],
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
            self.assertFalse(graceful_close.final_output.is_done())
            await drv.close()
            self.assertIsNone(await task)

            self.assertTrue(graceful_close.final_output.is_failed())
            self.assertEqual(
                writer.events,
                [
                    ('write', b'payload'),
                    'drain',
                    'close',
                    'wait_closed',
                    'abort',
                    'wait_closed',
                ],
            )
            self.assertEqual(lifecycle.removed, 1)
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
        graceful_close = GracefulCloseIoPipelineHandler()
        completion_errors = []
        graceful_close.final_output.add_listener(lambda msg: completion_errors.append(msg.get_exception()))
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [graceful_close],
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
            self.assertTrue(graceful_close.final_output.is_failed())
            self.assertEqual(completion_errors, [error])
            self.assertEqual(
                writer.events,
                [
                    ('write', b'payload'),
                    'drain',
                    'close',
                    'wait_closed',
                    'abort',
                    'wait_closed',
                ],
            )
            self.assertIs(drv.state, IoPipelineDriverState.FAILED)
            self.assertFalse(drv.pipeline.is_ready)
        finally:
            await drv.close()

        self.assertIs(drv.state, IoPipelineDriverState.FAILED)


class _ShutdownApp(IoPipelineHandler):
    def __init__(self, request: bytes) -> None:
        super().__init__()

        self._request = request
        self.shutdown_output = IoPipelineMessages.ShutdownOutput()
        self.final_output = IoPipelineMessages.FinalOutput()
        self.shutdown_errors: ta.List[ta.Optional[BaseException]] = []
        self.received = bytearray()
        self.shutdown_output.add_listener(
            lambda m: self.shutdown_errors.append(m.get_exception() if m.is_failed() else None),
        )

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            ctx.feed_out(self._request)
            ctx.feed_out(self.shutdown_output)
            return

        if ByteStreamBuffers.can_bytes(msg):
            self.received.extend(ByteStreamBuffers.to_bytes(msg, strict=True))
            return

        if isinstance(msg, IoPipelineMessages.FinalInput):
            ctx.feed_in(msg)
            ctx.feed_out(self.final_output)
            return

        ctx.feed_in(msg)


class TestPollAsyncioStreamIoPipelineDriverOutputShutdown(AsyncioIsolatedAsyncTestCase):
    async def test_shutdown_without_writer_completes(self) -> None:
        app = _ShutdownApp(b'dropped')
        reader = asyncio.StreamReader()
        reader.feed_eof()
        driver = PollAsyncioStreamIoPipelineDriver(IoPipeline.Spec([app]), reader)
        try:
            await asyncio.wait_for(driver.loop_until_done(), 5.)
            self.assertTrue(app.shutdown_output.is_succeeded())
            self.assertTrue(driver.output_shutdown)
            self.assertIs(driver.state, IoPipelineDriverState.CLOSED)
        finally:
            await driver.close()

    async def test_tls_stream_cannot_write_eof_so_shutdown_fails_and_stream_stays_usable(self) -> None:
        # An asyncio TLS transport cannot write EOF (TLS half-close belongs to the pipeline's own TLS handler), so the
        # message fails clearly - and the connection carries on.
        import ssl

        from ......secrets import tempssl
        from ......subprocesses import sync as _  # noqa  # import side-effect installing _DEFAULT_SUBPROCESSES
        from ....errors import UnsupportedIoPipelineError

        cert = tempssl.generate_temp_localhost_ssl_cert().cert
        server_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        server_ctx.load_cert_chain(cert.cert_file, cert.key_file)
        client_ctx = ssl.create_default_context(cafile=cert.cert_file)

        request = b'hello over asyncio tls'

        async def on_connect(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            data = await reader.readexactly(len(request))
            writer.write(data.upper())
            await writer.drain()
            writer.close()
            await writer.wait_closed()

        server = await asyncio.start_server(on_connect, '127.0.0.1', 0, ssl=server_ctx)
        try:
            port = server.sockets[0].getsockname()[1]
            reader, writer = await asyncio.open_connection(
                '127.0.0.1',
                port,
                ssl=client_ctx,
                server_hostname='localhost',
            )
            self.assertFalse(writer.can_write_eof())

            app = _ShutdownApp(request)
            driver = PollAsyncioStreamIoPipelineDriver(IoPipeline.Spec([app]), reader, writer)
            try:
                await asyncio.wait_for(driver.loop_until_done(), 10.)
            finally:
                await driver.close()

            self.assertTrue(app.shutdown_output.is_failed())
            self.assertEqual(len(app.shutdown_errors), 1)
            self.assertIsInstance(app.shutdown_errors[0], UnsupportedIoPipelineError)
            self.assertFalse(driver.output_shutdown)
            self.assertEqual(bytes(app.received), request.upper())
            self.assertTrue(app.final_output.is_succeeded())
            self.assertIs(driver.state, IoPipelineDriverState.CLOSED)

        finally:
            server.close()
            await server.wait_closed()
