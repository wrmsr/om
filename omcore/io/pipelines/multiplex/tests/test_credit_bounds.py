# ruff: noqa: SLF001 UP006 UP007 UP045 UP037
# @om-lite
import dataclasses as dc
import unittest

from ...core import IoPipelineHandler
from ...core import IoPipelineMessages
from ...flow.types import IoPipelineFlowMessages
from ..credit import ConnectionMultiplexCreditStrategy
from ..credit import StreamMultiplexCreditStrategy
from .apps import AppFactory
from .apps import Emit
from .apps import StreamApp
from .loopback import LBatch
from .loopback import LClose
from .loopback import LData
from .loopback import LGoodbye
from .loopback import LGrant
from .loopback import LMsg
from .loopback import LoopbackAdapter
from .loopback import LoopbackHarness
from .loopback import LOpen
from .loopback import LRefuse
from .loopback import LReset
from .loopback import data_of
from .loopback import of_type


@dc.dataclass(frozen=True)
class _Ext:
    data: bytes


class TestSplitMessageStall(unittest.TestCase):
    def test_split_message_with_ample_credit_is_fully_emitted(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp(close_on_final_input=False)),
            adapter=LoopbackAdapter(
                cost=lambda m: len(m.data) if isinstance(m, _Ext) else 0,
                split=lambda m, n: (_Ext(m.data[:n]), _Ext(m.data[n:])),
                max_unit=4,
            ),
            credit=StreamMultiplexCreditStrategy(),
        )
        try:
            h.feed(LOpen('k', credit=1000))
            fo = IoPipelineFlowMessages.FlushOutput()
            h.feed_stream('k', Emit(_Ext(b'0123456789abcdefghij'), 'after', fo))
            for _ in range(5):
                h.step()
            # The child's flush behind the message can never complete while the tail is stuck.
            self.assertTrue(fo.is_done(), 'child FlushOutput still pending')
            msgs = [f.msg for f in of_type(h.frames, LMsg)]
            # Credit (1000) is ample: all five 4-byte parts and the following message should go out now.
            self.assertEqual(msgs, [
                _Ext(b'0123'), _Ext(b'4567'), _Ext(b'89ab'), _Ext(b'cdef'), _Ext(b'ghij'), 'after',
            ])
        finally:
            h.close()


class _LateDataAdapter(LoopbackAdapter):
    """
    Absorbs data for streams already released - frames which crossed the reset on the wire - counting it against the
    connection window. Data for streams reset but not yet released goes to the core as usual.
    """

    def inbound(self, conn, msg):
        if isinstance(msg, LData) and conn.get(msg.key) is None:
            conn.discard(len(msg.data))
            return True
        return super().inbound(conn, msg)


class TestConnectionCreditLateData(unittest.TestCase):
    def test_data_crossing_a_local_reset_still_counts_against_the_connection_window(self) -> None:
        credit = ConnectionMultiplexCreditStrategy(send_credit=1 << 30, recv_window=100)
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp(close_on_final_input=False)),
            adapter=_LateDataAdapter(recv_window=1000, on_finish='reset'),
            credit=credit,
        )
        try:
            h.feed(LOpen('a'), LOpen('b'))
            # The local side finishes 'a' early; the adapter resets it since the peer has not ended.
            h.feed_stream('a', Emit(IoPipelineMessages.FinalOutput))
            self.assertEqual(len(of_type(h.frames, LReset, 'a')), 1)

            # The peer, which had not yet seen the reset, had 60 bytes in flight on 'a': its connection window (100)
            # is debited by them. It then spends the remaining 40 on 'b'.
            peer_window = 100
            h.feed(LData('a', b'x' * 60))
            peer_window -= 60
            h.feed(LData('b', b'y' * 40))
            peer_window -= 40
            self.assertEqual(peer_window, 0)

            # The peer can send nothing more until the connection window is replenished. Everything it sent has
            # arrived (and, in 'receive' mode, is freed on arrival), so a connection grant must have been sent.
            conn_grants = [f.n for f in of_type(h.frames, LGrant) if f.key is None]
            self.assertGreater(sum(conn_grants), 0, 'connection window never replenished: the peer is stalled')
        finally:
            h.close()


class TestRefusalCounters(unittest.TestCase):
    def test_child_construction_failure_is_counted_as_a_refusal(self) -> None:
        class FailsOnAdd(StreamApp):
            def notify(self, ctx, no):
                raise RuntimeError('boom')

        h = LoopbackHarness(AppFactory(lambda o: FailsOnAdd()))
        try:
            h.feed(LOpen('k'))
            self.assertEqual(len(of_type(h.frames, LRefuse, 'k')), 1)  # the peer is told it was refused
            st = h.mux.streams.stats
            # ... but the counters a protocol uses for its defenses record a locally reset (and opened) stream.
            self.assertEqual((st.refused_remote, st.reset_local), (1, 0))
        finally:
            h.close()


class TestGrantsAfterRemoteClose(unittest.TestCase):
    def test_no_credit_grant_for_a_stream_the_peer_closed(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp(close_on_final_input=False)),
            adapter=LoopbackAdapter(recv_window=10),
        )
        try:
            h.feed(LOpen('k'))
            before = len(h.frames)
            # One read: data, then the peer's close. The close is graceful - the child still gets the data - but the
            # peer "will neither send nor receive more" on the stream.
            h.feed(LBatch([LData('k', b'12345678'), LClose('k')]))
            self.assertEqual(bytes(h.app('k').received), b'12345678')
            late = of_type(h.frames[before:], LGrant, 'k')
            self.assertEqual(late, [], 'credit granted on a stream the peer already closed')
        finally:
            h.close()

    def test_sshlike_window_adjust_follows_close(self) -> None:
        from .sshlike import SshClose
        from .sshlike import SshData
        from .sshlike import SshLikeAdapter
        from .sshlike import SshOpen
        from .sshlike import SshWindowAdjust

        # A channel app reading in manual mode, which has not yet asked for input.
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp(close_on_final_input=False), auto_read=False),
            adapter=SshLikeAdapter(window=10, max_packet=100),  # type: ignore[arg-type]
        )
        try:
            h.feed(SshOpen('session', 7, 1000, 100, b''))
            (key,) = list(h.mux._children)
            assert isinstance(key, int)
            h.feed(SshData(key, b'12345678'))
            h.feed(SshClose(key))  # the adapter answers with its own CLOSE at once
            h.feed_stream(key, Emit(IoPipelineFlowMessages.ReadyForInput()))  # the app now reads what was queued
            self.assertEqual(bytes(h.app(key).received), b'12345678')
            kinds = [type(f).__name__ for f in h.frames if isinstance(f, (SshClose, SshWindowAdjust))]
            # RFC 4254 5.3: after sending CHANNEL_CLOSE a party MUST NOT send any more messages on the channel.
            self.assertEqual(kinds, ['SshClose'])
        finally:
            h.close()


class TestStaleReadinessSplit(unittest.TestCase):
    def test_stream_made_unsendable_by_shared_connection_credit_does_not_fail_the_connection(self) -> None:
        split_calls = []

        def split(m, n):
            split_calls.append(n)
            return (_Ext(m.data[:n]), _Ext(m.data[n:]))

        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp(close_on_final_input=False)),
            adapter=LoopbackAdapter(cost=lambda m: len(m.data) if isinstance(m, _Ext) else 0, split=split),
            credit=ConnectionMultiplexCreditStrategy(send_credit=10, recv_window=1 << 30),
        )
        try:
            h.feed(LOpen('a'), LOpen('b'))
            # Both streams queue output while the parent is paused, so both are marked ready together.
            h.enqueue(IoPipelineFlowMessages.PauseOutput())
            h.feed_stream('a', Emit(b'x' * 10))
            h.feed_stream('b', Emit(_Ext(b'hello')))
            h.enqueue(IoPipelineFlowMessages.ReadyForOutput())

            # 'a' spends the whole connection window; 'b' must then simply wait for connection credit.
            self.assertEqual(of_type(h.frames, LGoodbye), [])
            self.assertTrue(all(n > 0 for n in split_calls), f'split_message asked for a head costing {split_calls}')
            h.feed(LGrant(None, 100))
            self.assertEqual([f.msg for f in of_type(h.frames, LMsg, 'b')], [_Ext(b'hello')])
        finally:
            h.close()


class TestEmptyDataBound(unittest.TestCase):
    def test_zero_cost_empty_data_is_bounded_like_other_queued_input(self) -> None:
        h = LoopbackHarness(
            AppFactory(lambda o: StreamApp(close_on_final_input=False), auto_read=False),  # never reads
            adapter=LoopbackAdapter(recv_window=100),
        )
        try:
            h.feed(LOpen('k'))
            h.feed(LBatch([LData('k', b'') for _ in range(20_000)]))
            stream = h.mux.streams['k']
            # Flow-controlled input is bounded by the window (100) and uncontrolled messages by a count limit (1024);
            # empty data costs nothing and is counted by neither.
            self.assertLessEqual(stream.in_items, h.mux.config.max_stream_input_messages)
        finally:
            h.close()


class _ResetOnFirstData(IoPipelineHandler):
    """Outside the multiplexer: when it sees the first data frame of `trigger`, the peer's reset of `victim` arrives."""

    def __init__(self, trigger, victim):
        super().__init__()

        self._trigger = trigger
        self._victim = victim
        self._fired = False

    def outbound(self, ctx, msg):
        ctx.feed_out(msg)
        if not self._fired and isinstance(msg, LData) and msg.key == self._trigger:
            self._fired = True
            ctx.feed_in(LReset(self._victim, 'peer reset'))


class TestReentrantResetDuringEmission(unittest.TestCase):
    def test_stream_reset_reentrantly_while_ready_is_not_emitted(self) -> None:
        factory = AppFactory(lambda o: StreamApp(close_on_final_input=False))
        h = LoopbackHarness(factory, extra_outer=[_ResetOnFirstData('a', 'b')])
        try:
            h.feed(LOpen('a'), LOpen('b'))
            # Both streams queue output while the parent is paused, so both are ready when it resumes.
            h.enqueue(IoPipelineFlowMessages.PauseOutput())
            h.feed_stream('a', Emit(b'from a'))
            h.feed_stream('b', Emit(b'from b'))
            h.enqueue(IoPipelineFlowMessages.ReadyForOutput())

            self.assertEqual(of_type(h.frames, LGoodbye), [])
            self.assertEqual(data_of(h.frames, 'a'), b'from a')
            self.assertEqual(data_of(h.frames, 'b'), b'')
            self.assertEqual(len(factory.apps['b'].errors), 1)
        finally:
            h.close()

    def test_outer_handler_failure_during_emission_fails_the_connection_cleanly(self) -> None:
        class _FailsOnFirstData(IoPipelineHandler):
            fired = False

            def outbound(self, ctx, msg):
                if not self.fired and isinstance(msg, LData):
                    self.fired = True
                    raise RuntimeError('encoder failed')
                ctx.feed_out(msg)

        factory = AppFactory(lambda o: StreamApp(close_on_final_input=False))
        h = LoopbackHarness(factory, extra_outer=[_FailsOnFirstData()])
        try:
            h.feed(LOpen('a'), LOpen('b'))
            h.enqueue(IoPipelineFlowMessages.PauseOutput())
            h.feed_stream('a', Emit(b'from a'))
            h.feed_stream('b', Emit(b'from b'))
            h.enqueue(IoPipelineFlowMessages.ReadyForOutput())

            # The encoder's error reaches the multiplexer inbound and fails the connection: every stream is aborted.
            for k in ('a', 'b'):
                self.assertEqual(len(factory.apps[k].errors), 1)
            self.assertEqual(len(of_type(h.frames, LGoodbye)), 1)
        finally:
            h.close()
