# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
import unittest

from ...core import IoPipelineHandler
from ...core import IoPipelineMessages
from ...flow.types import IoPipelineFlowMessages
from ..handlers import MultiplexConfig
from ..types import MultiplexMessages
from .apps import AppFactory
from .apps import Emit
from .apps import StreamApp
from .apps import app_spec
from .loopback import LBatch
from .loopback import LClose
from .loopback import LConfirm
from .loopback import LData
from .loopback import LGoodbye
from .loopback import LoopbackAdapter
from .loopback import LoopbackHarness
from .loopback import LOpen
from .loopback import LReset
from .loopback import data_of
from .loopback import of_type


def _keep_open(**kwargs):
    return StreamApp(close_on_final_input=False, **kwargs)


class TestChildWritabilityWakeup(unittest.TestCase):
    def test_child_resumed_when_parent_writability_returns_and_queue_drains(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k'))
            app = h.app('k')

            h.enqueue(IoPipelineFlowMessages.PauseOutput())
            h.feed_stream('k', Emit(b'x' * (100 * 1024)))
            self.assertEqual(app.writability, [IoPipelineFlowMessages.PauseOutput])

            # The parent becomes writable again: the stream's whole queue is emitted ...
            h.enqueue(IoPipelineFlowMessages.ReadyForOutput())
            self.assertEqual(len(data_of(h.frames, 'k')), 100 * 1024)
            self.assertEqual(h.mux.streams['k'].out_bytes, 0)

            # ... so the child must be told it may write again.
            self.assertEqual(
                app.writability,
                [IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput],
            )
        finally:
            h.close()

    def test_child_resumed_when_turn_budget_continuation_drains_queue(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            adapter=LoopbackAdapter(max_unit=16 * 1024),
            config=MultiplexConfig(turn_output_budget=256 * 1024),
        )
        try:
            h.feed(LOpen('k'))
            app = h.app('k')

            # 300K in one go: more than one turn's budget, so emission continues through a parent Defer.
            h.feed_stream('k', Emit(b'x' * (300 * 1024)))
            self.assertEqual(len(data_of(h.frames, 'k')), 300 * 1024)
            self.assertEqual(h.mux.streams['k'].out_bytes, 0)

            self.assertEqual(
                app.writability,
                [IoPipelineFlowMessages.PauseOutput, IoPipelineFlowMessages.ReadyForOutput],
            )
        finally:
            h.close()


class _RemoveMuxOnFrame(IoPipelineHandler):
    """Outside the multiplexer: removes it from the pipeline as soon as a matching frame passes outward."""

    def __init__(self, match):
        super().__init__()

        self._match = match
        self.removed = False
        self.errors = []

    def inbound(self, ctx, msg):
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg.exc)
            return
        ctx.feed_in(msg)

    def outbound(self, ctx, msg):
        ctx.feed_out(msg)
        if not self.removed and self._match(msg):
            self.removed = True
            ctx.pipeline.remove(ctx.pipeline.handlers()[-1])  # the multiplexer, innermost


class _FailOnFrame(IoPipelineHandler):
    """Outside the multiplexer, like a frame encoder: raises on a matching outbound frame."""

    def __init__(self, match):
        super().__init__()

        self._match = match
        self.raised = 0

    def outbound(self, ctx, msg):
        if self._match(msg):
            self.raised += 1
            raise RuntimeError('cannot encode frame')
        ctx.feed_out(msg)


class TestStaleReadinessDuringEmission(unittest.TestCase):
    def _queue_on_two_streams_then_resume(self, h):
        h.feed(LOpen('a'), LOpen('b'))
        # Both streams queue output while the parent is paused, so both are ready together when it resumes.
        h.enqueue(IoPipelineFlowMessages.PauseOutput())
        h.feed_stream('a', Emit(b'aaaa'))
        h.feed_stream('b', Emit(b'bbbb'))
        h.enqueue(IoPipelineFlowMessages.ReadyForOutput())

    def test_removing_the_multiplexer_while_it_emits_stream_output(self) -> None:
        remover = _RemoveMuxOnFrame(lambda m: isinstance(m, LData) and m.key == 'a')
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()), extra_outer=[remover])
        try:
            self._queue_on_two_streams_then_resume(h)

            self.assertTrue(remover.removed)
            self.assertEqual(remover.errors, [])
            self.assertTrue(h.pipeline.is_ready)
            self.assertEqual(data_of(h.frames, 'b'), b'')
        finally:
            h.close()

    def test_removing_the_multiplexer_from_an_open_completion_listener(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            adapter=LoopbackAdapter(explicit_open=False, local_send_credit=1 << 20),
        )
        try:
            removed = []

            def on_open(m):
                # Application policy reacting to the open: tear the multiplexer down.
                with h.pipeline.enter():
                    h.pipeline.remove(h.pipeline.handlers()[-1])
                removed.append(m)

            msg = MultiplexMessages.OpenStream(app_spec(_keep_open(send=b'hello')))
            msg.add_listener(on_open)
            h.enqueue(msg)

            self.assertEqual(len(removed), 1)
            self.assertTrue(h.pipeline.is_ready)
        finally:
            h.close()

    def test_encoder_failure_on_one_stream_while_another_is_ready(self) -> None:
        enc = _FailOnFrame(lambda m: isinstance(m, LData) and m.key == 'a')
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()), extra_outer=[enc])
        try:
            # The encoder error is reported inbound to the multiplexer while it is emitting: the connection fails.
            self._queue_on_two_streams_then_resume(h)

            self.assertEqual(enc.raised, 1)
            self.assertIsInstance(h.mux._failed, RuntimeError)
            self.assertEqual(len(of_type(h.frames, LGoodbye)), 1)
            self.assertEqual(len(h.mux.streams), 0)
        finally:
            h.close()


class TestOpenCompletedWhenEndedBeforeEstablishment(unittest.TestCase):
    def _open(self, h):
        out = h.open(app_spec(_keep_open()))
        (opened,) = of_type(h.frames, LOpen)
        return out, opened.key

    def test_confirm_then_reset_in_one_read(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            out, key = self._open(h)
            h.feed(LBatch([LConfirm(key), LReset(key, 'gone')]))
            self.assertNotIn(key, h.mux.streams)
            self.assertTrue(out.done)  # the OpenStream must complete, one way or the other
        finally:
            h.close()

    def test_confirm_then_close_in_one_read(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            out, key = self._open(h)
            h.feed(LBatch([LConfirm(key), LClose(key)]))
            self.assertNotIn(key, h.mux.streams)
            self.assertTrue(out.done)
        finally:
            h.close()

    def test_confirm_then_connection_failure_in_one_read(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            out, key = self._open(h)
            # A frame for an unknown stream fails the connection.
            h.feed(LBatch([LConfirm(key), LData('nope', b'x')]))
            self.assertIsNotNone(h.mux._failed)
            self.assertNotIn(key, h.mux.streams)
            self.assertTrue(out.done)
        finally:
            h.close()


class TestDestroyedChild(unittest.TestCase):
    def test_opener_destroying_its_stream_pipeline(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: _keep_open()),
            adapter=LoopbackAdapter(explicit_open=False, local_send_credit=1 << 20),
        )
        try:
            out = h.open(app_spec(_keep_open()))
            key = out.result.key

            # The opener abandons the stream by destroying its pipeline, then asks for a graceful shutdown.
            out.result.pipeline.destroy()
            h.enqueue(MultiplexMessages.Shutdown())

            # The stream must not linger forever: it is reset towards the peer and released, and the connection
            # finishes.
            self.assertEqual(len(of_type(h.frames, LReset, key)), 1)
            self.assertNotIn(key, h.mux.streams)
            self.assertTrue(h.pipeline.saw_final_output)
        finally:
            h.close()
