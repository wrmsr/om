# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
import dataclasses as dc
import typing as ta
import unittest

from ...core import IoPipelineMessages
from ...errors import AbortedIoPipelineError
from ...errors import SawShutdownOutputIoPipelineError
from ...flow.types import IoPipelineFlowMessages
from ...yielding import CountingIoPipelineYieldPolicy
from ..children import MultiplexChildConfig
from ..credit import HalfWindowMultiplexCreditReplenishPolicy  # noqa
from ..credit import StreamMultiplexCreditStrategy
from ..handlers import MultiplexConfig
from ..schedulers import RoundRobinMultiplexOutputScheduler
from ..types import ConnectionClosedMultiplexError
from ..types import ControlOutputLimitMultiplexError
from ..types import InputLimitMultiplexError
from .apps import AppFactory
from .apps import Emit
from .apps import StreamApp
from .apps import payload
from .loopback import LAccept
from .loopback import LBatch
from .loopback import LData
from .loopback import LEnd
from .loopback import LFinish
from .loopback import LGoodbye
from .loopback import LGrant
from .loopback import LMsg
from .loopback import LoopbackAdapter
from .loopback import LoopbackHarness
from .loopback import LOpen
from .loopback import data_of
from .loopback import of_type


##


@dc.dataclass(frozen=True)
class _Ext:
    """A flow-controlled typed message, like SSH extended data."""

    data: bytes


def _keep_open(**kwargs: ta.Any) -> StreamApp:
    return StreamApp(close_on_final_input=False, **kwargs)


def _outcome(msg: ta.Any) -> ta.List[ta.Optional[BaseException]]:
    out: ta.List[ta.Optional[BaseException]] = []
    msg.add_listener(lambda m: out.append(m.get_exception() if m.is_failed() else None))
    return out


class TestChildFences(unittest.TestCase):
    def test_flush_completes_after_preceding_output_is_emitted_and_a_parent_flush_completes(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k', credit=0))
            flush = IoPipelineFlowMessages.FlushOutput()
            outcome = _outcome(flush)
            h.feed_stream('k', Emit(b'payload', flush))

            # Blocked by credit: nothing emitted, the flush pending.
            self.assertEqual(data_of(h.frames, 'k'), b'')
            self.assertEqual(outcome, [])

            # Emitted, but the parent flush after it has not crossed the parent's transport yet.
            h.hold_drain = True
            h.feed(LGrant('k', 100))
            self.assertEqual(data_of(h.frames, 'k'), b'payload')
            self.assertEqual(outcome, [])
            parent_flushes = [m for m in h.recorder.out if isinstance(m, IoPipelineFlowMessages.FlushOutput)]
            self.assertEqual(len(parent_flushes), 1)

            h.hold_drain = False
            h.step()
            self.assertEqual(outcome, [None])
        finally:
            h.close()

    def test_flush_fails_if_the_connection_dies_first(self) -> None:
        for how in ('destroy', 'emitted-then-destroy', 'remove'):
            with self.subTest(how=how):
                h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
                try:
                    h.feed(LOpen('k', credit=0 if how != 'emitted-then-destroy' else 100))
                    flush = IoPipelineFlowMessages.FlushOutput()
                    outcome = _outcome(flush)
                    h.hold_drain = True
                    h.feed_stream('k', Emit(b'payload', flush))
                    self.assertEqual(outcome, [])

                    if how == 'remove':
                        with h.pipeline.enter():
                            h.pipeline.remove(h.pipeline.handlers()[-1])
                    else:
                        h.pipeline.destroy()

                    self.assertEqual(len(outcome), 1)
                    self.assertIsInstance(outcome[0], AbortedIoPipelineError)
                finally:
                    h.close()

    def test_final_output_drains_under_credit_then_completes_and_finishes(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()), adapter=LoopbackAdapter(on_finish='wait'))
        try:
            h.feed(LOpen('k', credit=4))
            app = h.app('k')
            h.feed_stream('k', Emit(b'payload!', IoPipelineMessages.FinalOutput))
            stream = h.mux.streams['k']

            # Draining: the final output waits behind data waiting for credit.
            self.assertEqual(data_of(h.frames, 'k'), b'payl')
            self.assertFalse(app.final_output.is_done())
            self.assertFalse(stream.local_finished)
            self.assertEqual(of_type(h.frames, LFinish), [])

            h.hold_drain = True
            h.feed(LGrant('k', 4))
            self.assertEqual(data_of(h.frames, 'k'), b'payload!')
            self.assertEqual(of_type(h.frames, LFinish), [LFinish('k', False)])
            self.assertTrue(stream.local_finished)
            self.assertFalse(app.final_output.is_done())

            h.hold_drain = False
            h.step()
            self.assertTrue(app.final_output.is_succeeded())
            self.assertFalse(h.mux.child_pipeline('k').is_ready)  # type: ignore[union-attr]
        finally:
            h.close()

    def test_shutdown_output_then_continued_input_in_both_directions(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k'))
            app = h.app('k')
            shutdown_out = _outcome(app.shutdown_output)

            # Both ends half-close at once, then data keeps flowing the other way on each side.
            h.feed_stream('k', Emit(b'request', IoPipelineMessages.ShutdownOutput))
            h.feed(LData('k', b'response'), LEnd('k'))

            frames = h.frames
            ends = [i for i, f in enumerate(frames) if isinstance(f, LEnd)]
            datas = [i for i, f in enumerate(frames) if isinstance(f, LData)]
            self.assertEqual(len(ends), 1)
            self.assertLess(max(datas), ends[0])
            self.assertEqual(shutdown_out, [None])
            self.assertEqual(bytes(app.received), b'response')
            self.assertTrue(app.saw_final_input)
            self.assertTrue(h.mux.streams['k'].local_ended)
            self.assertTrue(h.mux.streams['k'].remote_ended)

            # Ordinary output after the shutdown is rejected inside the child only.
            h.feed_stream('k', Emit(b'too late'))
            self.assertEqual(len(app.errors), 1)
            self.assertIsInstance(app.errors[0], SawShutdownOutputIoPipelineError)
            self.assertEqual(data_of(h.frames, 'k'), b'request')
            self.assertIn('k', h.mux.streams)
        finally:
            h.close()


class TestInputFlow(unittest.TestCase):
    def test_child_input_mode_is_independent_of_the_parent(self) -> None:
        for parent_auto in (True, False):
            for child_auto in (True, False):
                with self.subTest(parent_auto=parent_auto, child_auto=child_auto):
                    h = LoopbackHarness(
                        AppFactory(lambda o: _keep_open(manual_read=not child_auto), auto_read=child_auto),
                        parent_auto_read=parent_auto,
                    )
                    try:
                        h.feed(LOpen('k'))
                        app = h.app('k')
                        for i in range(5):
                            h.feed(LData('k', b'%d' % i))
                        h.feed(LEnd('k'))

                        self.assertEqual(bytes(app.received), b'01234')
                        self.assertTrue(app.saw_final_input)
                        if not child_auto:
                            self.assertGreaterEqual(app.reads_requested, 5)
                        self.assertGreaterEqual(app.flush_inputs, 5)
                    finally:
                        h.close()

    def test_manual_child_receives_nothing_without_tokens(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open(), auto_read=False))
        try:
            h.feed(LOpen('k'))
            app = h.app('k')
            h.feed(LData('k', b'abc'), LData('k', b'def'), LMsg('k', 'm'), LEnd('k'))
            self.assertEqual(bytes(app.received), b'')
            self.assertEqual(h.mux.streams['k'].in_cost, 6)

            # One token: one batch, everything queued, then FlushInput - and the end with it.
            h.feed_stream('k', Emit(IoPipelineFlowMessages.ReadyForInput()))
            self.assertEqual(bytes(app.received), b'abcdef')
            self.assertEqual(app.messages, ['m'])
            self.assertEqual(app.flush_inputs, 1)
            self.assertTrue(app.saw_final_input)
        finally:
            h.close()

    def test_receive_credit_replenished_at_half_window_by_consumption(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open(), auto_read=False),
            adapter=LoopbackAdapter(recv_window=100),
        )
        try:
            h.feed(LOpen('k'))
            h.feed(LData('k', b'x' * 60))
            self.assertEqual(of_type(h.frames, LGrant), [])  # received, not consumed

            h.feed_stream('k', Emit(IoPipelineFlowMessages.ReadyForInput()))
            self.assertEqual(of_type(h.frames, LGrant), [LGrant('k', 60)])

            h.feed(LData('k', b'y' * 40))
            h.feed_stream('k', Emit(IoPipelineFlowMessages.ReadyForInput()))
            self.assertEqual(of_type(h.frames, LGrant), [LGrant('k', 60)])  # 40 < half of the window
            h.feed(LData('k', b'z' * 10))
            h.feed_stream('k', Emit(IoPipelineFlowMessages.ReadyForInput()))
            self.assertEqual(of_type(h.frames, LGrant), [LGrant('k', 60), LGrant('k', 50)])
        finally:
            h.close()

    def test_uncontrolled_input_count_limit(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open(), auto_read=False),
            config=MultiplexConfig(max_stream_input_messages=3),
        )
        try:
            h.feed(LOpen('k'))
            h.feed(LMsg('k', 1), LMsg('k', 2), LMsg('k', 3))
            self.assertEqual(h.mux.stats.queued_input['k'], (0, 3))
            h.feed(LMsg('k', 4))
            (bye,) = of_type(h.frames, LGoodbye)
            self.assertIsInstance(bye.exc, InputLimitMultiplexError)
        finally:
            h.close()


class TestOutputFlow(unittest.TestCase):
    def test_child_writability_follows_its_queued_output_with_hysteresis(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            config=MultiplexConfig(child=MultiplexChildConfig(write_high_watermark=10, write_low_watermark=4)),
        )
        try:
            h.feed(LOpen('k', credit=0))
            app = h.app('k')
            h.feed_stream('k', Emit(b'x' * 8))
            self.assertEqual(app.writability, [])
            h.feed_stream('k', Emit(b'x' * 8))
            self.assertEqual(app.writability, [IoPipelineFlowMessages.PauseOutput])
            h.feed_stream('k', Emit(b'x' * 8))
            self.assertEqual(app.writability, [IoPipelineFlowMessages.PauseOutput])

            h.feed(LGrant('k', 16))  # 8 left queued: above the low watermark
            self.assertEqual(app.writability, [IoPipelineFlowMessages.PauseOutput])
            h.feed(LGrant('k', 4))  # 4 left
            self.assertEqual(
                app.writability,
                [IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput],
            )
            h.feed(LGrant('k', 100))
            self.assertEqual(len(app.writability), 2)
        finally:
            h.close()

    def test_control_output_flows_while_data_is_blocked_by_credit_and_parent_writability(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            adapter=LoopbackAdapter(recv_window=10),
        )
        try:
            h.feed(LOpen('a', credit=0))
            h.feed_stream('a', Emit(b'blocked by credit'))
            h.enqueue(IoPipelineFlowMessages.PauseOutput())

            before = len(h.frames)
            h.feed(LData('a', b'x' * 10), LOpen('b'))
            new = h.frames[before:]
            # Credit grants and acceptances go out while paused; stream data does not.
            self.assertEqual(set(new), {LGrant('a', 10), LAccept('b')})
            self.assertEqual(data_of(h.frames, 'a'), b'')

            h.feed(LGrant('a', 100))
            self.assertEqual(data_of(h.frames, 'a'), b'')
            h.enqueue(IoPipelineFlowMessages.ReadyForOutput())
            self.assertEqual(data_of(h.frames, 'a'), b'blocked by credit')
        finally:
            h.close()

    def test_paused_backlog_resumes_fairly(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            adapter=LoopbackAdapter(max_unit=10),
            scheduler=RoundRobinMultiplexOutputScheduler(quantum=20),
        )
        try:
            h.feed(*[LOpen(k) for k in 'abc'])
            h.enqueue(IoPipelineFlowMessages.PauseOutput())
            for k in 'abc':
                h.feed_stream(k, Emit(k.encode() * 100))
            self.assertEqual(of_type(h.frames, LData), [])

            h.enqueue(IoPipelineFlowMessages.ReadyForOutput())
            order = [f.key for f in of_type(h.frames, LData)]
            self.assertEqual(len(order), 30)
            for k in 'abc':
                self.assertEqual(data_of(h.frames, k), k.encode() * 100)
            # Round robin with a 20 byte quantum: two 10 byte units per turn, in rotation.
            self.assertEqual(order[:12], list('aabbccaabbcc'))
        finally:
            h.close()

    def test_control_output_while_paused_is_bounded(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            config=MultiplexConfig(max_control_during_pause=5),
        )
        try:
            h.enqueue(IoPipelineFlowMessages.PauseOutput())
            h.feed(*[LOpen(i) for i in range(10)])
            (bye,) = of_type(h.frames, LGoodbye)
            self.assertIsInstance(bye.exc, ControlOutputLimitMultiplexError)
            for i in range(6):
                app = h.mux.child_pipeline(i)
                self.assertTrue(app is None or not app.is_ready)
        finally:
            h.close()

    def test_turn_output_is_bounded_and_continues_through_defer(self) -> None:
        budget = 64 * 1024
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            adapter=LoopbackAdapter(max_unit=16 * 1024),
            config=MultiplexConfig(turn_output_budget=budget),
        )
        try:
            h.feed(LOpen('k'))
            big = payload('big', 1024 * 1024)
            h.feed_stream('k', Emit(big))

            self.assertTrue(data_of(h.frames, 'k') == big)
            # Between consecutive Defers, the parent never received more than the budget plus one unit.
            emitted = 0
            max_turn = 0
            defers = 0
            for m in h.recorder.out:
                if isinstance(m, IoPipelineMessages.Defer):
                    defers += 1
                    max_turn = max(max_turn, emitted)
                    emitted = 0
                elif isinstance(m, LData):
                    emitted += len(m.data)
            max_turn = max(max_turn, emitted)
            self.assertLessEqual(max_turn, budget + 16 * 1024)
            self.assertGreaterEqual(defers, (len(big) // (budget + 16 * 1024)) - 1)
        finally:
            h.close()

    def test_yield_policy_bounds_units_per_turn(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            adapter=LoopbackAdapter(max_unit=10),
            config=MultiplexConfig(yield_policy=CountingIoPipelineYieldPolicy(3)),
        )
        try:
            h.feed(LOpen('k'))
            h.feed_stream('k', Emit(b'x' * 100))
            self.assertEqual(data_of(h.frames, 'k'), b'x' * 100)
            run = 0
            for m in h.recorder.out:
                if isinstance(m, IoPipelineMessages.Defer):
                    run = 0
                elif isinstance(m, LData):
                    run += 1
                    self.assertLessEqual(run, 3)
        finally:
            h.close()

    def test_flow_controlled_typed_messages_split_by_credit(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            adapter=LoopbackAdapter(
                cost=lambda m: len(m.data) if isinstance(m, _Ext) else 0,
                split=lambda m, n: (_Ext(m.data[:n]), _Ext(m.data[n:])),
                max_unit=8,
            ),
            credit=StreamMultiplexCreditStrategy(),
        )
        try:
            h.feed(LOpen('k', credit=5))
            h.feed_stream('k', Emit('uncontrolled', _Ext(b'ABCDEFGHIJKLMNOPQRST'), 'after'))
            msgs = [f.msg for f in of_type(h.frames, LMsg)]
            # The first part fits the 5 credits; the rest waits, and the message after it keeps its place.
            self.assertEqual(msgs, ['uncontrolled', _Ext(b'ABCDE')])
            h.feed(LGrant('k', 100))
            msgs = [f.msg for f in of_type(h.frames, LMsg)]
            self.assertEqual(msgs, ['uncontrolled', _Ext(b'ABCDE'), _Ext(b'FGHIJKLM'), _Ext(b'NOPQRST'), 'after'])
            self.assertEqual(h.mux.credit.totals('k').send_consumed, 20)
        finally:
            h.close()


class TestConnectionInputEnd(unittest.TestCase):
    def test_parent_eof_truncates_unended_streams_and_lets_ended_ones_finish(self) -> None:
        factory = AppFactory(lambda o: _keep_open())
        h = LoopbackHarness(factory, adapter=LoopbackAdapter(on_finish='close'))
        try:
            h.feed(LOpen('ended'), LOpen('open'))
            opening = h.open(__import__('omcore.io.pipelines.multiplex.tests.apps', fromlist=['x']).app_spec(_keep_open()))  # noqa
            h.feed(LEnd('ended'))
            ended_app, open_app = factory.apps['ended'], factory.apps['open']

            h.eof()

            self.assertEqual(len(open_app.errors), 1)
            self.assertIsInstance(open_app.errors[0], AbortedIoPipelineError)
            self.assertIn('open', str(open_app.errors[0]))
            self.assertIsInstance(opening.exc, ConnectionClosedMultiplexError)

            # The ended stream may still send; the connection finishes once it is done.
            self.assertEqual(ended_app.errors, [])
            self.assertFalse(h.pipeline.saw_final_output)
            h.feed_stream('ended', Emit(b'last words', IoPipelineMessages.FinalOutput))
            self.assertEqual(data_of(h.frames, 'ended'), b'last words')
            self.assertTrue(ended_app.final_output.is_succeeded())
            self.assertTrue(h.pipeline.saw_final_output)
            self.assertEqual(h.adapter.input_ended, 1)
        finally:
            h.close()


class TestEmissionProgress(unittest.TestCase):
    def test_unsplittable_typed_message_waits_for_enough_credit(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            adapter=LoopbackAdapter(cost=lambda m: len(m.data) if isinstance(m, _Ext) else 0, max_unit=100),
        )
        try:
            h.feed(LOpen('k', credit=5))
            h.feed_stream('k', Emit(_Ext(b'0123456789'), 'after'))
            self.assertEqual(of_type(h.frames, LMsg), [])
            h.feed(LGrant('k', 4))
            self.assertEqual(of_type(h.frames, LMsg), [])
            h.feed(LGrant('k', 1))
            self.assertEqual([f.msg for f in of_type(h.frames, LMsg)], [_Ext(b'0123456789'), 'after'])
        finally:
            h.close()

    def test_zero_maximum_unit_does_not_spin(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()), adapter=LoopbackAdapter(max_unit=0))
        try:
            h.feed(LOpen('k'))
            h.feed_stream('k', Emit(b'stuck'))
            self.assertEqual(data_of(h.frames, 'k'), b'')
            self.assertFalse(h.mux._scheduler.is_ready('k'))
        finally:
            h.close()

    def test_failure_during_emission_still_finishes_the_connection(self) -> None:
        # Without a parent flow service there is no trailing FlushInput to start another turn by accident: the turn
        # which fails while emitting must itself finish the connection.
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            config=MultiplexConfig(max_control_during_pause=2),
            parent_flow=False,
        )
        try:
            h.enqueue(IoPipelineFlowMessages.PauseOutput())
            h.feed(LOpen(0), LOpen(1))
            self.assertEqual(of_type(h.frames, LGoodbye), [])
            h.feed(LOpen(2))
            self.assertEqual(len(of_type(h.frames, LGoodbye)), 1)
            self.assertEqual(len(h.mux.streams), 0)
            self.assertTrue(h.pipeline.saw_final_output)
        finally:
            h.close()


class TestInputBatching(unittest.TestCase):
    def test_input_without_flush_input_still_reaches_children(self) -> None:
        # Frames injected at the parent's boundary come with no FlushInput; they must not wait for one.
        for parent_flow in (True, False):
            with self.subTest(parent_flow=parent_flow):
                h = LoopbackHarness(AppFactory(lambda o: _keep_open()), parent_flow=parent_flow)
                try:
                    h.enqueue(LOpen('k'))
                    app = h.app('k')
                    h.enqueue(LData('k', b'one'), LData('k', b'two'))
                    self.assertEqual(bytes(app.received), b'onetwo')
                finally:
                    h.close()

    def test_frames_of_one_read_batch_coalesce(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k'))
            app = h.app('k')
            before = app.flush_inputs
            h.feed(LBatch([LData('k', b'a'), LData('k', b'b'), LData('k', b'c')]))
            self.assertEqual(bytes(app.received), b'abc')
            self.assertEqual(app.flush_inputs - before, 1)
        finally:
            h.close()
