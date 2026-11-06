import unittest

from intervals import merge_intervals


##


class TestIntervals(unittest.TestCase):
    def test_unsorted_adjacent_chain(self):
        self.assertEqual(merge_intervals([(5, 8), (1, 3), (3, 6)]), [(1, 8)])

    def test_nested(self):
        self.assertEqual(merge_intervals([(1, 10), (3, 4), (8, 12)]), [(1, 12)])

    def test_empty_intervals(self):
        self.assertEqual(merge_intervals([(1, 1), (3, 3)]), [])
        self.assertEqual(merge_intervals([(1, 2), (2, 2), (2, 4)]), [(1, 4)])

    def test_reversed(self):
        with self.assertRaises(ValueError):
            merge_intervals([(3, 2)])
        with self.assertRaises(ValueError):
            merge_intervals([(1, 5), (3, 2)])

    def test_generator_and_input_preservation(self):
        intervals = [(5, 7), (0, 2), (1, 3)]
        original = list(intervals)
        self.assertEqual(merge_intervals(iter(intervals)), [(0, 3), (5, 7)])
        self.assertEqual(merge_intervals(intervals), [(0, 3), (5, 7)])
        self.assertEqual(intervals, original)

        already_merged = [(0, 3), (5, 7)]
        result = merge_intervals(already_merged)
        self.assertEqual(result, already_merged)
        self.assertIsNot(result, already_merged)

    def test_duplicates_negatives_and_disjoint(self):
        self.assertEqual(
            merge_intervals([(4, 9), (-3, -1), (4, 9), (-1, 0), (12, 13)]),
            [(-3, 0), (4, 9), (12, 13)],
        )

    def test_existing_behavior(self):
        self.assertEqual(merge_intervals([]), [])
        self.assertEqual(merge_intervals([(1, 4), (3, 6)]), [(1, 6)])
