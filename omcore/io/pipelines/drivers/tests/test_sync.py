# ruff: noqa: SLF001
# @om-lite
import socket
import typing as ta
import unittest

from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineHandlerRef
from ...core import IoPipelineMessages
from ...flow.stub import StubIoPipelineFlowService
from ...sched.types import IoPipelineScheduling
from ..sync import SyncSocketIoPipelineDriver


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
        ctx.feed_in(msg)


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
                self.assertEqual(sock.gettimeout(), 10.)
            finally:
                drv.close()

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
    def test_final_output_drains_preceding_bytes(self) -> None:
        sock, peer = socket.socketpair()
        with sock, peer:
            drv = SyncSocketIoPipelineDriver(
                IoPipeline.Spec(
                    [GracefulCloseIoPipelineHandler()],
                    services=[StubIoPipelineFlowService(auto_read=False)],
                ),
                sock,
            )
            try:
                self.assertIsNone(drv.next(read=False))
                drv.enqueue(_CLOSE)

                self.assertIsNone(drv.next(read=False))

                self.assertEqual(peer.recv(7), b'payload')
                self.assertFalse(drv.pipeline.is_ready)
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
                self.assertTrue(drv.pipeline.is_ready)
                self.assertFalse(drv.pipeline.saw_final_output)
            finally:
                drv.close()
