# ruff: noqa: UP006 UP007 UP045 UP037
# @om-lite
import random
import typing as ta
import unittest

from ..credit import ConnectionMultiplexCreditStrategy
from ..credit import HalfWindowMultiplexCreditReplenishPolicy
from ..credit import ImmediateMultiplexCreditReplenishPolicy
from ..credit import MultiplexCreditGrant
from ..credit import MultiplexCreditStrategy
from ..credit import StreamMultiplexCreditStrategy
from ..types import FlowControlMultiplexError
from ..types import UnknownStreamMultiplexError


##


class _Model:
    """Tracks, outside the strategy, what conservation demands of it."""

    def __init__(self) -> None:
        self.windows: ta.Dict[int, int] = {}
        self.queued: ta.Dict[int, int] = {}


def _strategies() -> ta.Sequence[ta.Tuple[str, ta.Callable[[], MultiplexCreditStrategy]]]:
    return [
        ('stream', lambda: StreamMultiplexCreditStrategy()),
        ('connection-receive', lambda: ConnectionMultiplexCreditStrategy(send_credit=5000, recv_window=4000)),
        (
            'connection-consume',
            lambda: ConnectionMultiplexCreditStrategy(
                send_credit=5000,
                recv_window=4000,
                connection_replenish_on='consume',
            ),
        ),
    ]


class TestMultiplexCreditConservation(unittest.TestCase):
    """The same property suite against every strategy: granted == consumed + available, both directions."""

    def _check_invariants(self, cs: MultiplexCreditStrategy, model: _Model, *, connection: bool) -> None:
        for key, window in model.windows.items():
            t = cs.totals(key)
            self.assertEqual(t.send_granted, t.send_consumed + t.send_available)
            self.assertEqual(t.recv_advertised, t.recv_received + t.recv_outstanding)
            self.assertEqual(cs.recv_queued(key), model.queued[key])
            # Credit never advertised beyond the window: outstanding + queued + unadvertised == window.
            self.assertLessEqual(t.recv_outstanding + model.queued[key], window)
            self.assertGreaterEqual(t.recv_outstanding, 0)

        if connection:
            t = cs.totals()
            self.assertEqual(t.send_granted, t.send_consumed + t.send_available)
            self.assertEqual(t.recv_advertised, t.recv_received + t.recv_outstanding)
            self.assertGreaterEqual(t.recv_outstanding, 0)
            self.assertLessEqual(t.recv_outstanding, 4000)

    def test_random_operation_sequences(self) -> None:
        for name, factory in _strategies():
            connection = name != 'stream'
            for seed in range(25):
                with self.subTest(strategy=name, seed=seed):
                    rnd = random.Random(seed)
                    cs = factory()
                    model = _Model()
                    next_key = 0

                    for _ in range(300):
                        op = rnd.choice([
                            'add', 'remove', 'send', 'grant', 'adjust', 'conn_grant', 'receive', 'overrun', 'consume',
                        ])
                        keys = list(model.windows)

                        if op == 'add' or not keys:
                            window = rnd.choice([0, 1, 100, 1000])
                            cs.add_stream(next_key, send_credit=rnd.randint(-50, 500), recv_window=window)
                            model.windows[next_key] = window
                            model.queued[next_key] = 0
                            next_key += 1

                        elif op == 'remove':
                            key = rnd.choice(keys)
                            cs.remove_stream(key)
                            del model.windows[key]
                            del model.queued[key]
                            self.assertFalse(cs.has_stream(key))
                            for g in cs.pending_grants():
                                self.assertIsNone(g.key)
                                self.assertGreater(g.amount, 0)

                        elif op == 'send':
                            key = rnd.choice(keys)
                            if (avail := cs.send_available(key)) > 0:
                                cs.consume_send(key, rnd.randint(0, avail))
                            else:
                                with self.assertRaises(Exception):  # noqa
                                    cs.consume_send(key, 1)

                        elif op == 'grant':
                            cs.grant_send(rnd.choice(keys), rnd.randint(-100, 300))

                        elif op == 'adjust':
                            cs.adjust_all_send(rnd.randint(-200, 200))

                        elif op == 'conn_grant':
                            if connection:
                                cs.grant_send(None, rnd.randint(-100, 1000))
                            else:
                                with self.assertRaises(TypeError):
                                    cs.grant_send(None, 1)

                        elif op in ('receive', 'overrun'):
                            key = rnd.choice(keys)
                            outstanding = cs.totals(key).recv_outstanding
                            if connection:
                                outstanding = min(outstanding, cs.totals().recv_outstanding)
                            if op == 'receive':
                                cost = rnd.randint(0, outstanding)
                                grants = cs.receive(key, cost)
                                model.queued[key] += cost
                                for g in grants:
                                    self.assertIsNone(g.key)
                            else:
                                before = cs.totals(key)
                                with self.assertRaises(FlowControlMultiplexError):
                                    cs.receive(key, outstanding + 1)
                                self.assertEqual(cs.totals(key), before)

                        elif op == 'consume':
                            key = rnd.choice(keys)
                            if (q := model.queued[key]):
                                cost = rnd.randint(1, q)
                                for g in cs.consume_receive(key, cost):
                                    self.assertGreater(g.amount, 0)
                                    self.assertIn(g.key, (key, None))
                                model.queued[key] -= cost

                        self._check_invariants(cs, model, connection=connection)


class TestStreamMultiplexCreditStrategy(unittest.TestCase):
    def test_send_credit_exhaustion_negative_and_recovery(self) -> None:
        cs = StreamMultiplexCreditStrategy()
        cs.add_stream('a', send_credit=10, recv_window=0)
        cs.add_stream('b', send_credit=0, recv_window=0)

        cs.consume_send('a', 10)
        self.assertEqual(cs.send_available('a'), 0)
        with self.assertRaises(Exception):  # noqa
            cs.consume_send('a', 1)

        cs.adjust_all_send(-5)
        self.assertEqual(cs.send_available('a'), -5)
        self.assertEqual(cs.send_available('b'), -5)

        cs.grant_send('a', 7)
        self.assertEqual(cs.send_available('a'), 2)
        self.assertEqual(cs.send_available('b'), -5)

    def test_zero_window_opened_later(self) -> None:
        cs = StreamMultiplexCreditStrategy()
        cs.add_stream('a', send_credit=0, recv_window=0)
        self.assertEqual(cs.send_available('a'), 0)
        cs.grant_send('a', 100)
        self.assertEqual(cs.send_available('a'), 100)

    def test_half_window_replenish_threshold(self) -> None:
        cs = StreamMultiplexCreditStrategy()
        cs.add_stream('a', recv_window=100)
        cs.receive('a', 100)
        with self.assertRaises(FlowControlMultiplexError) as cm:
            cs.receive('a', 1)
        self.assertEqual((cm.exception.scope, cm.exception.key), ('stream', 'a'))

        self.assertEqual(cs.consume_receive('a', 49), [])
        self.assertEqual(cs.consume_receive('a', 1), [MultiplexCreditGrant('a', 50)])
        cs.receive('a', 50)
        self.assertEqual(cs.consume_receive('a', 50), [MultiplexCreditGrant('a', 50)])
        self.assertEqual(cs.totals('a').recv_outstanding, 50)

    def test_immediate_replenish_and_unknown_streams(self) -> None:
        cs = StreamMultiplexCreditStrategy(stream_replenish=ImmediateMultiplexCreditReplenishPolicy())
        cs.add_stream('a', recv_window=10)
        cs.receive('a', 3)
        self.assertEqual(cs.consume_receive('a', 1), [MultiplexCreditGrant('a', 1)])
        with self.assertRaises(UnknownStreamMultiplexError):
            cs.send_available('zz')
        with self.assertRaises(UnknownStreamMultiplexError):
            cs.receive('zz', 1)


class TestConnectionMultiplexCreditStrategy(unittest.TestCase):
    def test_send_bounded_by_both_windows(self) -> None:
        cs = ConnectionMultiplexCreditStrategy(send_credit=15, recv_window=100)
        cs.add_stream('a', send_credit=10, recv_window=10)
        cs.add_stream('b', send_credit=10, recv_window=10)

        self.assertEqual(cs.send_available('a'), 10)
        cs.consume_send('a', 10)
        self.assertEqual(cs.send_available('b'), 5)  # the connection window binds
        cs.consume_send('b', 5)
        self.assertEqual(cs.send_available('b'), 0)

        cs.grant_send(None, 100)
        self.assertEqual(cs.send_available('b'), 5)  # now the stream window binds
        self.assertEqual(cs.send_available('a'), 0)

        cs.adjust_all_send(-10)
        self.assertEqual(cs.send_available('a'), -10)
        self.assertEqual(cs.totals().send_available, 100)  # the connection window is not shifted

    def test_stream_and_connection_overruns_are_distinguished(self) -> None:
        cs = ConnectionMultiplexCreditStrategy(send_credit=0, recv_window=15, connection_replenish_on='consume')
        cs.add_stream('a', recv_window=10)
        cs.add_stream('b', recv_window=10)

        cs.receive('a', 10)
        with self.assertRaises(FlowControlMultiplexError) as cm:
            cs.receive('b', 6)
        self.assertEqual(cm.exception.scope, 'connection')
        with self.assertRaises(FlowControlMultiplexError) as cm:
            cs.receive('a', 1)
        self.assertEqual(cm.exception.scope, 'stream')

    def test_slow_stream_holds_connection_credit_only_in_consume_mode(self) -> None:
        for mode in ('receive', 'consume'):
            with self.subTest(mode=mode):
                cs = ConnectionMultiplexCreditStrategy(
                    send_credit=0,
                    recv_window=20,
                    connection_replenish_on=mode,
                    connection_replenish=ImmediateMultiplexCreditReplenishPolicy(),
                )
                cs.add_stream('slow', recv_window=20)
                cs.add_stream('fast', recv_window=20)

                grants = cs.receive('slow', 20)  # never consumed
                if mode == 'receive':
                    self.assertEqual(grants, [MultiplexCreditGrant(None, 20)])
                    cs.receive('fast', 20)  # the slow stream did not stall it
                else:
                    self.assertEqual(grants, ())
                    with self.assertRaises(FlowControlMultiplexError):
                        cs.receive('fast', 1)

    def test_removed_stream_releases_connection_credit_in_consume_mode(self) -> None:
        cs = ConnectionMultiplexCreditStrategy(
            send_credit=0,
            recv_window=20,
            connection_replenish_on='consume',
            connection_replenish=HalfWindowMultiplexCreditReplenishPolicy(),
        )
        cs.add_stream('a', recv_window=20)
        cs.receive('a', 15)
        self.assertEqual(cs.pending_grants(), [])
        cs.remove_stream('a')
        self.assertEqual(cs.pending_grants(), [MultiplexCreditGrant(None, 15)])
        self.assertEqual(cs.totals().recv_outstanding, 20)
