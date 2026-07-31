# @om-lite
import unittest

from ..distribute import distribute_evenly


class TestDistributeEvenly(unittest.TestCase):
    def test_balances_items_and_preserves_values(self) -> None:
        items = [
            ('a', 4.),
            ('b', 3.),
            ('c', 2.),
            ('d', 1.),
        ]

        bins = distribute_evenly(iter(items), 2)

        self.assertEqual(bins, [
            [('a', 4.), ('d', 1.)],
            [('b', 3.), ('c', 2.)],
        ])
        self.assertCountEqual(
            [item for bin_items in bins for item in bin_items],
            items,
        )

    def test_can_return_empty_bins(self) -> None:
        self.assertEqual(
            distribute_evenly([('a', 1.)], 3),
            [[('a', 1.)], [], []],
        )

    def test_rejects_nonpositive_bin_count(self) -> None:
        for n_bins in (0, -1):
            with self.subTest(n_bins=n_bins):
                with self.assertRaises(ValueError):
                    distribute_evenly([], n_bins)


if __name__ == '__main__':
    unittest.main()
