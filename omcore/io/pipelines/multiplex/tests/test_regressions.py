# ruff: noqa: SLF001 UP006 UP007 UP037 UP045
# @om-lite
"""
Regression tests for defects found reviewing the multiplexing work. The ids in the comments (F1-F4, O1-O31, T1-T4) are
those of the review findings recorded in FINDINGS.md at commit 323de87b3; each comment describes the defect as it was
found.
"""
import asyncio
import dataclasses as dc
import gc
import socket
import typing as ta
import unittest
import weakref

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineMessages
from ...drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ...drivers.fdio import IoPipelineDriverSocketFdioHandler
from ...drivers.pure import PureIoPipelineDriver
from ...drivers.sync import FdSyncIoPipelineDriver
from ...drivers.sync import SocketSyncIoPipelineDriver
from ...drivers.tests.producers import DeferYieldingProducer
from ...drivers.types import IoPipelineDriverState
from ...flow.types import IoPipelineFlowMessages
from ...sched.types import IoPipelineScheduling
from ...yielding import CountingIoPipelineYieldPolicy
from ..children import IoPipelineMultiplexChildConfig
from ..credit import ConnectionMultiplexCreditStrategy
from ..handlers import IoPipelineMultiplexConfig
from ..handlers import MultiplexIoPipelineHandler
from ..types import IoPipelineMultiplexMessages
from ..types import IoPipelineMultiplexStreamState
from .apps import AppFactory
from .apps import Emit
from .apps import StreamApp
from .apps import app_spec
from .h2like import H2Data
from .h2like import H2LikeAdapter
from .h2like import Headers
from .h2like import h2_like_spec
from .loopback import LAccept
from .loopback import LBatch
from .loopback import LClose
from .loopback import LData
from .loopback import LEnd
from .loopback import LFinish
from .loopback import LGoodbye
from .loopback import LGrant
from .loopback import LMsg
from .loopback import LoopbackAdapter
from .loopback import LoopbackHarness
from .loopback import LOpen
from .loopback import LRefuse
from .loopback import LReset
from .loopback import Outcome
from .loopback import of_type
from .removers import RemoveMuxOnFrame


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
            self.assertIs(h.mux.streams['k'].state, IoPipelineMultiplexStreamState.HALF_CLOSED_LOCAL)

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


class TestPeerCloseFenceOrder(unittest.TestCase):
    # F4 again, from reviewer 2's angle (their MUX-08): the application sent data, a flush, and output shutdown, and
    # the parent's drain is held. A graceful peer close then makes the application finish. All three fences complete
    # once the held parent flush completes, in their original order - the final never ahead of the earlier two.

    def test_peer_close_completes_earlier_fences_before_final_output(self) -> None:
        app = StreamApp()
        h = LoopbackHarness(lambda o: app_spec(app))
        try:
            h.feed(LOpen('k'))
            h.hold_drain = True
            flush = IoPipelineFlowMessages.FlushOutput()
            order: ta.List[str] = []
            flush.add_listener(lambda m: order.append('flush'))
            app.shutdown_output.add_listener(lambda m: order.append('shutdown'))
            app.final_output.add_listener(lambda m: order.append('final'))
            h.feed_stream('k', Emit(b'request', flush, IoPipelineMessages.ShutdownOutput))
            self.assertEqual(order, [])

            h.feed(LClose('k'))
            self.assertEqual(order, [])  # Nothing may complete ahead of the held transport flush.

            h.hold_drain = False
            h.step()
            self.assertEqual(order, ['flush', 'shutdown', 'final'])
            self.assertTrue(flush.is_succeeded())
            self.assertTrue(app.shutdown_output.is_succeeded())
            self.assertTrue(app.final_output.is_succeeded())
        finally:
            h.close()


##


@dc.dataclass(frozen=True)
class _Trailer(IoPipelineMessages.AfterFinalInput):
    """A typed message which may follow end-of-data, like an SSH exit-status request after EOF."""

    name: str


class TestManualReadMessageAfterEnd(unittest.TestCase):
    # O2. DESIGN 13: "In manual-read mode one child ReadyForInput permits one batch: everything queued at that point".
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


class _ReadAfterEnd(StreamApp):
    """Requests one read at start and, a second later, one more after FinalInput - as if reacting on a timer."""

    def inbound(self, ctx, msg):
        super().inbound(ctx, msg)
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())
        elif isinstance(msg, IoPipelineMessages.FinalInput):
            ctx.services[IoPipelineScheduling].schedule_context(
                ctx.ref,
                1.,
                lambda ctx2: ctx2.feed_out(IoPipelineFlowMessages.ReadyForInput()),
            )


class TestReadTokenAfterEnd(unittest.TestCase):
    # O2, second shape (reviewer 2's MUX-07): a child which requests another read after FinalInput, from a timer, was
    # not served either. With post-EOF typed messages delivered without a token, the message arrives at once and the
    # later token is simply unused.

    def test_timer_read_token_delivers_typed_message_after_eof(self) -> None:
        app = _ReadAfterEnd(close_on_final_input=False)
        h = LoopbackHarness(lambda o: app_spec(app, auto_read=False))
        try:
            h.feed(LOpen('k'))
            msg = _Trailer('late')
            h.feed(LBatch([LEnd('k'), LMsg('k', msg)]))
            self.assertTrue(app.saw_final_input)
            self.assertEqual(app.messages, [msg])

            h.driver.advance_time(1.)
            h.step()
            self.assertEqual(app.messages, [msg])
            self.assertEqual(app.errors, [])
        finally:
            h.close()


class TestStreamSpecFactoryFailure(unittest.TestCase):
    # O5 (reviewer 2's MUX-11). A stream spec factory may refuse a stream by returning a MultiplexRefusal; one which
    # raises instead - an application error for one request - takes the whole connection down with it, although
    # nothing about the connection is wrong. A child which cannot be built is refused (DESIGN 13), and a factory which
    # cannot produce a spec is the same situation.

    def test_factory_exception_refuses_only_that_stream(self) -> None:
        good = StreamApp(close_on_final_input=False)

        def factory(opening):
            if opening.key == 'bad':
                raise RuntimeError('factory boom')
            return app_spec(good)

        h = LoopbackHarness(factory)
        try:
            frames = h.feed(LOpen('good'), LOpen('bad'))

            self.assertIsNone(h.mux._failed)
            self.assertEqual(of_type(frames, LGoodbye), [])
            self.assertEqual(len(of_type(frames, LRefuse, 'bad')), 1)
            self.assertEqual(of_type(frames, LAccept), [LAccept('good')])
            self.assertEqual(h.mux.streams.stats.refused_remote, 1)
            self.assertIn('good', h.mux.streams)

            # The healthy stream is unaffected.
            h.feed(LData('good', b'still usable'))
            self.assertEqual(bytes(good.received), b'still usable')
            self.assertEqual(good.errors, [])
        finally:
            h.close()


class TestAdapterFailuresWhileEncoding(unittest.TestCase):
    # O3. An adapter failing while decoding (`inbound`), or in its lifecycle hooks, fails the connection: the error is
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
    # O4. Once the local side has finished, data the peer still sends is consumed at once and its credit replenished
    # in the accounting - but the grant is then dropped rather than encoded (`_queue_grants` skips finished streams).
    # The window the multiplexer believes it advertised drifts above what the peer was told.

    def test_advertised_credit_matches_the_wire(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp(close_on_final_input=False)),
            adapter=LoopbackAdapter(recv_window=100, on_finish='wait'),
        )
        try:
            h.feed(LOpen('k'))
            h.feed_stream('k', Emit(IoPipelineMessages.FinalOutput))
            self.assertIs(h.mux.streams['k'].state, IoPipelineMultiplexStreamState.HALF_CLOSED_LOCAL)

            for n in (60, 40):
                h.feed(LData('k', b'x' * n))
                on_wire = 100 + sum(g.n for g in of_type(h.frames, LGrant, 'k'))
                totals = h.mux.credit.totals('k')
                self.assertEqual(totals.recv_advertised, on_wire)
                self.assertEqual(totals.recv_outstanding, on_wire - totals.recv_received)
        finally:
            h.close()


class TestOpenBeforeInitialInput(unittest.TestCase):
    # O6. The README documents opening a stream from outside the pipeline with `feed_in_to`. Done after the driver has
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

            msg = IoPipelineMultiplexMessages.OpenStream(app_spec(StreamApp(close_on_final_input=False)))
            out = Outcome(msg)
            h.pipeline.feed_in_to(ref, msg)
            h.step()

            self.assertIs(h.driver.state, IoPipelineDriverState.RUNNING)
            self.assertTrue(out.done)
            self.assertIsNotNone(out.result)
        finally:
            h.close()


class TestBatchedOpenDataClose(unittest.TestCase):
    # O9 (reviewer 2's MUX-01). A peer's open, request data, and graceful close decoded from one read: the factory
    # accepted the stream and its input was queued, but establishment is deferred to the pump, and `_close` finding no
    # child yet discards the pending establishment and closes the stream. The application never sees InitialInput or
    # the request. The same frames delivered separately work.

    def test_remote_open_data_close_in_one_batch_delivers_accepted_input(self) -> None:
        for batched in (False, True):
            with self.subTest(batched=batched):
                factory = AppFactory(lambda o: StreamApp())
                h = LoopbackHarness(factory)
                try:
                    frames = [LOpen('k'), LData('k', b'accepted request'), LClose('k')]
                    if batched:
                        h.feed(LBatch(frames))
                    else:
                        for frame in frames:
                            h.feed(frame)

                    app = factory.apps['k']
                    self.assertTrue(app.saw_initial_input)
                    self.assertEqual(bytes(app.received), b'accepted request')
                    self.assertTrue(app.saw_final_input)
                    self.assertTrue(app.final_output.is_succeeded())
                    self.assertEqual(app.errors, [])
                finally:
                    h.close()


class TestDeferredProducerBackpressure(unittest.TestCase):
    # O10 (reviewer 2's MUX-02). `collect_output` runs a child's Defers while draining its output, and the child's
    # writability is only re-derived after the collection returns, so a cooperative producer continuing through
    # Defers - one which stops on PauseOutput - produces its whole backlog before the first pause.

    def test_deferred_child_producer_is_paused_before_exhausting_output(self) -> None:
        # The same cooperative producer verifies the top-level asyncio driver's backpressure: each 16 KiB chunk is
        # followed by a flush and a Defer, and it stops as soon as it receives PauseOutput.
        app = DeferYieldingProducer()
        h = LoopbackHarness(
            lambda o: app_spec(app),
            config=IoPipelineMultiplexConfig(child=IoPipelineMultiplexChildConfig(
                write_high_watermark=64 * 1024,
                write_low_watermark=16 * 1024,
            )),
        )
        try:
            h.feed(LOpen('k', credit=0))
            self.assertIsNotNone(app.emitted_at_first_pause)
            assert app.emitted_at_first_pause is not None
            self.assertLessEqual(app.emitted_at_first_pause, 8)
            self.assertLessEqual(h.mux.streams['k'].out_bytes, 128 * 1024)
        finally:
            h.close()


@dc.dataclass(frozen=True)
class _ExtendedData:
    data: bytes


class TestTypedOutputWatermarks(unittest.TestCase):
    # O11 (reviewer 2's MUX-03). A flow-controlled typed message waits for send credit like data, but its payload is
    # not counted in the stream's queued bytes, from which child writability is derived: SSH extended data can pile up
    # without a PauseOutput.

    def test_flow_controlled_typed_output_applies_backpressure(self) -> None:
        app = StreamApp(close_on_final_input=False)
        h = LoopbackHarness(
            lambda o: app_spec(app),
            adapter=LoopbackAdapter(cost=lambda m: len(m.data)),
            config=IoPipelineMultiplexConfig(child=IoPipelineMultiplexChildConfig(
                write_high_watermark=16,
                write_low_watermark=4,
            )),
        )
        try:
            h.feed(LOpen('k', credit=0))
            h.feed_stream('k', Emit(_ExtendedData(b'x' * 128)))
            self.assertEqual(of_type(h.frames, LMsg), [])
            self.assertEqual(app.writability, [IoPipelineFlowMessages.PauseOutput])

            h.feed(LGrant('k', 128))
            self.assertEqual([f.msg for f in of_type(h.frames, LMsg)], [_ExtendedData(b'x' * 128)])
            self.assertEqual(app.writability, [
                IoPipelineFlowMessages.PauseOutput,
                IoPipelineFlowMessages.ReadyForOutput,
            ])
        finally:
            h.close()


class TestFinishedChildConnectionCredit(unittest.TestCase):
    # O12 (reviewer 2's MUX-04). With connection credit replenished on consumption, a manual-read child can hold the
    # whole connection window in unread input. When that child finishes and the adapter waits for the peer's close,
    # the destroyed child leaves the input - and the connection credit it occupies - on the stream until the peer's
    # close handshake, blocking every other stream meanwhile.

    def test_finished_child_releases_unread_connection_credit(self) -> None:
        credit = ConnectionMultiplexCreditStrategy(
            send_credit=100,
            recv_window=8,
            connection_replenish_on='consume',
        )
        factory = AppFactory(
            lambda o: StreamApp(
                close_on_final_input=False,
            ),
            auto_read=False)
        h = LoopbackHarness(
            factory,
            adapter=LoopbackAdapter(
                recv_window=8,
                on_finish='wait',
            ),
            credit=credit,
        )
        try:
            h.feed(LOpen('abandoned'), LOpen('other'))
            h.feed(LData('abandoned', b'12345678'))
            self.assertEqual(of_type(h.frames, LGrant), [])

            h.feed_stream('abandoned', Emit(IoPipelineMessages.FinalOutput))
            self.assertTrue(h.mux.streams['abandoned'].local_finished)
            self.assertTrue(factory.apps['abandoned'].final_output.is_succeeded())
            # The child has finished and can never consume the queued input. The peer's close handshake may arrive much
            # later; it must not hold the entire connection window until then.
            self.assertEqual(sum(f.n for f in of_type(h.frames, LGrant) if f.key is None), 8)
            self.assertEqual(h.mux.streams['abandoned'].in_bytes, 0)
        finally:
            h.close()


class TestControlOutputBound(unittest.TestCase):
    # O13 (reviewer 2's MUX-05). With the parent paused, control output is bounded by `max_control_during_pause`:
    # crossing it fails the connection - but `_emit` keeps draining the control queue it was already emitting, so one
    # decoded batch of 100 opens still produces 100 refusals.

    def test_control_output_limit_bounds_one_decoded_batch(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp()),
            config=IoPipelineMultiplexConfig(
                max_remote_streams=0,
                max_control_during_pause=3,
            ),
        )
        try:
            h.enqueue(IoPipelineFlowMessages.PauseOutput())
            h.feed(LBatch([LOpen(i) for i in range(100)]))
            self.assertEqual(len(of_type(h.frames, LGoodbye)), 1)
            self.assertLessEqual(len(of_type(h.frames, LRefuse)), 4)
        finally:
            h.close()


class _TwoFramesAdapter(LoopbackAdapter):
    """Encodes each data unit as two frames."""

    def encode_data(self, stream, data):
        raw = data.tobytes()
        return [LData(stream.key, raw[:1]), LData(stream.key, raw[1:])]


class TestRemovalDuringMultiFrameEmission(unittest.TestCase):
    # O14 (reviewer 2's MUX-09). `_emit` rechecks removal between units, but the loop feeding the frames of one unit
    # does not: when feeding the first frame removes the multiplexer, the second is fed through the invalidated
    # context and the parent fails instead of emission stopping cleanly.

    def test_removal_during_multi_frame_encoding_stops_emission(self) -> None:
        remover = RemoveMuxOnFrame(lambda msg: isinstance(msg, LData))
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp(close_on_final_input=False)),
            adapter=_TwoFramesAdapter(),
            extra_outer=[remover],
        )
        try:
            h.feed(LOpen('k'))
            h.feed_stream('k', Emit(b'ab'))
            self.assertTrue(remover.removed)
            self.assertEqual(remover.errors, [])
            self.assertTrue(h.pipeline.is_ready)
        finally:
            h.close()


class _QueuedMessage:
    pass


class TestTeardownReleasesInput(unittest.TestCase):
    # O15 (reviewer 2's MUX-10). Removing the multiplexer, or destroying its parent, aborts the children but leaves
    # the stream table, the credit and scheduler entries, and unread stream input in place: a retained handler keeps
    # application payloads which can never be processed alive, without cyclic garbage collection.

    def test_teardown_releases_queued_input_while_handler_is_retained(self) -> None:
        for destroy in (False, True):
            with self.subTest(destroy=destroy):
                h = LoopbackHarness(AppFactory(lambda o: StreamApp(), auto_read=False))
                was_enabled = gc.isenabled()
                gc.disable()
                try:
                    h.feed(LOpen('k'))
                    msg = _QueuedMessage()
                    msg_ref = weakref.ref(msg)
                    h.feed(LMsg('k', msg))
                    del msg
                    self.assertIsNotNone(msg_ref())

                    if destroy:
                        h.close()
                    else:
                        ref = h.pipeline.find_handler(h.mux)
                        assert ref is not None
                        h.pipeline.remove(ref)

                    self.assertIsNone(msg_ref(), 'removed multiplexer still owns unread stream input')
                    self.assertEqual(len(h.mux.streams), 0)
                    self.assertFalse(h.mux.credit.has_stream('k'))
                finally:
                    h.close()
                    if was_enabled:
                        gc.enable()


class _TimerDuringOutput(IoPipelineHandler):
    """Counts emitted data frames and, on the first, schedules an immediately due timer recording the count then."""

    def __init__(self) -> None:
        super().__init__()

        self.units = 0
        self.timer_at: ta.Optional[int] = None

    @staticmethod
    def _tick(ctx) -> None:
        ctx.handler.timer_at = ctx.handler.units

    def outbound(self, ctx, msg) -> None:
        if isinstance(msg, H2Data):
            self.units += 1
            if self.units == 1:
                ctx.services[IoPipelineScheduling].schedule_context(ctx.ref, 0., self._tick)
        ctx.feed_out(msg)


class TestDeferredYieldsAndTimers(AsyncioIsolatedAsyncTestCase):
    # O16 (reviewer 2's MUX-06). The yield policy's documented purpose is to let the driver interleave reads, writes
    # and timers between a handler's deferred turns. Every driver's output loop runs the deferred continuation at once,
    # before returning to due timers, so a timer due since the first of 256 units sees all 256 already emitted.

    async def test_counting_yields_interleave_a_due_parent_timer(self) -> None:
        for kind in ('pure', 'socket', 'fd', 'fdio', 'asyncio'):
            with self.subTest(driver=kind):
                spec, _ = h2_like_spec(
                    'client',
                    AppFactory(lambda o: StreamApp()),
                    adapter=H2LikeAdapter(
                        'client',
                        peer_initial_window=8192,
                        max_frame=16,
                    ),
                    config=IoPipelineMultiplexConfig(
                        turn_output_budget=16,
                        yield_policy=CountingIoPipelineYieldPolicy(1),
                    ),
                    connection_send_window=8192,
                )
                observer = _TimerDuringOutput()
                spec = dc.replace(spec, handlers=[*spec.handlers[:-1], observer, spec.handlers[-1]])
                sock, peer = socket.socketpair()
                driver: ta.Any
                if kind == 'pure':
                    driver = PureIoPipelineDriver(spec)
                elif kind == 'socket':
                    driver = SocketSyncIoPipelineDriver(spec, sock)
                elif kind == 'fd':
                    driver = FdSyncIoPipelineDriver(spec, sock.fileno(), sock.fileno())
                elif kind == 'fdio':
                    driver = IoPipelineDriverSocketFdioHandler(sock, ('local', 0), spec)
                else:
                    reader, writer = await asyncio.open_connection(sock=sock)
                    driver = PollAsyncioStreamIoPipelineDriver(spec, reader, writer)
                app = StreamApp(prelude=[Headers('request')], send=b'x' * 4096, close_on_final_input=False)
                try:
                    driver.enqueue(IoPipelineMultiplexMessages.OpenStream(app_spec(app)))
                    for _ in range(1024):
                        if kind == 'asyncio':
                            await driver.next(read=False)
                        else:
                            driver.next(read=False)
                            if kind == 'pure':
                                driver.drain_output()
                        if observer.units == 256 and observer.timer_at is not None:
                            break
                    self.assertEqual(observer.units, 256)
                    self.assertIsNotNone(observer.timer_at)
                    assert observer.timer_at is not None
                    self.assertLess(observer.timer_at, observer.units, 'every deferred turn ran before the due timer')
                finally:
                    if kind == 'asyncio':
                        await driver.close()
                    else:
                        driver.close()
                    sock.close()
                    peer.close()
