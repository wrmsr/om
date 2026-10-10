# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
"""
Adversarial integration tests for the multiplexing handler, written during a hostile review of the multiplex +
half-close change. All use the loopback harness (real pipelines, real pure driver, plain frame objects) - no mocks.

Covered here (beyond the neighboring suites):
 - open/refuse/limit races and duplicate remote keys,
 - open completion exactly once across reset/confirm races,
 - half-close ordering under credit block and write-after-shutdown rejection,
 - reset dropping queued output and failing fences, reset completing a finished stream's pending final output,
 - truncated and unconfirmed streams on connection EOF, ended streams carrying on after EOF,
 - negative window adjustment, zero window, and per-frame overhead credit accounting,
 - parent pause holding stream output, control-output bounding during a prolonged pause,
 - child timer failure isolation and timer cancellation on reset,
 - graceful shutdown waiting for a lingering stream,
 - connection teardown with many streams resolving every open and fence and releasing every child pipeline.
"""
import gc
import typing as ta
import unittest
import weakref

from ...core import IoPipelineMessages
from ...errors import SawShutdownOutputIoPipelineError
from ...flow.types import IoPipelineFlowMessages
from ..credit import ImmediateMultiplexCreditReplenishPolicy
from ..credit import StreamMultiplexCreditStrategy
from ..handlers import MultiplexConfig
from ..schedulers import RoundRobinMultiplexOutputScheduler
from ..types import StreamLimitMultiplexError
from ..types import StreamResetMultiplexError
from ..types import StreamTruncatedMultiplexError
from .apps import AppFactory
from .apps import Emit
from .apps import StreamApp
from .apps import app_spec
from .loopback import LAccept
from .loopback import LBatch
from .loopback import LConfirm
from .loopback import LData
from .loopback import LEnd
from .loopback import LFinish
from .loopback import LGoodbye
from .loopback import LGrant
from .loopback import LoopbackAdapter
from .loopback import LoopbackHarness
from .loopback import LOpen
from .loopback import LRefuse
from .loopback import LReset
from .loopback import data_of
from .loopback import of_type


def _keep_open(**kwargs: ta.Any) -> StreamApp:
    return StreamApp(close_on_final_input=False, **kwargs)


class TestOpenRaces(unittest.TestCase):
    def test_open_completed_exactly_once_on_reset_then_late_confirm(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            out = h.open(app_spec(_keep_open()))
            (opened,) = of_type(h.frames, LOpen)
            key = opened.key
            self.assertFalse(out.done)

            h.feed(LReset(key, 'nope'))
            self.assertTrue(out.done)
            self.assertIsInstance(out.exc, StreamResetMultiplexError)

            # A late confirm for the dead key is a protocol error and fails the connection - the completed open must
            # not be completed a second time.
            h.feed(LConfirm(key))
            self.assertTrue(of_type(h.frames, LGoodbye))
            self.assertTrue(out.done)
            self.assertIsInstance(out.exc, StreamResetMultiplexError)
        finally:
            h.close()

    def test_open_refused_by_factory_only_for_matching_info(self) -> None:
        factory = AppFactory(lambda o: _keep_open(), refuse=lambda o: 'no' if o.info == 'bad' else None)
        h = LoopbackHarness(factory)
        try:
            h.feed(LOpen('good'))
            h.feed(LOpen('bad', info='bad'))
            self.assertTrue(of_type(h.frames, LAccept, 'good'))
            (ref,) = of_type(h.frames, LRefuse, 'bad')
            self.assertEqual(ref.reason, 'no')
            self.assertEqual(h.mux.streams.stats.refused_remote, 1)
        finally:
            h.close()

    def test_local_open_over_limit_fails_open_not_connection(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.mux.streams.set_limits(max_local=0)
            out = h.open(app_spec(_keep_open()))
            self.assertTrue(out.done)
            self.assertIsInstance(out.exc, StreamLimitMultiplexError)
            self.assertFalse(of_type(h.frames, LGoodbye))
            self.assertEqual(len(h.mux.streams), 0)
        finally:
            h.close()

    def test_duplicate_remote_key_fails_connection(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k'))
            h.feed(LOpen('k'))
            self.assertTrue(of_type(h.frames, LGoodbye))
        finally:
            h.close()


class TestHalfClose(unittest.TestCase):
    def test_end_precedes_finish_under_order(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k', credit=1 << 30))
            app = h.app('k')
            h.feed_stream('k', Emit(b'data', IoPipelineMessages.ShutdownOutput, IoPipelineMessages.FinalOutput))
            h.step()
            kinds = [
                type(f).__name__
                for f in h.frames
                if type(f).__name__ in ('LData', 'LEnd', 'LFinish') and getattr(f, 'key', None) == 'k'
            ]
            self.assertEqual(kinds, ['LData', 'LEnd', 'LFinish'])
            self.assertTrue(app.shutdown_output.is_succeeded())
            self.assertTrue(app.final_output.is_succeeded())
        finally:
            h.close()

    def test_shutdown_output_waits_behind_credit_blocked_data(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k', credit=3))
            app = h.app('k')
            h.feed_stream('k', Emit(b'abcdef', IoPipelineMessages.ShutdownOutput))
            self.assertEqual(data_of(h.frames, 'k'), b'abc')
            self.assertFalse(of_type(h.frames, LEnd, 'k'))
            self.assertFalse(app.shutdown_output.is_done())

            h.feed(LGrant('k', 3))
            self.assertEqual(data_of(h.frames, 'k'), b'abcdef')
            self.assertTrue(of_type(h.frames, LEnd, 'k'))
            self.assertTrue(app.shutdown_output.is_succeeded())
        finally:
            h.close()

    def test_write_after_shutdown_output_fails_in_child(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k', credit=1 << 30))
            app = h.app('k')
            h.feed_stream('k', Emit(IoPipelineMessages.ShutdownOutput, b'later'))
            h.step()
            self.assertTrue(any(isinstance(e, SawShutdownOutputIoPipelineError) for e in app.errors), app.errors)
            self.assertEqual(data_of(h.frames, 'k'), b'')
            self.assertTrue(of_type(h.frames, LEnd, 'k'))
        finally:
            h.close()

    def test_half_closed_stream_still_receives(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k', credit=1 << 30))
            app = h.app('k')
            h.feed_stream('k', Emit(IoPipelineMessages.ShutdownOutput))
            self.assertTrue(of_type(h.frames, LEnd, 'k'))
            h.feed(LData('k', b'still-coming'))
            h.step()
            self.assertEqual(bytes(app.received), b'still-coming')
        finally:
            h.close()


class TestResetAndEof(unittest.TestCase):
    def test_reset_drops_queued_output_and_fails_fences(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k', credit=0))  # no credit: output stays queued
            flush = IoPipelineFlowMessages.FlushOutput()
            outcomes: ta.List[ta.Optional[BaseException]] = []
            flush.add_listener(lambda m: outcomes.append(m.get_exception() if m.is_failed() else None))
            h.feed_stream('k', Emit(b'blocked', flush, IoPipelineMessages.ShutdownOutput))
            self.assertEqual(outcomes, [])

            h.feed(LReset('k', 'bye'))
            self.assertEqual(len(outcomes), 1)
            self.assertIsInstance(outcomes[0], StreamResetMultiplexError)
            self.assertEqual(len(h.mux.streams), 0)
            self.assertEqual(h.adapter.released, ['k'])
        finally:
            h.close()

    def test_reset_of_finished_stream_completes_pending_final_output_on_flush(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()), adapter=LoopbackAdapter(on_finish='wait'))
        try:
            h.feed(LOpen('k', credit=1 << 30))
            app = h.app('k')
            h.hold_drain = True  # the parent's transport does not accept the flush yet
            h.feed_stream('k', Emit(IoPipelineMessages.FinalOutput))
            self.assertTrue(of_type(h.frames, LFinish, 'k'))
            self.assertFalse(app.final_output.is_done())

            h.feed(LReset('k', 'after-finish'))
            self.assertFalse(app.final_output.is_done())  # still pending until the transport boundary

            h.hold_drain = False
            h.step()
            # The child had finished; its pending final output completes normally once flushed.
            self.assertTrue(app.final_output.is_succeeded())
        finally:
            h.close()

    def test_truncated_and_ended_streams_on_connection_eof(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('ended', credit=1 << 30), LData('ended', b'data'), LEnd('ended'))
            h.feed(LOpen('open', credit=1 << 30))
            app_ended = h.app('ended')
            app_open = h.app('open')
            self.assertTrue(app_ended.saw_final_input)

            h.eof()

            # The stream whose peer had ended carries on; the other is truncated.
            self.assertTrue(any(isinstance(e, StreamTruncatedMultiplexError) for e in app_open.errors), app_open.errors)
            self.assertEqual(app_ended.errors, [])

            # The ended stream's output still flows after the connection's input ended.
            h.feed_stream('ended', Emit(b'final-words', IoPipelineMessages.FinalOutput))
            h.step()
            self.assertEqual(data_of(h.frames, 'ended'), b'final-words')
        finally:
            h.close()

    def test_unconfirmed_open_fails_on_connection_eof(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            out = h.open(app_spec(_keep_open()))
            self.assertTrue(of_type(h.frames, LOpen))
            self.assertFalse(out.done)
            h.eof()
            self.assertTrue(out.done)
            self.assertIsNotNone(out.exc)
        finally:
            h.close()


class TestCredit(unittest.TestCase):
    def test_negative_adjust_blocks_then_recovers(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            from .loopback import LAdjust
            h.feed(LOpen('k', credit=10))
            h.feed_stream('k', Emit(b'0123456789'))
            self.assertEqual(data_of(h.frames, 'k'), b'0123456789')

            h.feed_stream('k', Emit(b'more'))
            self.assertEqual(data_of(h.frames, 'k'), b'0123456789')

            h.feed(LAdjust(-100))  # drive every stream negative
            h.feed(LGrant('k', 100))  # back to zero
            self.assertEqual(data_of(h.frames, 'k'), b'0123456789')

            h.feed(LGrant('k', 4))
            self.assertEqual(data_of(h.frames, 'k'), b'0123456789more')
        finally:
            h.close()

    def test_zero_window_then_open(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k', credit=0))
            h.feed_stream('k', Emit(b'x'))
            self.assertEqual(data_of(h.frames, 'k'), b'')
            h.feed(LGrant('k', 1))
            self.assertEqual(data_of(h.frames, 'k'), b'x')
        finally:
            h.close()

    def test_per_frame_overhead_charges_credit(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()), adapter=LoopbackAdapter(overhead=2))
        try:
            h.feed(LOpen('k', credit=5))  # enough for 3 data bytes + 2 overhead
            h.feed_stream('k', Emit(b'abcdefgh'))
            self.assertEqual(data_of(h.frames, 'k'), b'abc')
            h.feed(LGrant('k', 7))  # 5 bytes + 2 overhead
            self.assertEqual(data_of(h.frames, 'k'), b'abcdefgh')
        finally:
            h.close()

    def test_overhead_exceeding_credit_blocks_entirely(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()), adapter=LoopbackAdapter(overhead=5))
        try:
            h.feed(LOpen('k', credit=3))  # 3 - 5 < 0: nothing may be sent
            h.feed_stream('k', Emit(b'hello'))
            self.assertEqual(data_of(h.frames, 'k'), b'')
            h.feed(LGrant('k', 10))  # min(5 bytes, max_unit, 10-5=5) = 5 bytes, cost 10
            self.assertEqual(data_of(h.frames, 'k'), b'hello')
        finally:
            h.close()


class TestFlowAndScheduling(unittest.TestCase):
    def test_parent_pause_holds_stream_output(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k'))
            h.enqueue(IoPipelineFlowMessages.PauseOutput())
            h.feed_stream('k', Emit(b'held'))
            h.step()
            self.assertEqual(data_of(h.frames, 'k'), b'')

            h.enqueue(IoPipelineFlowMessages.ReadyForOutput())
            h.step()
            self.assertEqual(data_of(h.frames, 'k'), b'held')
        finally:
            h.close()

    def test_control_output_bounded_during_pause(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            config=MultiplexConfig(max_control_during_pause=20),
            credit=StreamMultiplexCreditStrategy(stream_replenish=ImmediateMultiplexCreditReplenishPolicy()),
            adapter=LoopbackAdapter(recv_window=100),
        )
        try:
            h.feed(LOpen('k', credit=1 << 30))
            h.enqueue(IoPipelineFlowMessages.PauseOutput())
            for _ in range(50):
                h.feed(LData('k', b'x' * 10))  # each consumption immediately re-advertises (control output)
            h.step()
            gb = of_type(h.frames, LGoodbye)
            self.assertTrue(gb)
            self.assertIn('Control', type(gb[0].exc).__name__)
        finally:
            h.close()

    def test_no_starvation_under_small_quantum(self) -> None:
        n = 8
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            scheduler=RoundRobinMultiplexOutputScheduler(quantum=100),
        )
        try:
            for i in range(n):
                h.feed(LOpen(f's{i}', credit=1 << 30))
            for i in range(n):
                h.feed_stream(f's{i}', Emit(b'x' * 1000))
            h.step()
            for i in range(n):
                self.assertEqual(len(data_of(h.frames, f's{i}')), 1000, f's{i} starved')
        finally:
            h.close()

    def test_grants_suppressed_for_stream_ended_in_same_batch(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp()),
            adapter=LoopbackAdapter(recv_window=100),
            credit=StreamMultiplexCreditStrategy(stream_replenish=ImmediateMultiplexCreditReplenishPolicy()),
        )
        try:
            h.feed(LBatch([LOpen('k', credit=1 << 30), LData('k', b'x' * 50), LEnd('k')]))
            h.step()
            self.assertEqual(of_type(h.frames, LGrant, 'k'), [])
        finally:
            h.close()


class _TimerStreamApp(StreamApp):
    def __init__(self, delay_s: float, *, boom: bool = False) -> None:
        super().__init__(close_on_final_input=False)

        self._delay_s = delay_s
        self._boom = boom
        self.fired = 0

    def _on_timer(self) -> None:
        if self._boom:
            raise RuntimeError('timer boom')
        self.fired += 1

    def inbound(self, ctx, msg):
        if isinstance(msg, IoPipelineMessages.InitialInput) and not self.saw_initial_input:
            from ...sched.types import IoPipelineScheduling
            ctx.services[IoPipelineScheduling].schedule(ctx.ref, self._delay_s, self._on_timer)
        super().inbound(ctx, msg)


class TestChildIsolation(unittest.TestCase):
    def test_child_timer_failure_resets_only_its_stream(self) -> None:
        h = LoopbackHarness(AppFactory(
            lambda o: _TimerStreamApp(5.0, boom=True) if o.key == 'k' else _TimerStreamApp(1000.0),
        ))
        try:
            h.feed(LOpen('k'))
            h.feed(LOpen('j'))
            h.driver.advance_time(10.0)
            for _ in range(4):
                h.step()

            self.assertFalse(of_type(h.frames, LGoodbye))  # connection survives
            self.assertTrue(of_type(h.frames, LReset, 'k'))
            self.assertFalse(of_type(h.frames, LReset, 'j'))
            keys = [s.key for s in h.mux.streams]
            self.assertNotIn('k', keys)
            self.assertIn('j', keys)
        finally:
            h.close()

    def test_child_timer_cancelled_on_reset(self) -> None:
        apps: ta.Dict[ta.Any, _TimerStreamApp] = {}
        h = LoopbackHarness(AppFactory(lambda o: apps.setdefault(o.key, _TimerStreamApp(10.0))))
        try:
            h.feed(LOpen('k'))
            app = apps['k']
            self.assertIsNotNone(h.driver.next_deadline())
            h.feed(LReset('k'))
            self.assertIsNone(h.driver.next_deadline())  # the child's timer was cancelled
            h.driver.advance_time(20.0)
            for _ in range(4):
                h.step()
            self.assertEqual(app.fired, 0)
        finally:
            h.close()


class TestTeardown(unittest.TestCase):
    def test_graceful_shutdown_waits_for_lingering_stream(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k', credit=1 << 30), LData('k', b'x'), LEnd('k'))
            app = h.app('k')
            h.eof()
            for _ in range(4):
                h.step()
            self.assertTrue(h.mux._shutting_down)
            self.assertFalse(h.mux._final_output_sent)

            h.feed_stream('k', Emit(IoPipelineMessages.FinalOutput))
            for _ in range(6):
                h.step()
            self.assertTrue(h.mux._final_output_sent)
            self.assertTrue(app.final_output.is_succeeded())
        finally:
            h.close()

    def test_mass_teardown_resolves_everything_and_releases_children(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            pending = [h.open(app_spec(_keep_open())) for _ in range(5)]
            for opened in of_type(h.frames, LOpen)[:3]:
                h.feed(LConfirm(opened.key))
            h.feed(LOpen('r0'), LOpen('r1'))

            fences = []
            for s in list(h.mux.streams):
                if h.mux.child_pipeline(s.key) is not None:
                    fl = IoPipelineFlowMessages.FlushOutput()
                    fences.append(fl)
                    h.feed_stream(s.key, Emit(b'x' * 100, fl))
            h.hold_drain = True
            h.step()

            child_refs = [
                weakref.ref(h.mux.child_pipeline(s.key))
                for s in h.mux.streams
                if h.mux.child_pipeline(s.key) is not None
            ]
            self.assertTrue(child_refs)

            # MultiplexOpenedStream.pipeline holds the child strongly, by design; drop the results.
            for o in pending:
                o.result = None

            h.pipeline.destroy()
            gc.collect()

            self.assertTrue(all(o.done for o in pending))
            self.assertTrue(all(f.is_done() for f in fences))
            self.assertTrue(all(r() is None for r in child_refs))
        finally:
            h.close()


if __name__ == '__main__':
    unittest.main()
