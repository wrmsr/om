# ruff: noqa: SLF001 UP006 UP007 UP037 UP045
# @om-lite
import gc
import hashlib
import typing as ta
import unittest
import weakref

from .....sockets.endpoints import TcpSocketEndpoint
from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerContext
from ...core import IoPipelineMessages
from ...drivers.pure.drivers import PureIoPipelineDriver
from ...drivers.pure.hosts import MemoryHostedIoPipelineDriver
from ...drivers.pure.hosts import MemoryIoPipelineHost
from ...drivers.types import IoPipelineDriverState
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ...hosts.types import IoPipelineHostedDriver
from ...multiplex.children import IoPipelineMultiplexChildConfig
from ...multiplex.handlers import IoPipelineMultiplexConfig
from ...multiplex.tests.loopback import LGrant
from ...multiplex.tests.loopback import LoopbackAdapter
from ...multiplex.tests.loopback import LoopbackHarness
from ...multiplex.tests.loopback import LOpen
from ...multiplex.tests.loopback import data_of
from ..handlers import AutoReadRelayIoPipelineError
from ..handlers import IoPipelineRelay
from ..handlers import IoPipelineRelayEndHandler
from ..handlers import PeerGoneRelayIoPipelineError
from ..handlers import UnmappedMessageRelayIoPipelineError
from .forwarder import IoPipelinePortForwarder


##


def _payload(seed: str, size: int) -> bytes:
    out = bytearray()
    block = hashlib.sha256(seed.encode()).digest()
    while len(out) < size:
        out.extend(block)
        block = hashlib.sha256(block).digest()
    return bytes(out[:size])


class _Typed:
    def __init__(self, value: ta.Any) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Typed) and other.value == self.value

    def __hash__(self) -> int:
        return hash(self.value)


class _PeerApp(IoPipelineHandler):
    """
    A transport-side application: sends `send` in chunks on start (then shuts down its output unless told not to),
    records what it receives, and in manual-read mode reads only when `allow_reads` permits.
    """

    def __init__(
            self,
            *,
            send: bytes = b'',
            shutdown_after_send: bool = True,
            manual_read: bool = False,
            allow_reads: ta.Optional[int] = None,
            chunk_size: int = 4096,
            send_messages: ta.Sequence[ta.Any] = (),
            close_on_final_input: bool = True,
    ) -> None:
        super().__init__()

        self._send = send
        self._shutdown_after_send = shutdown_after_send
        self._manual_read = manual_read
        self.allow_reads = allow_reads
        self._chunk_size = chunk_size
        self._send_messages = send_messages
        self._close_on_final_input = close_on_final_input

        self.received = bytearray()
        self.messages: ta.List[ta.Any] = []
        self.saw_final_input = False
        self.errors: ta.List[BaseException] = []
        self.reads_requested = 0
        self.final_output: ta.Optional[IoPipelineMessages.FinalOutput] = None
        self.writability: ta.List[str] = []
        self._ctx_pending_read = False

    def _read(self, ctx: IoPipelineHandlerContext) -> None:
        if not self._manual_read or self.saw_final_input:
            return
        if self.allow_reads is not None and self.allow_reads <= 0:
            self._ctx_pending_read = True
            return
        if self.allow_reads is not None:
            self.allow_reads -= 1
        self._ctx_pending_read = False
        self.reads_requested += 1
        ctx.feed_out(IoPipelineFlowMessages.ReadyForInput())

    def allow(self, ctx: IoPipelineHandlerContext, n: int) -> None:
        """Run inside the pipeline (posted): permits `n` more reads."""

        self.allow_reads = (self.allow_reads or 0) + n
        if self._ctx_pending_read:
            self._read(ctx)

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, IoPipelineMessages.InitialInput):
            ctx.feed_in(msg)
            mv = memoryview(self._send)
            for pos in range(0, len(mv), self._chunk_size):
                ctx.feed_out(mv[pos:pos + self._chunk_size])
            for m in self._send_messages:
                ctx.feed_out(m)
            if self._shutdown_after_send:
                ctx.feed_shutdown_output()
            self._read(ctx)
            return
        if isinstance(msg, IoPipelineFlowMessages.FlushInput):
            self._read(ctx)
            return
        if isinstance(msg, IoPipelineMessages.FinalInput):
            self.saw_final_input = True
            ctx.feed_in(msg)
            if self._close_on_final_input:
                self.final_output = ctx.feed_final_output()
            return
        if isinstance(msg, IoPipelineMessages.Error):
            self.errors.append(msg.exc)
            return
        if isinstance(msg, IoPipelineFlowMessages.PauseOutput):
            self.writability.append('pause')
            return
        if isinstance(msg, IoPipelineFlowMessages.ReadyForOutput):
            self.writability.append('ready')
            return
        if ByteStreamBuffers.can_bytes(msg):
            self.received.extend(ByteStreamBuffers.to_bytes(msg, strict=True))
            return
        if isinstance(msg, IoPipelineMessages.MayPropagate):
            ctx.feed_in(msg)
            return
        self.messages.append(msg)


def _peer_spec(app: _PeerApp, *, manual_read: bool = False) -> IoPipeline.Spec:
    return IoPipeline.Spec([app], services=[StubIoPipelineFlowService(auto_read=not manual_read)])


class _Inject(IoPipelineHandler):
    """Ahead of a relay end: feeds the given messages inward on start, as a decoder producing typed messages would."""

    def __init__(self, *msgs: ta.Any) -> None:
        super().__init__()

        self._msgs = msgs

    def inbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        ctx.feed_in(msg)
        if isinstance(msg, IoPipelineMessages.InitialInput):
            for m in self._msgs:
                ctx.feed_in(m)


class _CaptureOutbound(IoPipelineHandler):
    """Outside a relay end: keeps the typed messages it feeds outbound, which no byte transport could carry."""

    def __init__(self) -> None:
        super().__init__()

        self.messages: ta.List[ta.Any] = []

    def outbound(self, ctx: IoPipelineHandlerContext, msg: ta.Any) -> None:
        if isinstance(msg, _Typed):
            self.messages.append(msg)
            return
        ctx.feed_out(msg)


class _Joined:
    """Two peers joined through a relay on the memory host: peer1 <-> relay a | relay b <-> peer2."""

    def __init__(
            self,
            peer1: _PeerApp,
            peer2: _PeerApp,
            *,
            manual_peers: bool = False,
            link_capacity: ta.Optional[int] = None,
            config: ta.Optional[PureIoPipelineDriver.Config] = None,
            map_message: ta.Any = None,
            outer_a: ta.Sequence[IoPipelineHandler] = (),
            outer_b: ta.Sequence[IoPipelineHandler] = (),
    ) -> None:
        super().__init__()

        self.host = MemoryIoPipelineHost(link_capacity=link_capacity, driver_config=config)
        self.relay = IoPipelineRelay()
        self.end_a = self.relay.end('a', map_message=map_message)
        self.end_b = self.relay.end('b', map_message=map_message)
        p1, ra = self.host.pair()
        rb, p2 = self.host.pair()
        self.peer1 = self.host.adopt(p1, _peer_spec(peer1, manual_read=manual_peers))
        self.side_a = self.host.adopt(ra, IoPipeline.Spec(
            [*outer_a, self.end_a],
            services=[StubIoPipelineFlowService(auto_read=False)],
        ))
        self.side_b = self.host.adopt(rb, IoPipeline.Spec(
            [*outer_b, self.end_b],
            services=[StubIoPipelineFlowService(auto_read=False)],
        ))
        self.peer2 = self.host.adopt(p2, _peer_spec(peer2, manual_read=manual_peers))

    def end(self, side: str) -> IoPipelineRelayEndHandler:
        return self.end_a if side == 'a' else self.end_b

    def run(self) -> None:
        self.host.run()

    def close(self) -> None:
        self.host.close()


class TestRelay(unittest.TestCase):
    def test_large_transfers_both_ways_are_byte_exact(self) -> None:
        data1 = _payload('one', 300_000)
        data2 = _payload('two', 450_000)
        app1 = _PeerApp(send=data1, chunk_size=7000)
        app2 = _PeerApp(send=data2, chunk_size=9000)
        j = _Joined(
            app1,
            app2,
            link_capacity=10_000,
            config=PureIoPipelineDriver.Config(
                read_batch_max_bytes=8192,
                write_high_watermark=16_384,
                write_low_watermark=4096,
            ),
        )
        try:
            j.run()

            self.assertEqual(bytes(app1.received), data2)
            self.assertEqual(bytes(app2.received), data1)
            self.assertTrue(app1.saw_final_input)
            self.assertTrue(app2.saw_final_input)
            self.assertEqual(app1.errors, [])
            self.assertEqual(app2.errors, [])
            for handle in (j.peer1, j.side_a, j.side_b, j.peer2):
                self.assertIs(handle.state, IoPipelineDriverState.CLOSED)
            self.assertEqual(j.end('a').relayed_in, len(data1))
            self.assertEqual(j.end('b').relayed_out, len(data1))
            self.assertEqual(j.end('b').relayed_in, len(data2))
            self.assertEqual(j.end('a').relayed_out, len(data2))
            self.assertTrue(j.end('a').finished)
            self.assertTrue(j.end('b').finished)
        finally:
            j.close()

    def test_backpressure_crosses_the_relay(self) -> None:
        # Peer 2 reads nothing until allowed: relay b's output backs up to its watermark, pauses, and relay a stops
        # reading, so peer 1's output stays in peer 1's own queue and the link - never unbounded in the relay.
        data1 = _payload('one', 200_000)
        app1 = _PeerApp(send=data1, chunk_size=4096)
        app2 = _PeerApp(manual_read=True, allow_reads=0, shutdown_after_send=False)
        config = PureIoPipelineDriver.Config(
            read_batch_max_bytes=4096,
            write_high_watermark=8192,
            write_low_watermark=2048,
        )
        j = _Joined(app1, app2, manual_peers=True, link_capacity=4096, config=config)
        try:
            j.run()

            side_b = j.end('b')
            side_a = j.end('a')
            self.assertTrue(side_b.paused)
            self.assertTrue(side_a.awaiting_ack)
            self.assertEqual(app2.received, b'')
            # In flight: relay b's queued output (bounded by its watermark plus one batch) and one batch posted.
            self.assertLessEqual(
                ta.cast(MemoryHostedIoPipelineDriver, j.side_b).driver.pending_output_bytes,
                config.write_high_watermark + config.read_batch_max_bytes,
            )
            self.assertLess(side_a.relayed_in, len(data1))
            self.assertEqual(side_a.relayed_in, side_b.relayed_out)

            # Letting peer 2 read drains everything through.
            j.peer2.posting.post_context(
                ta.cast(IoPipeline, j.peer2.pipeline).handlers()[0],
                lambda ctx: app2.allow(ctx, 1_000_000),
            )
            j.run()
            self.assertEqual(bytes(app2.received), data1)
            self.assertFalse(side_b.paused)
            self.assertTrue(app2.saw_final_input)
        finally:
            j.close()

    def test_half_close_in_each_direction_and_both(self) -> None:
        for first in ('1', '2'):
            with self.subTest(first=first):
                # Neither peer closes on EOF: a half-close must leave the other direction open.
                app1 = _PeerApp(send=b'from one', shutdown_after_send=(first == '1'), close_on_final_input=False)
                app2 = _PeerApp(send=b'from two', shutdown_after_send=(first == '2'), close_on_final_input=False)
                j = _Joined(app1, app2)
                try:
                    j.run()
                    ended, open_ = (app2, app1) if first == '1' else (app1, app2)
                    self.assertTrue(ended.saw_final_input)
                    self.assertFalse(open_.saw_final_input)
                    self.assertEqual(bytes(app1.received), b'from two')
                    self.assertEqual(bytes(app2.received), b'from one')
                    self.assertFalse(j.end('a').finished)
                    self.assertFalse(j.end('b').finished)
                    self.assertIs(j.side_a.state, IoPipelineDriverState.RUNNING)
                    self.assertIs(j.side_b.state, IoPipelineDriverState.RUNNING)

                    # The side still open ends its output too: both directions have ended, both sides finish.
                    still_open = j.peer1 if first == '2' else j.peer2
                    still_open.posting.post_context(
                        ta.cast(IoPipeline, still_open.pipeline).handlers()[0],
                        lambda ctx: ctx.feed_shutdown_output(),
                    )
                    j.run()
                    self.assertTrue(app1.saw_final_input)
                    self.assertTrue(app2.saw_final_input)
                    self.assertTrue(j.end('a').finished)
                    self.assertTrue(j.end('b').finished)
                    for handle in (j.side_a, j.side_b):
                        self.assertIs(handle.state, IoPipelineDriverState.CLOSED)
                    self.assertEqual(app1.errors, [])
                    self.assertEqual(app2.errors, [])
                finally:
                    j.close()

    def test_abort_from_either_side(self) -> None:
        # A relay side closed abortively - its driver failed, say - takes the other side down with it; the peers see
        # their transports end.
        for aborting in ('a', 'b'):
            with self.subTest(aborting=aborting):
                app1 = _PeerApp(send=b'x' * 10_000, shutdown_after_send=False)
                app2 = _PeerApp(send=b'y' * 10_000, shutdown_after_send=False)
                j = _Joined(app1, app2)
                try:
                    j.run()
                    self.assertEqual(bytes(app2.received), b'x' * 10_000)
                    (j.side_a if aborting == 'a' else j.side_b).close()
                    j.run()

                    for handle in (j.side_a, j.side_b):
                        self.assertIs(handle.state, IoPipelineDriverState.CLOSED)
                    self.assertTrue(j.relay.aborted)
                    other = j.end('b' if aborting == 'a' else 'a')
                    self.assertTrue(other.aborted)
                    self.assertIsInstance(other.abort_cause, PeerGoneRelayIoPipelineError)
                    self.assertFalse(other.finished)
                    self.assertTrue(app1.saw_final_input)
                    self.assertTrue(app2.saw_final_input)
                finally:
                    j.close()

        # An error reported inside a side aborts both.
        app1 = _PeerApp(send=b'x', shutdown_after_send=False)
        app2 = _PeerApp(shutdown_after_send=False)
        error = RuntimeError('transport broke')
        j = _Joined(app1, app2, outer_a=[_Inject(IoPipelineMessages.Error(error))])
        try:
            j.run()
            self.assertTrue(j.relay.aborted)
            self.assertIs(j.end('a').abort_cause, error)
            self.assertIsInstance(j.end('b').abort_cause, RuntimeError)
            for handle in (j.side_a, j.side_b):
                self.assertIs(handle.state, IoPipelineDriverState.CLOSED)
        finally:
            j.close()

    def test_messages_are_mapped_or_rejected(self) -> None:
        # Typed messages reach a relay end from handlers ahead of it in its own pipeline - a decoder, a multiplexed
        # stream - never over a byte transport; mapped, they are fed outbound on the other side, in order with data.
        app1 = _PeerApp(send=b'data', shutdown_after_send=False)
        app2 = _PeerApp(shutdown_after_send=False)
        capture = _CaptureOutbound()
        j = _Joined(
            app1,
            app2,
            map_message=lambda m: _Typed(m.value * 10) if m.value != 2 else None,
            outer_a=[_Inject(_Typed(1), _Typed(2))],
            outer_b=[capture],
        )
        try:
            j.run()
            self.assertEqual(bytes(app2.received), b'data')
            self.assertEqual(capture.messages, [_Typed(10)])
            self.assertIs(j.side_a.state, IoPipelineDriverState.RUNNING)
            self.assertFalse(j.relay.aborted)
        finally:
            j.close()

        app1 = _PeerApp(shutdown_after_send=False)
        app2 = _PeerApp(shutdown_after_send=False)
        j = _Joined(app1, app2, outer_a=[_Inject(_Typed(1))])
        try:
            j.run()
            self.assertTrue(j.relay.aborted)
            self.assertIs(j.side_a.state, IoPipelineDriverState.CLOSED)
            self.assertIs(j.side_b.state, IoPipelineDriverState.CLOSED)
            self.assertIsInstance(j.end('a').abort_cause, UnmappedMessageRelayIoPipelineError)
        finally:
            j.close()

    def test_auto_read_is_refused(self) -> None:
        relay = IoPipelineRelay()
        with self.assertRaises(AutoReadRelayIoPipelineError):
            IoPipeline.new([relay.end('a')])
        relay = IoPipelineRelay()
        with self.assertRaises(AutoReadRelayIoPipelineError):
            IoPipeline.new([relay.end('b')], services=[StubIoPipelineFlowService(auto_read=True)])
        # The spec helper installs manual flow; a driven pipeline is still required for posting.
        relay = IoPipelineRelay()
        spec = relay.spec('a')
        self.assertFalse(ta.cast(ta.Any, next(iter(spec.services))).is_auto_read())

    def test_finished_relay_is_released_without_cyclic_gc(self) -> None:
        was_enabled = gc.isenabled()
        gc.disable()
        try:
            refs = self._run_and_release()
            self.assertEqual([r() for r in refs], [None] * len(refs))
        finally:
            if was_enabled:
                gc.enable()

    def _run_and_release(self) -> ta.List[ta.Any]:
        app1 = _PeerApp(send=b'a' * 1000)
        app2 = _PeerApp(send=b'b' * 1000)
        j = _Joined(app1, app2)
        j.run()
        refs = [weakref.ref(x) for x in (
            j.relay,
            j.end('a'),
            j.end('b'),
            ta.cast(MemoryHostedIoPipelineDriver, j.side_a).driver,
            ta.cast(MemoryHostedIoPipelineDriver, j.side_b).driver,
            ta.cast(IoPipeline, j.side_a.pipeline),
        )]
        j.close()
        return refs

    def test_relay_to_a_multiplexed_stream_under_credit(self) -> None:
        # Transport side: peer 1 on the memory host, relayed into a multiplexed stream's child whose send credit the
        # stream's peer (the loopback harness) controls.
        host = MemoryIoPipelineHost(driver_config=PureIoPipelineDriver.Config(read_batch_max_bytes=1000))
        data = _payload('mux', 20_000)
        app1 = _PeerApp(send=data, chunk_size=1000, shutdown_after_send=True)
        relay = IoPipelineRelay()
        p1, ra = host.pair()
        peer1 = host.adopt(p1, _peer_spec(app1))
        side_a = host.adopt(ra, relay.spec('a'))

        h = LoopbackHarness(
            lambda o: relay.spec('b'),
            adapter=LoopbackAdapter(recv_window=1 << 20, local_send_credit=0),
            config=IoPipelineMultiplexConfig(child=IoPipelineMultiplexChildConfig(
                write_high_watermark=4000,
                write_low_watermark=1000,
            )),
        )
        try:
            h.feed(LOpen('k', credit=2500))

            def pump() -> None:
                for _ in range(10_000):
                    progressed = host.step()
                    before = len(h.frames)
                    h.step()
                    progressed |= len(h.frames) != before
                    if not progressed:
                        return
                raise RuntimeError('did not quiesce')

            pump()
            # Only the credit's worth crossed; the child's output backed up past its watermark, pausing it, and the
            # relay's reading side stopped once the batch in flight went unacknowledged.
            self.assertEqual(len(data_of(h.frames, 'k')), 2500)
            end_a = ta.cast(IoPipelineRelayEndHandler, ta.cast(IoPipeline, side_a.pipeline).handlers()[0].handler)  # noqa
            end_b = ta.cast(IoPipelineRelayEndHandler, h.app('k'))
            self.assertTrue(end_b.paused)
            self.assertTrue(end_a.awaiting_ack)
            self.assertLess(end_a.relayed_in, len(data))
            self.assertLessEqual(end_a.relayed_in, 2500 + 4000 + 1000)

            h.feed(LGrant('k', 1 << 20))
            pump()
            self.assertEqual(data_of(h.frames, 'k'), data)
            self.assertFalse(end_b.paused)
            self.assertFalse(end_a.awaiting_ack)
            self.assertEqual(end_a.relayed_in, len(data))
            self.assertIsNotNone(peer1)
        finally:
            h.close()
            host.close()


class TestPortForwarder(unittest.TestCase):
    def test_forwards_on_the_memory_host(self) -> None:
        host = MemoryIoPipelineHost()
        try:
            targets: ta.List[_PeerApp] = []

            def target_spec(info: ta.Any) -> IoPipeline.Spec:
                app = _PeerApp(send=b'welcome', shutdown_after_send=False)
                targets.append(app)
                return _peer_spec(app)

            target = host.listen(TcpSocketEndpoint('127.0.0.1', 0), target_spec)
            forwarder = IoPipelinePortForwarder(host, TcpSocketEndpoint('127.0.0.1', 0), target.bound_endpoint)

            client = _PeerApp(send=b'hello there', shutdown_after_send=True)
            connected: ta.List[IoPipelineHostedDriver] = []
            host.connect(
                forwarder.bound_endpoint,
                lambda info: _peer_spec(client),
                on_connected=lambda c, h: connected.append(h),
                on_failed=lambda c, e: self.fail(repr(e)),
            )
            host.run()

            self.assertEqual(len(targets), 1)
            self.assertEqual(bytes(targets[0].received), b'hello there')
            self.assertTrue(targets[0].saw_final_input)
            self.assertEqual(bytes(client.received), b'welcome')
            self.assertEqual(forwarder.failures, [])
            forwarder.close()
        finally:
            host.close()
