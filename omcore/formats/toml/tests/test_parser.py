# ruff: noqa: DTZ001 UP017
# @om-lite
import datetime
import decimal
import io
import unittest

from ..parser import TomlDecodeError
from ..parser import toml_load
from ..parser import toml_loads


BS = chr(92)


TEST_SRC = """
# This is a TOML document

title = "TOML Example"

[owner]
name = "Tom Preston-Werner"
dob = 1979-05-27T07:32:00-08:00

[database]
enabled = true
ports = [ 8000, 8001, 8002 ]
data = [ ["delta", "phi"], [3.14] ]
temp_targets = { cpu = 79.5, case = 72.0 }

[servers]

[servers.alpha]
ip = "10.0.0.1"
role = "frontend"

[servers.beta]
ip = "10.0.0.2"
role = "backend"
"""


class TestTomlLoads(unittest.TestCase):
    def test_example(self):
        d = toml_loads(TEST_SRC)
        self.assertEqual(d['title'], 'TOML Example')
        self.assertEqual(d['owner']['name'], 'Tom Preston-Werner')
        self.assertEqual(
            d['owner']['dob'],
            datetime.datetime(1979, 5, 27, 7, 32, tzinfo=datetime.timezone(datetime.timedelta(hours=-8))),
        )
        self.assertEqual(d['database'], {
            'enabled': True,
            'ports': [8000, 8001, 8002],
            'data': [['delta', 'phi'], [3.14]],
            'temp_targets': {'cpu': 79.5, 'case': 72.0},
        })
        self.assertEqual(d['servers'], {
            'alpha': {'ip': '10.0.0.1', 'role': 'frontend'},
            'beta': {'ip': '10.0.0.2', 'role': 'backend'},
        })

    def test_empty_and_trivia_only(self):
        self.assertEqual(toml_loads(''), {})
        self.assertEqual(toml_loads('   \n\t\n'), {})
        self.assertEqual(toml_loads('# only a comment'), {})
        self.assertEqual(toml_loads('# c1\n\n  # c2\n'), {})

    def test_comments_and_whitespace(self):
        src = '# c1\n\n  # c2\n\ta\t=\t1\t# c3\n[ t ]  # c4\n  b = 2\n'
        self.assertEqual(toml_loads(src), {'a': 1, 't': {'b': 2}})
        self.assertEqual(toml_loads('a = 1 # c'), {'a': 1})
        self.assertEqual(toml_loads('a=1'), {'a': 1})

    def test_basic_string_escapes(self):
        src = r'k = "a\tb\nc\"d\\e\bf\fg\rh"'
        self.assertEqual(toml_loads(src), {'k': 'a\tb\nc"d\\e\bf\fg\rh'})

    def test_unicode_escapes(self):
        src = 'k = "' + BS + 'u00E9' + BS + 'U0001F600"'
        self.assertEqual(toml_loads(src), {'k': chr(0xE9) + chr(0x1F600)})

    def test_literal_string(self):
        src = r"k = 'C:\Users\nobody'"
        self.assertEqual(toml_loads(src), {'k': r'C:\Users\nobody'})

    def test_multiline_basic_string(self):
        src = 'k = """\nRoses are red\nViolets are blue"""'
        self.assertEqual(toml_loads(src)['k'], 'Roses are red\nViolets are blue')

        src = 'k = """The quick \\\n\n  brown fox \\\n  jumps."""'
        self.assertEqual(toml_loads(src)['k'], 'The quick brown fox jumps.')

        src = 'k = """here are "two" quotes, and three: ""\\""""'
        self.assertEqual(toml_loads(src)['k'], 'here are "two" quotes, and three: """')

        src = 'k = """trailing two"""""'
        self.assertEqual(toml_loads(src)['k'], 'trailing two""')

        src = 'k = """\n  keep\ttab\n"""'
        self.assertEqual(toml_loads(src)['k'], '  keep\ttab\n')

    def test_multiline_literal_string(self):
        src = "k = '''\nraw \\n text\nline2'''"
        self.assertEqual(toml_loads(src)['k'], 'raw \\n text\nline2')

        src = "k = ''''one leading quote'''"
        self.assertEqual(toml_loads(src)['k'], "'one leading quote")

        src = "k = '''trailing two'''''"
        self.assertEqual(toml_loads(src)['k'], "trailing two''")

    def test_integers(self):
        src = '\n'.join([
            'a = 42',
            'b = +99',
            'c = -17',
            'd = 1_000_000',
            'e = 0',
            'f = -0',
            'h = 0xDEADBEEF',
            'h2 = 0xdead_beef',
            'o = 0o755',
            'bn = 0b1101_0110',
        ])
        self.assertEqual(toml_loads(src), {
            'a': 42,
            'b': 99,
            'c': -17,
            'd': 1000000,
            'e': 0,
            'f': 0,
            'h': 0xDEADBEEF,
            'h2': 0xDEADBEEF,
            'o': 0o755,
            'bn': 0b11010110,
        })

    def test_floats(self):
        src = '\n'.join([
            'a = +1.0',
            'b = 3.1415',
            'c = -0.01',
            'd = 5e+22',
            'e = 1e06',
            'f = -2E-2',
            'g = 6.626e-34',
            'h = 224_617.445_991_228',
        ])
        d = toml_loads(src)
        self.assertEqual(d, {
            'a': 1.0,
            'b': 3.1415,
            'c': -0.01,
            'd': 5e22,
            'e': 1e6,
            'f': -0.02,
            'g': 6.626e-34,
            'h': 224617.445991228,
        })
        for v in d.values():
            self.assertIsInstance(v, float)

    def test_special_floats(self):
        d = toml_loads('a = inf\nb = +inf\nc = -inf\nd = nan\ne = +nan\nf = -nan')
        self.assertEqual(d['a'], float('inf'))
        self.assertEqual(d['b'], float('inf'))
        self.assertEqual(d['c'], float('-inf'))
        for k in 'def':
            self.assertIsInstance(d[k], float)
            self.assertNotEqual(d[k], d[k])

    def test_booleans(self):
        d = toml_loads('a = true\nb = false')
        self.assertIs(d['a'], True)
        self.assertIs(d['b'], False)

    def test_datetimes(self):
        src = '\n'.join([
            'odt1 = 1979-05-27T07:32:00Z',
            'odt2 = 1979-05-27T00:32:00-07:00',
            'odt3 = 1979-05-27T00:32:00.999999-07:00',
            'odt4 = 1979-05-27 07:32:00Z',
            'odt5 = 1979-05-27t07:32:00z',
            'ldt1 = 1979-05-27T07:32:00',
            'ldt2 = 1979-05-27T00:32:00.999999',
            'ld1 = 1979-05-27',
            'lt1 = 07:32:00',
            'lt2 = 00:32:00.999999',
            'lt3 = 00:32:00.9999999999',
        ])
        d = toml_loads(src)
        utc = datetime.timezone.utc
        m7 = datetime.timezone(datetime.timedelta(hours=-7))
        self.assertEqual(d['odt1'], datetime.datetime(1979, 5, 27, 7, 32, tzinfo=utc))
        self.assertIs(d['odt1'].tzinfo, utc)
        self.assertEqual(d['odt2'], datetime.datetime(1979, 5, 27, 0, 32, tzinfo=m7))
        self.assertEqual(d['odt3'], datetime.datetime(1979, 5, 27, 0, 32, 0, 999999, tzinfo=m7))
        self.assertEqual(d['odt4'], d['odt1'])
        self.assertEqual(d['odt5'], d['odt1'])
        self.assertIs(d['odt5'].tzinfo, utc)
        self.assertEqual(d['ldt1'], datetime.datetime(1979, 5, 27, 7, 32))
        self.assertIsNone(d['ldt1'].tzinfo)
        self.assertEqual(d['ldt2'], datetime.datetime(1979, 5, 27, 0, 32, 0, 999999))
        self.assertEqual(d['ld1'], datetime.date(1979, 5, 27))
        self.assertNotIsInstance(d['ld1'], datetime.datetime)
        self.assertEqual(d['lt1'], datetime.time(7, 32))
        self.assertEqual(d['lt2'], datetime.time(0, 32, 0, 999999))
        self.assertEqual(d['lt3'], datetime.time(0, 32, 0, 999999))

    def test_arrays(self):
        src = '\n'.join([
            'ints = [ 1, 2, 3 ]',
            'nested = [ [ 1, 2 ], ["a", "b", "c"] ]',
            'mixed = [ 0.1, 0.2, 1, "x", true, 1979-05-27, { a = 1 } ]',
            'trailing = [ 1, 2, ]',
            'multi = [',
            '  1, # one',
            '  # standalone',
            '  2,',
            ']',
            'empty = []',
            'empty2 = [ ]',
            'empty3 = [ # c',
            ']',
        ])
        d = toml_loads(src)
        self.assertEqual(d['ints'], [1, 2, 3])
        self.assertEqual(d['nested'], [[1, 2], ['a', 'b', 'c']])
        self.assertEqual(d['mixed'], [0.1, 0.2, 1, 'x', True, datetime.date(1979, 5, 27), {'a': 1}])
        self.assertEqual(d['trailing'], [1, 2])
        self.assertEqual(d['multi'], [1, 2])
        self.assertEqual(d['empty'], [])
        self.assertEqual(d['empty2'], [])
        self.assertEqual(d['empty3'], [])

    def test_inline_tables(self):
        src = 'a = { x = 1, y.z = "two", "q k" = [1] }\nb = {}\nc = { d = { e = { f = true } } }'
        d = toml_loads(src)
        self.assertEqual(d['a'], {'x': 1, 'y': {'z': 'two'}, 'q k': [1]})
        self.assertEqual(d['b'], {})
        self.assertEqual(d['c'], {'d': {'e': {'f': True}}})

    def test_tables(self):
        src = '\n'.join([
            'root = 1',
            '[a]',
            'x = 1',
            '[a.b]',
            'y = 2',
            '[ c . "d e" . f ]',
            'z = 3',
            '[g.h]',
            'i = 4',
            '[g]',
            'j = 5',
        ])
        self.assertEqual(toml_loads(src), {
            'root': 1,
            'a': {'x': 1, 'b': {'y': 2}},
            'c': {'d e': {'f': {'z': 3}}},
            'g': {'h': {'i': 4}, 'j': 5},
        })

    def test_dotted_keys(self):
        src = 'a.b.c = 1\na.b.d = 2\na.e = 3\n"x.y".z = 4\n[t]\nf.g = 5\n[t.f.h]\ni = 6'
        self.assertEqual(toml_loads(src), {
            'a': {'b': {'c': 1, 'd': 2}, 'e': 3},
            'x.y': {'z': 4},
            't': {'f': {'g': 5, 'h': {'i': 6}}},
        })

    def test_array_of_tables(self):
        src = '\n'.join([
            '[[products]]',
            'name = "Hammer"',
            'sku = 738594937',
            '[[products]]',
            '[[products]]',
            'name = "Nail"',
            '[[fruits]]',
            'name = "apple"',
            '[fruits.physical]',
            'color = "red"',
            '[[fruits.varieties]]',
            'name = "red delicious"',
            '[[fruits.varieties]]',
            'name = "granny smith"',
            '[[fruits]]',
            'name = "banana"',
            '[[fruits.varieties]]',
            'name = "plantain"',
        ])
        self.assertEqual(toml_loads(src), {
            'products': [{'name': 'Hammer', 'sku': 738594937}, {}, {'name': 'Nail'}],
            'fruits': [
                {
                    'name': 'apple',
                    'physical': {'color': 'red'},
                    'varieties': [{'name': 'red delicious'}, {'name': 'granny smith'}],
                },
                {
                    'name': 'banana',
                    'varieties': [{'name': 'plantain'}],
                },
            ],
        })

    def test_crlf(self):
        d = toml_loads('a = 1\r\nb = """x\r\ny"""\r\n[t]\r\nc = 2\r\n')
        self.assertEqual(d, {'a': 1, 'b': 'x\ny', 't': {'c': 2}})

    def test_parse_float(self):
        d = toml_loads('a = 0.1\nb = 1e3\nc = 1', parse_float=decimal.Decimal)
        self.assertEqual(d['a'], decimal.Decimal('0.1'))
        self.assertIsInstance(d['a'], decimal.Decimal)
        self.assertEqual(d['b'], decimal.Decimal('1e3'))
        self.assertIsInstance(d['c'], int)

        with self.assertRaises(ValueError) as cm:  # noqa
            toml_loads('a = 0.1', parse_float=lambda s: [])
        self.assertIn('parse_float must not return dicts or lists', str(cm.exception))

    def test_type_errors(self):
        with self.assertRaises(TypeError):
            toml_loads(b'a = 1')  # type: ignore
        with self.assertRaises(TypeError):
            toml_load(io.StringIO('a = 1'))  # type: ignore
        self.assertEqual(toml_load(io.BytesIO(b'a = 1')), {'a': 1})

    def test_errors(self):
        cases = [
            ('a = ', 'Invalid value (at end of document)'),
            ('a = 1\na = 2', 'Cannot overwrite a value'),
            ('[a]\n[a]', 'Cannot declare'),
            ('[a]\nb = 1\n[a.b]', 'Cannot overwrite a value'),
            ('a.b = 1\n[a]', 'Cannot declare'),
            ('a = {b = 1}\na.c = 2', 'Cannot mutate immutable namespace'),
            ('a = [1]\n[a]', 'Cannot declare'),
            ('a = [1]\n[[a]]', 'Cannot mutate immutable namespace'),
            ('[[a]]\n[a]', 'Cannot declare'),
            ('[a]\n[[a]]', 'Cannot overwrite a value'),
            ('[a.b]\n[a]\nb = 1', 'Cannot overwrite a value'),
            ('a = 1\n[a.b]', 'Cannot overwrite a value'),
            ('a = [1, 2', 'Unclosed array'),
            ('a = [1 2]', 'Unclosed array'),
            ('a = {b = 1', 'Unclosed inline table'),
            ('a = {b = 1 c = 2}', 'Unclosed inline table'),
            ('a = {b = 1, b = 2}', 'Duplicate inline table key'),
            ('a = {b = {}, b.c = 1}', 'Cannot mutate immutable namespace'),
            ('a = "x', 'Unterminated string'),
            ('a = """x', 'Unterminated string'),
            ("a = 'x", 'Expected "\'"'),
            ("a = '''x", 'Expected "\'\'\'"'),
            ('a = "' + BS + 'q"', "Unescaped '" + BS + "' in a string"),
            ('a = "' + BS + 'u12"', 'Invalid hex value'),
            ('a = "' + BS + 'uD800"', 'Escaped character is not a Unicode scalar value'),
            ('a = 1979-02-30', 'Invalid date or datetime'),
            ('a = 1979-05-27T25:00:00', 'Expected newline or end of document after a statement'),
            ('x = 1 y = 2', 'Expected newline or end of document after a statement'),
            ('a = 01', 'Expected newline or end of document after a statement'),
            ('= 1', 'Invalid statement'),
            ('.a = 1', 'Invalid statement'),
            ('a. = 1', 'Invalid initial character for a key part'),
            ('[a', "Expected ']' at the end of a table declaration"),
            ('[[a]', "Expected ']]' at the end of an array declaration"),
            ('a b = 1', "Expected '=' after a key in a key/value pair"),
            ('a = .5', 'Invalid value'),
            ('a = 1 # c' + chr(1), 'Found invalid character'),
            ('a = "x' + chr(1) + 'x"', 'Illegal character'),
            ("a = 'x\nx'", 'Found invalid character'),
        ]
        for src, expected in cases:
            with self.subTest(src=src):
                with self.assertRaises(TomlDecodeError) as cm:
                    toml_loads(src)
                self.assertIn(expected, str(cm.exception))


class TestTomlDecodeError(unittest.TestCase):
    def test_attributes(self):
        with self.assertRaises(TomlDecodeError) as cm:
            toml_loads('\n\nval=.')
        e = cm.exception
        self.assertEqual(str(e), 'Invalid value (at line 3, column 5)')
        self.assertEqual(e.msg, 'Invalid value')
        self.assertEqual(e.doc, '\n\nval=.')
        self.assertEqual(e.pos, 6)
        self.assertEqual(e.lineno, 3)
        self.assertEqual(e.colno, 5)

    def test_end_of_document(self):
        with self.assertRaises(TomlDecodeError) as cm:
            toml_loads('a =')
        e = cm.exception
        self.assertEqual(str(e), 'Invalid value (at end of document)')
        self.assertEqual(e.pos, 3)
        self.assertEqual(e.lineno, 1)
        self.assertEqual(e.colno, 4)

    def test_crlf_coordinates(self):
        with self.assertRaises(TomlDecodeError) as cm:
            toml_loads('a = 1\r\nb = ?')
        e = cm.exception
        self.assertEqual(e.doc, 'a = 1\nb = ?')
        self.assertEqual(e.lineno, 2)
        self.assertEqual(e.colno, 5)

    def test_bare(self):
        e = TomlDecodeError('oops')
        self.assertEqual(str(e), 'oops')
        self.assertEqual(e.msg, 'oops')
        self.assertIsNone(e.doc)
        self.assertIsNone(e.pos)
        self.assertIsNone(e.lineno)
        self.assertIsNone(e.colno)
        self.assertIsInstance(e, ValueError)
