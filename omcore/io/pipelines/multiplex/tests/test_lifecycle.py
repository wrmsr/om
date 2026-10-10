# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
import typing as ta
import unittest

from ...core import IoPipelineMessages
from ..types import ConnectionClosedMultiplexIoPipelineError
from ..types import IoPipelineMultiplexOpenedStream
from ..types import IoPipelineMultiplexStreamState
from ..types import StreamRefusedMultiplexIoPipelineError
from ..types import StreamResetMultiplexIoPipelineError
from .apps import AppFactory
from .apps import Emit
from .apps import StreamApp
from .apps import app_spec
from .loopback import LAccept
from .loopback import LClose
from .loopback import LConfirm
from .loopback import LData
from .loopback import LEnd
from .loopback import LFinish
from .loopback import LGoodbye
from .loopback import LoopbackAdapter
from .loopback import LoopbackHarness
from .loopback import LOpen
from .loopback import LRefuse
from .loopback import LReset
from .loopback import data_of
from .loopback import of_type


##


def _keep_open() -> StreamApp:
    return StreamApp(close_on_final_input=False)


class TestLocalOpens(unittest.TestCase):
    def test_confirmed_open_establishes_the_child_on_confirmation(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            app = _keep_open()
            out = h.open(app_spec(app), info='hello')
            (opened,) = of_type(h.frames, LOpen)
            key = opened.key
            self.assertEqual(opened.info, 'hello')

            stream = h.mux.streams[key]
            self.assertIs(stream.state, IoPipelineMultiplexStreamState.OPENING)
            self.assertFalse(app.saw_initial_input)
            self.assertFalse(out.done)

            h.feed(LConfirm(key, credit=10))
            self.assertIs(stream.state, IoPipelineMultiplexStreamState.OPEN)
            self.assertTrue(app.saw_initial_input)
            self.assertIsInstance(out.result, IoPipelineMultiplexOpenedStream)
            self.assertEqual(out.result.key, key)
            self.assertIs(out.result.pipeline, h.mux.child_pipeline(key))
            self.assertEqual(h.mux.credit.send_available(key), 10)
            assert app.metadata is not None
            self.assertEqual((app.metadata.key, app.metadata.origin, app.metadata.info), (key, 'local', 'hello'))
        finally:
            h.close()

    def test_refused_open(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            app = _keep_open()
            out = (h.open(app_spec(app)))
            (opened,) = of_type(h.frames, LOpen)

            h.feed(LRefuse(opened.key, 'no thanks'))
            self.assertIsInstance(out.exc, StreamRefusedMultiplexIoPipelineError)
            self.assertEqual(out.exc.reason, 'no thanks')  # type: ignore[union-attr]
            self.assertFalse(app.saw_initial_input)
            self.assertEqual(len(h.mux.streams), 0)
            self.assertEqual(h.mux.streams.stats.refused_local, 1)
            self.assertEqual(h.adapter.released, [opened.key])
        finally:
            h.close()

    def test_implicit_open_establishes_at_once(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()), adapter=LoopbackAdapter(explicit_open=False))
        try:
            app = StreamApp(send=b'early', close_on_final_input=False)
            out = (h.open(app_spec(app)))
            self.assertIsInstance(out.result, IoPipelineMultiplexOpenedStream)
            self.assertTrue(app.saw_initial_input)
            # No send credit was granted yet: the data waits.
            self.assertEqual(data_of(h.frames, out.result.key), b'')
        finally:
            h.close()

    def test_local_stream_limit(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.mux.streams.set_limits(max_local=2)
            outs = [(h.open(app_spec(_keep_open()))) for _ in range(3)]
            self.assertEqual(len(of_type(h.frames, LOpen)), 2)
            self.assertFalse(outs[0].done)
            self.assertFalse(outs[1].done)
            self.assertIn('local', str(outs[2].exc))

            # Raising the limit at runtime admits new ones.
            h.mux.streams.set_limits(max_local=3)
            out = (h.open(app_spec(_keep_open())))
            self.assertFalse(out.done)
            self.assertEqual(len(of_type(h.frames, LOpen)), 3)
        finally:
            h.close()


class TestRemoteOpens(unittest.TestCase):
    def test_accept_precedes_any_stream_output(self) -> None:
        factory = AppFactory(lambda o: StreamApp(send=b'greeting', close_on_final_input=False))
        h = LoopbackHarness(factory)
        try:
            frames = h.feed(LOpen('k', info='x'))
            self.assertEqual(frames[0], LAccept('k'))
            self.assertEqual(data_of(frames, 'k'), b'greeting')
            self.assertEqual(factory.openings[0].info, 'x')
            self.assertEqual(factory.openings[0].origin, 'remote')
        finally:
            h.close()

    def test_refused_by_factory_and_by_limit(self) -> None:
        factory = AppFactory(lambda o: _keep_open(), refuse=lambda o: 'nope' if o.info == 'bad' else None)
        h = LoopbackHarness(factory)
        try:
            h.mux.streams.set_limits(max_remote=1)
            h.feed(LOpen('bad', info='bad'), LOpen('good'), LOpen('over'))
            self.assertEqual(of_type(h.frames, LRefuse, 'bad'), [LRefuse('bad', 'nope')])
            self.assertEqual(of_type(h.frames, LAccept), [LAccept('good')])
            (over,) = of_type(h.frames, LRefuse, 'over')
            self.assertIn('remote', str(over.reason))
            self.assertEqual(list(factory.apps), ['good'])
            self.assertEqual(h.mux.streams.stats.refused_remote, 2)
        finally:
            h.close()

    def test_child_construction_failure_is_a_refusal(self) -> None:
        class FailsOnAdd(StreamApp):
            def notify(self, ctx: ta.Any, no: ta.Any) -> None:
                raise RuntimeError('boom')

        h = LoopbackHarness(AppFactory(lambda o: FailsOnAdd()))
        try:
            h.feed(LOpen('k'))
            (refused,) = of_type(h.frames, LRefuse, 'k')
            self.assertIsInstance(refused.reason, RuntimeError)
            self.assertEqual(of_type(h.frames, LAccept), [])
            self.assertEqual(len(h.mux.streams), 0)
        finally:
            h.close()


class TestCloseAndResetInEachState(unittest.TestCase):
    """Close and reset arriving from the peer in every lifecycle state."""

    def _open_remote(self, h: LoopbackHarness, key: str, state: IoPipelineMultiplexStreamState) -> StreamApp:
        h.feed(LOpen(key))
        app = h.app(key)
        assert isinstance(app, StreamApp)
        if state in (IoPipelineMultiplexStreamState.HALF_CLOSED_REMOTE, IoPipelineMultiplexStreamState.ENDED):
            h.feed(LEnd(key))
        if state in (IoPipelineMultiplexStreamState.HALF_CLOSED_LOCAL, IoPipelineMultiplexStreamState.ENDED):
            h.feed_stream(key, Emit(IoPipelineMessages.ShutdownOutput))
        self.assertIs(h.mux.streams[key].state, state)
        return app

    def test_close_in_each_state(self) -> None:
        for state in (
                IoPipelineMultiplexStreamState.OPEN,
                IoPipelineMultiplexStreamState.HALF_CLOSED_LOCAL,
                IoPipelineMultiplexStreamState.HALF_CLOSED_REMOTE,
                IoPipelineMultiplexStreamState.ENDED,
        ):
            with self.subTest(state=state):
                h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
                try:
                    app = self._open_remote(h, 'k', state)
                    h.feed(LData('k', b'tail') if state in (
                        IoPipelineMultiplexStreamState.OPEN,
                        IoPipelineMultiplexStreamState.HALF_CLOSED_LOCAL,
                    ) else LClose('k'))
                    if state in (IoPipelineMultiplexStreamState.OPEN, IoPipelineMultiplexStreamState.HALF_CLOSED_LOCAL):
                        h.feed(LClose('k'))

                    # A graceful remote close: the pipeline gets what was queued, then FinalInput, and lives on.
                    self.assertTrue(app.saw_final_input)
                    if state in (IoPipelineMultiplexStreamState.OPEN, IoPipelineMultiplexStreamState.HALF_CLOSED_LOCAL):
                        self.assertEqual(bytes(app.received), b'tail')
                    self.assertEqual(app.errors, [])
                    self.assertIn('k', h.mux.streams)

                    # Output after the close is discarded; the pipeline finishing releases the stream.
                    before = len(h.frames)
                    if state in (
                            IoPipelineMultiplexStreamState.HALF_CLOSED_LOCAL,
                            IoPipelineMultiplexStreamState.ENDED,
                    ):
                        h.feed_stream('k', Emit(IoPipelineMessages.FinalOutput))
                    else:
                        h.feed_stream('k', Emit(b'discarded', IoPipelineMessages.FinalOutput))
                    self.assertEqual(h.frames[before:], [])
                    self.assertTrue(app.final_output.is_succeeded())
                    self.assertNotIn('k', h.mux.streams)
                    self.assertEqual(h.mux.streams.stats.closed, 1)
                finally:
                    h.close()

    def test_close_after_local_finish_releases_at_once(self) -> None:
        factory = AppFactory(lambda o: StreamApp())
        h = LoopbackHarness(factory, adapter=LoopbackAdapter(on_finish='wait'))
        try:
            h.feed(LOpen('k'), LEnd('k'))
            # The app closed on FinalInput; the finish went out and the stream awaits the peer's close.
            self.assertEqual(of_type(h.frames, LFinish), [LFinish('k', False)])
            stream = h.mux.streams['k']
            self.assertTrue(stream.local_finished)
            self.assertIs(stream.state, IoPipelineMultiplexStreamState.ENDED)
            self.assertTrue(factory.apps['k'].final_output.is_succeeded())
            self.assertFalse(ta.cast(ta.Any, h.mux.child_pipeline('k')).is_ready)

            h.feed(LClose('k'))
            self.assertNotIn('k', h.mux.streams)
            self.assertEqual(h.adapter.released, ['k'])
        finally:
            h.close()

    def test_reset_in_each_state(self) -> None:
        for state in (
                IoPipelineMultiplexStreamState.OPEN,
                IoPipelineMultiplexStreamState.HALF_CLOSED_LOCAL,
                IoPipelineMultiplexStreamState.HALF_CLOSED_REMOTE,
                IoPipelineMultiplexStreamState.ENDED,
        ):
            with self.subTest(state=state):
                h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
                try:
                    app = self._open_remote(h, 'k', state)
                    child_pipeline = h.mux.child_pipeline('k')
                    assert child_pipeline is not None
                    h.feed(LReset('k', 'cancelled'))

                    self.assertEqual(len(app.errors), 1)
                    err = app.errors[0]
                    self.assertIsInstance(err, StreamResetMultiplexIoPipelineError)
                    self.assertEqual((err.reason, err.by), ('cancelled', 'remote'))  # type: ignore[attr-defined]
                    self.assertFalse(child_pipeline.is_ready)
                    self.assertNotIn('k', h.mux.streams)
                    self.assertEqual(h.mux.streams.stats.reset_remote, 1)
                    self.assertEqual(of_type(h.frames, LReset), [])  # nothing is echoed for a peer's reset
                finally:
                    h.close()

    def test_reset_while_opening_fails_the_open(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            app = _keep_open()
            out = (h.open(app_spec(app)))
            (opened,) = of_type(h.frames, LOpen)
            h.feed(LReset(opened.key, 'gone'))
            self.assertIsInstance(out.exc, StreamResetMultiplexIoPipelineError)
            self.assertFalse(app.saw_initial_input)
            self.assertNotIn(opened.key, h.mux.streams)
        finally:
            h.close()

    def test_close_while_opening_fails_the_open(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            out = (h.open(app_spec(_keep_open())))
            (opened,) = of_type(h.frames, LOpen)
            h.feed(LClose(opened.key))
            self.assertIsInstance(out.exc, StreamResetMultiplexIoPipelineError)
            self.assertNotIn(opened.key, h.mux.streams)
        finally:
            h.close()

    def test_reset_after_local_finish_lets_the_finish_complete(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: StreamApp()), adapter=LoopbackAdapter(on_finish='wait'))
        try:
            h.hold_drain = True
            h.feed(LOpen('k'), LEnd('k'))
            app = h.app('k')
            # The finish is out but its parent flush is still pending.
            self.assertFalse(app.final_output.is_done())

            h.feed(LReset('k', 'late'))
            self.assertEqual(app.errors, [])
            h.hold_drain = False
            h.step()
            self.assertTrue(app.final_output.is_succeeded())
            self.assertNotIn('k', h.mux.streams)
        finally:
            h.close()


class TestProtocolViolations(unittest.TestCase):
    def test_unknown_stream_fails_the_connection(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k'))
            app = h.app('k')
            h.feed(LData('nope', b'x'))

            (bye,) = of_type(h.frames, LGoodbye)
            self.assertIn('nope', str(bye.exc))
            self.assertEqual(len(app.errors), 1)
            self.assertIsInstance(app.errors[0], ConnectionClosedMultiplexIoPipelineError)
            self.assertTrue(h.pipeline.saw_final_output)
        finally:
            h.close()

    def test_data_after_peer_end_fails_the_connection(self) -> None:
        h = LoopbackHarness(AppFactory(lambda o: _keep_open()))
        try:
            h.feed(LOpen('k'), LEnd('k'))
            h.feed(LData('k', b'late'))
            self.assertEqual(len(of_type(h.frames, LGoodbye)), 1)
        finally:
            h.close()
