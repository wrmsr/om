import decimal
import json
import os
import subprocess
import sys
import tempfile
import unittest

from totals import sum_amounts


##


class TestTotals(unittest.TestCase):
    def test_exact_totals_and_whitespace(self):
        result = sum_amounts([
            {'category': ' books ', 'amount': ' 0.1 '},
            {'category': 'books', 'amount': '0.2'},
            {'category': 'books', 'amount': '-0.1'},
        ])
        self.assertIsInstance(result['books'], decimal.Decimal)
        self.assertEqual(result, {'books': decimal.Decimal('0.2')})

    def test_validation(self):
        for category, amount in [('', '1'), ('   ', '1'), ('x', 'oops'), ('x', 'NaN'), ('x', 'Infinity')]:
            with self.subTest(category=category, amount=amount):
                with self.assertRaises(ValueError):
                    sum_amounts([{'category': category, 'amount': amount}])

    def test_empty_and_case(self):
        self.assertEqual(sum_amounts(iter([])), {})
        self.assertEqual(sum_amounts([
            {'category': 'a', 'amount': '1'},
            {'category': 'A', 'amount': '2'},
        ]), {'a': decimal.Decimal(1), 'A': decimal.Decimal(2)})


class TestCli(unittest.TestCase):
    def _run(self, text, *args):
        return subprocess.run(  # noqa
            [sys.executable, 'cli.py', *args],
            input=text,
            capture_output=True,
            text=True,
            timeout=10,
        )

    def _assert_output(self, result, expected):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, '')
        self.assertTrue(result.stdout.endswith('\n'))
        actual = json.loads(result.stdout)
        self.assertEqual(actual, expected)
        self.assertEqual(list(actual), sorted(actual))

    def test_stdin_csv_and_round_after_sum(self):
        result = self._run('amount,extra,category\n0.005,x,"a,b"\n0.005,y,"a,b"\n1.235,z,café\n')
        self._assert_output(result, {'a,b': '0.01', 'café': '1.24'})

    def test_dash_stdin_multiline_and_negative(self):
        result = self._run('category,amount\n"one\ntwo",-1.235\n', '-')
        self._assert_output(result, {'one\ntwo': '-1.24'})

    def test_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'input file.csv')
            with open(path, 'w', encoding='utf-8', newline='') as file:
                file.write('category,amount\nz,1\na,2\n')
            result = self._run('', path)
        self._assert_output(result, {'a': '2.00', 'z': '1.00'})

    def test_invalid_input(self):
        cases = [
            'name,amount\na,1\n',
            'category,amount\na\n',
            'category,amount\na,1,extra\n',
            'category,amount\na,bad\n',
            'category,amount\na,Infinity\n',
            'category,amount\n ,1\n',
        ]
        for text in cases:
            with self.subTest(text=text):
                result = self._run(text)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertTrue(result.stderr.strip())
                self.assertNotIn('Traceback', result.stderr)

    def test_header_only(self):
        result = self._run('category,amount\n')
        self._assert_output(result, {})
