# ruff: noqa: SLF001 UP045
# @om-lite
import gc
import socket
import time
import typing as ta
import unittest
import weakref

from .....lite.check import check
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineHandlerRef
from ...core import IoPipelineMessages
from ...core import IoPipelineService
from ...core import IoPipelineUpdate
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ...sched.timeouts import ReadTimeoutIoPipelineHandler
from ...sched.types import IoPipelineScheduling
from ..sync import SyncSocketIoPipelineDriver
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


class ReschedulingTimerIoPipelineHandler(IoPipelineHandler):
    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            sched = ctx.services[IoPipelineScheduling]

            def first() -> None:
                ctx.feed_out('first')
                sched.schedule(ctx.ref, 0., lambda: ctx.feed_out('third'))

            sched.schedule(ctx.ref, 0., first)
            sched.schedule(ctx.ref, 0., lambda: ctx.feed_out('second'))

        ctx.feed_in(msg)


class NopIoPipelineHandler(IoPipelineHandler):
    pass


_CLOSE = object()
_WRITE = object()


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


class WriteIoPipelineHandler(IoPipelineHandler):
    def __init__(self, data: bytes) -> None:
        super().__init__()

        self._data = data

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _WRITE:
            ctx.feed_out(self._data)
        else:
            ctx.feed_in(msg)


class WriteAndFlushIoPipelineHandler(IoPipelineHandler):
    def __init__(self, data: bytes, flush_output: IoPipelineFlowMessages.FlushOutput) -> None:
        super().__init__()

        self._data = data
        self._flush_output = flush_output

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if msg is _WRITE:
            ctx.feed_out(self._data)
            ctx.feed_out(self._flush_output)
        else:
            ctx.feed_in(msg)


class CaptureOutputWritabilityIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.events: list[ta.Any] = []

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, (IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput)):
            self.events.append(msg)
        ctx.feed_in(msg)


class CaptureFinalInputIoPipelineHandler(IoPipelineHandler):
    def __init__(self) -> None:
        super().__init__()

        self.saw_final_input = False

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self.saw_final_input = True
        ctx.feed_in(msg)


class FailingSendSocket:
    def __init__(self, exc: BaseException) -> None:
        self._exc = exc

    def send(self, data: ta.Any) -> int:
        raise self._exc


class FailingRecvSocket:
    def __init__(self, sock: socket.socket, exc: BaseException) -> None:
        self._sock = sock
        self._exc = exc

    def fileno(self) -> int:
        return self._sock.fileno()

    def gettimeout(self) -> ta.Optional[float]:
        return self._sock.gettimeout()

    def setblocking(self, flag: bool) -> None:
        self._sock.setblocking(flag)

    def settimeout(self, value: ta.Optional[float]) -> None:
        self._sock.settimeout(value)

    def recv(self, size: int) -> bytes:
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


def drain_socket(sock: socket.socket) -> bytes:
    timeout = sock.gettimeout()
    sock.setblocking(False)
    chunks = []
    try:
        while True:
            try:
                chunks.append(sock.recv(64 * 1024))
            except BlockingIOError:
                return b''.join(chunks)
    finally:
        sock.settimeout(timeout)


class TestSyncSocketIoPipelineDriverScheduling(unittest.TestCase):
    def make_driver(self, *handlers: IoPipelineHandler) -> SyncSocketIoPipelineDriver:
        drv = SyncSocketIoPipelineDriver(
            IoPipeline.Spec(
                handlers,
                services=[
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
            object(),
        )
        self.assertIsNone(drv.next(read=False))
        return drv

    def find_handler_ref(
            self,
            drv: SyncSocketIoPipelineDriver,
            handler: IoPipelineHandler,
    ) -> IoPipelineHandlerRef:
        ref = drv.pipeline.find_handler(handler)
        if ref is None:
            self.fail('Expected handler in pipeline')
        return ref

    def test_active_handler_timer_does_not_require_cyclic_gc(self) -> None:
        def make_refs():
            drv = self.make_driver(ReadTimeoutIoPipelineHandler(60.))
            handler_ref = check.not_none(drv.pipeline.find_single_handler_of_type(ReadTimeoutIoPipelineHandler))
            handler = handler_ref.handler
            handle = check.not_none(handler._handle)  # noqa
            return (
                weakref.ref(drv),
                weakref.ref(drv.pipeline),
                weakref.ref(handler),
                weakref.ref(handle),
            )

        was_enabled = gc.isenabled()
        gc.disable()
        try:
            refs = make_refs()
            self.assertTrue(all(ref() is None for ref in refs))
        finally:
            if was_enabled:
                gc.enable()

    def test_timer_wakes_read_select(self):
        sock, peer = socket.socketpair()
        with sock, peer:
            sock.settimeout(10.)
            drv = SyncSocketIoPipelineDriver(
                IoPipeline.Spec([
                    TimerOutputIoPipelineHandler(.01, 'timer'),
                ]),
                sock,
            )
            try:
                self.assertEqual(drv.next(), 'timer')
                self.assertEqual(sock.gettimeout(), 0.)
            finally:
                drv.close()
            self.assertEqual(sock.gettimeout(), 10.)

    def test_timer_wakes_saturated_write_select(self):
        sock, peer = socket.socketpair()
        with sock, peer:
            self.assertGreater(fill_socket_send_buffer(sock), 0)
            capture = CaptureOutputWritabilityIoPipelineHandler()
            drv = SyncSocketIoPipelineDriver(
                IoPipeline.Spec(
                    [
                        TimerOutputIoPipelineHandler(.01, 'timer'),
                        capture,
                        WriteIoPipelineHandler(b'payload'),
                    ],
                    services=[StubIoPipelineFlowService(auto_read=False)],
                ),
                sock,
                SyncSocketIoPipelineDriver.Config(
                    write_high_watermark=4,
                    write_low_watermark=2,
                ),
            )
            try:
                self.assertIsNone(drv.next(read=False))
                drv.enqueue(_WRITE)

                start = time.monotonic()
                self.assertEqual(drv.next(), 'timer')
                self.assertLess(time.monotonic() - start, .5)

                self.assertEqual(drv._write_q_bytes, len(b'payload'))
                self.assertEqual(
                    [type(event) for event in capture.events],
                    [IoPipelineFlowMessages.PauseOutput],
                )
                self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
                self.assertTrue(drv.pipeline.is_ready)
            finally:
                drv.close()

            self.assertIsNone(sock.gettimeout())

    def test_handle_and_owner_cancellation(self):
        ah = NopIoPipelineHandler()
        bh = NopIoPipelineHandler()
        drv = self.make_driver(ah, bh)
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

            self.assertEqual(drv._sched._run_due(), 1)
            self.assertEqual(events, ['live'])
        finally:
            drv.close()

    def test_removal_cancels_timer_in_current_due_batch(self):
        removing_handler = NopIoPipelineHandler()
        removed_handler = NopIoPipelineHandler()
        drv = self.make_driver(removing_handler, removed_handler)
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

            self.assertEqual(drv._sched._run_due(), 1)
            self.assertEqual(events, [])
            self.assertTrue(removed_ref.invalidated)
            self.assertIsNone(drv._sched.next_delay())
            with self.assertRaises(RuntimeError):
                drv._sched.schedule(removed_ref, 0., lambda: events.append('orphan'))
        finally:
            drv.close()

    def test_destroy_cancels_all_timers(self):
        handler = NopIoPipelineHandler()
        drv = self.make_driver(handler)
        ref = self.find_handler_ref(drv, handler)

        events = []
        drv._sched.schedule(ref, 60., lambda: events.append('timer'))

        drv.close()

        self.assertIsNone(drv._sched.next_delay())
        self.assertEqual(drv._sched._run_due(), 0)
        self.assertEqual(events, [])

    def test_timer_without_read_interest(self):
        drv = SyncSocketIoPipelineDriver(
            IoPipeline.Spec(
                [
                    TimerOutputIoPipelineHandler(0., 'timer'),
                ],
                services=[
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
            object(),
        )
        try:
            self.assertEqual(drv.next(), 'timer')
        finally:
            drv.close()

    def test_due_timer_runs_with_read_false(self):
        drv = SyncSocketIoPipelineDriver(
            IoPipeline.Spec(
                [
                    TimerOutputIoPipelineHandler(0., 'timer'),
                ],
                services=[
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
            object(),
        )
        try:
            self.assertIsNone(drv.next(read=False))
            self.assertEqual(drv.next(read=False), 'timer')
        finally:
            drv.close()

    def test_future_delay_is_positive(self):
        sock, peer = socket.socketpair()
        with sock, peer:
            drv = SyncSocketIoPipelineDriver(
                IoPipeline.Spec([
                    TimerOutputIoPipelineHandler(60., 'timer'),
                ]),
                sock,
            )
            try:
                self.assertIsNone(drv.next(read=False))

                delay = drv._sched.next_delay()
                if delay is None:
                    self.fail('Expected a pending timer')
                self.assertLess(0., delay)
                self.assertLessEqual(delay, 60.)
            finally:
                drv.close()

    def test_due_batch_is_snapshotted(self):
        sock, peer = socket.socketpair()
        with sock, peer:
            drv = SyncSocketIoPipelineDriver(
                IoPipeline.Spec([
                    ReschedulingTimerIoPipelineHandler(),
                ]),
                sock,
            )
            try:
                self.assertEqual(drv.next(), 'first')
                self.assertEqual(drv.next(), 'second')
                self.assertEqual(drv.next(), 'third')
            finally:
                drv.close()


class TestSyncSocketIoPipelineDriverLifecycle(unittest.TestCase):
    def test_close_before_pipeline_initialization(self) -> None:
        drv = SyncSocketIoPipelineDriver(IoPipeline.Spec(), object())

        drv.close()
        drv.close()

        self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
        self.assertIsNone(drv._opt_pipeline())

    def test_repeated_close_destroys_pipeline_once(self) -> None:
        lifecycle = LifecycleIoPipelineService()
        drv = SyncSocketIoPipelineDriver(
            IoPipeline.Spec(
                services=[
                    lifecycle,
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
            object(),
        )
        self.assertIsNone(drv.next(read=False))

        drv.close()
        drv.close()

        self.assertEqual(lifecycle.removed, 1)
        self.assertIs(drv.state, IoPipelineDriverState.CLOSED)

    def test_pipeline_output_error_is_non_terminal(self) -> None:
        error = RuntimeError('pipeline')
        drv = SyncSocketIoPipelineDriver(
            IoPipeline.Spec(
                [OutputErrorIoPipelineHandler(error)],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            object(),
        )
        try:
            self.assertIsNone(drv.next(read=False))
            drv.enqueue(_ERROR)

            self.assertIs(drv.next(read=False), error)
            self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
            self.assertTrue(drv.pipeline.is_ready)
        finally:
            drv.close()

    def test_transport_read_failure_fails_driver(self) -> None:
        error = ConnectionResetError('reset')
        sock, peer = socket.socketpair()
        with sock, peer:
            sock.settimeout(2.)
            drv = SyncSocketIoPipelineDriver(
                IoPipeline.Spec(),
                FailingRecvSocket(sock, error),
            )
            peer.sendall(b'x')
            try:
                with self.assertRaises(ConnectionResetError) as raised:
                    drv.next()

                self.assertIs(raised.exception, error)
                self.assertIs(drv.state, IoPipelineDriverState.FAILED)
                self.assertFalse(drv.pipeline.is_ready)
                self.assertEqual(sock.gettimeout(), 2.)
            finally:
                drv.close()

        self.assertIs(drv.state, IoPipelineDriverState.FAILED)

    def test_pipeline_removal_failure_fails_close(self) -> None:
        error = RuntimeError('remove')
        lifecycle = LifecycleIoPipelineService(error)
        drv = SyncSocketIoPipelineDriver(
            IoPipeline.Spec(
                services=[
                    lifecycle,
                    StubIoPipelineFlowService(auto_read=False),
                ],
            ),
            object(),
        )
        self.assertIsNone(drv.next(read=False))

        with self.assertRaises(RuntimeError) as raised:
            drv.close()

        self.assertIs(raised.exception, error)
        self.assertEqual(lifecycle.removed, 1)
        self.assertIs(drv.state, IoPipelineDriverState.FAILED)
        self.assertFalse(drv.pipeline.is_ready)

        drv.close()
        self.assertEqual(lifecycle.removed, 1)

    def test_invalid_chunk_sizes(self) -> None:
        with self.assertRaises(ValueError):
            SyncSocketIoPipelineDriver.Config(read_chunk_size=0)
        with self.assertRaises(ValueError):
            SyncSocketIoPipelineDriver.Config(write_chunk_max=0)

    def test_invalid_watermarks(self) -> None:
        with self.assertRaises(ValueError):
            SyncSocketIoPipelineDriver.Config(
                write_high_watermark=1,
                write_low_watermark=2,
            )

    def test_stall_does_not_fail_driver(self) -> None:
        drv = SyncSocketIoPipelineDriver(
            IoPipeline.Spec(
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            object(),
        )
        try:
            self.assertIsNone(drv.next(read=False))

            with self.assertRaises(RuntimeError):
                drv.next()

            self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
            self.assertTrue(drv.pipeline.is_ready)
        finally:
            drv.close()

    def test_final_output_drains_preceding_bytes(self) -> None:
        sock, peer = socket.socketpair()
        with sock, peer:
            sock.settimeout(2.)
            graceful_close = GracefulCloseIoPipelineHandler()
            completion_socket_states = []
            graceful_close.final_output.add_listener(lambda msg: completion_socket_states.append((
                msg.is_succeeded(),
                sock.fileno() >= 0,
                sock.gettimeout(),
            )))
            drv = SyncSocketIoPipelineDriver(
                IoPipeline.Spec(
                    [graceful_close],
                    services=[StubIoPipelineFlowService(auto_read=False)],
                ),
                sock,
            )
            try:
                self.assertIsNone(drv.next(read=False))
                self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
                drv.enqueue(_CLOSE)

                self.assertIsNone(drv.next(read=False))

                self.assertEqual(peer.recv(7), b'payload')
                self.assertTrue(graceful_close.final_output.is_succeeded())
                self.assertEqual(completion_socket_states, [(True, True, 2.)])
                self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
                self.assertFalse(drv.pipeline.is_ready)
            finally:
                drv.close()

    def test_close_while_draining_discards_queued_bytes(self) -> None:
        sock, peer = socket.socketpair()
        with sock, peer:
            self.assertGreater(fill_socket_send_buffer(sock), 0)
            lifecycle = LifecycleIoPipelineService()
            graceful_close = GracefulCloseIoPipelineHandler()
            drv = SyncSocketIoPipelineDriver(
                IoPipeline.Spec(
                    [graceful_close],
                    services=[
                        lifecycle,
                        StubIoPipelineFlowService(auto_read=False),
                    ],
                ),
                sock,
            )
            self.assertIsNone(drv.next(read=False))
            drv.enqueue(_CLOSE)
            self.assertIsNone(drv.next(read=False))

            self.assertIs(drv.state, IoPipelineDriverState.DRAINING)
            self.assertEqual(drv._write_q_bytes, len(b'payload'))
            self.assertFalse(graceful_close.final_output.is_done())

            drv.close()

            self.assertTrue(graceful_close.final_output.is_failed())
            self.assertEqual(drv._write_q_bytes, 0)
            self.assertEqual(list(drv._write_q), [])
            self.assertEqual(lifecycle.removed, 1)
            self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
            self.assertFalse(drv.pipeline.is_ready)

    def test_output_writability_watermark_hysteresis(self) -> None:
        sock, peer = socket.socketpair()
        with sock, peer:
            self.assertGreater(fill_socket_send_buffer(sock), 0)
            capture = CaptureOutputWritabilityIoPipelineHandler()
            drv = SyncSocketIoPipelineDriver(
                IoPipeline.Spec(
                    [
                        capture,
                        WriteIoPipelineHandler(b'abcde'),
                    ],
                    services=[StubIoPipelineFlowService(auto_read=False)],
                ),
                sock,
                SyncSocketIoPipelineDriver.Config(
                    write_chunk_max=2,
                    write_high_watermark=4,
                    write_low_watermark=2,
                ),
            )
            try:
                self.assertIsNone(drv.next(read=False))
                drv.enqueue(_WRITE)
                self.assertIsNone(drv.next(read=False))

                self.assertEqual(drv._write_q_bytes, 5)
                self.assertEqual(
                    [type(event) for event in capture.events],
                    [IoPipelineFlowMessages.PauseOutput],
                )

                self.assertIsNone(drv.next(read=False))
                self.assertEqual(len(capture.events), 1)

                self.assertTrue(drain_socket(peer))
                self.assertTrue(drv._try_write())
                self.assertEqual(drv._write_q_bytes, 3)
                self.assertEqual(len(capture.events), 1)

                self.assertTrue(drv._try_write())
                self.assertEqual(drv._write_q_bytes, 1)
                self.assertEqual(
                    [type(event) for event in capture.events],
                    [
                        IoPipelineFlowMessages.PauseOutput,
                        IoPipelineFlowMessages.ReadyForOutput,
                    ],
                )

                self.assertIsNone(drv.next(read=False))
                self.assertEqual(drv._write_q_bytes, 0)
                self.assertEqual(len(capture.events), 2)
                self.assertEqual(peer.recv(len(b'abcde')), b'abcde')
            finally:
                drv.close()

    def test_flush_output_completes_after_preceding_bytes_are_sent(self) -> None:
        sock, peer = socket.socketpair()
        with sock, peer:
            self.assertGreater(fill_socket_send_buffer(sock), 0)
            flush_output = IoPipelineFlowMessages.FlushOutput()
            completions = []
            flush_output.add_listener(lambda msg: completions.append(msg.is_succeeded()))
            drv = SyncSocketIoPipelineDriver(
                IoPipeline.Spec(
                    [WriteAndFlushIoPipelineHandler(b'abcde', flush_output)],
                    services=[StubIoPipelineFlowService(auto_read=False)],
                ),
                sock,
                SyncSocketIoPipelineDriver.Config(write_chunk_max=2),
            )
            try:
                self.assertIsNone(drv.next(read=False))
                drv.enqueue(_WRITE)
                self.assertIsNone(drv.next(read=False))

                self.assertEqual(drv._write_q_bytes, 5)
                self.assertIs(drv._write_q[-1], flush_output)
                self.assertFalse(flush_output.is_done())

                self.assertTrue(drain_socket(peer))
                for remaining in (3, 1, 0):
                    self.assertTrue(drv._try_write())
                    self.assertEqual(drv._write_q_bytes, remaining)
                    self.assertFalse(flush_output.is_done())

                self.assertTrue(drv._try_write())
                self.assertTrue(flush_output.is_succeeded())
                self.assertEqual(completions, [True])
                self.assertEqual(peer.recv(5), b'abcde')
            finally:
                drv.close()

    def test_read_false_queues_and_later_drains_saturated_write(self) -> None:
        sock, peer = socket.socketpair()
        with sock, peer:
            self.assertGreater(fill_socket_send_buffer(sock), 0)
            capture = CaptureOutputWritabilityIoPipelineHandler()
            drv = SyncSocketIoPipelineDriver(
                IoPipeline.Spec(
                    [
                        capture,
                        GracefulCloseIoPipelineHandler(),
                    ],
                    services=[StubIoPipelineFlowService(auto_read=False)],
                ),
                sock,
                SyncSocketIoPipelineDriver.Config(
                    write_chunk_max=2,
                    write_high_watermark=4,
                    write_low_watermark=2,
                ),
            )
            try:
                self.assertIsNone(drv.next(read=False))
                self.assertEqual(sock.gettimeout(), 0.)
                drv.enqueue(_CLOSE)

                start = time.monotonic()
                self.assertIsNone(drv.next(read=False))
                self.assertLess(time.monotonic() - start, .5)
                self.assertIs(drv.state, IoPipelineDriverState.DRAINING)
                self.assertTrue(drv.is_running)
                self.assertEqual(drv._write_q_bytes, len(b'payload'))
                self.assertEqual(
                    [type(event) for event in capture.events],
                    [IoPipelineFlowMessages.PauseOutput],
                )

                self.assertTrue(drain_socket(peer))
                self.assertIsNone(drv.next(read=False))

                self.assertIs(drv.state, IoPipelineDriverState.CLOSED)
                self.assertFalse(drv.is_running)
                self.assertFalse(drv.pipeline.is_ready)
                self.assertIsNone(sock.gettimeout())
                self.assertEqual(peer.recv(len(b'payload')), b'payload')
                self.assertEqual(
                    [type(event) for event in capture.events],
                    [IoPipelineFlowMessages.PauseOutput],
                )
            finally:
                drv.close()

    def test_final_input_does_not_close_output(self) -> None:
        sock, peer = socket.socketpair()
        with sock, peer:
            capture = CaptureFinalInputIoPipelineHandler()
            drv = SyncSocketIoPipelineDriver(IoPipeline.Spec([capture]), sock)
            try:
                peer.shutdown(socket.SHUT_WR)

                self.assertIsNone(drv.next(raise_on_stall=False))

                self.assertTrue(capture.saw_final_input)
                self.assertIs(drv.state, IoPipelineDriverState.RUNNING)
                self.assertTrue(drv.pipeline.is_ready)
                self.assertFalse(drv.pipeline.saw_final_output)
            finally:
                drv.close()

    def test_write_failure_is_reported(self) -> None:
        error = BrokenPipeError('broken')
        drv = SyncSocketIoPipelineDriver(
            IoPipeline.Spec(
                [GracefulCloseIoPipelineHandler()],
                services=[StubIoPipelineFlowService(auto_read=False)],
            ),
            FailingSendSocket(error),
        )
        try:
            self.assertIsNone(drv.next(read=False))
            drv.enqueue(_CLOSE)

            with self.assertRaises(BrokenPipeError) as raised:
                drv.next(read=False)

            self.assertIs(raised.exception, error)
            self.assertIs(drv.state, IoPipelineDriverState.FAILED)
            self.assertFalse(drv.pipeline.is_ready)
        finally:
            drv.close()

        self.assertIs(drv.state, IoPipelineDriverState.FAILED)
