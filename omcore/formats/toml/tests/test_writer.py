# ruff: noqa: UP006
# @om-lite
import typing as ta
import unittest

from ..parser import TomlDocumentError
from ..parser import TomlInline
from ..parser import TomlMultiline
from ..parser import TomlRaw
from ..parser import TomlStyle
from ..parser import toml_loads
from ..writer import TomlBuilder
from ..writer import toml_dumps


class TestTomlDumps(unittest.TestCase):
    def test_legacy_writer_output(self):
        d: ta.Dict[str, ta.Any] = {
            'build-system': {
                'requires': ['setuptools'],
                'build-backend': 'setuptools.build_meta',
            },
            'project': {
                'name': 'omcore',
                'authors': [{'name': 'wrmsr'}],
                'urls': {'source': 'https://github.com/wrmsr/om'},
                'version': '0.0.59',
                'classifiers': [],
            },
            'project.optional-dependencies': {
                'async': ['anyio ~= 4.15', 'trio ~= 0.34'],
            },
            'project.entry-points': {
                'omcore.manifests': {'omcore': 'omcore'},
            },
            'tool.setuptools.package-data': {
                '*': ['*.c', '*.h'],
            },
        }
        expected = '\n'.join([
            '[build-system]',
            'requires = [',
            "    'setuptools',",
            ']',
            "build-backend = 'setuptools.build_meta'",
            '',
            '[project]',
            "name = 'omcore'",
            'authors = [',
            "    {name = 'wrmsr'},",
            ']',
            "urls = {source = 'https://github.com/wrmsr/om'}",
            "version = '0.0.59'",
            'classifiers = []',
            '',
            '[project.optional-dependencies]',
            'async = [',
            "    'anyio ~= 4.15',",
            "    'trio ~= 0.34',",
            ']',
            '',
            '[project.entry-points]',
            "'omcore.manifests' = {omcore = 'omcore'}",
            '',
            '[tool.setuptools.package-data]',
            "'*' = [",
            "    '*.c',",
            "    '*.h',",
            ']',
            '',
        ])
        self.assertEqual(toml_dumps(d), expected)
        self.assertEqual(toml_loads(expected), {
            'build-system': d['build-system'],
            'project': {
                **d['project'],
                'optional-dependencies': d['project.optional-dependencies'],
                'entry-points': d['project.entry-points'],
            },
            'tool': {'setuptools': {'package-data': d['tool.setuptools.package-data']}},
        })

    def test_root_pairs_before_tables(self):
        self.assertEqual(toml_dumps({'t': {'b': 2}, 'a': 1}), 'a = 1\n\n[t]\nb = 2\n')

    def test_empty(self):
        self.assertEqual(toml_dumps({}), '')

    def test_nested_mappings_are_inline_tables(self):
        self.assertEqual(toml_dumps({'t': {'a': {'b': {'c': 1}}}}), '[t]\na = {b = {c = 1}}\n')

    def test_inline_root_mapping(self):
        self.assertEqual(toml_dumps({'a': TomlInline({'x': 1})}), 'a = {x = 1}\n')

    def test_path_keys(self):
        self.assertEqual(
            toml_dumps({('a.b', 'c'): {'k': 1}, 'd.e': {'k': 2}}),
            "['a.b'.c]\nk = 1\n\n[d.e]\nk = 2\n",
        )

    def test_key_quoting(self):
        self.assertEqual(
            toml_dumps({'t': {'8': 1, '_x': 2, 'a b': 3, 5: 4, TomlRaw("'q'"): 5}}),
            "[t]\n'8' = 1\n_x = 2\n'a b' = 3\n'5' = 4\n'q' = 5\n",
        )

    def test_styles(self):
        st = TomlStyle(quotes='basic', array_layout='auto', inline_table_padding=' ')
        d = {'t': {
            'short': ['a', 'b'],
            'nested': [['a'], {'k': 'v'}],
            'long': ['x' * 30] * 3,
            'it': {'k': [1]},
            'e': [],
        }}
        expected = '\n'.join([
            '[t]',
            'short = ["a", "b"]',
            'nested = [',
            '    ["a"],',
            '    { k = "v" },',
            ']',
            'long = [',
            '    "' + 'x' * 30 + '",',
            '    "' + 'x' * 30 + '",',
            '    "' + 'x' * 30 + '",',
            ']',
            'it = { k = [1] }',
            'e = []',
            '',
        ])
        self.assertEqual(toml_dumps(d, style=st), expected)
        self.assertEqual(toml_loads(expected), d)

    def test_invalid_style(self):
        with self.assertRaises(TomlDocumentError):
            toml_dumps({}, style=TomlStyle(quotes='fancy'))
        with self.assertRaises(TomlDocumentError):
            toml_dumps({}, style=TomlStyle(array_layout='zig'))


class TestTomlBuilder(unittest.TestCase):
    def test_pyproject_like(self):
        b = TomlBuilder()
        b.comment('##').comment('pyproject')
        b.table('tool.om.pyproject', {'pkgs': ['omcore', 'omdev']})
        b.table('tool.om.pyproject.srcs')
        b.pair('main', ['omcore', 'omdev'])
        b.pair('all', ['@main', 'x'], layout='inline')
        b.blank().comment('#')
        b.table('tool.om.pyproject.venvs._defaults', {
            'requires': TomlInline(['-rrequirements-dev.txt']),
            'use_uv': True,
        })
        b.blank(2).comment('#')
        b.table(
            ('tool', 'om', 'pyproject', 'venvs', '8'),
            {'inherits': TomlInline(['_lite']), 'interp': '@8'},
            comments=['lite'],
        )
        expected = '\n'.join([
            '##',
            '# pyproject',
            '',
            '[tool.om.pyproject]',
            'pkgs = [',
            "    'omcore',",
            "    'omdev',",
            ']',
            '',
            '[tool.om.pyproject.srcs]',
            'main = [',
            "    'omcore',",
            "    'omdev',",
            ']',
            "all = ['@main', 'x']",
            '',
            '#',
            '',
            '[tool.om.pyproject.venvs._defaults]',
            "requires = ['-rrequirements-dev.txt']",
            'use_uv = true',
            '',
            '',
            '#',
            '',
            '# lite',
            "[tool.om.pyproject.venvs.'8']",
            "inherits = ['_lite']",
            "interp = '@8'",
            '',
        ])
        self.assertEqual(b.render(), expected)
        doc = b.document()
        self.assertEqual(doc.data['tool']['om']['pyproject']['venvs']['8'], {'inherits': ['_lite'], 'interp': '@8'})
        self.assertEqual(doc.data['tool']['om']['pyproject']['srcs']['all'], ['@main', 'x'])

    def test_comments_and_blanks(self):
        b = TomlBuilder()
        b.comment('a\nb').comment().comment('#c').blank().pair('k', 1, comment='why').raw('x = 2 # raw\n')
        self.assertEqual(b.render(), '# a\n# b\n#\n#c\n\nk = 1  # why\nx = 2 # raw\n')
        self.assertEqual(b.document().data, {'k': 1, 'x': 2})

    def test_layouts(self):
        b = TomlBuilder()
        b.pair('a', [1, 2], layout='inline')
        b.pair('b', [1], layout='multiline')
        b.pair('c', TomlInline([{'k': [1]}]))
        b.pair('d', [TomlInline([1, 2])])
        self.assertEqual(b.render(), 'a = [1, 2]\nb = [\n    1,\n]\nc = [{k = [1]}]\nd = [\n    [1, 2],\n]\n')
        with self.assertRaises(TomlDocumentError):
            b.pair('e', 1, layout='zig')

    def test_multiline_inline_tables(self):
        b = TomlBuilder(style=TomlStyle(toml_1_1=True))
        b.pair('t', TomlMultiline({'a': 1, 'b': [1]}))
        self.assertEqual(b.render(), 't = {\n    a = 1,\n    b = [\n        1,\n    ],\n}\n')
        self.assertEqual(b.document().data, {'t': {'a': 1, 'b': [1]}})
        with self.assertRaises(TomlDocumentError):
            TomlBuilder().pair('t', TomlMultiline({'a': 1}))

    def test_separation(self):
        b = TomlBuilder(style=TomlStyle(blank_lines_between_tables=2))
        b.pair('r', 1).table('a').table('b').blank().table('c')
        self.assertEqual(b.render(), 'r = 1\n\n\n[a]\n\n\n[b]\n\n[c]\n')

    def test_table_comments_attached(self):
        self.assertEqual(TomlBuilder().table('a').table('b', comments=['about b']).render(), '[a]\n\n# about b\n[b]\n')

    def test_array_tables_and_dotted_pairs(self):
        b = TomlBuilder()
        b.table('f', {'n': 1}, array=True).table(('f',), array=True).pair(('a', 'b'), 2).pair(('x y', 'z'), 3)
        self.assertEqual(b.render(), "[[f]]\nn = 1\n\n[[f]]\na.b = 2\n'x y'.z = 3\n")
        self.assertEqual(b.document().data, {'f': [{'n': 1}, {'a': {'b': 2}, 'x y': {'z': 3}}]})

    def test_key_types(self):
        b = TomlBuilder()
        b.pair(5, 1).pair(TomlRaw('"q"'), 2).pair(('a', TomlRaw("'b'")), 3).table(TomlRaw("'t.u'"))
        self.assertEqual(b.render(), "'5' = 1\n\"q\" = 2\na.'b' = 3\n\n['t.u']\n")
        with self.assertRaises(TomlDocumentError):
            b.table(())

    def test_document_roundtrip_and_style_carries(self):
        b = TomlBuilder(style=TomlStyle(quotes='basic'))
        b.table('t', {'k': 'v'})
        doc = b.document()
        self.assertEqual(doc.data, {'t': {'k': 'v'}})
        self.assertEqual(doc.set_value(('t', 'n'), 'w').src, '[t]\nk = "v"\nn = "w"\n')

    def test_empty(self):
        self.assertEqual(TomlBuilder().render(), '')
        self.assertEqual(TomlBuilder().document().data, {})

    def test_crlf(self):
        self.assertEqual(TomlBuilder(newline='\r\n').table('t', {'a': [1]}).render(), '[t]\r\na = [\r\n    1,\r\n]\r\n')

    def test_invalid_style(self):
        with self.assertRaises(TomlDocumentError):
            TomlBuilder(style=TomlStyle(quotes='fancy'))
