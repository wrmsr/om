# ruff: noqa: UP006 UP045 UP037
# @om-lite
import collections
import typing as ta
import unittest

from ..schedulers import RoundRobinMultiplexOutputScheduler


##


def _run(
        sched: RoundRobinMultiplexOutputScheduler,
        steps: int,
        unit: ta.Callable[[ta.Any], int],
) -> ta.List[ta.Any]:
    order = []
    for _ in range(steps):
        if (key := sched.next()) is None:
            break
        order.append(key)
        sched.account(key, unit(key))
    return order


class TestRoundRobinMultiplexOutputScheduler(unittest.TestCase):
    def test_quantum_shares_are_fair(self) -> None:
        sched = RoundRobinMultiplexOutputScheduler(quantum=100)
        for k in 'abc':
            sched.add(k)
            sched.set_ready(k, True)

        order = _run(sched, 300, lambda _: 25)
        # Four 25-cost units per turn, then the next stream.
        self.assertEqual(order[:12], list('aaaabbbbcccc'))
        counts = collections.Counter(order)
        self.assertEqual(set(counts.values()), {100})

    def test_large_units_take_a_whole_turn_each(self) -> None:
        sched = RoundRobinMultiplexOutputScheduler(quantum=10)
        for k in 'ab':
            sched.add(k)
            sched.set_ready(k, True)
        self.assertEqual(_run(sched, 6, lambda _: 1000), list('ababab'))

    def test_zero_cost_units_cannot_hold_a_turn(self) -> None:
        sched = RoundRobinMultiplexOutputScheduler(quantum=3)
        for k in 'ab':
            sched.add(k)
            sched.set_ready(k, True)
        self.assertEqual(_run(sched, 12, lambda _: 0), list('aaabbbaaabbb'))

    def test_weights(self) -> None:
        sched = RoundRobinMultiplexOutputScheduler(quantum=10)
        sched.add('heavy', weight=3)
        sched.add('light')
        for k in ('heavy', 'light'):
            sched.set_ready(k, True)
        counts = collections.Counter(_run(sched, 400, lambda _: 10))
        self.assertEqual(counts['heavy'], 3 * counts['light'])

    def test_unready_streams_are_skipped_and_rejoin_at_the_back(self) -> None:
        sched = RoundRobinMultiplexOutputScheduler(quantum=10)
        for k in 'abc':
            sched.add(k)
            sched.set_ready(k, True)

        self.assertEqual(sched.next(), 'a')
        sched.set_ready('b', False)
        sched.account('a', 10)
        self.assertEqual(sched.next(), 'c')
        sched.set_ready('b', True)
        sched.account('c', 10)
        self.assertEqual(sched.next(), 'a')
        sched.account('a', 10)
        self.assertEqual(sched.next(), 'b')

    def test_current_stream_going_unready_or_removed(self) -> None:
        sched = RoundRobinMultiplexOutputScheduler(quantum=100)
        for k in 'ab':
            sched.add(k)
            sched.set_ready(k, True)

        self.assertEqual(sched.next(), 'a')
        sched.set_ready('a', False)  # e.g. ran out of credit mid-turn
        self.assertEqual(sched.next(), 'b')
        sched.remove('b')
        self.assertIsNone(sched.next())
        self.assertFalse(sched.is_ready('a'))

        sched.set_ready('a', True)
        sched.set_ready('a', True)  # idempotent
        self.assertEqual(_run(sched, 3, lambda _: 100), list('aaa'))

    def test_no_stream_is_starved_under_churn(self) -> None:
        sched = RoundRobinMultiplexOutputScheduler(quantum=50)
        keys = list(range(10))
        for k in keys:
            sched.add(k)
            sched.set_ready(k, True)

        last_served: ta.Dict[ta.Any, int] = {k: 0 for k in keys}
        for step in range(1, 2000):
            nk = sched.next()
            assert nk is not None
            last_served[nk] = step
            sched.account(nk, 50)
            # Every ready stream is served at least once per len(keys) turns.
            self.assertTrue(all(step - s <= len(keys) for s in last_served.values()))
