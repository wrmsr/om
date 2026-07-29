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
from ...core import IoPipelineService
from ...core import IoPipelineUpdate
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
    def test_invalid_chunk_sizes(self):
        with self.assertRaises(ValueError):
            PollAsyncioStreamIoPipelineDriver.Config(read_chunk_size=0)
        with self.assertRaises(ValueError):
            PollAsyncioStreamIoPipelineDriver.Config(write_chunk_max=0)

    def test_invalid_watermarks(self):
        with self.assertRaises(ValueError):
            PollAsyncioStreamIoPipelineDriver.Config(
                write_high_watermark=1,
                write_low_watermark=2,
            )

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
            self.assertIsNone(drv._drain_task)
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
            drain_task = drv._drain_task
            if drain_task is None:
                self.fail('Expected a pending drain task')
            await drain_task
            await asyncio.sleep(0)
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
            self.assertIsNotNone(drv._drain_task)

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
            self.assertEqual(await drv._handle_output(b'abcde'), 'handled')
            first_flush_output = IoPipelineFlowMessages.FlushOutput()
            self.assertEqual(
                await drv._handle_output(first_flush_output),
                'handled',
            )
            await writer.drain_started.wait()
            self.assertFalse(first_flush_output.is_done())

            first_task = drv._drain_task
            if first_task is None:
                self.fail('Expected a pending drain task')
            second_flush_output = IoPipelineFlowMessages.FlushOutput()
            self.assertEqual(
                await drv._handle_output(second_flush_output),
                'handled',
            )
            self.assertIs(drv._drain_task, first_task)
            self.assertTrue(drv._drain_again)
            self.assertFalse(second_flush_output.is_done())

            writer.allow_drain.set()
            await first_task
            await asyncio.sleep(0)
            self.assertIsNone(await drv.next(read=False))
            self.assertTrue(first_flush_output.is_succeeded())
            self.assertFalse(second_flush_output.is_done())

            second_task = drv._drain_task
            if second_task is None:
                self.fail('Expected a coalesced follow-up drain task')
            self.assertIsNot(second_task, first_task)
            await second_task
            await asyncio.sleep(0)
            self.assertIsNone(await drv.next(read=False))
            self.assertTrue(second_flush_output.is_succeeded())

            self.assertEqual(writer.drain_calls, 2)
            self.assertEqual(writer.max_active_drains, 1)
            self.assertIsNone(drv._drain_task)
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

            drain_task = drv._drain_task
            if drain_task is None:
                self.fail('Expected a pending drain task')
            with self.assertRaises(BrokenPipeError) as task_raised:
                await drain_task
            self.assertIs(task_raised.exception, error)

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
            self.assertIsNotNone(drv._drain_task)
            self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
            self.assertEqual(
                [type(event) for event in capture.events],
                [IoPipelineFlowMessages.PauseOutput],
            )

            writer.allow_drain.set()
            drain_task = drv._drain_task
            if drain_task is None:
                self.fail('Expected a pending drain task')
            await drain_task
            await asyncio.sleep(0)
            self.assertIsNone(await drv.next(read=False))

            self.assertIsNone(drv._drain_task)
            self.assertFalse(drv._drain_again)
            self.assertEqual(
                [type(event) for event in capture.events],
                [
                    IoPipelineFlowMessages.PauseOutput,
                    IoPipelineFlowMessages.ReadyForOutput,
                    IoPipelineFlowMessages.PauseOutput,
                ],
            )
            self.assertEqual(
                writer.events,
                [
                    ('write', b'abcde'),
                    'drain',
                    ('write', b'payload'),
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

    async def test_close_while_draining_is_abortive(self) -> None:
        lifecycle = LifecycleIoPipelineService()
        writer = AbortableBlockingCloseStreamWriter()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [GracefulCloseIoPipelineHandler()],
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
            await drv.close()
            self.assertIsNone(await task)

            self.assertEqual(
                writer.events,
                [
                    ('write', b'payload'),
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
            self.assertEqual(
                writer.events,
                [
                    ('write', b'payload'),
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
