# ruff: noqa: UP006 UP007 UP045
# @om-lite
import asyncio
import dataclasses as dc
import gc
import socket
import typing as ta
import unittest
import weakref

from .....testing.unittest.asyncs import AsyncioIsolatedAsyncTestCase
from ...core import IoPipelineHandler
from ...core import IoPipelineMessages
from ...drivers.asyncio import PollAsyncioStreamIoPipelineDriver
from ...drivers.fdio import IoPipelineDriverSocketFdioHandler
from ...drivers.pure import PureIoPipelineDriver
from ...drivers.sync import FdSyncIoPipelineDriver
from ...drivers.sync import SocketSyncIoPipelineDriver
from ...drivers.tests.test_asyncio_backpressure import _DeferYieldingProducer
from ...flow.types import IoPipelineFlowMessages
from ...sched.types import IoPipelineScheduling
from ...yielding import CountingIoPipelineYieldPolicy
from ..children import MultiplexChildConfig
from ..credit import ConnectionMultiplexCreditStrategy
from ..handlers import MultiplexConfig
from ..types import MultiplexMessages
from .apps import AppFactory
from .apps import Emit
from .apps import StreamApp
from .apps import app_spec
from .h2like import H2Data
from .h2like import H2LikeAdapter
from .h2like import Headers
from .h2like import h2_like_spec
from .loopback import LBatch
from .loopback import LClose
from .loopback import LData
from .loopback import LEnd
from .loopback import LGoodbye
from .loopback import LGrant
from .loopback import LMsg
from .loopback import LoopbackAdapter
from .loopback import LoopbackHarness
from .loopback import LOpen
from .loopback import LRefuse
from .loopback import of_type
from .test_emission import _RemoveMuxOnFrame


##


@dc.dataclass(frozen=True)
class _ExtendedData:
    data: bytes


class _QueuedMessage:
    pass


class _AfterEnd(IoPipelineMessages.AfterFinalInput):
    pass


class _ReadAfterEnd(StreamApp):
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


class _TwoFramesAdapter(LoopbackAdapter):
    def encode_data(self, stream, data):
        raw = data.tobytes()
        return [LData(stream.key, raw[:1]), LData(stream.key, raw[1:])]


class _TimerDuringOutput(IoPipelineHandler):
    def __init__(self):
        super().__init__()

        self.units = 0
        self.timer_at = None

    @staticmethod
    def _tick(ctx):
        ctx.handler.timer_at = ctx.handler.units

    def outbound(self, ctx, msg):
        if isinstance(msg, H2Data):
            self.units += 1
            if self.units == 1:
                ctx.services[IoPipelineScheduling].schedule_context(ctx.ref, 0., self._tick)
        ctx.feed_out(msg)


class TestMultiplexYielding(AsyncioIsolatedAsyncTestCase):
    async def test_counting_yields_interleave_a_due_parent_timer(self):
        for kind in ('pure', 'socket', 'fd', 'fdio', 'asyncio'):
            with self.subTest(driver=kind):
                spec, _ = h2_like_spec(
                    'client',
                    AppFactory(lambda o: StreamApp()),
                    adapter=H2LikeAdapter('client', peer_initial_window=8192, max_frame=16),
                    config=MultiplexConfig(turn_output_budget=16, yield_policy=CountingIoPipelineYieldPolicy(1)),
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
                    driver.enqueue(MultiplexMessages.OpenStream(app_spec(app)))
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


class TestMultiplexAdversarial(unittest.TestCase):

    def test_deferred_child_producer_is_paused_before_exhausting_output(self):
        # This is the same cooperative producer used to verify top-level driver backpressure: each 16 KiB chunk is
        # followed by a flush and a Defer, and it stops as soon as it receives PauseOutput.
        app = _DeferYieldingProducer()
        h = LoopbackHarness(
            lambda o: app_spec(app),
            config=MultiplexConfig(child=MultiplexChildConfig(
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

    def test_timer_read_token_delivers_typed_message_after_eof(self):
        app = _ReadAfterEnd(close_on_final_input=False)
        h = LoopbackHarness(lambda o: app_spec(app, auto_read=False))
        try:
            h.feed(LOpen('k'))
            msg = _AfterEnd()
            h.feed(LBatch([LEnd('k'), LMsg('k', msg)]))
            self.assertTrue(app.saw_final_input)
            self.assertEqual(app.messages, [])

            h.driver.advance_time(1.)
            h.step()
            self.assertEqual(app.messages, [msg])
            self.assertEqual(app.errors, [])
        finally:
            h.close()

    def test_factory_exception_isolated_to_the_refused_stream(self):
        good = StreamApp(close_on_final_input=False)

        def factory(opening):
            if opening.key == 'bad':
                raise ValueError('invalid application stream parameters')
            return app_spec(good)

        h = LoopbackHarness(factory)
        try:
            h.feed(LOpen('good'), LOpen('bad'))
            self.assertEqual(of_type(h.frames, LGoodbye), [])
            self.assertEqual(len(of_type(h.frames, LRefuse, 'bad')), 1)
            h.feed(LData('good', b'still usable'))
            self.assertEqual(bytes(good.received), b'still usable')
            self.assertEqual(good.errors, [])
        finally:
            h.close()

    def test_control_output_limit_bounds_one_decoded_batch(self):
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp()),
            config=MultiplexConfig(max_remote_streams=0, max_control_during_pause=3),
        )
        try:
            h.enqueue(IoPipelineFlowMessages.PauseOutput())
            h.feed(LBatch([LOpen(i) for i in range(100)]))
            self.assertEqual(len(of_type(h.frames, LGoodbye)), 1)
            self.assertLessEqual(len(of_type(h.frames, LRefuse)), 4)
        finally:
            h.close()

    def test_removal_during_multi_frame_encoding_stops_emission(self):
        remover = _RemoveMuxOnFrame(lambda msg: isinstance(msg, LData))
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

    def test_peer_close_completes_earlier_fences_before_final_output(self):
        app = StreamApp()
        h = LoopbackHarness(lambda o: app_spec(app))
        try:
            h.feed(LOpen('k'))
            h.hold_drain = True
            flush = IoPipelineFlowMessages.FlushOutput()
            order = []
            flush.add_listener(lambda m: order.append('flush'))
            app.shutdown_output.add_listener(lambda m: order.append('shutdown'))
            app.final_output.add_listener(lambda m: order.append('final'))
            h.feed_stream('k', Emit(b'request', flush, IoPipelineMessages.ShutdownOutput))
            self.assertEqual(order, [])

            h.feed(LClose('k'))
            self.assertEqual(order, ['flush', 'shutdown', 'final'])
        finally:
            h.close()

    def test_flow_controlled_typed_output_applies_backpressure(self):
        app = StreamApp(close_on_final_input=False)
        h = LoopbackHarness(
            lambda o: app_spec(app),
            adapter=LoopbackAdapter(cost=lambda m: len(m.data)),
            config=MultiplexConfig(child=MultiplexChildConfig(
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

    def test_remote_open_data_close_in_one_batch_delivers_accepted_input(self):
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

    def test_teardown_releases_queued_input_while_handler_is_retained(self):
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

    def test_finished_child_releases_unread_connection_credit(self):
        credit = ConnectionMultiplexCreditStrategy(
            send_credit=100,
            recv_window=8,
            connection_replenish_on='consume',
        )
        factory = AppFactory(lambda o: StreamApp(close_on_final_input=False), auto_read=False)
        h = LoopbackHarness(
            factory,
            adapter=LoopbackAdapter(recv_window=8, on_finish='wait'),
            credit=credit,
        )
        try:
            h.feed(LOpen('abandoned'), LOpen('other'))
            h.feed(LData('abandoned', b'12345678'))
            self.assertEqual(of_type(h.frames, LGrant), [])

            h.feed_stream('abandoned', Emit(IoPipelineMessages.FinalOutput))
            self.assertTrue(h.mux.streams['abandoned'].local_finished)
            self.assertTrue(factory.apps['abandoned'].final_output.is_succeeded())
            # The child has finished and can never consume the queued input. The peer's close handshake may arrive
            # much later; it must not hold the entire connection window until then.
            self.assertEqual(sum(f.n for f in of_type(h.frames, LGrant) if f.key is None), 8)
            self.assertEqual(h.mux.streams['abandoned'].in_bytes, 0)
        finally:
            h.close()
