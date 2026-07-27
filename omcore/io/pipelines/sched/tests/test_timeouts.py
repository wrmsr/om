# ruff: noqa: SLF001 UP006 UP045
# @om-lite
import asyncio
import typing as ta
import unittest

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineHandlerRef
from ...core import IoPipelineMessages
from ...core import IoPipelineService
from ...drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ...drivers.sync import SyncSocketIoPipelineDriver
from ...errors import IoPipelineError
from ...errors import TimeoutIoPipelineError
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ..timeouts import IdleStateIoPipelineEvent
from ..timeouts import IdleStateIoPipelineHandler
from ..timeouts import IoPipelineIdleState
from ..timeouts import ReadTimeoutIoPipelineHandler
from ..types import IoPipelineScheduling


class ManualIoPipelineScheduling(IoPipelineScheduling, IoPipelineService):
    class Handle(IoPipelineScheduling.Handle):
        def __init__(
                self,
                owner: IoPipelineHandlerRef,
                delay_s: float,
                fn: ta.Callable[[], None],
        ) -> None:
            super().__init__()

            self.owner = owner
            self.delay_s = delay_s
            self.fn = fn

            self.cancelled = False
            self.done = False

        def cancel(self) -> None:
            self.cancelled = True

        def run(self, pipeline: IoPipeline) -> None:
            if self.cancelled or self.done:
                raise RuntimeError('Scheduled handle is not live')

            self.done = True
            with pipeline.enter():
                self.fn()

    def __init__(self) -> None:
        super().__init__()

        self.handles: ta.List[ManualIoPipelineScheduling.Handle] = []

    def schedule(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[], None],
    ) -> IoPipelineScheduling.Handle:
        handle = self.Handle(handler_ref, delay_s, fn)
        self.handles.append(handle)
        return handle

    def cancel_all(self, handler_ref: ta.Optional[IoPipelineHandlerRef] = None) -> None:
        for handle in self.handles:
            if handler_ref is None or handle.owner is handler_ref:
                handle.cancel()

    def live_handles(self) -> ta.List[Handle]:
        return [handle for handle in self.handles if not handle.cancelled and not handle.done]


class CaptureIdleStateIoPipelineHandler(IoPipelineHandler):
    def __init__(self, *, emit: bool = False) -> None:
        super().__init__()

        self._emit = emit
        self.events: ta.List[IdleStateIoPipelineEvent] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IdleStateIoPipelineEvent):
            self.events.append(msg)
            if self._emit:
                ctx.feed_out(msg.state.value)

        elif isinstance(msg, IoPipelineMessages.MustPropagate):
            ctx.feed_in(msg)


_WRITE_ACTIVITY = object()
_WRITE_CONTROL = object()
_FINAL_OUTPUT = object()


class IdleStateActivityIoPipelineHandler(CaptureIdleStateIoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _WRITE_ACTIVITY:
            ctx.feed_out('write')

        elif msg is _WRITE_CONTROL:
            ctx.feed_out(IoPipelineFlowMessages.FlushOutput())
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

        elif msg is _FINAL_OUTPUT:
            ctx.feed_final_output()

        else:
            super().inbound(ctx, msg)


def make_idle_channel(
        idle: IdleStateIoPipelineHandler,
        capture: ta.Optional[CaptureIdleStateIoPipelineHandler] = None,
) -> ta.Tuple[IoPipeline, ManualIoPipelineScheduling, CaptureIdleStateIoPipelineHandler]:
    scheduling = ManualIoPipelineScheduling()
    if capture is None:
        capture = CaptureIdleStateIoPipelineHandler()
    pipeline = IoPipeline.new([idle, capture], services=[scheduling])
    pipeline.feed_initial_input()
    return (pipeline, scheduling, capture)


class TestIdleStateIoPipelineHandler(unittest.TestCase):
    def test_invalid_timeouts(self):
        constructors = [
            lambda timeout_s: IdleStateIoPipelineHandler(read_idle_timeout_s=timeout_s),
            lambda timeout_s: IdleStateIoPipelineHandler(write_idle_timeout_s=timeout_s),
            lambda timeout_s: IdleStateIoPipelineHandler(all_idle_timeout_s=timeout_s),
        ]
        for constructor in constructors:
            for timeout_s in [0., -1., float('inf'), float('-inf'), float('nan')]:
                with self.subTest(constructor=constructor, timeout_s=timeout_s):
                    with self.assertRaises(ValueError):
                        constructor(timeout_s)

    def test_unconfigured_is_tickless_and_does_not_require_scheduler(self):
        idle = IdleStateIoPipelineHandler()
        pipeline = IoPipeline.new(
            [idle],
            IoPipeline.Config(inbound_terminal='drop'),
        )
        try:
            pipeline.feed_initial_input()
            pipeline.feed_in(b'read')

            self.assertEqual(idle._handles, {})
            self.assertIsNone(pipeline.services.find(IoPipelineScheduling))
        finally:
            pipeline.destroy()

    def test_configured_timeout_requires_scheduler(self):
        with self.assertRaises(ValueError):
            IoPipeline.new([IdleStateIoPipelineHandler(read_idle_timeout_s=1.)])

    def test_independent_events_repeat_and_activity_resets_first(self):
        idle = IdleStateIoPipelineHandler(
            read_idle_timeout_s=1.,
            write_idle_timeout_s=2.,
            all_idle_timeout_s=3.,
        )
        pipeline, scheduling, capture = make_idle_channel(idle)
        try:
            initial_handles = ta.cast(
                ta.Dict[IoPipelineIdleState, ManualIoPipelineScheduling.Handle],
                dict(idle._handles),
            )
            self.assertEqual(
                {state: handle.delay_s for state, handle in initial_handles.items()},
                {
                    IoPipelineIdleState.READ_IDLE: 1.,
                    IoPipelineIdleState.WRITE_IDLE: 2.,
                    IoPipelineIdleState.ALL_IDLE: 3.,
                },
            )

            for state in IdleStateIoPipelineHandler._STATES:
                initial_handles[state].run(pipeline)

            self.assertEqual(
                capture.events,
                [
                    IdleStateIoPipelineEvent(IoPipelineIdleState.READ_IDLE, True),
                    IdleStateIoPipelineEvent(IoPipelineIdleState.WRITE_IDLE, True),
                    IdleStateIoPipelineEvent(IoPipelineIdleState.ALL_IDLE, True),
                ],
            )

            repeated_handles = ta.cast(
                ta.Dict[IoPipelineIdleState, ManualIoPipelineScheduling.Handle],
                dict(idle._handles),
            )
            for state in IdleStateIoPipelineHandler._STATES:
                repeated_handles[state].run(pipeline)

            self.assertEqual(
                capture.events[3:],
                [
                    IdleStateIoPipelineEvent(IoPipelineIdleState.READ_IDLE, False),
                    IdleStateIoPipelineEvent(IoPipelineIdleState.WRITE_IDLE, False),
                    IdleStateIoPipelineEvent(IoPipelineIdleState.ALL_IDLE, False),
                ],
            )

            pipeline.feed_in(b'read')
            ta.cast(
                ManualIoPipelineScheduling.Handle,
                idle._handles[IoPipelineIdleState.READ_IDLE],
            ).run(pipeline)
            ta.cast(
                ManualIoPipelineScheduling.Handle,
                idle._handles[IoPipelineIdleState.ALL_IDLE],
            ).run(pipeline)

            self.assertEqual(
                capture.events[-2:],
                [
                    IdleStateIoPipelineEvent(IoPipelineIdleState.READ_IDLE, True),
                    IdleStateIoPipelineEvent(IoPipelineIdleState.ALL_IDLE, True),
                ],
            )
            self.assertEqual(len(scheduling.live_handles()), 3)
        finally:
            pipeline.destroy()

    def test_read_write_and_control_activity(self):
        idle = IdleStateIoPipelineHandler(
            read_idle_timeout_s=1.,
            write_idle_timeout_s=1.,
            all_idle_timeout_s=1.,
        )
        capture = IdleStateActivityIoPipelineHandler()
        pipeline, scheduling, _ = make_idle_channel(idle, capture)
        try:
            initial_handles = dict(idle._handles)

            pipeline.feed_in(IoPipelineFlowMessages.FlushInput())
            pipeline.feed_in(IoPipelineFlowMessages.PauseOutput())
            pipeline.feed_in(IoPipelineFlowMessages.ReadyForOutput())
            self.assertEqual(idle._handles, initial_handles)

            pipeline.feed_in(b'read')
            self.assertIsNot(
                idle._handles[IoPipelineIdleState.READ_IDLE],
                initial_handles[IoPipelineIdleState.READ_IDLE],
            )
            self.assertIs(
                idle._handles[IoPipelineIdleState.WRITE_IDLE],
                initial_handles[IoPipelineIdleState.WRITE_IDLE],
            )
            self.assertIsNot(
                idle._handles[IoPipelineIdleState.ALL_IDLE],
                initial_handles[IoPipelineIdleState.ALL_IDLE],
            )

            write_handle = idle._handles[IoPipelineIdleState.WRITE_IDLE]
            pipeline.feed_in(_WRITE_CONTROL)
            self.assertIs(idle._handles[IoPipelineIdleState.WRITE_IDLE], write_handle)
            pipeline.output.drain()

            pipeline.feed_in(_WRITE_ACTIVITY)
            self.assertIsNot(idle._handles[IoPipelineIdleState.WRITE_IDLE], write_handle)
            self.assertEqual(pipeline.output.drain(), ['write'])

            pipeline.feed_in(_FINAL_OUTPUT)
            self.assertEqual(idle._handles, {})
            self.assertEqual(scheduling.live_handles(), [])
            final_output = pipeline.output.drain()
            self.assertEqual(len(final_output), 1)
            self.assertIsInstance(final_output[0], IoPipelineMessages.FinalOutput)
        finally:
            pipeline.destroy()

    def test_read_idle_stops_at_final_input(self):
        idle = IdleStateIoPipelineHandler(read_idle_timeout_s=1.)
        pipeline, scheduling, _ = make_idle_channel(idle)
        try:
            pipeline.feed_final_input()

            self.assertEqual(idle._handles, {})
            self.assertEqual(scheduling.live_handles(), [])
        finally:
            pipeline.destroy()

    def test_idle_event_does_not_reset_read_timeout(self):
        idle = IdleStateIoPipelineHandler(read_idle_timeout_s=1.)
        read_timeout = ReadTimeoutIoPipelineHandler(2.)
        scheduling = ManualIoPipelineScheduling()
        pipeline = IoPipeline.new(
            [idle, read_timeout, CaptureIdleStateIoPipelineHandler()],
            services=[scheduling],
        )
        try:
            pipeline.feed_initial_input()
            read_timeout_handle = read_timeout._handle

            ta.cast(
                ManualIoPipelineScheduling.Handle,
                idle._handles[IoPipelineIdleState.READ_IDLE],
            ).run(pipeline)

            self.assertIs(read_timeout._handle, read_timeout_handle)
        finally:
            pipeline.destroy()


class TestSyncIdleStateIoPipelineHandler(unittest.TestCase):
    def test_expires(self):
        idle = IdleStateIoPipelineHandler(read_idle_timeout_s=.01)
        capture = CaptureIdleStateIoPipelineHandler(emit=True)
        drv = SyncSocketIoPipelineDriver(
            IoPipeline.Spec(
                [idle, capture],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            object(),
        )
        try:
            self.assertEqual(drv.next(), IoPipelineIdleState.READ_IDLE.value)
            self.assertEqual(
                capture.events,
                [IdleStateIoPipelineEvent(IoPipelineIdleState.READ_IDLE, True)],
            )
        finally:
            drv.close()


class TestAsyncioIdleStateIoPipelineHandler(AsyncioIsolatedAsyncTestCase):
    async def test_expires(self):
        idle = IdleStateIoPipelineHandler(read_idle_timeout_s=.01)
        capture = CaptureIdleStateIoPipelineHandler(emit=True)
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [idle, capture],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            asyncio.StreamReader(),
        )
        try:
            self.assertEqual(await drv.next(), IoPipelineIdleState.READ_IDLE.value)
            self.assertEqual(
                capture.events,
                [IdleStateIoPipelineEvent(IoPipelineIdleState.READ_IDLE, True)],
            )
        finally:
            await drv.close()


class CaptureReadTimeoutIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.errors: ta.List[IoPipelineMessages.Error] = []
        self.reads: ta.List[bytes] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg)
            ctx.feed_out(msg.exc)

        elif isinstance(msg, bytes):
            self.reads.append(msg)

        else:
            ctx.feed_in(msg)


def make_spec(
        timeout: ReadTimeoutIoPipelineHandler,
        capture: CaptureReadTimeoutIoPipelineHandler,
) -> IoPipeline.Spec:
    return IoPipeline.Spec(
        [
            timeout,
            capture,
        ],
        services=[
            StubIoPipelineFlowService(auto_read=False),
        ],
    )


class TestTimeoutIoPipelineError(unittest.TestCase):
    def test_error_hierarchy(self):
        error = TimeoutIoPipelineError()

        self.assertIsInstance(error, IoPipelineError)
        self.assertIsInstance(error, TimeoutError)


class TestSyncReadTimeoutIoPipelineHandler(unittest.TestCase):
    def test_expires(self):
        timeout = ReadTimeoutIoPipelineHandler(.01)
        capture = CaptureReadTimeoutIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, capture), object())
        try:
            error = drv.next()

            self.assertIsInstance(error, TimeoutIoPipelineError)
            self.assertEqual(len(capture.errors), 1)
            self.assertIs(capture.errors[0].exc, error)
            self.assertEqual(capture.errors[0].direction, 'inbound')
            handler_ref = capture.errors[0].handler
            if handler_ref is None:
                self.fail('Expected timeout handler ref')
            self.assertIs(handler_ref.handler, timeout)

            self.assertIsNone(drv.next(read=False))
            self.assertEqual(len(capture.errors), 1)
        finally:
            drv.close()

    def test_resets_and_stops_at_final_input(self):
        timeout = ReadTimeoutIoPipelineHandler(60.)
        capture = CaptureReadTimeoutIoPipelineHandler()
        drv = SyncSocketIoPipelineDriver(make_spec(timeout, capture), object())
        try:
            self.assertIsNone(drv.next(read=False))
            first_handle = timeout._handle
            self.assertIsNotNone(first_handle)

            drv.enqueue(IoPipelineFlowMessages.FlushInput())
            self.assertIsNone(drv.next(read=False))
            self.assertIs(timeout._handle, first_handle)

            drv.enqueue(b'read')
            self.assertIsNone(drv.next(read=False))
            second_handle = timeout._handle
            self.assertIsNotNone(second_handle)
            self.assertIsNot(second_handle, first_handle)
            self.assertEqual(capture.reads, [b'read'])

            drv.enqueue(IoPipelineMessages.FinalInput())
            self.assertIsNone(drv.next(read=False))
            self.assertIsNone(timeout._handle)
            self.assertIsNone(drv._sched.next_delay())
        finally:
            drv.close()


class TestAsyncioReadTimeoutIoPipelineHandler(AsyncioIsolatedAsyncTestCase):
    async def test_expires(self):
        timeout = ReadTimeoutIoPipelineHandler(.01)
        capture = CaptureReadTimeoutIoPipelineHandler()
        drv = PollAsyncioStreamIoPipelineDriver(
            make_spec(timeout, capture),
            asyncio.StreamReader(),
        )
        try:
            error = await drv.next()

            self.assertIsInstance(error, TimeoutIoPipelineError)
            self.assertEqual(len(capture.errors), 1)
            self.assertIs(capture.errors[0].exc, error)
            self.assertEqual(capture.errors[0].direction, 'inbound')
            handler_ref = capture.errors[0].handler
            if handler_ref is None:
                self.fail('Expected timeout handler ref')
            self.assertIs(handler_ref.handler, timeout)

            self.assertIsNone(await drv.next(read=False))
            self.assertEqual(len(capture.errors), 1)
        finally:
            await drv.close()

    async def test_resets_and_stops_at_final_input(self):
        timeout = ReadTimeoutIoPipelineHandler(60.)
        capture = CaptureReadTimeoutIoPipelineHandler()
        drv = PollAsyncioStreamIoPipelineDriver(
            make_spec(timeout, capture),
            asyncio.StreamReader(),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            first_handle = timeout._handle
            self.assertIsNotNone(first_handle)

            drv.enqueue(IoPipelineFlowMessages.FlushInput())
            self.assertIsNone(await drv.next(read=False))
            self.assertIs(timeout._handle, first_handle)

            drv.enqueue(b'read')
            self.assertIsNone(await drv.next(read=False))
            second_handle = timeout._handle
            self.assertIsNotNone(second_handle)
            self.assertIsNot(second_handle, first_handle)
            self.assertEqual(capture.reads, [b'read'])

            drv.enqueue(IoPipelineMessages.FinalInput())
            self.assertIsNone(await drv.next(read=False))
            self.assertIsNone(timeout._handle)
            self.assertEqual(drv._sched._live, set())
        finally:
            await drv.close()
