# ruff: noqa: SLF001 UP006 UP007 UP045
# @om-lite
"""
Manual-read batching, the read-work yield policy, the sliced shutdown backlog, and read errors retained behind an
authenticated prefix. Real TLS 1.2 and 1.3 pairs cover the batching itself; scripted engines cover the rare engine
dependencies (WANT_READ on write, WANT_WRITE on read, errors at exact points) without a peer having to produce them.
"""
import collections
import random
import ssl
import typing as ta
import unittest

from ....streambufs.segmented import SegmentedByteStreamBufferView
from ....streambufs.utils import ByteStreamBuffers
from ...core import IoPipeline
from ...core import IoPipelineHandler
from ...core import IoPipelineHandlerNotifications
from ...core import IoPipelineMessages
from ...flow.stub import StubIoPipelineFlowService
from ...flow.types import IoPipelineFlowMessages
from ...yielding import CountingIoPipelineYieldPolicy
from ..handlers import SslIoPipelineHandler
from .test_halfclose import _App
from .test_halfclose import _cert
from .test_halfclose import _pure
from .test_halfclose import _PureLink
from .test_halfclose import _ssl_handlers
from .test_handlers import Ctx
from .test_handlers import app_bytes
from .test_handlers import make_pair


##


_RFI = IoPipelineFlowMessages.ReadyForInput
_FI = IoPipelineFlowMessages.FlushInput
_TLS_VERSIONS = [ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_3]


def _data_messages(ctx):
    return [msg for msg in ctx.app_msgs if ByteStreamBuffers.can_bytes(msg)]


def _count(msgs, cls):
    return sum(isinstance(msg, cls) for msg in msgs)


def _random_bytes(rng, n):
    return rng.getrandbits(n * 8).to_bytes(n, 'little')


def _real_receiver(config=None, *, version=ssl.TLSVersion.TLSv1_3):
    pair = make_pair(_cert(), server_auto=False, server_config=config, tls_version=version)
    ch, sh, cctx, sctx, ct, st = pair
    sh.inbound(sctx, IoPipelineMessages.InitialInput())
    ch.inbound(cctx, IoPipelineMessages.InitialInput())
    assert ch.state == sh.state == SslIoPipelineHandler.State.ESTABLISHED
    # From here input is admitted explicitly, so the tests can exercise several records per transport delivery or
    # one record split over arbitrarily many deliveries without the loopback transport coalescing anything for us.
    ct.peer = st.peer = None
    ct.wire_out.clear()
    st.wire_out.clear()
    cctx.app_msgs.clear()
    sctx.app_msgs.clear()
    return pair


def _wire(pair, *chunks):
    ch, _, cctx, _, ct, _ = pair
    ct.wire_out.clear()
    for chunk in chunks:
        ch.outbound(cctx, chunk)
    return b''.join(ByteStreamBuffers.to_bytes(m, strict=True) for m in ct.wire_out if ByteStreamBuffers.can_bytes(m))


class _ProbeCounter:
    """Wraps a real engine to count its reads and the WANT_READs among them."""

    def __init__(self, obj):
        self._obj = obj
        self.reads = 0
        self.want_reads = 0

    def read(self, size):
        self.reads += 1
        try:
            return self._obj.read(size)
        except ssl.SSLWantReadError:
            self.want_reads += 1
            raise

    def __getattr__(self, name):
        return getattr(self._obj, name)


##


class TestSslReadBatchesRealTls(unittest.TestCase):
    def test_manual_batch_combines_records_and_stops_without_demand(self):
        for version in _TLS_VERSIONS:
            with self.subTest(version=version):
                pair = _real_receiver(version=version)
                _, h, _, ctx, _, wire = pair
                data = bytes(range(256)) * 1024
                h.inbound(ctx, _wire(pair, data))
                self.assertFalse(_data_messages(ctx))
                wire.wire_out.clear()

                for batch in range(4):
                    before = len(_data_messages(ctx))
                    h.outbound(ctx, _RFI())
                    self.assertEqual(len(_data_messages(ctx)), before + 1)
                    msg = _data_messages(ctx)[-1]
                    self.assertIsInstance(msg, SegmentedByteStreamBufferView)
                    self.assertEqual(len(msg), 64 * 1024)
                    self.assertEqual(len(msg.segments()), 4)
                    self.assertEqual(_count(ctx.app_msgs, _FI), batch + 1)
                    self.assertEqual(app_bytes(ctx), data[:(batch + 1) * 64 * 1024])
                    # Duplicate transport boundaries and unrelated output-control events cannot deliver a second batch.
                    h.inbound(ctx, _FI())
                    h.inbound(ctx, IoPipelineFlowMessages.ReadyForOutput())
                    self.assertEqual(len(_data_messages(ctx)), before + 1)
                    self.assertEqual(_count(ctx.app_msgs, _FI), batch + 1)
                    self.assertEqual(_count(wire.wire_out, _RFI), 0)

    def test_exact_byte_limits_and_stable_emitted_views(self):
        for version in _TLS_VERSIONS:
            for limit, chunk_size in [(1, 65536), (17, 7), (20000, 65536), (65536, 4096), (262144, 65536)]:
                with self.subTest(version=version, limit=limit, chunk_size=chunk_size):
                    cfg = SslIoPipelineHandler.Config(
                        read_chunk_size=chunk_size,
                        read_batch_max_bytes=limit,
                        read_batch_max_chunks=128,
                        read_yield_policy=None,
                    )
                    pair = _real_receiver(cfg, version=version)
                    _, h, _, ctx, _, _ = pair
                    size = min(limit * 3 + 5, 400_001)
                    data = (bytes(range(251)) * (size // 251 + 1))[:size]
                    h.inbound(ctx, _wire(pair, data))
                    saved = []
                    while len(app_bytes(ctx)) < len(data):
                        h.outbound(ctx, _RFI())
                        msg = _data_messages(ctx)[-1]
                        self.assertTrue(0 < len(msg) <= limit)
                        self.assertLessEqual(len(msg.segments()), 128)
                        saved.append((msg, msg.tobytes()))
                    self.assertEqual(app_bytes(ctx), data)
                    for msg, expected in saved:
                        self.assertEqual(msg.tobytes(), expected)

    def test_drained_engine_ends_a_batch_without_a_probe(self):
        # OpenSSL takes one record at a time from the BIO, so once it and the current record are both empty the
        # handler records the WANT_READ a further read would report instead of paying for it. A partial record or a
        # transport EOF behind the data is still read for.
        for version in _TLS_VERSIONS:
            with self.subTest(version=version):
                pair = _real_receiver(version=version)
                _, h, _, ctx, _, transport = pair
                engine = _ProbeCounter(h._ssl_obj)
                h._ssl_obj = engine
                records = [bytes([i]) * 4000 for i in range(4)]
                data = b''.join(records)
                h.inbound(ctx, _wire(pair, *records))
                h.outbound(ctx, _RFI())
                self.assertEqual(app_bytes(ctx), data)
                self.assertEqual((engine.reads, engine.want_reads), (4, 0))
                self.assertEqual(_count(transport.wire_out, _RFI), 0)
                self.assertFalse(h._read_requested)

                engine.reads = engine.want_reads = 0
                first, second = _wire(pair, b'first'), _wire(pair, b'second')
                h.inbound(ctx, first + second[:-1])
                h.outbound(ctx, _RFI())
                self.assertEqual(app_bytes(ctx), data + b'first')
                self.assertEqual((engine.reads, engine.want_reads), (2, 1))
                h.inbound(ctx, second[-1:])
                h.outbound(ctx, _RFI())
                self.assertEqual(app_bytes(ctx), data + b'firstsecond')

                engine.reads = engine.want_reads = 0
                h.inbound(ctx, _wire(pair, b'last'))
                h.inbound(ctx, IoPipelineMessages.FinalInput())
                h.outbound(ctx, _RFI())
                self.assertEqual(app_bytes(ctx), data + b'firstsecondlast')
                self.assertEqual(_count(ctx.app_msgs, IoPipelineMessages.FinalInput), 1)
                self.assertEqual((engine.reads, engine.want_reads), (2, 0))

    def test_tiny_records_obey_fragment_limit_not_just_byte_limit(self):
        for version in _TLS_VERSIONS:
            with self.subTest(version=version):
                pair = _real_receiver(SslIoPipelineHandler.Config(read_batch_max_chunks=3), version=version)
                _, h, _, ctx, _, _ = pair
                h.inbound(ctx, _wire(pair, *(bytes([i]) for i in range(10))))
                sizes = []
                for _ in range(4):
                    h.outbound(ctx, _RFI())
                    msg = _data_messages(ctx)[-1]
                    sizes.append(len(msg))
                    self.assertLessEqual(len(msg.segments()), 3)
                self.assertEqual(sizes, [3, 3, 3, 1])
                self.assertEqual(app_bytes(ctx), bytes(range(10)))

    def test_short_batch_is_immediate_and_does_not_read_ahead(self):
        for version in _TLS_VERSIONS:
            with self.subTest(version=version):
                pair = _real_receiver(version=version)
                _, h, _, ctx, _, transport = pair
                h.inbound(ctx, _wire(pair, b'short request'))
                h.outbound(ctx, _RFI())
                self.assertEqual(app_bytes(ctx), b'short request')
                self.assertEqual(_count(ctx.app_msgs, _FI), 1)
                self.assertEqual(_count(transport.wire_out, _RFI), 0)
                # A genuinely new demand with no available plaintext DOES request a wire read, only once.
                h.outbound(ctx, _RFI())
                h.outbound(ctx, _RFI())
                h.inbound(ctx, _FI())
                self.assertEqual(_count(transport.wire_out, _RFI), 1)
                self.assertEqual(_count(ctx.app_msgs, _FI), 1)

    def test_partial_next_record_does_not_extend_satisfied_demand(self):
        for version in _TLS_VERSIONS:
            with self.subTest(version=version):
                pair = _real_receiver(version=version)
                _, h, _, ctx, _, transport = pair
                first = _wire(pair, b'first')
                second = _wire(pair, b'second')
                h.inbound(ctx, first + second[:-1])
                h.outbound(ctx, _RFI())
                self.assertEqual(app_bytes(ctx), b'first')
                self.assertEqual(_count(transport.wire_out, _RFI), 0)
                # Repeated demands coalesce while waiting for an incomplete record; no empty deliveries are generated.
                h.outbound(ctx, _RFI())
                h.outbound(ctx, _RFI())
                self.assertEqual(_count(transport.wire_out, _RFI), 1)
                h.inbound(ctx, second[-1:])
                h.inbound(ctx, _FI())
                self.assertEqual(app_bytes(ctx), b'firstsecond')
                self.assertEqual(len(_data_messages(ctx)), 2)
                self.assertEqual(_count(ctx.app_msgs, _FI), 2)
                self.assertFalse(h._read_requested)

    def test_fragmented_ciphertext_retains_demand_without_spinning(self):
        for version in _TLS_VERSIONS:
            with self.subTest(version=version):
                pair = _real_receiver(version=version)
                _, h, _, ctx, _, _ = pair
                data = _wire(pair, b'only one record')
                h.outbound(ctx, _RFI())
                for octet in data[:-1]:
                    h.inbound(ctx, bytes([octet]))
                    h.inbound(ctx, _FI())
                    self.assertFalse(_data_messages(ctx))
                    self.assertTrue(h._read_requested)
                h.inbound(ctx, data[-1:])
                h.inbound(ctx, _FI())
                self.assertEqual(app_bytes(ctx), b'only one record')
                self.assertEqual(_count(ctx.app_msgs, _FI), 1)

    def test_synchronous_reread_does_not_lose_credit_or_duplicate_completion(self):
        for version in _TLS_VERSIONS:
            for on_data in (False, True):
                with self.subTest(version=version, on_data=on_data):
                    pair = _real_receiver(version=version)
                    _, h, _, ctx, _, _ = pair
                    data = b'x' * (64 * 1024 * 4 + 3)
                    h.inbound(ctx, _wire(pair, data))

                    def on_app(msg):
                        if (
                                (ByteStreamBuffers.can_bytes(msg) if on_data else isinstance(msg, _FI)) and
                                len(app_bytes(ctx)) < len(data)
                        ):
                            h.outbound(ctx, _RFI())

                    ctx.on_app = on_app
                    h.outbound(ctx, _RFI())
                    self.assertEqual(app_bytes(ctx), data)
                    self.assertEqual([len(msg) for msg in _data_messages(ctx)], [65536, 65536, 65536, 65536, 3])
                    self.assertEqual(_count(ctx.app_msgs, _FI), 5)
                    self.assertFalse(h._read_requested)

    def test_paused_write_queue_cannot_turn_batch_probe_into_wire_read(self):
        for version in _TLS_VERSIONS:
            with self.subTest(version=version):
                pair = _real_receiver(version=version)
                _, h, _, ctx, _, transport = pair
                h.inbound(ctx, IoPipelineFlowMessages.PauseOutput())
                h.outbound(ctx, b'queued but not attempted')
                self.assertEqual(h.outbound_buffered_bytes(), len(b'queued but not attempted'))
                transport.wire_out.clear()
                h.inbound(ctx, _wire(pair, b'response'))
                h.outbound(ctx, _RFI())
                self.assertEqual(app_bytes(ctx), b'response')
                self.assertFalse(_count(transport.wire_out, _RFI))

    def test_reentrant_ciphertext_invalidates_stale_want_read(self):
        for version in _TLS_VERSIONS:
            with self.subTest(version=version):
                pair = _real_receiver(version=version)
                _, h, _, ctx, _, transport = pair
                first, second = _wire(pair, b'one'), _wire(pair, b'two')
                h.inbound(ctx, first)

                def on_app(msg):
                    if isinstance(msg, _FI) and app_bytes(ctx) == b'one':
                        h.inbound(ctx, second)
                        h.outbound(ctx, _RFI())

                ctx.on_app = on_app
                h.outbound(ctx, _RFI())
                self.assertEqual(app_bytes(ctx), b'onetwo')
                self.assertEqual(_count(transport.wire_out, _RFI), 0)
                self.assertEqual(_count(ctx.app_msgs, _FI), 2)

    def test_shutdown_backlog_slices_are_bounded_and_precede_final(self):
        for version in _TLS_VERSIONS:
            with self.subTest(version=version):
                cfg = SslIoPipelineHandler.Config(read_batch_max_bytes=7000, read_yield_policy=None)
                pair = _real_receiver(cfg, version=version)
                ch, h, cctx, ctx, _, transport = pair
                data = b'payload' * 14000
                wire = _wire(pair, data, IoPipelineMessages.ShutdownOutput())
                h.inbound(ctx, wire)
                # Closing has to save the unread input before unwrap; it cannot deliver it without demand.
                final = IoPipelineMessages.FinalOutput()
                h.outbound(ctx, final)
                self.assertFalse(_data_messages(ctx))
                self.assertEqual(h._plaintext_backlog_bytes, len(data))
                self.assertFalse(_count(transport.wire_out, IoPipelineMessages.FinalOutput))
                self.assertEqual(h.state, SslIoPipelineHandler.State.CLOSED)
                saved = []
                while len(app_bytes(ctx)) < len(data):
                    h.outbound(ctx, _RFI())
                    msg = _data_messages(ctx)[-1]
                    self.assertTrue(0 < len(msg) <= 7000)
                    saved.append((msg, msg.tobytes()))
                    self.assertEqual(h._plaintext_backlog_bytes, len(data) - len(app_bytes(ctx)))
                    if len(app_bytes(ctx)) < len(data):
                        self.assertFalse(_count(transport.wire_out, IoPipelineMessages.FinalOutput))
                self.assertEqual(app_bytes(ctx), data)
                self.assertEqual(_count(ctx.app_msgs, IoPipelineMessages.FinalInput), 1)
                self.assertEqual(_count(transport.wire_out, IoPipelineMessages.FinalOutput), 1)
                self.assertEqual(h._staged_plaintext_bytes, 0)
                for msg, value in saved:
                    self.assertEqual(msg.tobytes(), value)

    def test_real_bad_record_preserves_authenticated_prefix(self):
        for version in _TLS_VERSIONS:
            with self.subTest(version=version):
                pair = _real_receiver(SslIoPipelineHandler.Config(suppress_ragged_eofs=False), version=version)
                _, h, _, ctx, _, _ = pair
                first = _wire(pair, b'authenticated prefix')
                broken = bytearray(_wire(pair, b'must not be emitted'))
                broken[-1] ^= 1
                h.inbound(ctx, first + broken)
                with self.assertRaises(ssl.SSLError):
                    h.outbound(ctx, _RFI())
                self.assertEqual(app_bytes(ctx), b'authenticated prefix')
                self.assertEqual(_count(ctx.app_msgs, _FI), 1)
                self.assertFalse(_count(ctx.app_msgs, IoPipelineMessages.FinalInput))

    def test_transport_eof_never_suppresses_record_authentication_failure(self):
        for version in _TLS_VERSIONS:
            for strict in (False, True):
                with self.subTest(version=version, strict=strict):
                    pair = _real_receiver(
                        SslIoPipelineHandler.Config(suppress_ragged_eofs=not strict),
                        version=version,
                    )
                    _, h, _, ctx, _, _ = pair
                    first = _wire(pair, b'valid prefix')
                    bad = bytearray(_wire(pair, b'corrupted record'))
                    bad[-1] ^= 1
                    h.inbound(ctx, first + bad)
                    h.inbound(ctx, IoPipelineMessages.FinalInput())
                    with self.assertRaises(ssl.SSLError):
                        h.outbound(ctx, _RFI())
                    self.assertEqual(app_bytes(ctx), b'valid prefix')
                    self.assertFalse(_count(ctx.app_msgs, IoPipelineMessages.FinalInput))

    def test_seeded_fragmentation_manual_demand_and_transport_pauses(self):
        for seed in range(20):
            with self.subTest(seed=seed):
                rng = random.Random(seed)
                cap = rng.choice([31, 4000, 20000, 65536])
                chunks = rng.choice([1, 3, 8, 16])
                pair = _real_receiver(SslIoPipelineHandler.Config(
                    read_batch_max_bytes=cap,
                    read_batch_max_chunks=chunks,
                    read_yield_policy=None,
                ), version=_TLS_VERSIONS[seed % 2])
                _, h, _, ctx, _, transport = pair
                records = [_random_bytes(rng, rng.randint(1, 18000)) for _ in range(8)]
                data = b''.join(records)
                wire = _wire(pair, *records)
                received = bytearray()
                batches = []

                def on_app(msg):
                    if ByteStreamBuffers.can_bytes(msg):
                        batches.append(msg)
                        received.extend(msg.tobytes())

                ctx.on_app = on_app
                pos = 0
                reads = 0
                for _ in range(10000):
                    if pos >= len(wire) and len(received) >= len(data):
                        break
                    if not h._read_requested and (rng.randrange(3) or pos == len(wire)):
                        reads += 1
                        before = len(batches)
                        h.outbound(ctx, _RFI())
                        self.assertLessEqual(len(batches) - before, 1)
                    elif pos < len(wire):
                        count = rng.randint(1, 12000)
                        before = len(batches)
                        permitted = h._read_requested
                        h.inbound(ctx, wire[pos:pos + count])
                        pos = min(pos + count, len(wire))
                        h.inbound(ctx, _FI())
                        self.assertLessEqual(len(batches) - before, int(permitted))
                    if rng.randrange(5) == 0:
                        before = len(batches)
                        h.inbound(ctx, IoPipelineFlowMessages.PauseOutput())
                        h.inbound(ctx, IoPipelineFlowMessages.ReadyForOutput())
                        self.assertEqual(len(batches), before)
                    self.assertTrue(data.startswith(received))
                    self.assertLess(reads, len(data) + 10)
                else:
                    self.fail('fragmentation/demand test did not finish')
                self.assertEqual(bytes(received), data)
                self.assertEqual(_count(ctx.app_msgs, _FI), len(batches))
                self.assertTrue(all(0 < len(msg) <= cap and len(msg.segments()) <= chunks for msg in batches))


##
# Scripted engines exercise rare TLS dependencies without relying on a peer initiating renegotiation/KeyUpdate.


class _Engine:
    def __init__(self, reads=()):
        self.reads = collections.deque(reads)
        self.read_sizes = []
        self.write_args = []
        self.want_write_input = False
        self.unwrap_calls = 0
        self.out_bio: ta.Any = None
        self.emit_control_on_read = False

    def read(self, size):
        self.read_sizes.append(size)
        if self.emit_control_on_read:
            self.emit_control_on_read = False
            self.out_bio.write(b'control record')
            raise ssl.SSLWantWriteError
        if not self.reads:
            raise ssl.SSLWantReadError
        item = self.reads.popleft()
        if isinstance(item, BaseException):
            raise item
        if len(item) > size:
            self.reads.appendleft(item[size:])
            item = item[:size]
        return item

    def write(self, data):
        self.write_args.append(data)
        if self.want_write_input:
            raise ssl.SSLWantReadError
        return len(data)

    def pending(self):
        # The handler ends a batch without probing once the BIO and the current record are both empty. A real
        # engine's BIO holds whatever is scripted here, so report it all as pending, a scripted EOF or error too.
        return sum(max(len(item), 1) if isinstance(item, bytes) else 1 for item in self.reads)

    def unwrap(self):
        self.unwrap_calls += 1
        assert not any(isinstance(item, bytes) and item for item in self.reads)
        raise ssl.SSLWantReadError


class _DeferredCtx(Ctx):
    def __init__(self, handler, *, auto=False):
        super().__init__('scripted', StubIoPipelineFlowService(auto_read=auto))
        self.handler = handler
        self.deferred: ta.Deque[ta.Any] = collections.deque()
        self.wire_out: ta.List[ta.Any] = []
        self.trace: ta.List[ta.Any] = []
        self.max_deferred = 0

    def feed_in(self, msg):
        self.trace.append(('in', msg))
        super().feed_in(msg)

    def feed_out(self, msg):
        self.trace.append(('out', msg))
        self.wire_out.append(msg)

    def defer(self, fn):
        self.deferred.append(fn)
        self.max_deferred = max(self.max_deferred, len(self.deferred))

    def resume(self):
        self.deferred.popleft()(self)

    def drain(self):
        for _ in range(10000):
            if not self.deferred:
                return
            self.resume()
        raise AssertionError('continuation did not quiesce')


def _scripted(reads=(), config=None, *, auto=False):
    h = SslIoPipelineHandler(
        ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT),
        server_side=False,
        server_hostname='localhost',
        config=config,
    )
    h._ensure_state()
    h._state = SslIoPipelineHandler.State.ESTABLISHED
    engine = _Engine(reads)
    engine.out_bio = h._out_bio
    h._ssl_obj = engine  # type: ignore[assignment]
    return h, _DeferredCtx(h, auto=auto), engine


class TestSslReadBatchesScripted(unittest.TestCase):
    def test_actual_write_want_read_arms_input_without_application_demand(self):
        h, ctx, engine = _scripted()
        engine.want_write_input = True
        h.outbound(ctx, b'first')
        h.outbound(ctx, b'second')
        self.assertEqual(_count(ctx.wire_out, _RFI), 1)
        first_buffer = engine.write_args[0]
        self.assertTrue(all(item is first_buffer for item in engine.write_args))
        engine.want_write_input = False
        h.inbound(ctx, b'peer key update')
        self.assertIs(engine.write_args[-2], first_buffer)
        self.assertEqual(bytes(engine.write_args[-1]), b'second')
        self.assertFalse(h._write_q)

    def test_want_write_retains_control_ciphertext_before_plaintext(self):
        h, ctx, engine = _scripted([b'reply'])
        engine.emit_control_on_read = True
        h.outbound(ctx, _RFI())
        self.assertEqual(app_bytes(ctx), b'reply')
        out = [msg for msg in ctx.wire_out if ByteStreamBuffers.can_bytes(msg)]
        self.assertEqual(b''.join(msg.tobytes() for msg in out), b'control record')
        self.assertEqual(ctx.trace[0][0], 'out')
        self.assertEqual(_count(ctx.wire_out, IoPipelineFlowMessages.FlushOutput), 1)

    def test_yield_budget_spans_reentrant_batches_and_new_intake_waits_for_defer(self):
        h, ctx, engine = _scripted([b'a'] * 25, SslIoPipelineHandler.Config(
            read_batch_max_chunks=2,
            read_yield_policy=CountingIoPipelineYieldPolicy(5),
        ))

        def on_app(msg):
            if isinstance(msg, _FI):
                h.outbound(ctx, _RFI())

        ctx.on_app = on_app
        h.outbound(ctx, _RFI())
        self.assertEqual(len(engine.read_sizes), 5)
        self.assertEqual(app_bytes(ctx), b'a' * 5)
        self.assertEqual(len(ctx.deferred), 1)
        self.assertTrue(h._read_requested)
        for _ in range(10):
            h.inbound(ctx, _FI())
            h.outbound(ctx, _RFI())
            h.inbound(ctx, b'more admitted ciphertext')
        self.assertEqual(len(engine.read_sizes), 5)
        self.assertEqual(len(ctx.deferred), 1)
        ctx.drain()
        self.assertEqual(app_bytes(ctx), b'a' * 25)
        self.assertEqual(ctx.max_deferred, 1)
        self.assertEqual(_count(ctx.app_msgs, _FI), len(_data_messages(ctx)))
        self.assertEqual(_count(ctx.wire_out, _RFI), 1)

    def test_yield_counts_backlog_slices_and_does_not_create_read_demand(self):
        h, ctx, engine = _scripted(config=SslIoPipelineHandler.Config(
            read_chunk_size=3,
            read_yield_policy=CountingIoPipelineYieldPolicy(2),
        ))
        h._plaintext_backlog = collections.deque([memoryview(b'0123456789')])
        h._plaintext_backlog_bytes = 10
        h.outbound(ctx, _RFI())
        self.assertEqual(app_bytes(ctx), b'012345')
        self.assertEqual(h._plaintext_backlog_bytes, 4)
        self.assertEqual(len(ctx.deferred), 1)
        ctx.drain()
        self.assertEqual(app_bytes(ctx), b'012345')
        self.assertFalse(h._read_requested)
        h.outbound(ctx, _RFI())
        self.assertEqual(app_bytes(ctx), b'0123456789')
        ctx.drain()
        self.assertFalse(ctx.deferred)

    def test_yield_during_shutdown_drain_never_calls_unwrap_prematurely(self):
        h, ctx, engine = _scripted([b'x'] * 8, SslIoPipelineHandler.Config(
            read_yield_policy=CountingIoPipelineYieldPolicy(2),
        ))
        shutdown = IoPipelineMessages.ShutdownOutput()
        h.outbound(ctx, shutdown)
        self.assertEqual(engine.unwrap_calls, 0)
        self.assertEqual(h._plaintext_backlog_bytes, 2)
        self.assertFalse(_data_messages(ctx))
        ctx.drain()
        self.assertEqual(engine.unwrap_calls, 1)
        self.assertEqual(h._plaintext_backlog_bytes, 8)
        self.assertFalse(_data_messages(ctx))
        self.assertIn(shutdown, ctx.wire_out)

    def test_automatic_reads_yield_and_emit_short_completed_batches(self):
        h, ctx, engine = _scripted([b'x'] * 9, SslIoPipelineHandler.Config(
            read_yield_policy=CountingIoPipelineYieldPolicy(3),
        ), auto=True)
        h.inbound(ctx, b'ciphertext')
        self.assertEqual(app_bytes(ctx), b'xxx')
        self.assertEqual(_count(ctx.app_msgs, _FI), 1)
        ctx.drain()
        h.inbound(ctx, _FI())
        self.assertEqual(app_bytes(ctx), b'x' * 9)
        self.assertTrue(all(len(msg) <= 3 for msg in _data_messages(ctx)))
        self.assertEqual(_count(ctx.app_msgs, _FI), 3)

    def test_automatic_yield_keeps_transport_flush_for_the_continuation(self):
        # A real transport feeds its FlushInput right behind the bytes. Each yielded turn flushes the prefix it
        # delivered, and the continuation which finishes the batch must still flush the rest: with 8 chunks and a
        # budget of 3 the last continuation delivers 2 chunks without yielding.
        for n in (8, 9):
            with self.subTest(n=n):
                h, ctx, _ = _scripted([b'x'] * n, SslIoPipelineHandler.Config(
                    read_yield_policy=CountingIoPipelineYieldPolicy(3),
                ), auto=True)
                h.inbound(ctx, b'ciphertext')
                h.inbound(ctx, _FI())
                self.assertEqual(_count(ctx.app_msgs, _FI), 1)
                ctx.drain()
                self.assertEqual(app_bytes(ctx), b'x' * n)
                self.assertEqual(_count(ctx.app_msgs, _FI), len(_data_messages(ctx)))
                self.assertIsInstance(ctx.trace[-1][1], _FI)
                self.assertFalse(h._delivered_plaintext)
                self.assertFalse(h._flush_in_seen)

    def test_removal_with_pending_continuation_does_not_resume_engine(self):
        h, ctx, engine = _scripted([b'x'] * 10, SslIoPipelineHandler.Config(
            read_yield_policy=CountingIoPipelineYieldPolicy(2),
        ))
        h.outbound(ctx, _RFI())
        self.assertEqual(len(ctx.deferred), 1)
        h.notify(ctx, IoPipelineHandlerNotifications.Removed(ctx))
        calls = len(engine.read_sizes)
        ctx.drain()
        self.assertEqual(len(engine.read_sizes), calls)
        self.assertFalse(h._plaintext_backlog)
        self.assertEqual(h._staged_plaintext_bytes, 0)

    def test_final_output_cannot_overtake_last_staged_backlog_batch(self):
        h, ctx, engine = _scripted()
        h._state = SslIoPipelineHandler.State.CLOSED
        h._plaintext_eof = True
        h._plaintext_backlog = collections.deque([memoryview(b'last data')])
        h._plaintext_backlog_bytes = len(b'last data')
        final = IoPipelineMessages.FinalOutput()
        h.outbound(ctx, final)
        self.assertNotIn(final, ctx.wire_out)
        h.outbound(ctx, _RFI())
        self.assertEqual([type(msg) for _, msg in ctx.trace], [
            SegmentedByteStreamBufferView, IoPipelineMessages.FinalInput, _FI, IoPipelineMessages.FinalOutput,
        ])
        self.assertEqual(h._plaintext_backlog_bytes, 0)
        self.assertEqual(h._staged_plaintext_bytes, 0)

    def test_error_after_authenticated_prefix_is_not_early_or_clean_eof(self):
        exc = ssl.SSLError('bad record authentication')
        h, ctx, engine = _scripted([b'good', b' prefix', exc])
        with self.assertRaises(ssl.SSLError) as caught:
            h.outbound(ctx, _RFI())
        self.assertIs(caught.exception, exc)
        self.assertEqual(app_bytes(ctx), b'good prefix')
        self.assertEqual(_count(ctx.app_msgs, _FI), 1)
        self.assertFalse(_count(ctx.app_msgs, IoPipelineMessages.FinalInput))
        self.assertEqual(h.state, SslIoPipelineHandler.State.CLOSED)
        calls = len(engine.read_sizes)
        h.outbound(ctx, _RFI())
        self.assertEqual(len(engine.read_sizes), calls)

    def test_shutdown_error_preserves_backlog_under_demand_and_fails_fences(self):
        exc = ssl.SSLError('bad record')
        h, ctx, engine = _scripted([b'1234567890', exc], SslIoPipelineHandler.Config(read_batch_max_bytes=4))
        shutdown = IoPipelineMessages.ShutdownOutput()
        final = IoPipelineMessages.FinalOutput()
        h.outbound(ctx, shutdown)
        self.assertTrue(shutdown.is_failed())
        self.assertFalse(_data_messages(ctx))
        self.assertEqual(h._plaintext_backlog_bytes, 10)
        h.outbound(ctx, final)
        self.assertNotIn(final, ctx.wire_out)
        for expected in [b'1234', b'12345678']:
            h.outbound(ctx, _RFI())
            self.assertEqual(app_bytes(ctx), expected)
        with self.assertRaises(ssl.SSLError) as caught:
            h.outbound(ctx, _RFI())
        self.assertIs(caught.exception, exc)
        self.assertEqual(app_bytes(ctx), b'1234567890')
        self.assertIn(final, ctx.wire_out)
        self.assertFalse(_count(ctx.app_msgs, IoPipelineMessages.FinalInput))

    def test_legacy_generic_unexpected_eof_error_is_still_suppressible(self):
        exc = ssl.SSLError('unexpected eof')
        exc.reason = 'UNEXPECTED_EOF_WHILE_READING'
        h, ctx, _ = _scripted([b'prefix', exc])
        h._transport_eof = True
        h.outbound(ctx, _RFI())
        self.assertEqual(app_bytes(ctx), b'prefix')
        self.assertEqual(_count(ctx.app_msgs, IoPipelineMessages.FinalInput), 1)

    def test_no_flow_service_still_delivers_automatically(self):
        h, ctx, _ = _scripted([b'a', b'b'])
        ctx.services._flow = None
        h.inbound(ctx, b'ciphertext')
        self.assertEqual(app_bytes(ctx), b'ab')
        self.assertFalse(_count(ctx.wire_out, _RFI))

    def test_removal_during_plaintext_callback_does_not_emit_more_notifications(self):
        h, ctx, _ = _scripted([b'prefix', b''])

        def on_app(msg):
            if ByteStreamBuffers.can_bytes(msg):
                h.notify(ctx, IoPipelineHandlerNotifications.Removed(ctx))

        ctx.on_app = on_app
        h.outbound(ctx, _RFI())
        self.assertEqual(app_bytes(ctx), b'prefix')
        self.assertEqual(len(ctx.app_msgs), 1)
        self.assertFalse(ctx.deferred)

    def test_staged_plaintext_is_included_in_buffer_accounting_during_ciphertext_callback(self):
        h, ctx, engine = _scripted([b'prefix'])
        engine.emit_control_on_read = True
        original_feed = ctx.feed_out
        observed = []

        def feed(msg):
            if ByteStreamBuffers.can_bytes(msg):
                observed.append(h.inbound_buffered_bytes())
            original_feed(msg)

        ctx.feed_out = feed
        h.outbound(ctx, _RFI())
        self.assertEqual(observed, [len(b'prefix')])
        self.assertEqual(h.inbound_buffered_bytes(), 0)

    def test_starved_app_read_cannot_consume_every_shutdown_turn(self):
        h, ctx, engine = _scripted(config=SslIoPipelineHandler.Config(
            read_yield_policy=CountingIoPipelineYieldPolicy(1),
        ))
        h._read_requested = True
        h.outbound(ctx, IoPipelineMessages.ShutdownOutput())
        ctx.drain()
        self.assertEqual(engine.unwrap_calls, 1)
        self.assertLessEqual(len(engine.read_sizes), 2)
        self.assertTrue(h._shutdown_output_sent)
        self.assertTrue(h._read_requested)
        self.assertEqual(_count(ctx.wire_out, _RFI), 1)


##


class TestSslReadBatchesConfig(unittest.TestCase):
    def test_read_limit_validation(self):
        for name in ('read_chunk_size', 'read_batch_max_bytes', 'read_batch_max_chunks'):
            for value in (0, -1, True, 1.5):
                with self.subTest(name=name, value=value):
                    kwargs: ta.Dict[str, ta.Any] = {name: value}
                    with self.assertRaises(ValueError):
                        SslIoPipelineHandler.Config(**kwargs)

    def test_caller_ssl_context_configuration_is_preserved(self):
        option = getattr(ssl, 'OP_IGNORE_UNEXPECTED_EOF', None)
        if option is None:
            self.skipTest('SSL library does not expose OP_IGNORE_UNEXPECTED_EOF')
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.options |= option
        cfg = SslIoPipelineHandler.Config(suppress_ragged_eofs=False)
        with self.assertRaises(SslIoPipelineHandler.SslConfigurationError):
            SslIoPipelineHandler(context, server_side=False, config=cfg)
        self.assertTrue(context.options & option)
        self.assertIs(SslIoPipelineHandler.configure_ssl_context(context, cfg), context)
        h = SslIoPipelineHandler(context, server_side=False, config=cfg)
        self.assertIs(h._ssl_ctx, context)
        self.assertFalse(context.options & option)


##


class TestSslReadBatchesPipelines(unittest.TestCase):
    def test_real_pure_driver_manual_round_trip_with_fairness_and_half_close(self):
        for version in _TLS_VERSIONS:
            for budget in (1, 3, 17):
                with self.subTest(version=version, budget=budget):
                    cfg = SslIoPipelineHandler.Config(
                        read_batch_max_bytes=20000,
                        read_yield_policy=CountingIoPipelineYieldPolicy(budget),
                    )
                    client_ssl, server_ssl = _ssl_handlers(
                        max_version=version,
                        client_config=cfg,
                        server_config=cfg,
                    )
                    request, response = b'abc' * 33001, b'defg' * 70001
                    ca = _App(send_on_start=request, manual_read=True)
                    sa = _App(respond=response, manual_read=True)
                    client = _pure(client_ssl, ca, manual_read=True)
                    server = _pure(server_ssl, sa, manual_read=True)
                    try:
                        _PureLink(client, server).pump()
                        self.assertEqual(bytes(sa.received), request)
                        self.assertEqual(bytes(ca.received), response)
                        for app in (ca, sa):
                            self.assertEqual(app.errors, [])
                            self.assertTrue(app.saw_final_input)
                            self.assertTrue(app.shutdown_output.is_succeeded())
                            self.assertTrue(app.final_output.is_succeeded())
                    finally:
                        client.close()
                        server.close()

    def test_real_pipeline_abort_fails_defer_and_releases_buffered_plaintext(self):
        h, _, engine = _scripted([b'x'] * 10, SslIoPipelineHandler.Config(
            read_yield_policy=CountingIoPipelineYieldPolicy(2),
        ))

        class ReadApp(IoPipelineHandler):
            def inbound(self, ctx, msg):
                if msg == 'read':
                    ctx.feed_out(_RFI())
                    return
                if ByteStreamBuffers.can_bytes(msg) or isinstance(msg, _FI):
                    return
                ctx.feed_in(msg)

        pipeline = IoPipeline.new([h, ReadApp()], services=[StubIoPipelineFlowService(auto_read=False)])
        pipeline.feed_in('read')
        self.assertEqual(len(engine.read_sizes), 2)
        pending = pipeline.output.drain()
        deferred = [msg for msg in pending if isinstance(msg, IoPipelineMessages.Defer)]
        self.assertEqual(len(deferred), 1)
        pipeline.destroy()
        self.assertTrue(deferred[0].is_failed())
        self.assertEqual(h.state, SslIoPipelineHandler.State.CLOSED)
        self.assertEqual(h._plaintext_backlog_bytes, 0)
        self.assertEqual(h._staged_plaintext_bytes, 0)

    def test_backlog_after_final_output_is_served_without_yielding(self):
        # A shutdown timeout releases the close with a preserved backlog still behind it. Nothing may follow that
        # FinalOutput at the terminal, a continuation's Defer included, so an app reading the backlog synchronously
        # past the whole read budget must be served without a yield rather than wedged behind one that cannot run.
        h, _, _ = _scripted([], SslIoPipelineHandler.Config(read_batch_max_chunks=16))
        received = bytearray()
        errors: ta.List[ta.Any] = []
        finals: ta.List[ta.Any] = []

        class ReadApp(IoPipelineHandler):
            def inbound(self, ctx, msg):
                if msg == 'read':
                    ctx.feed_out(_RFI())
                    return
                if ByteStreamBuffers.can_bytes(msg):
                    received.extend(msg.tobytes())
                    ctx.feed_out(_RFI())
                    return
                if isinstance(msg, IoPipelineMessages.Error):
                    errors.append(msg)
                    return
                if isinstance(msg, IoPipelineMessages.FinalInput):
                    finals.append(msg)
                if isinstance(msg, _FI):
                    return
                ctx.feed_in(msg)

        pipeline = IoPipeline.new([h, ReadApp()], services=[StubIoPipelineFlowService(auto_read=False)])
        ref = pipeline.handlers()[0]
        self.assertIs(ref.handler, h)
        ctx = ref._context
        data = bytes(i % 256 for i in range(300))
        h._state = SslIoPipelineHandler.State.CLOSED
        h._close_requested = True
        h._plaintext_eof = True
        h._plaintext_backlog = collections.deque(memoryview(data[i:i + 1]) for i in range(len(data)))
        h._plaintext_backlog_bytes = len(data)
        with pipeline.enter():
            h._send_final_output(ctx, IoPipelineMessages.FinalOutput())
        self.assertTrue(pipeline.saw_final_output)

        pipeline.feed_in('read')

        self.assertEqual(bytes(received), data)
        self.assertEqual(errors, [])
        self.assertFalse(h._continuation_pending)
        self.assertEqual(h._plaintext_backlog_bytes, 0)
        self.assertEqual(len(finals), 1)
        self.assertFalse([msg for msg in pipeline.output.drain() if isinstance(msg, IoPipelineMessages.Defer)])
