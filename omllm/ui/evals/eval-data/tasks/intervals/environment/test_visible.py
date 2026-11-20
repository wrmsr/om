import unittest

from intervals import merge_intervals


##


class TestVisible(unittest.TestCase):
    def test_simple_overlap(self):
        self.assertEqual(merge_intervals([(1, 4), (3, 6)]), [(1, 6)])

    def test_disjoint(self):
        self.assertEqual(merge_intervals([(1, 2), (4, 5)]), [(1, 2), (4, 5)])

    def test_empty_input(self):
        self.assertEqual(merge_intervals([]), [])
