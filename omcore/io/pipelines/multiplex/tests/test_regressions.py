# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
"""Regression tests for defects found reviewing the multiplexing work. See ../../FINDINGS.md."""
import unittest

from ...core import IoPipeline
from ...core import IoPipelineMessages
from ...flow.types import IoPipelineFlowMessages
from ..types import MultiplexStreamState
from .apps import AppFactory
from .apps import Emit
from .apps import StreamApp
from .loopback import LBatch
from .loopback import LClose
from .loopback import LEnd
from .loopback import LFinish
from .loopback import LoopbackAdapter
from .loopback import LoopbackHarness
from .loopback import LOpen
from .loopback import LReset
from .loopback import of_type


##


class TestChildDestroyedFromItsOwnCompletion(unittest.TestCase):
    # A stream's pipeline is destroyed by its driver once its FinalOutput completed. An application hook on that very
    # completion which destroys the pipeline itself - redundantly, but harmlessly for a top-level driver - is a
    # reaction to the finish, not an abandonment of the stream: the stream must still close normally, not be reset.

    def test_destroy_in_final_output_listener_after_adapter_close(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: StreamApp(close_on_final_input=False)))
        try:
            h.feed(LOpen('k'))
            app = h.app('k')
            pipeline = h.mux.child_pipeline('k')
            assert pipeline is not None
            app.final_output.add_listener(lambda m: pipeline.destroy())

            frames = h.feed_stream('k', Emit(IoPipelineMessages.FinalOutput))

            self.assertEqual(of_type(frames, LFinish), [LFinish('k', False)])
            self.assertEqual(of_type(frames, LReset), [])
            self.assertTrue(app.final_output.is_succeeded())
            self.assertIs(pipeline.state, IoPipeline.State.DESTROYED)
            self.assertNotIn('k', h.mux.streams)
            self.assertEqual(h.mux.streams.stats.closed, 1)
            self.assertEqual(h.mux.streams.stats.reset_local, 0)
        finally:
            h.close()

    def test_destroy_in_final_output_listener_while_awaiting_peer_close(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp(close_on_final_input=False)),
            adapter=LoopbackAdapter(on_finish='wait'),
        )
        try:
            h.feed(LOpen('k'))
            app = h.app('k')
            pipeline = h.mux.child_pipeline('k')
            assert pipeline is not None
            app.final_output.add_listener(lambda m: pipeline.destroy())

            frames = h.feed_stream('k', Emit(IoPipelineMessages.FinalOutput))

            self.assertEqual(of_type(frames, LReset), [])
            self.assertTrue(app.final_output.is_succeeded())
            self.assertIs(h.mux.streams['k'].state, MultiplexStreamState.HALF_CLOSED_LOCAL)

            h.feed(LClose('k'))
            self.assertNotIn('k', h.mux.streams)
            self.assertEqual(h.mux.streams.stats.closed, 1)
            self.assertEqual(h.mux.streams.stats.reset_local, 0)
        finally:
            h.close()


class TestRemoteCloseBehindPendingParentFlush(unittest.TestCase):
    # A child fence completes once a parent FlushOutput issued after its emission completes. If the peer closes the
    # stream before that parent flush has completed, and the child then finishes, its FinalOutput - discarded output
    # on a remote-closed stream, completed at once - must not complete ahead of the earlier fence (DESIGN 5), and
    # finishing the child must not fail that fence: it was emitted and will cross the transport with the flush.

    def _run(self, app, before_close):
        h = LoopbackHarness(AppFactory(lambda o: app))
        try:
            h.hold_drain = True  # The parent's output, and so its flushes, stay pending.
            h.feed(LOpen('k'))
            fence = before_close(h)
            self.assertFalse(fence.is_done())

            # End and close in one read, so the child sees FinalInput and closes while the stream is remote-closed.
            h.feed(LBatch([LEnd('k'), LClose('k')]))
            self.assertFalse(fence.is_done())
            self.assertFalse(app.final_output.is_done())

            h.hold_drain = False
            h.step()
            self.assertTrue(fence.is_succeeded())
            self.assertTrue(app.final_output.is_succeeded())
            self.assertNotIn('k', h.mux.streams)
            self.assertEqual(h.mux.streams.stats.closed, 1)
        finally:
            h.close()

    def test_shutdown_output_then_remote_close(self) -> None:
        app = StreamApp(send=b'data', shutdown_after_send=True, close_on_final_input=True)
        self._run(app, lambda h: app.shutdown_output)

    def test_flush_output_then_remote_close(self) -> None:
        app = StreamApp(send=b'data', close_on_final_input=True)

        def flush(h):
            fo = IoPipelineFlowMessages.FlushOutput()
            h.feed_stream('k', Emit(fo))
            return fo

        self._run(app, flush)
