# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
"""
Demonstrations of open findings from reviewing the multiplexing work: each test here fails on purpose until its
finding is resolved. See ../../FINDINGS.md for the discussion.
"""
import dataclasses as dc
import unittest

from ...core import IoPipelineMessages
from ...drivers.types import IoPipelineDriverState
from ..handlers import MultiplexIoPipelineHandler
from ..types import MultiplexMessages
from ..types import MultiplexStreamState
from .apps import AppFactory
from .apps import Emit
from .apps import StreamApp
from .apps import app_spec
from .loopback import LAccept
from .loopback import LData
from .loopback import LEnd
from .loopback import LGoodbye
from .loopback import LGrant
from .loopback import LMsg
from .loopback import LoopbackAdapter
from .loopback import LoopbackHarness
from .loopback import LOpen
from .loopback import LRefuse
from .loopback import Outcome
from .loopback import of_type


##


@dc.dataclass(frozen=True)
class _Trailer(IoPipelineMessages.AfterFinalInput):
    """A typed message which may follow end-of-data, like an SSH exit-status request after EOF."""

    name: str


class TestManualReadMessageAfterEnd(unittest.TestCase):
    # DESIGN 13: "In manual-read mode one child ReadyForInput permits one batch: everything queued at that point".
    # Delivery stops at end-of-input, though, so a typed message queued behind it is left for a further token - which
    # a child has no reason to request once it has seen FinalInput. The message is never delivered.

    def _harness(self) -> LoopbackHarness:
        return LoopbackHarness(AppFactory(
            lambda o: StreamApp(manual_read=True, close_on_final_input=False),
            auto_read=False,
        ))

    def test_message_following_end_in_the_same_read_is_delivered(self) -> None:
        h = self._harness()
        try:
            h.feed(LOpen('k'))
            app = h.app('k')
            self.assertEqual(app.reads_requested, 1)

            # One transport read decoding to three frames. (Decoded within one adapter call, as `LBatch` would, the
            # message happens to be rescued by the token the child requests on the data batch's FlushInput, which is
            # still outstanding when FinalInput follows.)
            h.feed(LData('k', b'abc'), LEnd('k'), LMsg('k', _Trailer('exit-status')))

            self.assertEqual(bytes(app.received), b'abc')
            self.assertTrue(app.saw_final_input)
            self.assertEqual(app.messages, [_Trailer('exit-status')])
            self.assertEqual(h.mux.stats.queued_input['k'], (0, 0))
        finally:
            h.close()

    def test_message_arriving_after_end_is_delivered(self) -> None:
        h = self._harness()
        try:
            h.feed(LOpen('k'))
            app = h.app('k')
            h.feed(LData('k', b'abc'), LEnd('k'))
            self.assertTrue(app.saw_final_input)

            h.feed(LMsg('k', _Trailer('exit-status')))

            self.assertEqual(app.messages, [_Trailer('exit-status')])
            self.assertEqual(h.mux.stats.queued_input['k'], (0, 0))
        finally:
            h.close()


class TestStreamSpecFactoryFailure(unittest.TestCase):
    # A stream spec factory may refuse a stream by returning a MultiplexRefusal; one which raises instead - an
    # application error for one request - takes the whole connection down with it, although nothing about the
    # connection is wrong. A child which cannot be built is refused (DESIGN 13), and a factory which cannot produce a
    # spec is the same situation.

    def test_factory_exception_refuses_only_that_stream(self) -> None:
        def factory(opening):
            if opening.key == 'bad':
                raise RuntimeError('factory boom')
            return app_spec(StreamApp(close_on_final_input=False))

        h = LoopbackHarness(factory)
        try:
            frames = h.feed(LOpen('bad'), LOpen('good'))

            self.assertIsNone(h.mux._failed)
            self.assertEqual(of_type(frames, LGoodbye), [])
            self.assertEqual(len(of_type(frames, LRefuse, 'bad')), 1)
            self.assertEqual(of_type(frames, LAccept), [LAccept('good')])
            self.assertEqual(h.mux.streams.stats.refused_remote, 1)
            self.assertIn('good', h.mux.streams)
        finally:
            h.close()


class TestAdapterFailuresWhileEncoding(unittest.TestCase):
    # An adapter failing while decoding (`inbound`), or in its lifecycle hooks, fails the connection: the error is
    # encoded for the peer, every stream is aborted, and the connection finishes gracefully - `_fail`. An adapter
    # failing while encoding, or in `on_stream_released`, is not guarded: the exception escapes the multiplexing
    # handler as an inbound Error which, with the handler innermost, is unhandleable and fails the driver outright.

    def _assert_failed_gracefully(self, h: LoopbackHarness) -> None:
        self.assertIsInstance(h.mux._failed, RuntimeError)
        self.assertEqual(len(of_type(h.frames, LGoodbye)), 1)
        self.assertTrue(h.pipeline.saw_final_output)
        self.assertIs(h.driver.state, IoPipelineDriverState.CLOSED)
        self.assertEqual(len(h.mux.streams), 0)

    def test_encode_data_raising(self) -> None:
        class _Adapter(LoopbackAdapter):
            def encode_data(self, stream, data):
                raise RuntimeError('encode boom')

        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp(send=b'hello', close_on_final_input=False)),
            adapter=_Adapter(),
        )
        try:
            h.feed(LOpen('k'))
            self._assert_failed_gracefully(h)
        finally:
            h.close()

    def test_on_stream_released_raising(self) -> None:
        class _Adapter(LoopbackAdapter):
            def on_stream_released(self, stream):
                raise RuntimeError('release boom')

        h = LoopbackHarness(AppFactory(lambda o: StreamApp()), adapter=_Adapter())
        try:
            h.feed(LOpen('k'), LEnd('k'))
            self._assert_failed_gracefully(h)
        finally:
            h.close()


class TestReceiveCreditAfterLocalFinish(unittest.TestCase):
    # Once the local side has finished, data the peer still sends is consumed at once and its credit replenished in
    # the accounting - but the grant is then dropped rather than encoded (`_queue_grants` skips finished streams). The
    # window the multiplexer believes it advertised drifts above what the peer was told: the peer stalls on a window
    # which is never replenished, and a peer overrunning the real window by up to the dropped amount is not caught.

    def test_advertised_credit_matches_the_wire(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp(close_on_final_input=False)),
            adapter=LoopbackAdapter(recv_window=100, on_finish='wait'),
        )
        try:
            h.feed(LOpen('k'))
            h.feed_stream('k', Emit(IoPipelineMessages.FinalOutput))
            self.assertIs(h.mux.streams['k'].state, MultiplexStreamState.HALF_CLOSED_LOCAL)

            for n in (60, 40):
                h.feed(LData('k', b'x' * n))
                on_wire = 100 + sum(g.n for g in of_type(h.frames, LGrant, 'k'))
                totals = h.mux.credit.totals('k')
                self.assertEqual(totals.recv_advertised, on_wire)
                self.assertEqual(totals.recv_outstanding, on_wire - totals.recv_received)
        finally:
            h.close()


class TestOpenBeforeInitialInput(unittest.TestCase):
    # The README documents opening a stream from outside the pipeline with `feed_in_to`. Done after the driver has
    # built the pipeline but before its first step - which feeds InitialInput - the injected open counts as input, the
    # InitialInput is rejected, and the driver fails. (The core variant is `tests/test_findings.py`.)

    def test_open_fed_before_the_driver_starts(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp(close_on_final_input=False)),
            adapter=LoopbackAdapter(explicit_open=False),
        )
        try:
            h.driver.drain_output()  # Builds the pipeline; InitialInput is still queued for the first step.
            ref = h.pipeline.find_single_handler_of_type(MultiplexIoPipelineHandler)
            assert ref is not None

            msg = MultiplexMessages.OpenStream(app_spec(StreamApp(close_on_final_input=False)))
            out = Outcome(msg)
            h.pipeline.feed_in_to(ref, msg)
            h.step()

            self.assertIs(h.driver.state, IoPipelineDriverState.RUNNING)
            self.assertTrue(out.done)
            self.assertIsNotNone(out.result)
        finally:
            h.close()
