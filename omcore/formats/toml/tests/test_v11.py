# ruff: noqa: DTZ001 UP017
# @om-lite
"""Tests for the TOML 1.1 additions."""
import datetime
import unittest

from ..parser import TomlDecodeError
from ..parser import toml_loads


BS = chr(92)


class TestToml11(unittest.TestCase):
    def test_multiline_inline_table(self):
        src = '\n'.join([
            'multiline = {',
            '  "a" = 1, "b" = 2,',
            '  c = [',
            '       1,',
            '       2,',
            '       3,',
            '      ],# comment',
            '  d = 3,',
            '  e = 4, f = {',
            '              # comment',
            '             },',
            '}',
        ])
        self.assertEqual(toml_loads(src), {
            'multiline': {'a': 1, 'b': 2, 'c': [1, 2, 3], 'd': 3, 'e': 4, 'f': {}},
        })

    def test_inline_table_trailing_comma(self):
        self.assertEqual(toml_loads('t = { a = 1, }'), {'t': {'a': 1}})
        self.assertEqual(toml_loads('t = { a = 1, b = 2, }'), {'t': {'a': 1, 'b': 2}})
        self.assertEqual(toml_loads('t = {\n  a = 1,\n  b = 2,\n}'), {'t': {'a': 1, 'b': 2}})
        self.assertEqual(toml_loads('t = {a = 1,}'), {'t': {'a': 1}})

    def test_inline_table_comments_and_blank_lines(self):
        src = 't = { # open\n\n  a = 1, # a\n  # standalone\n  b = 2 # b\n}'
        self.assertEqual(toml_loads(src), {'t': {'a': 1, 'b': 2}})
        self.assertEqual(toml_loads('t = {\n  # only a comment\n}'), {'t': {}})
        self.assertEqual(toml_loads('t = {\n\n}'), {'t': {}})
        self.assertEqual(toml_loads('t = { a = { # c\n } }'), {'t': {'a': {}}})

    def test_nested_multiline_inline_tables(self):
        src = 'a = {\n  b = {\n    c = [\n      1,\n    ],\n  },\n}'
        self.assertEqual(toml_loads(src), {'a': {'b': {'c': [1]}}})

    def test_inline_table_errors(self):
        for src in [
            't = { a = 1,, }',
            't = { , }',
            't = { a\n= 1 }',
            't = { a =\n1 }',
            't = { a = 1 b = 2 }',
            't = {\n  a = {}, a.b = 1\n}',
            't = {\n  a.b = 1, a = 2\n}',
            't = { a = 1',
            't = { a = 1,',
            't = {\n  a = 1,\n',
        ]:
            with self.subTest(src=src):
                with self.assertRaises(TomlDecodeError):
                    toml_loads(src)

    def test_inline_table_still_frozen(self):
        with self.assertRaises(TomlDecodeError):
            toml_loads('t = {\n  a = 1,\n}\nt.b = 2')
        with self.assertRaises(TomlDecodeError):
            toml_loads('t = {\n  a = 1,\n}\n[t]')

    def test_escape_e(self):
        self.assertEqual(toml_loads('k = "' + BS + 'e[0m"'), {'k': chr(27) + '[0m'})
        self.assertEqual(toml_loads('k = """' + BS + 'e"""'), {'k': chr(27)})
        self.assertEqual(toml_loads('"' + BS + 'e" = 1'), {chr(27): 1})

    def test_escape_x(self):
        src = 'k = "' + BS + 'x41' + BS + 'x4a' + BS + 'x4A' + BS + 'x00' + BS + 'xff' + BS + 'x7f"'
        self.assertEqual(toml_loads(src), {'k': 'AJJ' + chr(0) + chr(255) + chr(127)})
        self.assertEqual(toml_loads('"' + BS + 'x41" = 1'), {'A': 1})
        self.assertEqual(toml_loads('k = """' + BS + 'x41\n' + BS + 'x42"""'), {'k': 'A\nB'})

    def test_escape_x_errors(self):
        for src in [
            'k = "' + BS + 'x4"',
            'k = "' + BS + 'xZZ"',
            'k = "' + BS + 'x"',
            'k = "' + BS + 'x4G"',
        ]:
            with self.subTest(src=src):
                with self.assertRaises(TomlDecodeError) as cm:
                    toml_loads(src)
                self.assertIn('Invalid hex value', str(cm.exception))

    def test_literal_strings_do_not_escape(self):
        src = "k = '" + BS + 'x41' + BS + "e'"
        self.assertEqual(toml_loads(src), {'k': BS + 'x41' + BS + 'e'})

    def test_upstream_replacements_fixture(self):
        src = '\n'.join([
            'escape = "' + BS + 'e"',
            'tab = "' + BS + 'x09"',
            'upper-j = "' + BS + 'x4a"',
            'upper-j-2 = "' + BS + 'x4A"',
        ])
        self.assertEqual(toml_loads(src), {'escape': chr(27), 'tab': '\t', 'upper-j': 'J', 'upper-j-2': 'J'})

    def test_optional_seconds(self):
        src = '\n'.join([
            'lt = 14:15',
            'lt2 = 00:00',
            'ldt = 2010-02-03 14:15',
            'ldt2 = 2010-02-03T14:15',
            'odt = 2010-02-03T14:15Z',
            'odt2 = 2010-02-03T14:15+01:00',
            'odt3 = 2010-02-03t14:15z',
        ])
        d = toml_loads(src)
        self.assertEqual(d['lt'], datetime.time(14, 15))
        self.assertEqual(d['lt2'], datetime.time(0, 0))
        self.assertEqual(d['ldt'], datetime.datetime(2010, 2, 3, 14, 15))
        self.assertEqual(d['ldt2'], datetime.datetime(2010, 2, 3, 14, 15))
        self.assertEqual(d['odt'], datetime.datetime(2010, 2, 3, 14, 15, tzinfo=datetime.timezone.utc))
        self.assertEqual(
            d['odt2'],
            datetime.datetime(2010, 2, 3, 14, 15, tzinfo=datetime.timezone(datetime.timedelta(hours=1))),
        )
        self.assertEqual(d['odt3'], d['odt'])

    def test_optional_seconds_in_arrays(self):
        self.assertEqual(toml_loads('a = [14:15, 2010-02-03T14:15]'), {
            'a': [datetime.time(14, 15), datetime.datetime(2010, 2, 3, 14, 15)],
        })

    def test_seconds_required_for_fraction(self):
        for src in [
            'lt = 14:15.5',
            'lt = 14:15:',
            'lt = 14:1',
            'dt = 2010-02-03T14:15.5',
            'dt = 2010-02-03T14:15:',
            'dt = 2010-02-03T14',
        ]:
            with self.subTest(src=src):
                with self.assertRaises(TomlDecodeError):
                    toml_loads(src)

    def test_upstream_datetime_fixtures(self):
        d = toml_loads('\n'.join([
            'local-dt=1988-10-27t01:01:01',
            'local-dt-no-seconds=2025-04-18T20:05',
            'zulu-dt=1988-10-27t01:01:01z',
        ]))
        self.assertEqual(d['local-dt'], datetime.datetime(1988, 10, 27, 1, 1, 1))
        self.assertEqual(d['local-dt-no-seconds'], datetime.datetime(2025, 4, 18, 20, 5))
        self.assertEqual(d['zulu-dt'], datetime.datetime(1988, 10, 27, 1, 1, 1, tzinfo=datetime.timezone.utc))

        d = toml_loads('t=00:00:00.99999999999999\nt2=00:00')
        self.assertEqual(d['t'], datetime.time(0, 0, 0, 999999))
        self.assertEqual(d['t2'], datetime.time(0, 0))
