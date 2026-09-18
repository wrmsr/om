# ruff: noqa: DTZ001 UP017
# @om-lite
import datetime
import unittest

from ..parser import TomlTokenKinds as K
from ..parser import toml_loads
from ..parser import toml_parse_document


def kinds_and_raws(src):
    return [(t.kind, t.raw) for t in toml_parse_document(src).tokens]


def line_col(doc, kind, raw, n=0):
    return [(t.line, t.col) for t in doc.tokens if t.kind == kind and t.raw == raw][n]


ROUNDTRIP_SRCS = [
    '',
    '   ',
    '\n\n',
    '\t\n \t',
    '# only',
    '# c1\n# c2\n',
    'a=1',
    'a = 1 # c',
    'a = 1\n',
    '  a  =  1  \n\n',
    'a."b c".\'d\' = [ 1 , 2 , ]',
    's = """\n  multi\n  line \\\n  joined"""\nt = \'\'\'\nraw\'\'\'\n',
    'a = [\n  1, # one\n\n  # standalone\n  [2, [3]],\n]\n',
    't = {\n  a = 1, # a\n  b = { c = [] },\n}\n',
    '[ t . u ]  # c\n  k = 1\n[[ a ]]\n[a.b]\nx = 1979-05-27T07:32:00Z\n',
    'a = 1\r\nb = 2\r\n',
    'a = 1\nb = 2\r\nc = 3\n',
    's = """x\r\ny"""\r\n',
    "s = '''x\r\ny'''\r\n",
]


class TestTokens(unittest.TestCase):
    def assert_partition(self, src):
        doc = toml_parse_document(src)
        self.assertEqual(''.join(t.raw for t in doc.tokens), src)
        ofs = 0
        for t in doc.tokens:
            self.assertEqual(t.ofs, ofs)
            self.assertEqual(t.end, ofs + len(t.raw))
            self.assertNotEqual(t.raw, '')
            ofs = t.end
        self.assertEqual(ofs, len(src))
        self.assertEqual(doc.data, toml_loads(src))
        self.assertEqual(doc.src, src)
        return doc

    def test_partition_roundtrip(self):
        for src in ROUNDTRIP_SRCS:
            with self.subTest(src=src):
                self.assert_partition(src)

    def test_empty(self):
        doc = toml_parse_document('')
        self.assertEqual(list(doc.tokens), [])
        self.assertEqual(doc.data, {})

    def test_simple_statement(self):
        self.assertEqual(kinds_and_raws('a = 1 # c\n'), [
            (K.BARE_KEY, 'a'),
            (K.WS, ' '),
            (K.EQUALS, '='),
            (K.WS, ' '),
            (K.INTEGER, '1'),
            (K.WS, ' '),
            (K.COMMENT, '# c'),
            (K.NEWLINE, '\n'),
        ])

    def test_table_headers(self):
        self.assertEqual(kinds_and_raws('[t]\n[[ a . "b" ]]'), [
            (K.TABLE_OPEN, '['),
            (K.BARE_KEY, 't'),
            (K.TABLE_CLOSE, ']'),
            (K.NEWLINE, '\n'),
            (K.ARRAY_TABLE_OPEN, '[['),
            (K.WS, ' '),
            (K.BARE_KEY, 'a'),
            (K.WS, ' '),
            (K.DOT, '.'),
            (K.WS, ' '),
            (K.BASIC_STRING, '"b"'),
            (K.WS, ' '),
            (K.ARRAY_TABLE_CLOSE, ']]'),
        ])

    def test_arrays_and_inline_tables(self):
        self.assertEqual(kinds_and_raws("a = [1, 'x', # c\n  { b = true },\n]"), [
            (K.BARE_KEY, 'a'),
            (K.WS, ' '),
            (K.EQUALS, '='),
            (K.WS, ' '),
            (K.ARRAY_OPEN, '['),
            (K.INTEGER, '1'),
            (K.COMMA, ','),
            (K.WS, ' '),
            (K.LITERAL_STRING, "'x'"),
            (K.COMMA, ','),
            (K.WS, ' '),
            (K.COMMENT, '# c'),
            (K.NEWLINE, '\n'),
            (K.WS, '  '),
            (K.INLINE_TABLE_OPEN, '{'),
            (K.WS, ' '),
            (K.BARE_KEY, 'b'),
            (K.WS, ' '),
            (K.EQUALS, '='),
            (K.WS, ' '),
            (K.BOOL, 'true'),
            (K.WS, ' '),
            (K.INLINE_TABLE_CLOSE, '}'),
            (K.COMMA, ','),
            (K.NEWLINE, '\n'),
            (K.ARRAY_CLOSE, ']'),
        ])

    def test_scalar_kinds_and_values(self):
        src = '\n'.join([
            's1 = "b\\tq"',
            "s2 = 'lit'",
            's3 = """\nml\nb"""',
            "s4 = '''ml\nl'''",
            'i = 0x10',
            'f = 1.5',
            'f2 = -inf',
            'b = false',
            'odt = 1979-05-27T07:32:00Z',
            'ldt = 1979-05-27T07:32:00',
            'ld = 1979-05-27',
            'lt = 07:32:00',
        ])
        doc = self.assert_partition(src)
        expected = {
            's1': (K.BASIC_STRING, '"b\\tq"', 'b\tq'),
            's2': (K.LITERAL_STRING, "'lit'", 'lit'),
            's3': (K.ML_BASIC_STRING, '"""\nml\nb"""', 'ml\nb'),
            's4': (K.ML_LITERAL_STRING, "'''ml\nl'''", 'ml\nl'),
            'i': (K.INTEGER, '0x10', 16),
            'f': (K.FLOAT, '1.5', 1.5),
            'f2': (K.FLOAT, '-inf', float('-inf')),
            'b': (K.BOOL, 'false', False),
            'odt': (K.OFFSET_DATETIME, '1979-05-27T07:32:00Z', datetime.datetime(1979, 5, 27, 7, 32, tzinfo=datetime.timezone.utc)),  # noqa: E501
            'ldt': (K.LOCAL_DATETIME, '1979-05-27T07:32:00', datetime.datetime(1979, 5, 27, 7, 32)),
            'ld': (K.LOCAL_DATE, '1979-05-27', datetime.date(1979, 5, 27)),
            'lt': (K.LOCAL_TIME, '07:32:00', datetime.time(7, 32)),
        }
        seen = set()
        for k, (kind, raw, value) in expected.items():
            with self.subTest(key=k):
                tok = doc.node_at_path((k,)).token
                self.assertEqual(tok.kind, kind)
                self.assertEqual(tok.raw, raw)
                self.assertEqual(tok.value, value)
                self.assertIs(tok.value, doc.data[k])
                seen.add(kind)
        self.assertEqual(seen, set(K.SCALARS))

    def test_key_tokens(self):
        doc = toml_parse_document('a."b c".\'d\' = 1')
        toks = list(doc.tokens)
        self.assertEqual([(t.kind, t.raw, t.value) for t in toks[:5]], [
            (K.BARE_KEY, 'a', 'a'),
            (K.DOT, '.', None),
            (K.BASIC_STRING, '"b c"', 'b c'),
            (K.DOT, '.', None),
            (K.LITERAL_STRING, "'d'", 'd'),
        ])
        self.assertEqual(doc.data, {'a': {'b c': {'d': 1}}})

    def test_non_value_tokens_have_no_value(self):
        doc = toml_parse_document('[ t ]\na = [ 1, { b = "x" } ] # c\n')
        for t in doc.tokens:
            if t.kind not in K.SCALARS and t.kind != K.BARE_KEY:
                self.assertIsNone(t.value, t)

    def test_all_kinds_emitted(self):
        src = '\n'.join([
            '# c',
            'a . "b" = 1',
            "'c' = [1.5, true, 1979-05-27, 07:32:00, 1979-05-27T07:32:00, 1979-05-27T07:32:00Z]",
            'd = { e = """x""", f = \'\'\'y\'\'\' }',
            '[t]',
            '[[u]]',
        ])
        seen = {t.kind for t in toml_parse_document(src).tokens}
        all_kinds = {v for k, v in vars(K).items() if k.isupper() and isinstance(v, str)}
        self.assertEqual(seen, all_kinds)

    def test_crlf_tokens(self):
        src = 'a = 1\r\nb = """x\r\ny"""\r\n\r\n[t]\r\nc = [\r\n  1,\r\n]\r\n'
        doc = self.assert_partition(src)
        nls = [t for t in doc.tokens if t.kind == K.NEWLINE]
        self.assertEqual(len(nls), 7)
        self.assertTrue(all(t.raw == '\r\n' for t in nls))
        self.assertEqual(doc.newline, '\r\n')

        ml = doc.node_at_path(('b',)).token
        self.assertEqual(ml.raw, '"""x\r\ny"""')
        self.assertEqual(ml.value, 'x\ny')

        self.assertEqual(line_col(doc, K.BARE_KEY, 'b'), (2, 1))
        self.assertEqual(line_col(doc, K.TABLE_OPEN, '['), (5, 1))
        self.assertEqual(line_col(doc, K.BARE_KEY, 'c'), (6, 1))
        self.assertEqual(line_col(doc, K.ARRAY_OPEN, '['), (6, 5))
        self.assertEqual(line_col(doc, K.INTEGER, '1', 1), (7, 3))
        self.assertEqual(line_col(doc, K.ARRAY_CLOSE, ']'), (8, 1))

    def test_mixed_newlines(self):
        doc = self.assert_partition('a = 1\nb = 2\r\nc = 3\n')
        self.assertEqual([t.raw for t in doc.tokens if t.kind == K.NEWLINE], ['\n', '\r\n', '\n'])
        self.assertEqual(doc.newline, '\n')

    def test_line_and_col(self):
        src = 'a = 1\n  bb = """x\ny"""  # c\n[t]\n'
        doc = self.assert_partition(src)
        self.assertEqual(line_col(doc, K.BARE_KEY, 'a'), (1, 1))
        self.assertEqual(line_col(doc, K.INTEGER, '1'), (1, 5))
        self.assertEqual(line_col(doc, K.WS, '  ', 0), (2, 1))
        self.assertEqual(line_col(doc, K.BARE_KEY, 'bb'), (2, 3))
        self.assertEqual(line_col(doc, K.ML_BASIC_STRING, '"""x\ny"""'), (2, 8))
        self.assertEqual(line_col(doc, K.WS, '  ', 1), (3, 5))
        self.assertEqual(line_col(doc, K.COMMENT, '# c'), (3, 7))
        self.assertEqual(line_col(doc, K.TABLE_OPEN, '['), (4, 1))

    def test_tokens_dont_change_parse(self):
        for src in ROUNDTRIP_SRCS:
            with self.subTest(src=src):
                self.assertEqual(toml_parse_document(src).data, toml_loads(src))
