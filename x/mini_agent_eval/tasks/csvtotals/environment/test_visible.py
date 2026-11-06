import unittest

from totals import sum_amounts


##


class TestVisible(unittest.TestCase):
    def test_basic_total(self):
        self.assertEqual(sum_amounts([
            {'category': 'books', 'amount': '2'},
            {'category': 'books', 'amount': '3'},
        ]), {'books': 5})

    def test_empty(self):
        self.assertEqual(sum_amounts([]), {})
