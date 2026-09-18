# @om-lite
import unittest

from ....lite.check import check
from ..parser import TomlArrayNode
from ..parser import TomlDocumentError
from ..parser import TomlInlineTableNode
from ..parser import TomlKeyNode
from ..parser import TomlKeyValueNode
from ..parser import TomlParser
from ..parser import TomlScalarNode
from ..parser import TomlTableHeaderNode
from ..parser import TomlTableNode
from ..parser import TomlTokenKinds as K
from ..parser import toml_parse_document


SRC = '\n'.join([
    '# leading comment',
    'title = "t"',
    'a . b = [1, [2, 3]]',
    'inline = { x = 1, y.z = "q" }',
    '',
    '[owner]  # header comment',
    "name = 'me'",
    '',
    '[servers.alpha]',
    'ip = "1"',
    '',
    '[[fruits]]',
    'name = "apple"',
    '[fruits.physical]',
    'color = "red"',
    '[[fruits]]',
    'name = "banana"',
    '',
])


class TestDocument(unittest.TestCase):
    def setUp(self):
        self.doc = toml_parse_document(SRC)

    def test_tables(self):
        doc = self.doc
        tbls = doc.tables
        self.assertEqual([t.path for t in tbls], [
            (),
            ('owner',),
            ('servers', 'alpha'),
            ('fruits', 0),
            ('fruits', 0, 'physical'),
            ('fruits', 1),
        ])
        self.assertIs(tbls[0], doc.root)
        self.assertTrue(doc.root.is_root)
        self.assertIsNone(doc.root.header)
        self.assertEqual([t.is_array for t in tbls], [False, False, False, True, False, True])
        self.assertEqual([check.not_none(t.header).raw for t in tbls[1:]], [
            '[owner]',
            '[servers.alpha]',
            '[[fruits]]',
            '[fruits.physical]',
            '[[fruits]]',
        ])
        self.assertEqual([check.not_none(t.header).key.key for t in tbls[1:]], [
            ('owner',),
            ('servers', 'alpha'),
            ('fruits',),
            ('fruits', 'physical'),
            ('fruits',),
        ])
        self.assertEqual([len(t.pairs) for t in tbls], [3, 1, 1, 1, 1, 1])

        self.assertEqual(doc.root.raw, 'title = "t"\na . b = [1, [2, 3]]\ninline = { x = 1, y.z = "q" }')
        self.assertEqual(tbls[1].raw, "[owner]  # header comment\nname = 'me'")
        self.assertEqual(tbls[3].raw, '[[fruits]]\nname = "apple"')

        d = doc.data
        self.assertIs(doc.root.value, d)
        self.assertIs(tbls[1].value, d['owner'])
        self.assertIs(tbls[2].value, d['servers']['alpha'])
        self.assertIs(tbls[3].value, d['fruits'][0])
        self.assertIs(tbls[4].value, d['fruits'][0]['physical'])
        self.assertIs(tbls[5].value, d['fruits'][1])

    def test_key_value_nodes(self):
        doc = self.doc
        kv = check.not_none(doc.key_value_at_path(('a', 'b')))
        self.assertEqual(kv.raw, 'a . b = [1, [2, 3]]')
        self.assertEqual(kv.key.raw, 'a . b')
        self.assertEqual(kv.key.key, ('a', 'b'))
        self.assertEqual(kv.path, ('a', 'b'))
        self.assertIsInstance(kv.value, TomlArrayNode)
        self.assertIs(doc.parent_of(kv), doc.root)

        kv2 = check.not_none(doc.key_value_at_path(('inline', 'y', 'z')))
        self.assertEqual(kv2.raw, 'y.z = "q"')
        self.assertIsInstance(doc.parent_of(kv2), TomlInlineTableNode)

        self.assertIsNone(doc.key_value_at_path(('owner',)))
        self.assertIsNone(doc.key_value_at_path(('nope',)))

    def test_value_nodes(self):
        doc = self.doc
        arr = check.isinstance(doc.node_at_path(('a', 'b')), TomlArrayNode)
        self.assertEqual(arr.raw, '[1, [2, 3]]')
        self.assertEqual([i.path for i in arr.items], [('a', 'b', 0), ('a', 'b', 1)])
        inner = check.isinstance(arr.items[1], TomlArrayNode)
        self.assertEqual(inner.items[0].path, ('a', 'b', 1, 0))
        self.assertEqual(inner.items[0].value, 2)
        self.assertIs(arr.value, doc.data['a']['b'])
        self.assertIs(inner.value, doc.data['a']['b'][1])

        it = check.isinstance(doc.node_at_path(('inline',)), TomlInlineTableNode)
        self.assertEqual([p.path for p in it.pairs], [('inline', 'x'), ('inline', 'y', 'z')])
        self.assertEqual(it.raw, '{ x = 1, y.z = "q" }')

        sc = check.isinstance(doc.node_at_path(('owner', 'name')), TomlScalarNode)
        self.assertEqual(sc.token.kind, K.LITERAL_STRING)
        self.assertEqual(sc.raw, "'me'")
        self.assertEqual(sc.value, 'me')

        self.assertEqual(check.not_none(doc.node_at_path(('fruits', 0, 'physical', 'color'))).value, 'red')
        self.assertEqual(check.not_none(doc.node_at_path(('fruits', 1, 'name'))).raw, '"banana"')
        self.assertEqual(check.not_none(doc.node_at_path(['a', 'b', 1, 1])).value, 3)

    def test_lookup_misses(self):
        doc = self.doc
        self.assertIsNone(doc.node_at_path(('a',)))
        self.assertIsNone(doc.node_at_path(('servers',)))
        self.assertIsNone(doc.node_at_path(('fruits',)))
        self.assertIsNone(doc.node_at_path(('nope',)))
        self.assertIsNone(doc.node_at_path(('a', 'b', 5)))
        self.assertIsNone(doc.node_at_path(('inline', 'y')))
        self.assertIs(doc.node_at_path(()), doc.root)

        self.assertIs(doc.table_at_path(('owner',)), doc.tables[1])
        self.assertIsNone(doc.table_at_path(('title',)))
        self.assertIsNone(doc.table_at_path(('inline',)))
        self.assertTrue(check.not_none(doc.table_at_path(('fruits', 1))).is_array)

    def test_node_for_value(self):
        doc = self.doc
        d = doc.data
        self.assertIs(doc.node_for_value(d), doc.root)
        self.assertIs(doc.node_for_value(d['owner']), doc.tables[1])
        self.assertEqual(check.not_none(doc.node_for_value(d['a']['b'])).path, ('a', 'b'))
        self.assertEqual(check.not_none(doc.node_for_value(d['a']['b'][1])).path, ('a', 'b', 1))
        self.assertIs(doc.node_for_value(d['fruits'][1]), doc.tables[5])
        self.assertEqual(check.not_none(doc.node_for_value(d['inline'])).path, ('inline',))
        self.assertIsNone(doc.node_for_value(d['a']))
        self.assertIsNone(doc.node_for_value(d['fruits']))
        self.assertIsNone(doc.node_for_value(d['inline']['y']))
        self.assertIsNone(doc.node_for_value({}))
        self.assertIsNone(doc.node_for_value([]))
        self.assertIsNone(doc.node_for_value('t'))

    def test_node_at_offset(self):
        doc = self.doc
        sc = check.isinstance(doc.node_at_offset(SRC.index('"t"')), TomlScalarNode)
        self.assertEqual(sc.path, ('title',))

        kn = check.isinstance(doc.node_at_offset(SRC.index('title')), TomlKeyNode)
        self.assertEqual(kn.key, ('title',))

        kv = check.isinstance(doc.node_at_offset(SRC.index(' = [1')), TomlKeyValueNode)
        self.assertEqual(kv.path, ('a', 'b'))

        arr = check.isinstance(doc.node_at_offset(SRC.index('[2, 3]')), TomlArrayNode)
        self.assertEqual(arr.path, ('a', 'b', 1))

        sc = check.isinstance(doc.node_at_offset(SRC.index('3]')), TomlScalarNode)
        self.assertEqual(sc.path, ('a', 'b', 1, 1))

        self.assertIsNone(doc.node_at_offset(SRC.index('# leading')))

        tbl = check.isinstance(doc.node_at_offset(SRC.index('# header comment')), TomlTableNode)
        self.assertEqual(tbl.path, ('owner',))

        check.isinstance(doc.node_at_offset(SRC.index('[owner]')), TomlTableHeaderNode)
        check.isinstance(doc.node_at_offset(SRC.index('owner]')), TomlKeyNode)

        self.assertIsNone(doc.node_at_offset(SRC.index('\n\n[owner]') + 1))
        self.assertIsNone(doc.node_at_offset(len(SRC)))
        self.assertIsNone(doc.node_at_offset(-1))

    def test_parents_and_walk(self):
        doc = self.doc
        sc = check.not_none(doc.node_at_path(('owner', 'name')))
        kv = check.isinstance(doc.parent_of(sc), TomlKeyValueNode)
        self.assertIs(doc.parent_of(kv), doc.tables[1])
        self.assertIsNone(doc.parent_of(doc.tables[1]))
        self.assertIs(doc.parent_of(check.not_none(doc.tables[1].header)), doc.tables[1])

        item = check.not_none(doc.node_at_path(('a', 'b', 1, 0)))
        self.assertEqual(check.isinstance(doc.parent_of(item), TomlArrayNode).path, ('a', 'b', 1))

        self.assertEqual([type(n).__name__ for n in doc.tables[1].walk()], [
            'TomlTableNode',
            'TomlTableHeaderNode',
            'TomlKeyNode',
            'TomlKeyValueNode',
            'TomlKeyNode',
            'TomlScalarNode',
        ])

    def test_root_without_pairs(self):
        doc = toml_parse_document('# c\n[t]\nx = 1\n')
        self.assertEqual((doc.root.start, doc.root.end), (0, 0))
        self.assertEqual(doc.root.raw, '')
        self.assertEqual(doc.root.pairs, ())
        self.assertIs(doc.root.value, doc.data)
        self.assertEqual(len(doc.tables), 2)

        doc = toml_parse_document('')
        self.assertEqual(len(doc.tables), 1)
        self.assertEqual(doc.root.raw, '')
        self.assertEqual((doc.root.ofs, doc.root.end_ofs), (0, 0))
        self.assertIsNone(doc.node_at_offset(0))

    def test_table_spans_exclude_trailing_trivia(self):
        doc = toml_parse_document('[a]\nx = 1 # c\n\n# next\n[b]\n')
        self.assertEqual(doc.tables[1].raw, '[a]\nx = 1')
        self.assertEqual(doc.tables[2].raw, '[b]')
        self.assertEqual(doc.tables[2].pairs, ())

    def test_keys_exclude_whitespace(self):
        doc = toml_parse_document('[ t . u ]\nk   =  1\n')
        hdr = check.not_none(doc.tables[1].header)
        self.assertEqual(hdr.key.raw, 't . u')
        self.assertEqual(hdr.raw, '[ t . u ]')
        kv = doc.tables[1].pairs[0]
        self.assertEqual(kv.key.raw, 'k')
        self.assertEqual(kv.raw, 'k   =  1')

    def test_array_of_tables_paths(self):
        doc = toml_parse_document('[[a]]\n[[a.b]]\nx = 1\n[[a.b]]\n[[a]]\n[[a.b]]\ny = 2\n[a.c]\n')
        self.assertEqual([t.path for t in doc.tables], [
            (),
            ('a', 0),
            ('a', 0, 'b', 0),
            ('a', 0, 'b', 1),
            ('a', 1),
            ('a', 1, 'b', 0),
            ('a', 1, 'c'),
        ])
        self.assertEqual(check.not_none(doc.node_at_path(('a', 0, 'b', 0, 'x'))).value, 1)
        self.assertEqual(check.not_none(doc.node_at_path(('a', 1, 'b', 0, 'y'))).value, 2)

    def test_dotted_keys_under_array_of_tables(self):
        doc = toml_parse_document('[[a]]\nb.c = 1\n[[a]]\nb.c = 2\n')
        self.assertEqual(check.not_none(doc.node_at_path(('a', 0, 'b', 'c'))).value, 1)
        self.assertEqual(check.not_none(doc.node_at_path(('a', 1, 'b', 'c'))).value, 2)
        self.assertIsNone(doc.node_at_path(('a', 1, 'b')))

    def test_nodes_hashable_and_equal(self):
        doc = self.doc
        n = check.not_none(doc.node_at_path(('title',)))
        self.assertEqual(hash(n), hash(n))
        self.assertEqual(n, n)
        self.assertNotEqual(n, doc.node_at_path(('owner', 'name')))
        self.assertEqual(len({doc.root, doc.tables[1], doc.root}), 2)

    def test_parser_document_access(self):
        p = TomlParser('a = 1')
        p.parse()
        with self.assertRaises(TomlDocumentError):
            p.document()

        p = TomlParser('a = 1', build_document=True)
        with self.assertRaises(TomlDocumentError):
            p.document()
        p.parse()
        doc = p.document()
        self.assertEqual(doc.data, {'a': 1})
        self.assertEqual(doc.src, 'a = 1')

    def test_type_error(self):
        with self.assertRaises(TypeError):
            toml_parse_document(b'a = 1')  # type: ignore

    def test_newline(self):
        self.assertEqual(toml_parse_document('').newline, '\n')
        self.assertEqual(toml_parse_document('a = 1').newline, '\n')
        self.assertEqual(toml_parse_document('a = 1\r\n').newline, '\r\n')
        self.assertEqual(toml_parse_document('a = """\r\n"""\nb = 1\r\n').newline, '\n')
