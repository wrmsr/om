# ruff: noqa: SLF001 UP006 UP045
# @om-lite
import asyncio
import gc
import socket
import time
import typing as ta
import unittest
import weakref

from .....lite.check import check
from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ....fdio.manager import FdioManager
from ....fdio.pollers import SelectFdioPoller
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineHandlerRef
from ...core import IoPipelineMessages
from ...core import IoPipelineService
from ...drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ...drivers.fdio import IoPipelineDriverSocketFdioHandler
from ...drivers.sync import SyncSocketIoPipelineDriver
from ...errors import IoPipelineError
from ...errors import TimeoutIoPipelineError
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ..timeouts import IdleStateIoPipelineEvent
from ..timeouts import IdleStateIoPipelineHandler
from ..timeouts import IoPipelineIdleState
from ..timeouts import ReadTimeoutIoPipelineHandler
from ..timeouts import WriteTimeoutIoPipelineHandler
from ..types import IoPipelineScheduling


class ManualIoPipelineScheduling(IoPipelineScheduling, IoPipelineService):
    class Handle(IoPipelineScheduling.Handle):
        def __init__(
                self,
                owner: IoPipelineHandlerRef,
                delay_s: float,
                fn: ta.Callable[..., None],
                with_context: bool,
        ) -> None:
            super().__init__()

            self.__context_ref = weakref.ref(owner._context)
            self.delay_s = delay_s
            self.fn = fn
            self.with_context = with_context

            self.cancelled = False
            self.done = False

        def cancel(self) -> None:
            self.cancelled = True

        def run(self, pipeline: IoPipeline) -> None:
            if self.cancelled or self.done:
                raise RuntimeError('Scheduled handle is not live')

            self.done = True
            with pipeline.enter():
                if self.with_context:
                    self.fn(self.context)
                else:
                    self.fn()

        @property
        def context(self) -> IoPipelineHandlerContext:
            return check.not_none(self.__context_ref())

    def __init__(self) -> None:
        super().__init__()

        self.handles: ta.List[ManualIoPipelineScheduling.Handle] = []

    def schedule(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[], None],
    ) -> IoPipelineScheduling.Handle:
        handle = self.Handle(handler_ref, delay_s, fn, False)
        self.handles.append(handle)
        return handle

    def schedule_context(
            self,
            handler_ref: IoPipelineHandlerRef,
            delay_s: float,
            fn: ta.Callable[[IoPipelineHandlerContext], None],
    ) -> IoPipelineScheduling.Handle:
        handle = self.Handle(handler_ref, delay_s, fn, True)
        self.handles.append(handle)
        return handle

    def cancel_all(self, handler_ref: ta.Optional[IoPipelineHandlerRef] = None) -> None:
        for handle in self.handles:
            if handler_ref is None or handle.context is handler_ref._context:
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
    def __init__(self, *, emit: bool = False) -> None:
        super().__init__(emit=emit)

        self.flush_outputs: ta.List[IoPipelineFlowMessages.FlushOutput] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _WRITE_ACTIVITY:
            ctx.feed_out('write')

        elif msg is _WRITE_CONTROL:
            flush_output = IoPipelineFlowMessages.FlushOutput()
            self.flush_outputs.append(flush_output)
            ctx.feed_out(flush_output)
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
            all_handle = idle._handles[IoPipelineIdleState.ALL_IDLE]
            pipeline.feed_in(_WRITE_CONTROL)
            self.assertIs(idle._handles[IoPipelineIdleState.WRITE_IDLE], write_handle)
            self.assertIsNot(idle._handles[IoPipelineIdleState.ALL_IDLE], all_handle)
            outputs = pipeline.output.drain()
            self.assertEqual(len(outputs), 2)
            flush_output = check.isinstance(outputs[0], IoPipelineFlowMessages.FlushOutput)
            all_handle = idle._handles[IoPipelineIdleState.ALL_IDLE]
            read_handle = idle._handles[IoPipelineIdleState.READ_IDLE]

            with pipeline.enter():
                flush_output.set_succeeded(None)

            self.assertIs(idle._handles[IoPipelineIdleState.READ_IDLE], read_handle)
            self.assertIsNot(idle._handles[IoPipelineIdleState.WRITE_IDLE], write_handle)
            self.assertIsNot(idle._handles[IoPipelineIdleState.ALL_IDLE], all_handle)

            write_handle = idle._handles[IoPipelineIdleState.WRITE_IDLE]
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

    def test_failed_flush_completion_is_not_activity(self) -> None:
        idle = IdleStateIoPipelineHandler(write_idle_timeout_s=1., all_idle_timeout_s=1.)
        capture = IdleStateActivityIoPipelineHandler()
        pipeline, scheduling, _ = make_idle_channel(idle, capture)
        try:
            pipeline.feed_in(_WRITE_CONTROL)
            outputs = pipeline.output.drain()
            flush_output = check.isinstance(outputs[0], IoPipelineFlowMessages.FlushOutput)
            handles_before_completion = dict(idle._handles)

            with pipeline.enter():
                flush_output.set_failed(BrokenPipeError())

            self.assertEqual(idle._handles, handles_before_completion)
            self.assertEqual(len(scheduling.live_handles()), 2)
        finally:
            pipeline.destroy()

    def test_irrelevant_flush_completion_is_not_observed(self) -> None:
        idle = IdleStateIoPipelineHandler(read_idle_timeout_s=1.)
        capture = IdleStateActivityIoPipelineHandler()
        pipeline, _, _ = make_idle_channel(idle, capture)
        try:
            pipeline.feed_in(_WRITE_CONTROL)
            outputs = pipeline.output.drain()
            flush_output = check.isinstance(outputs[0], IoPipelineFlowMessages.FlushOutput)

            self.assertFalse(hasattr(flush_output, '_completion_'))
        finally:
            pipeline.destroy()

    def test_flush_completion_after_final_output_does_not_restart_timers(self) -> None:
        idle = IdleStateIoPipelineHandler(write_idle_timeout_s=1., all_idle_timeout_s=1.)
        capture = IdleStateActivityIoPipelineHandler()
        pipeline, scheduling, _ = make_idle_channel(idle, capture)
        try:
            pipeline.feed_in(_WRITE_CONTROL)
            outputs = pipeline.output.drain()
            flush_output = check.isinstance(outputs[0], IoPipelineFlowMessages.FlushOutput)

            pipeline.feed_in(_FINAL_OUTPUT)
            self.assertEqual(idle._handles, {})
            self.assertEqual(scheduling.live_handles(), [])

            with pipeline.enter():
                flush_output.set_succeeded(None)

            self.assertEqual(idle._handles, {})
            self.assertEqual(scheduling.live_handles(), [])
        finally:
            pipeline.destroy()

    def test_pending_flush_does_not_retain_removed_handler(self) -> None:
        was_enabled = gc.isenabled()
        gc.disable()
        pipeline: ta.Optional[IoPipeline] = None
        try:
            idle = IdleStateIoPipelineHandler(write_idle_timeout_s=60.)
            capture = IdleStateActivityIoPipelineHandler()
            pipeline, scheduling, _ = make_idle_channel(idle, capture)
            pipeline.feed_in(_WRITE_CONTROL)
            outputs = pipeline.output.drain()
            flush_output = check.isinstance(outputs[0], IoPipelineFlowMessages.FlushOutput)

            idle_ref = weakref.ref(idle)
            pipeline.remove(check.not_none(pipeline.find_handler(idle)))
            del idle

            self.assertIsNone(idle_ref())
            self.assertFalse(flush_output.is_done())
            self.assertEqual(scheduling.live_handles(), [])
        finally:
            if pipeline is not None:
                pipeline.destroy()
            if was_enabled:
                gc.enable()

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

    def test_flush_completion_records_write_activity(self) -> None:
        idle = IdleStateIoPipelineHandler(write_idle_timeout_s=60.)
        capture = IdleStateActivityIoPipelineHandler()
        sock, peer = socket.socketpair()
        with sock, peer:
            drv = SyncSocketIoPipelineDriver(
                IoPipeline.Spec(
                    [idle, capture],
                    services=[StubIoPipelineFlowService(auto_read=False)],
                ),
                sock,
            )
            try:
                self.assertIsNone(drv.next(read=False))
                initial_handle = idle._handles[IoPipelineIdleState.WRITE_IDLE]

                drv.enqueue(_WRITE_CONTROL)
                self.assertIsNone(drv.next(read=False))

                self.assertTrue(check.single(capture.flush_outputs).is_succeeded())
                self.assertIsNot(idle._handles[IoPipelineIdleState.WRITE_IDLE], initial_handle)
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

    async def test_flush_completion_records_write_activity(self) -> None:
        idle = IdleStateIoPipelineHandler(write_idle_timeout_s=60.)
        capture = IdleStateActivityIoPipelineHandler()
        drv = PollAsyncioStreamIoPipelineDriver(
            IoPipeline.Spec(
                [idle, capture],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            asyncio.StreamReader(),
        )
        try:
            self.assertIsNone(await drv.next(read=False))
            initial_handle = idle._handles[IoPipelineIdleState.WRITE_IDLE]

            drv.enqueue(_WRITE_CONTROL)
            self.assertIsNone(await drv.next(read=False))

            self.assertTrue(check.single(capture.flush_outputs).is_succeeded())
            self.assertIsNot(idle._handles[IoPipelineIdleState.WRITE_IDLE], initial_handle)
        finally:
            await drv.close()


class TestFdioIdleStateIoPipelineHandler(unittest.TestCase):
    def test_flush_completion_records_write_activity(self) -> None:
        idle = IdleStateIoPipelineHandler(write_idle_timeout_s=60.)
        capture = IdleStateActivityIoPipelineHandler()
        sock, peer = socket.socketpair()
        with sock, peer:
            drv = IoPipelineDriverSocketFdioHandler(
                sock,
                ('local', 0),
                IoPipeline.Spec(
                    [idle, capture],
                    services=[StubIoPipelineFlowService(auto_read=False)],
                ),
            )
            try:
                self.assertIsNone(drv.next(read=False))
                initial_handle = idle._handles[IoPipelineIdleState.WRITE_IDLE]

                drv.enqueue(_WRITE_CONTROL)
                self.assertIsNone(drv.next(read=False))

                self.assertTrue(check.single(capture.flush_outputs).is_succeeded())
                self.assertIsNot(idle._handles[IoPipelineIdleState.WRITE_IDLE], initial_handle)
            finally:
                drv.close()


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


_EMIT_OUTPUT = object()


class WriteTimeoutTestIoPipelineHandler(IoPipelineHandler):
    def __init__(self, outputs: ta.Iterable[ta.Any], *, output_errors: bool = False) -> None:
        super().__init__()

        self._outputs = tuple(outputs)
        self._output_errors = output_errors
        self.errors: ta.List[IoPipelineMessages.Error] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _EMIT_OUTPUT:
            for output in self._outputs:
                ctx.feed_out(output)

        elif isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg)
            if self._output_errors:
                ctx.feed_out(msg.exc)

        else:
            ctx.feed_in(msg)


def make_write_timeout_pipeline(
        timeout: WriteTimeoutIoPipelineHandler,
        app: WriteTimeoutTestIoPipelineHandler,
) -> ta.Tuple[IoPipeline, ManualIoPipelineScheduling]:
    scheduling = ManualIoPipelineScheduling()
    pipeline = IoPipeline.new([timeout, app], services=[scheduling])
    pipeline.feed_initial_input()
    return (pipeline, scheduling)


def fill_socket_send_buffer(sock: socket.socket) -> int:
    timeout = sock.gettimeout()
    sock.setblocking(False)
    total = 0
    try:
        while True:
            try:
                total += sock.send(b'x' * 64 * 1024)
            except BlockingIOError:
                return total
    finally:
        sock.settimeout(timeout)


class TestWriteTimeoutIoPipelineHandler(unittest.TestCase):
    def test_invalid_timeout(self) -> None:
        for timeout_s in [0., -1., float('inf'), float('-inf'), float('nan')]:
            with self.subTest(timeout_s=timeout_s):
                with self.assertRaises(ValueError):
                    WriteTimeoutIoPipelineHandler(timeout_s)

    def test_requires_scheduler(self) -> None:
        with self.assertRaises(ValueError):
            IoPipeline.new([WriteTimeoutIoPipelineHandler(1.)])

    def test_ordinary_output_is_tickless(self) -> None:
        timeout = WriteTimeoutIoPipelineHandler(1.)
        app = WriteTimeoutTestIoPipelineHandler([b'output'])
        pipeline, scheduling = make_write_timeout_pipeline(timeout, app)
        try:
            pipeline.feed_in(_EMIT_OUTPUT)

            self.assertEqual(pipeline.output.drain(), [b'output'])
            self.assertEqual(timeout._handles, {})
            self.assertEqual(scheduling.live_handles(), [])
        finally:
            pipeline.destroy()

    def test_flush_completion_cancels_independent_deadlines(self) -> None:
        first = IoPipelineFlowMessages.FlushOutput()
        second = IoPipelineFlowMessages.FlushOutput()
        timeout = WriteTimeoutIoPipelineHandler(1.)
        app = WriteTimeoutTestIoPipelineHandler([b'output', first, second])
        pipeline, scheduling = make_write_timeout_pipeline(timeout, app)
        try:
            pipeline.feed_in(_EMIT_OUTPUT)
            self.assertEqual(pipeline.output.drain(), [b'output', first, second])
            self.assertEqual(len(scheduling.live_handles()), 2)

            with pipeline.enter():
                first.set_succeeded(None)
            self.assertEqual(len(scheduling.live_handles()), 1)

            with pipeline.enter():
                second.set_succeeded(None)
            self.assertEqual(timeout._handles, {})
            self.assertEqual(scheduling.live_handles(), [])
            self.assertEqual(app.errors, [])
        finally:
            pipeline.destroy()

    def test_oldest_pending_fence_times_out_once(self) -> None:
        first = IoPipelineFlowMessages.FlushOutput()
        second = IoPipelineFlowMessages.FlushOutput()
        timeout = WriteTimeoutIoPipelineHandler(1.)
        app = WriteTimeoutTestIoPipelineHandler([first, second])
        pipeline, scheduling = make_write_timeout_pipeline(timeout, app)
        try:
            pipeline.feed_in(_EMIT_OUTPUT)
            pipeline.output.drain()
            handles = scheduling.live_handles()
            self.assertEqual(len(handles), 2)

            handles[0].run(pipeline)

            self.assertTrue(timeout._timed_out)
            self.assertEqual(timeout._handles, {})
            self.assertEqual(scheduling.live_handles(), [])
            self.assertEqual(len(app.errors), 1)
            error = app.errors[0]
            self.assertIsInstance(error.exc, TimeoutIoPipelineError)
            self.assertEqual(str(error.exc), 'Write timed out after 1 seconds')
            self.assertEqual(error.direction, 'outbound')
            handler_ref = check.not_none(error.handler)
            self.assertIs(handler_ref.handler, timeout)
            self.assertFalse(first.is_done())
            self.assertFalse(second.is_done())

            with pipeline.enter():
                first.set_succeeded(None)
                second.set_succeeded(None)
            self.assertTrue(first.is_succeeded())
            self.assertTrue(second.is_succeeded())
            self.assertEqual(len(app.errors), 1)
        finally:
            pipeline.destroy()

    def test_final_output_is_timed_until_completion(self) -> None:
        final_output = IoPipelineMessages.FinalOutput()
        timeout = WriteTimeoutIoPipelineHandler(1.)
        app = WriteTimeoutTestIoPipelineHandler([final_output])
        pipeline, scheduling = make_write_timeout_pipeline(timeout, app)
        try:
            pipeline.feed_in(_EMIT_OUTPUT)
            self.assertEqual(pipeline.output.drain(), [final_output])
            self.assertEqual(len(scheduling.live_handles()), 1)

            with pipeline.enter():
                final_output.set_succeeded(None)

            self.assertTrue(final_output.is_succeeded())
            self.assertFalse(timeout._active)
            self.assertEqual(timeout._handles, {})
            self.assertEqual(scheduling.live_handles(), [])
        finally:
            pipeline.destroy()

    def test_final_output_timeout_preserves_late_completion(self) -> None:
        final_output = IoPipelineMessages.FinalOutput()
        timeout = WriteTimeoutIoPipelineHandler(1.)
        app = WriteTimeoutTestIoPipelineHandler([final_output])
        pipeline, scheduling = make_write_timeout_pipeline(timeout, app)
        try:
            pipeline.feed_in(_EMIT_OUTPUT)
            self.assertEqual(pipeline.output.drain(), [final_output])

            check.single(scheduling.live_handles()).run(pipeline)

            self.assertEqual(len(app.errors), 1)
            self.assertIsInstance(app.errors[0].exc, TimeoutIoPipelineError)
            self.assertFalse(final_output.is_done())

            with pipeline.enter():
                final_output.set_succeeded(None)
            self.assertTrue(final_output.is_succeeded())
            self.assertFalse(timeout._active)
            self.assertEqual(len(app.errors), 1)
        finally:
            pipeline.destroy()

    def test_pending_fence_does_not_retain_removed_handler(self) -> None:
        was_enabled = gc.isenabled()
        gc.disable()
        pipeline: ta.Optional[IoPipeline] = None
        try:
            flush_output = IoPipelineFlowMessages.FlushOutput()
            timeout = WriteTimeoutIoPipelineHandler(60.)
            app = WriteTimeoutTestIoPipelineHandler([flush_output])
            pipeline, scheduling = make_write_timeout_pipeline(timeout, app)
            pipeline.feed_in(_EMIT_OUTPUT)
            self.assertEqual(pipeline.output.drain(), [flush_output])
            self.assertEqual(len(scheduling.live_handles()), 1)

            timeout_ref = weakref.ref(timeout)
            pipeline.remove(check.not_none(pipeline.find_handler(timeout)))
            del timeout

            self.assertIsNone(timeout_ref())
            self.assertFalse(flush_output.is_done())
            self.assertEqual(scheduling.live_handles(), [])
        finally:
            if pipeline is not None:
                pipeline.destroy()
            if was_enabled:
                gc.enable()


def make_write_timeout_driver_spec(
        timeout: WriteTimeoutIoPipelineHandler,
        app: WriteTimeoutTestIoPipelineHandler,
) -> IoPipeline.Spec:
    return IoPipeline.Spec(
        [timeout, app],
        services=[StubIoPipelineFlowService(auto_read=False)],
    )


class TestSyncWriteTimeoutIoPipelineHandler(unittest.TestCase):
    def test_stalled_socket_flush_expires(self) -> None:
        sock, peer = socket.socketpair()
        with sock, peer:
            self.assertGreater(fill_socket_send_buffer(sock), 0)
            flush_output = IoPipelineFlowMessages.FlushOutput()
            timeout = WriteTimeoutIoPipelineHandler(.01)
            app = WriteTimeoutTestIoPipelineHandler([b'output', flush_output], output_errors=True)
            driver = SyncSocketIoPipelineDriver(make_write_timeout_driver_spec(timeout, app), sock)
            try:
                self.assertIsNone(driver.next(read=False))
                driver.enqueue(_EMIT_OUTPUT)

                start = time.monotonic()
                error = driver.next()
                elapsed = time.monotonic() - start

                self.assertIsInstance(error, TimeoutIoPipelineError)
                self.assertGreaterEqual(elapsed, .005)
                self.assertLess(elapsed, .5)
                self.assertEqual(len(app.errors), 1)
                self.assertIs(app.errors[0].exc, error)
                self.assertFalse(flush_output.is_done())
                self.assertGreater(driver._write_q_bytes, 0)
                self.assertIsNone(driver._sched.next_delay())
            finally:
                driver.close()


class TestAsyncioWriteTimeoutIoPipelineHandler(AsyncioIsolatedAsyncTestCase):
    async def test_stalled_stream_flush_expires(self) -> None:
        sock, peer = socket.socketpair()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 4096)
        peer.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
        writer: ta.Optional[asyncio.StreamWriter] = None
        driver: ta.Optional[PollAsyncioStreamIoPipelineDriver] = None
        try:
            reader, writer = await asyncio.open_connection(sock=sock)
            flush_output = IoPipelineFlowMessages.FlushOutput()
            timeout = WriteTimeoutIoPipelineHandler(.01)
            app = WriteTimeoutTestIoPipelineHandler([
                b'x' * (4 * 1024 * 1024),
                flush_output,
            ], output_errors=True)
            driver = PollAsyncioStreamIoPipelineDriver(
                make_write_timeout_driver_spec(timeout, app),
                reader,
                writer,
                PollAsyncioStreamIoPipelineDriver.Config(
                    write_high_watermark=1024,
                    write_low_watermark=512,
                ),
            )
            self.assertIsNone(await driver.next(read=False))
            driver.enqueue(_EMIT_OUTPUT)
            self.assertIsNone(await driver.next(read=False))
            self.assertFalse(flush_output.is_done())

            start = time.monotonic()
            error = await asyncio.wait_for(driver.next(), .5)
            elapsed = time.monotonic() - start

            self.assertIsInstance(error, TimeoutIoPipelineError)
            self.assertGreaterEqual(elapsed, .005)
            self.assertLess(elapsed, .5)
            self.assertEqual(len(app.errors), 1)
            self.assertIs(app.errors[0].exc, error)
            self.assertFalse(flush_output.is_done())
            self.assertEqual(driver._sched._live, set())
        finally:
            if driver is not None:
                await driver.close()
            elif writer is not None:
                writer.close()
                await writer.wait_closed()
            sock.close()
            peer.close()


class TestFdioWriteTimeoutIoPipelineHandler(unittest.TestCase):
    def test_stalled_socket_flush_expires(self) -> None:
        sock, peer = socket.socketpair()
        poller = SelectFdioPoller()
        with sock, peer:
            self.assertGreater(fill_socket_send_buffer(sock), 0)
            flush_output = IoPipelineFlowMessages.FlushOutput()
            timeout = WriteTimeoutIoPipelineHandler(.01)
            app = WriteTimeoutTestIoPipelineHandler([b'output', flush_output])
            driver = IoPipelineDriverSocketFdioHandler(
                sock,
                ('local', 0),
                make_write_timeout_driver_spec(timeout, app),
            )
            manager = FdioManager(poller)
            try:
                self.assertIsNone(driver.next(read=False))
                driver.enqueue(_EMIT_OUTPUT)
                self.assertIsNone(driver.next(read=False))
                self.assertFalse(flush_output.is_done())
                self.assertGreater(driver._write_q_bytes, 0)
                manager.register(driver)

                start = time.monotonic()
                manager.poll()
                elapsed = time.monotonic() - start

                self.assertGreaterEqual(elapsed, .005)
                self.assertLess(elapsed, .5)
                self.assertEqual(len(app.errors), 1)
                self.assertIsInstance(app.errors[0].exc, TimeoutIoPipelineError)
                self.assertFalse(flush_output.is_done())
                self.assertIsNone(driver.next_deadline())
            finally:
                if id(driver) in manager._handlers:
                    manager.unregister(driver)
                driver.close()
                poller.close()
