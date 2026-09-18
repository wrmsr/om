# ruff: noqa: DTZ001 UP017
# @om-lite
import datetime
import decimal
import unittest

from ....lite.check import check
from ..parser import TomlDecodeError
from ..parser import TomlDocumentError
from ..parser import TomlInline
from ..parser import TomlMultiline
from ..parser import TomlRaw
from ..parser import TomlStyle
from ..parser import TomlValueRenderer
from ..parser import toml_loads
from ..parser import toml_parse_document


BS = chr(92)


class RewritingTestCase(unittest.TestCase):
    def check(self, src, fn, expected):
        doc = toml_parse_document(src)
        out = fn(doc)
        self.assertEqual(out.src, expected)
        self.assertEqual(out.data, toml_loads(expected))
        self.assertEqual(doc.src, src)
        return out


class TestSetValueReplace(RewritingTestCase):
    def test_scalars_in_place(self):
        src = 'a = "x" # c\nb = 1\n'
        self.check(src, lambda d: d.set_value(('a',), 'y "q"\n'), 'a = "y \\"q\\"\\n" # c\nb = 1\n')
        self.check(src, lambda d: d.set_value(('b',), 2.5), 'a = "x" # c\nb = 2.5\n')
        self.check(src, lambda d: d.set_value(['b'], True), 'a = "x" # c\nb = true\n')
        self.check('[t]\n  k = 1  # c\n', lambda d: d.set_value(('t', 'k'), 2), '[t]\n  k = 2  # c\n')

    def test_string_styles(self):
        self.check("a = 'x'", lambda d: d.set_value(('a',), 'y'), "a = 'y'")
        self.check("a = 'x'", lambda d: d.set_value(('a',), "it's"), 'a = "it\'s"')
        self.check("a = 'x'", lambda d: d.set_value(('a',), 'tab\there'), "a = 'tab\there'")
        self.check("a = 'x'", lambda d: d.set_value(('a',), 'nl\nhere'), 'a = "nl\\nhere"')
        self.check('a = "x"', lambda d: d.set_value(('a',), 'y'), 'a = "y"')
        self.check('a = """\nx\ny"""', lambda d: d.set_value(('a',), 'p\nq'), 'a = """\np\nq"""')
        self.check('a = """\nx\ny"""', lambda d: d.set_value(('a',), 'single'), 'a = "single"')
        self.check("a = '''\nx'''", lambda d: d.set_value(('a',), 'p\nq'), "a = '''\np\nq'''")
        self.check("a = '''\nx'''", lambda d: d.set_value(('a',), "p'''q\nz"), 'a = """\np\'\'\'q\nz"""')
        self.check("a = '''\nx'''", lambda d: d.set_value(('a',), 'single'), "a = 'single'")
        self.check('a = """\nx"""', lambda d: d.set_value(('a',), 'a"""b\nc'), 'a = """\na\\"\\"\\"b\nc"""')
        self.check('a = """\nx"""', lambda d: d.set_value(('a',), 'a"b\nc'), 'a = """\na"b\nc"""')
        self.check('a = """\nx"""', lambda d: d.set_value(('a',), 'a\tb\nc'), 'a = """\na\tb\nc"""')
        self.check(
            'a = "x"',
            lambda d: d.set_value(('a',), chr(1) + chr(127)),
            'a = "' + BS + 'u0001' + BS + 'u007F"',
        )
        self.check('a = "x"', lambda d: d.set_value(('a',), 'q\\b\b\f\r'), 'a = "q\\\\b\\b\\f\\r"')
        self.check('a = "x"', lambda d: d.set_value(('a',), ''), 'a = ""')
        self.check("a = 'x'", lambda d: d.set_value(('a',), ''), "a = ''")

    def test_int_styles(self):
        self.check('a = 0xff', lambda d: d.set_value(('a',), 16), 'a = 0x10')
        self.check('a = 0xFF', lambda d: d.set_value(('a',), 255), 'a = 0xFF')
        self.check('a = 0o17', lambda d: d.set_value(('a',), 8), 'a = 0o10')
        self.check('a = 0b101', lambda d: d.set_value(('a',), 2), 'a = 0b10')
        self.check('a = 0xff', lambda d: d.set_value(('a',), -1), 'a = -1')
        self.check('a = 1_000', lambda d: d.set_value(('a',), 5), 'a = 5')
        self.check('a = 1', lambda d: d.set_value(('a',), -7), 'a = -7')
        self.check('a = 1.5', lambda d: d.set_value(('a',), 2), 'a = 2')
        self.check('a = 1', lambda d: d.set_value(('a',), 2.0), 'a = 2.0')

    def test_floats(self):
        for v, s in [
            (1e-05, '1e-05'),
            (float('inf'), 'inf'),
            (float('-inf'), '-inf'),
            (100.0, '100.0'),
            (0.1, '0.1'),
            (1e16, '1e+16'),
            (-0.0, '-0.0'),
        ]:
            with self.subTest(v=v):
                self.check('a = 1.0', lambda d, v=v: d.set_value(('a',), v), 'a = ' + s)
        out = toml_parse_document('a = 1.0').set_value(('a',), float('nan'))
        self.assertEqual(out.src, 'a = nan')
        self.assertNotEqual(out.data['a'], out.data['a'])

    def test_datetimes(self):
        utc = datetime.timezone.utc
        self.check(
            'a = 1',
            lambda d: d.set_value(('a',), datetime.datetime(2020, 1, 2, 3, 4, 5, tzinfo=utc)),
            'a = 2020-01-02T03:04:05+00:00',
        )
        self.check(
            'a = 1',
            lambda d: d.set_value(('a',), datetime.datetime(2020, 1, 2, 3, 4, 5, 6)),
            'a = 2020-01-02T03:04:05.000006',
        )
        self.check('a = 1', lambda d: d.set_value(('a',), datetime.date(2020, 1, 2)), 'a = 2020-01-02')
        self.check('a = 1', lambda d: d.set_value(('a',), datetime.time(3, 4)), 'a = 03:04:00')
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('a = 1').set_value(('a',), datetime.time(3, 4, tzinfo=utc))

    def test_decimal(self):
        self.check('a = 1', lambda d: d.set_value(('a',), decimal.Decimal('1.5')), 'a = 1.5')
        self.check('a = 1', lambda d: d.set_value(('a',), decimal.Decimal(2)), 'a = 2.0')
        self.check('a = 1', lambda d: d.set_value(('a',), decimal.Decimal('-inf')), 'a = -inf')
        doc = toml_parse_document('a = 0.1\nb = 0.2', parse_float=decimal.Decimal)
        out = doc.set_value(('a',), 0.5)
        self.assertEqual(out.src, 'a = 0.5\nb = 0.2')
        self.assertIsInstance(out.data['a'], decimal.Decimal)
        self.assertIsInstance(out.data['b'], decimal.Decimal)

    def test_containers(self):
        self.check('a = 1', lambda d: d.set_value(('a',), {}), 'a = {}')
        self.check('a = 1', lambda d: d.set_value(('a',), []), 'a = []')
        self.check('a = 1', lambda d: d.set_value(('a',), (1, 2)), 'a = [\n    1,\n    2,\n]')
        self.check(
            'a = 1',
            lambda d: d.set_value(('a',), {'k k': 1, '': 2, 'n': {'x': [1]}}),
            "a = {'k k' = 1, '' = 2, n = {x = [1]}}",
        )
        self.check('a = [\n 1,\n]\nb = 2\n', lambda d: d.set_value(('a',), 1), 'a = 1\nb = 2\n')
        self.check('a = { x = 1 }\n', lambda d: d.set_value(('a',), [1]), 'a = [1]\n')
        self.check('a = [1]\n', lambda d: d.set_value(('a', 0), {'x': 1}), 'a = [{x = 1}]\n')

        st = TomlStyle(array_layout='inline', inline_table_padding=' ')
        doc = toml_parse_document('a = 1', style=st)
        out = doc.set_value(('a',), [1, 'x', True, [2], {'k': 1}])
        self.assertEqual(out.src, "a = [1, 'x', true, [2], { k = 1 }]")
        self.assertIs(out.style, st)

    def test_unrenderable(self):
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('a = 1').set_value(('a',), object())
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('a = 1').set_value(('a',), [object()])

    def test_table_paths_rejected(self):
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('[t]\n').set_value(('t',), 1)
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('[t]\n').set_value((), 1)
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('[[t]]\n').set_value(('t', 0), {})


class TestSetValueInsert(RewritingTestCase):
    def test_append_to_table(self):
        self.check('[t]\nk=1\n', lambda d: d.set_value(('t', 'n'), 2), '[t]\nk=1\nn=2\n')
        self.check('[t]\n  k = 1\n', lambda d: d.set_value(('t', 'n'), 2), '[t]\n  k = 1\n  n = 2\n')
        self.check('[t]\nk = 1 # c\n', lambda d: d.set_value(('t', 'n'), 2), '[t]\nk = 1 # c\nn = 2\n')
        self.check('[t]\nk = 1', lambda d: d.set_value(('t', 'n'), 2), '[t]\nk = 1\nn = 2')
        self.check('[t]\nk = 1 # c', lambda d: d.set_value(('t', 'n'), 2), '[t]\nk = 1 # c\nn = 2')
        self.check('[t]\n\n[u]\nx = 1\n', lambda d: d.set_value(('t', 'n'), 2), '[t]\nn = 2\n\n[u]\nx = 1\n')
        self.check('[t]', lambda d: d.set_value(('t', 'n'), 2), '[t]\nn = 2')
        self.check('[t] # c\n', lambda d: d.set_value(('t', 'n'), 2), '[t] # c\nn = 2\n')
        self.check(
            '[t]\nk = [\n  1,\n]\n\n[u]\n',
            lambda d: d.set_value(('t', 'n'), 2),
            '[t]\nk = [\n  1,\n]\nn = 2\n\n[u]\n',
        )
        self.check('[[t]]\nk = 1\n[[t]]\nk = 2\n', lambda d: d.set_value(('t', 0, 'n'), 3), '[[t]]\nk = 1\nn = 3\n[[t]]\nk = 2\n')  # noqa: E501

    def test_append_to_root(self):
        self.check('# c\n[t]\nk = 1\n', lambda d: d.set_value(('r',), 1), '# c\nr = 1\n\n[t]\nk = 1\n')
        self.check('', lambda d: d.set_value(('r',), 1), 'r = 1\n')
        self.check('# c', lambda d: d.set_value(('r',), 1), '# c\nr = 1')
        self.check('# c\n', lambda d: d.set_value(('r',), 1), '# c\nr = 1\n')
        self.check('a = 1', lambda d: d.set_value(('b',), 2), 'a = 1\nb = 2')
        self.check('a = 1\n', lambda d: d.set_value(('b',), 2), 'a = 1\nb = 2\n')
        self.check('a = 1\n\n[t]\n', lambda d: d.set_value(('b',), 2), 'a = 1\nb = 2\n\n[t]\n')

    def test_dotted_keys(self):
        self.check('[t]\nk = 1\n', lambda d: d.set_value(('t', 'a', 'b'), 2), '[t]\nk = 1\na.b = 2\n')
        self.check('x = 1\n', lambda d: d.set_value(('a', 'b', 'c'), 2), 'x = 1\na.b.c = 2\n')
        self.check('[t]\nk = 1\n', lambda d: d.set_value(('t', 'weird key'), 2), "[t]\nk = 1\n'weird key' = 2\n")
        self.check('[t]\nk = 1\n', lambda d: d.set_value(('t', ''), 2), "[t]\nk = 1\n'' = 2\n")
        self.check('[t]\na.b = 1\n', lambda d: d.set_value(('t', 'a', 'c'), 2), '[t]\na.b = 1\na.c = 2\n')
        self.check('[t.u]\nk = 1\n', lambda d: d.set_value(('t', 'u', 'v', 'w'), 2), '[t.u]\nk = 1\nv.w = 2\n')
        self.check('[t.u]\nk = 1\n', lambda d: d.set_value(('t', 'x'), 2), 't.x = 2\n\n[t.u]\nk = 1\n')

    def test_inline_tables(self):
        self.check('t = { a = 1 }', lambda d: d.set_value(('t', 'b'), 2), 't = { a = 1, b = 2 }')
        self.check('t = {a = 1,b = 2}', lambda d: d.set_value(('t', 'c'), 3), 't = {a = 1,b = 2,c = 3}')
        self.check('t = {}', lambda d: d.set_value(('t', 'c'), 3), 't = {c = 3}')
        self.check('t = { }', lambda d: d.set_value(('t', 'c'), 3), 't = {c = 3}')
        self.check('t = {\n  a = 1,\n}', lambda d: d.set_value(('t', 'b'), 2), 't = {\n  a = 1,\n  b = 2,\n}')
        self.check('t = {\n  a = 1\n}', lambda d: d.set_value(('t', 'b'), 2), 't = {\n  a = 1,\n  b = 2,\n}')
        self.check(
            't = {\n  a = 1, # a\n  b = 2, # b\n}',
            lambda d: d.set_value(('t', 'c'), 3),
            't = {\n  a = 1, # a\n  b = 2, # b\n  c = 3,\n}',
        )
        self.check('t = { a = 1 }', lambda d: d.set_value(('t', 'x', 'y'), 2), 't = { a = 1, x.y = 2 }')
        self.check('t = { a = { b = 1 } }', lambda d: d.set_value(('t', 'a', 'c'), 2), 't = { a = { b = 1, c = 2 } }')

    def test_arrays(self):
        self.check('a = [1, 2]', lambda d: d.set_value(('a', 2), 3), 'a = [1, 2, 3]')
        self.check('a = [1,2]', lambda d: d.set_value(('a', 2), 3), 'a = [1,2,3]')
        self.check('a = []', lambda d: d.set_value(('a', 0), 3), 'a = [3]')
        self.check('a = [ ]', lambda d: d.set_value(('a', 0), 3), 'a = [3]')
        self.check('a = [1]', lambda d: d.set_value(('a', 1), 3), 'a = [1, 3]')
        self.check('a = [1, 2,]', lambda d: d.set_value(('a', 2), 3), 'a = [1, 2, 3,]')
        self.check('a = [\n  1,\n]', lambda d: d.set_value(('a', 1), 2), 'a = [\n  1,\n  2,\n]')
        self.check('a = [\n  1,\n  2\n]', lambda d: d.set_value(('a', 2), 3), 'a = [\n  1,\n  2,\n  3,\n]')
        self.check(
            'a = [\n  1, # one\n  2, # two\n]',
            lambda d: d.set_value(('a', 2), 3),
            'a = [\n  1, # one\n  2, # two\n  3,\n]',
        )
        self.check('a = [\n  1, 2,\n]', lambda d: d.set_value(('a', 2), 3), 'a = [\n  1, 2, 3,\n]')
        self.check('a = [1,\n     2]', lambda d: d.set_value(('a', 2), 3), 'a = [1,\n     2,\n     3]')
        self.check('a = [[1], [2]]', lambda d: d.set_value(('a', 1, 1), 3), 'a = [[1], [2, 3]]')
        self.check('a = [1]\r\n', lambda d: d.set_value(('a', 1), [2]), 'a = [1, [2]]\r\n')

    def test_errors(self):
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('a = [1]').set_value(('a', 5), 1)
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('a = [1]').set_value(('a', 0, 'x'), 1)
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('a = 1').set_value(('a', 'b'), 1)
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('[[f]]\nx = 1\n').set_value(('f', 1, 'x'), 1)
        with self.assertRaises(TomlDecodeError):
            toml_parse_document('[[f]]\nx = 1\n').set_value(('f', 'x'), 1)

    def test_reparse_validation(self):
        doc = toml_parse_document('a = 1\n')
        a = check.not_none(doc.node_at_path(('a',)))
        kv = check.not_none(doc.key_value_at_path(('a',)))
        with self.assertRaises(TomlDecodeError):
            doc.replace_node(a, '= =')
        with self.assertRaises(TomlDocumentError):
            doc.splice(5, 2, '')
        with self.assertRaises(TomlDocumentError):
            doc.splice(0, 100, '')
        self.assertEqual(doc.splice(0, 0, 'z = 0\n').src, 'z = 0\na = 1\n')
        self.assertEqual(doc.replace_node(a, '0x1').data, {'a': 1})
        self.assertEqual(doc.replace_node(kv, 'b = 2').src, 'b = 2\n')
        self.assertEqual(doc.replace_node(kv.key, 'c').src, 'c = 1\n')


class TestDeletePath(RewritingTestCase):
    def test_statements(self):
        src = 'a = 1\nb = 2\nc = 3\n'
        self.check(src, lambda d: d.delete_path(('b',)), 'a = 1\nc = 3\n')
        self.check(src, lambda d: d.delete_path(('a',)), 'b = 2\nc = 3\n')
        self.check(src, lambda d: d.delete_path(('c',)), 'a = 1\nb = 2\n')
        self.check('a = 1\nb = 2', lambda d: d.delete_path(('b',)), 'a = 1\n')
        self.check('a = 1', lambda d: d.delete_path(('a',)), '')
        self.check('  a = 1 # c\n', lambda d: d.delete_path(('a',)), '')
        self.check('a = [\n 1,\n]\nb = 2\n', lambda d: d.delete_path(('a',)), 'b = 2\n')
        self.check('a = 1\n# about b\nb = 2\n', lambda d: d.delete_path(('b',)), 'a = 1\n# about b\n')
        self.check('[t]\na = 1\nb.c = 2\n[u]\n', lambda d: d.delete_path(('t', 'b')), '[t]\na = 1\n[u]\n')
        self.check('[t]\na = 1\nb.c = 2\n[u]\n', lambda d: d.delete_path(('t', 'b', 'c')), '[t]\na = 1\n[u]\n')

    def test_array_items(self):
        src = 'a = [1, 2, 3] # c'
        self.check(src, lambda d: d.delete_path(('a', 1)), 'a = [1, 3] # c')
        self.check(src, lambda d: d.delete_path(('a', 0)), 'a = [2, 3] # c')
        self.check(src, lambda d: d.delete_path(('a', 2)), 'a = [1, 2] # c')
        self.check('a = [1, 2, 3,]', lambda d: d.delete_path(('a', 2)), 'a = [1, 2]')
        self.check('a = [1, 2, 3 ]', lambda d: d.delete_path(('a', 2)), 'a = [1, 2 ]')
        self.check('a = [ 1 ]', lambda d: d.delete_path(('a', 0)), 'a = []')
        self.check('a = [\n  1,\n]', lambda d: d.delete_path(('a', 0)), 'a = []')
        src = 'a = [\n  1, # one\n  2, # two\n  3,\n]'
        self.check(src, lambda d: d.delete_path(('a', 0)), 'a = [\n  2, # two\n  3,\n]')
        self.check(src, lambda d: d.delete_path(('a', 1)), 'a = [\n  1, # one\n  3,\n]')
        self.check(src, lambda d: d.delete_path(('a', 2)), 'a = [\n  1, # one\n  2, # two\n]')
        self.check('a = [\n  1,\n  2\n]', lambda d: d.delete_path(('a', 1)), 'a = [\n  1,\n]')
        self.check('a = [\n  1,\n  2 ]', lambda d: d.delete_path(('a', 1)), 'a = [\n  1,\n]')
        self.check('a = [[1, 2], [3]]', lambda d: d.delete_path(('a', 0, 1)), 'a = [[1], [3]]')
        self.check('a = [[1, 2], [3]]', lambda d: d.delete_path(('a', 1)), 'a = [[1, 2]]')
        self.check('a = [[1, 2], [3]]', lambda d: d.delete_path(('a', 0)), 'a = [[3]]')

    def test_inline_table_pairs(self):
        src = 't = { a = 1, b = 2, c = 3 }'
        self.check(src, lambda d: d.delete_path(('t', 'b')), 't = { a = 1, c = 3 }')
        self.check(src, lambda d: d.delete_path(('t', 'a')), 't = { b = 2, c = 3 }')
        self.check(src, lambda d: d.delete_path(('t', 'c')), 't = { a = 1, b = 2 }')
        self.check('t = { a = 1 }', lambda d: d.delete_path(('t', 'a')), 't = {}')
        src = 't = {\n  a = 1,\n  b = 2, # b\n}'
        self.check(src, lambda d: d.delete_path(('t', 'b')), 't = {\n  a = 1,\n}')
        self.check(src, lambda d: d.delete_path(('t', 'a')), 't = {\n  b = 2, # b\n}')
        self.check('t = { a.b = 1, c = 2 }', lambda d: d.delete_path(('t', 'a')), 't = { c = 2 }')
        self.check('t = { a.b = 1, c = 2 }', lambda d: d.delete_path(('t', 'a', 'b')), 't = { c = 2 }')
        self.check('t = { a = { b = 1, c = 2 } }', lambda d: d.delete_path(('t', 'a', 'c')), 't = { a = { b = 1 } }')

    def test_tables(self):
        src = '[a]\nx = 1\n\n[b]\ny = 2\n'
        self.check(src, lambda d: d.delete_path(('a',)), '[b]\ny = 2\n')
        self.check(src, lambda d: d.delete_path(('b',)), '[a]\nx = 1\n')
        self.check('[a]\nx = 1\n[a.b]\ny = 2\n[c]\nz = 3\n', lambda d: d.delete_path(('a',)), '[c]\nz = 3\n')
        self.check(
            '[a]\nx = 1\n[a.b]\ny = 2\n[c]\nz = 3\n',
            lambda d: d.delete_path(('a', 'b')),
            '[a]\nx = 1\n[c]\nz = 3\n',
        )
        self.check('a.x = 1\n[a.b]\ny = 2\n[c]\n', lambda d: d.delete_path(('a',)), '[c]\n')
        self.check('[[f]]\nn = 1\n[[f]]\nn = 2\n', lambda d: d.delete_path(('f', 0)), '[[f]]\nn = 2\n')
        self.check('[[f]]\nn = 1\n[[f]]\nn = 2\n', lambda d: d.delete_path(('f',)), '')
        self.check('[[f]]\nn = 1\n[[f]]\nn = 2\n', lambda d: d.delete_path(('f', 1, 'n')), '[[f]]\nn = 1\n[[f]]\n')
        self.check('[a] # c\nx = 1 # d\n\n\n[b]', lambda d: d.delete_path(('a',)), '[b]')
        self.check('[a]\nx = 1\n\n[b]\ny = 2', lambda d: d.delete_path(('b',)), '[a]\nx = 1\n')
        self.check(
            '[a]\nx = 1\n\n# about b\n[b]\ny = 2\n',
            lambda d: d.delete_path(('a',)),
            '# about b\n[b]\ny = 2\n',
        )
        self.check('  [a]\n  x = 1\n[b]\n', lambda d: d.delete_path(('a',)), '[b]\n')
        self.check('[a]\n', lambda d: d.delete_path(('a',)), '')
        self.check('[a]', lambda d: d.delete_path(('a',)), '')
        self.check('r = 1\n\n[a]\nx = 1\n', lambda d: d.delete_path(('a',)), 'r = 1\n')
        self.check('r = 1\r\n\r\n[a]\r\nx = 1\r\n', lambda d: d.delete_path(('a',)), 'r = 1\r\n')

    def test_errors(self):
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('a = 1').delete_path(('b',))
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('a = 1').delete_path(())
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('a = [1]').delete_path(('a', 3))


class TestAddTable(RewritingTestCase):
    def test_add_table(self):
        self.check(
            'a = 1\n',
            lambda d: d.add_table(('t',), {'k': 'v', 'n': 2, 'd': {'x': 1}}),
            "a = 1\n\n[t]\nk = 'v'\nn = 2\nd = {x = 1}\n",
        )
        self.check('a = 1', lambda d: d.add_table(('t',)), 'a = 1\n\n[t]\n')
        self.check('', lambda d: d.add_table(('t',)), '[t]\n')
        self.check('\n', lambda d: d.add_table(('t',)), '\n[t]\n')
        self.check('a = 1\n\n', lambda d: d.add_table(('t',)), 'a = 1\n\n[t]\n')
        self.check('a = 1\n', lambda d: d.add_table(('t',), array=True), 'a = 1\n\n[[t]]\n')
        self.check('a = 1\n', lambda d: d.add_table(('a b', 'c')), "a = 1\n\n['a b'.c]\n")
        self.check(
            '[[t]]\nx = 1\n',
            lambda d: d.add_table(['t'], {'x': 2}, array=True),
            '[[t]]\nx = 1\n\n[[t]]\nx = 2\n',
        )
        self.check('a = 1\r\n', lambda d: d.add_table(('t',), {'k': 1}), 'a = 1\r\n\r\n[t]\r\nk = 1\r\n')

    def test_errors(self):
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('').add_table(())
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('').add_table(('a', 1))
        with self.assertRaises(TomlDecodeError):
            toml_parse_document('[t]\n').add_table(('t',))


class TestNewlines(RewritingTestCase):
    def test_crlf(self):
        src = 'a = 1\r\n[t]\r\nk = 1\r\n'
        self.check(src, lambda d: d.set_value(('t', 'n'), 2), 'a = 1\r\n[t]\r\nk = 1\r\nn = 2\r\n')
        self.check(src, lambda d: d.set_value(('x',), 2), 'a = 1\r\nx = 2\r\n[t]\r\nk = 1\r\n')
        self.check(src, lambda d: d.add_table(('u',), {'k': 1}), 'a = 1\r\n[t]\r\nk = 1\r\n\r\n[u]\r\nk = 1\r\n')
        self.check('s = """\r\nx"""\r\n', lambda d: d.set_value(('s',), 'p\nq'), 's = """\r\np\nq"""\r\n')
        self.check('a = [\r\n  1,\r\n]\r\n', lambda d: d.set_value(('a', 1), 2), 'a = [\r\n  1,\r\n  2,\r\n]\r\n')
        self.check('a = 1\r\nb = 2\r\n', lambda d: d.delete_path(('a',)), 'b = 2\r\n')

    def test_mixed(self):
        self.check('a = 1\nb = 2\r\n', lambda d: d.set_value(('c',), 3), 'a = 1\nb = 2\r\nc = 3\r\n')
        self.check('a = 1\r\nb = 2\n', lambda d: d.set_value(('c',), 3), 'a = 1\r\nb = 2\nc = 3\n')


class TestChainedEdits(RewritingTestCase):
    def test_chain(self):
        src = '\n'.join([
            '# pyproject-ish',
            '[project]',
            'name = "x"',
            'version = "0.1"',
            'deps = [',
            '  "a",',
            ']',
            '',
            '[tool.om]',
            'flag = false',
            '',
        ])
        doc = toml_parse_document(src)
        out = (
            doc
            .set_value(('project', 'version'), '0.2')
            .set_value(('project', 'deps', 1), 'b>=1')
            .delete_path(('tool', 'om', 'flag'))
            .set_value(('tool', 'om', 'mode'), 'fast')
            .add_table(('tool', 'other'), {'k': [1, 2]})
        )
        self.assertEqual(out.src, '\n'.join([
            '# pyproject-ish',
            '[project]',
            'name = "x"',
            'version = "0.2"',
            'deps = [',
            '  "a",',
            '  "b>=1",',
            ']',
            '',
            '[tool.om]',
            "mode = 'fast'",
            '',
            '[tool.other]',
            'k = [',
            '    1,',
            '    2,',
            ']',
            '',
        ]))
        self.assertEqual(out.data, {
            'project': {'name': 'x', 'version': '0.2', 'deps': ['a', 'b>=1']},
            'tool': {'om': {'mode': 'fast'}, 'other': {'k': [1, 2]}},
        })
        self.assertEqual(doc.src, src)
        self.assertEqual(doc.data['project']['version'], '0.1')


class TestValueRenderer(unittest.TestCase):
    def test_keys(self):
        r = TomlValueRenderer()
        self.assertEqual(r.render_key(('a', 'b-c', 'd e', '', 'f.g')), "a.b-c.'d e'.''.'f.g'")
        self.assertEqual(r.render_key_part('123'), "'123'")
        self.assertEqual(r.render_key_part('_x1'), '_x1')
        self.assertEqual(r.render_key_part(5), "'5'")
        self.assertEqual(r.render_key_part('q"q'), "'q\"q'")
        self.assertEqual(r.render_key_part("q'q"), '"q\'q"')
        self.assertEqual(r.render_key_part(TomlRaw('"raw"')), '"raw"')
        self.assertEqual(TomlValueRenderer(TomlStyle(quotes='basic')).render_key_part('d e'), '"d e"')
        with self.assertRaises(TomlDocumentError):
            r.render_key_part(1.5)

    def test_strings(self):
        r = TomlValueRenderer()
        self.assertEqual(r.render_value('x'), "'x'")
        self.assertEqual(TomlValueRenderer(TomlStyle(quotes='basic')).render_value('x'), '"x"')
        self.assertEqual(r.render_value("it's"), '"it\'s"')
        self.assertEqual(r.render_value('a\nb'), '"a\\nb"')
        self.assertEqual(r.render_str('x', like='LITERAL_STRING'), "'x'")
        self.assertEqual(r.render_str('a\nb', like='ML_LITERAL_STRING'), "'''\na\nb'''")
        self.assertEqual(TomlValueRenderer(newline='\r\n').render_str('a\nb', like='ML_BASIC_STRING'), '"""\r\na\nb"""')


class TestStyleAndPlacement(RewritingTestCase):
    def test_style_from_parse(self):
        st = TomlStyle(quotes='basic', array_layout='inline', inline_table_padding=' ')
        doc = toml_parse_document('a = 1\n', style=st)
        out = doc.set_value(('b',), ['x', {'k': 1}]).set_value(('c',), 's')
        self.assertEqual(out.src, 'a = 1\nb = ["x", { k = 1 }]\nc = "s"\n')
        self.assertIs(out.style, st)
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('', style=TomlStyle(quotes='fancy')).set_value(('a',), 1)

    def test_default_style_new_arrays_are_multiline(self):
        self.check('a = 1\n', lambda d: d.set_value(('b',), [1, 'x']), "a = 1\nb = [\n    1,\n    'x',\n]\n")
        self.check(
            '[t]\n  a = 1\n',
            lambda d: d.set_value(('t', 'b'), [1]),
            '[t]\n  a = 1\n  b = [\n      1,\n  ]\n',
        )
        self.check('a = 1\n', lambda d: d.set_value(('b',), [[1], {'k': [2]}]), 'a = 1\nb = [\n    [\n        1,\n    ],\n    {k = [2]},\n]\n')  # noqa: E501

    def test_auto_layout(self):
        st = TomlStyle(array_layout='auto', max_inline_width=20)
        doc = toml_parse_document('', style=st)
        self.assertEqual(doc.set_value(('a',), [1, 2, 3]).src, 'a = [1, 2, 3]\n')
        self.assertEqual(doc.set_value(('a',), [[1], 2]).src, 'a = [\n    [1],\n    2,\n]\n')
        self.assertEqual(
            doc.set_value(('a',), ['x' * 10, 'y' * 10]).src,
            "a = [\n    'xxxxxxxxxx',\n    'yyyyyyyyyy',\n]\n",
        )

    def test_replace_keeps_container_layout(self):
        self.check('a = [\n  1,\n]\n', lambda d: d.set_value(('a',), [2, 3]), 'a = [\n    2,\n    3,\n]\n')
        self.check('a = [1]\n', lambda d: d.set_value(('a',), [2, 3]), 'a = [2, 3]\n')
        self.check('a = [1]\n', lambda d: d.set_value(('a', 0), [2, 3]), 'a = [[2, 3]]\n')
        self.check('a = [\n  1,\n]\n', lambda d: d.set_value(('a', 0), [2]), 'a = [\n  [\n      2,\n  ],\n]\n')
        self.check('t = { a = 1 }\n', lambda d: d.set_value(('t', 'a'), [2, 3]), 't = { a = [2, 3] }\n')
        self.check(
            't = {\n  a = 1,\n}\n',
            lambda d: d.set_value(('t', 'a'), [2]),
            't = {\n  a = [\n      2,\n  ],\n}\n',
        )

    def test_sibling_mimicry(self):
        self.check('a = ["x"]\n', lambda d: d.set_value(('a', 1), 'y'), 'a = ["x", "y"]\n')
        self.check("a = ['x']\n", lambda d: d.set_value(('a', 1), 'y'), "a = ['x', 'y']\n")
        self.check('a = [1]\n', lambda d: d.set_value(('a', 1), 'y'), "a = [1, 'y']\n")
        self.check('t = { a = "x" }\n', lambda d: d.set_value(('t', 'b'), 'y'), 't = { a = "x", b = "y" }\n')
        self.check('a = [0x1]\n', lambda d: d.set_value(('a', 1), 255), 'a = [0x1, 0xff]\n')
        self.check('a = [0x1]\n', lambda d: d.set_value(('a', 1), 'z'), "a = [0x1, 'z']\n")

    def test_markers(self):
        self.check('a = 1\n', lambda d: d.set_value(('b',), TomlInline([1, 2])), 'a = 1\nb = [1, 2]\n')
        self.check('a = 1\n', lambda d: d.set_value(('b',), TomlRaw('[ 1 ]')), 'a = 1\nb = [ 1 ]\n')
        self.check('a = [1, 2]\n', lambda d: d.set_value(('a',), TomlMultiline([3])), 'a = [\n    3,\n]\n')
        self.check('a = 1\n', lambda d: d.set_value(('b',), [TomlInline([1, 2])]), 'a = 1\nb = [\n    [1, 2],\n]\n')
        with self.assertRaises(TomlDocumentError):
            toml_parse_document('').set_value(('a',), TomlMultiline({'k': 1}))
        doc = toml_parse_document('', style=TomlStyle(toml_1_1=True))
        self.assertEqual(doc.set_value(('a',), TomlMultiline({'k': 1})).src, 'a = {\n    k = 1,\n}\n')

    def test_add_table_placement(self):
        src = '[a]\nx = 1\n\n[c]\nz = 3\n'
        self.check(
            src,
            lambda d: d.add_table(('b',), {'y': 2}, after=('a',)),
            '[a]\nx = 1\n\n[b]\ny = 2\n\n[c]\nz = 3\n',
        )
        self.check(src, lambda d: d.add_table(('b',), after=('c',)), '[a]\nx = 1\n\n[c]\nz = 3\n\n[b]\n')
        self.check('[a]\nx = 1', lambda d: d.add_table(('b',), after=('a',)), '[a]\nx = 1\n\n[b]\n')
        self.check('r = 1\n[a]\n', lambda d: d.add_table(('b',), after=()), 'r = 1\n\n[b]\n[a]\n')
        self.check('# c\n[a]\n', lambda d: d.add_table(('b',), after=()), '# c\n[b]\n\n[a]\n')
        self.check('', lambda d: d.add_table(('b',), after=()), '[b]\n')
        with self.assertRaises(TomlDocumentError):
            toml_parse_document(src).add_table(('b',), after=('nope',))

    def test_add_table_comments_and_spacing(self):
        self.check(
            '[a]\n',
            lambda d: d.add_table(('b',), comments=['##', 'about b', '']),
            '[a]\n\n##\n# about b\n#\n[b]\n',
        )
        doc = toml_parse_document('[a]\n', style=TomlStyle(blank_lines_between_tables=2))
        self.assertEqual(doc.add_table(('b',)).src, '[a]\n\n\n[b]\n')
        self.assertEqual(doc.add_table(('b',), after=('a',)).src, '[a]\n\n\n[b]\n')
        self.assertEqual(doc.add_table(('b',)).add_table(('c',), after=('a',)).src, '[a]\n\n\n[c]\n\n\n[b]\n')
