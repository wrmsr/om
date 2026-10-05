import io

import pytest

from omcore import dataclasses as dc

from ..exec import ExecError
from ..helper import parse_files
from ..tmpl import Template


def _render(source, data=None, *, funcs=None, options=()):
    tmpl = Template.new('test')
    if funcs:
        tmpl.funcs(funcs)
    if options:
        tmpl.option(*options)
    return tmpl.parse(source).render(data)


def test_values_and_control():
    assert _render('Hello, {{.Name}}!', {'Name': 'Gopher'}) == 'Hello, Gopher!'
    assert _render('{{if .}}yes{{else}}no{{end}}', []) == 'no'
    assert _render('{{with .User}}{{.Name}}{{end}}', {'User': {'Name': 'Gopher'}}) == 'Gopher'
    assert _render('{{range .}}{{.}},{{else}}empty{{end}}', []) == 'empty'
    assert _render('{{range $i, $v := .}}{{$i}}={{$v}};{{end}}', ['a', 'b']) == '0=a;1=b;'
    assert (
        _render('{{range .}}{{if eq . 2}}{{continue}}{{end}}{{.}}{{if eq . 3}}{{break}}{{end}}{{end}}', [1, 2, 3, 4])
        == '13'
    )
    assert _render('{{range .}}{{.}}{{end}}', 4) == '0123'
    assert _render('{{range .}}{{.}}{{end}}', {'b': 2, 'a': 1}) == '12'


def test_variables_and_pipelines():
    funcs = {
        'add': lambda a, b: a + b,
        'twice': lambda value: value * 2,
    }
    assert _render('{{3 | add 4 | twice}}', funcs=funcs) == '14'
    assert _render('{{$x := 1}}{{$x = 2}}{{$x}}') == '2'
    assert _render('{{and false (missing .X)}}', {}, funcs={'missing': lambda value: value}) == 'false'
    assert _render('{{or "ok" (missing .X)}}', {}, funcs={'missing': lambda value: value}) == 'ok'


def test_templates_clone_and_delimiters():
    tmpl = Template.new('root').parse('{{define "row"}}[{{.}}]{{end}}{{template "row" .Value}}')
    assert tmpl.render({'Value': 3}) == '[3]'

    clone = tmpl.clone().parse('{{define "row"}}<{{.}}>{{end}}')
    assert tmpl.render({'Value': 3}) == '[3]'
    assert clone.render({'Value': 3}) == '<3>'

    custom = Template.new('custom').delims('<<', '>>').parse('<<if .>>yes<<else>>no<<end>>')
    assert custom.render(True) == 'yes'
    tree = custom.tree
    assert tree is not None
    root = tree.root
    assert root is not None
    assert root.string() == '<<if .>>yes<<else>>no<<end>>'

    custom_block = Template.new('custom').delims('<<', '>>').parse('<<block "row" .>>[<<.>>]<<end>>')
    row = custom_block.lookup('row')
    assert row is not None
    row_tree = row.tree
    assert row_tree is not None
    row_root = row_tree.root
    assert row_root is not None
    assert row_root.string() == '[<<.>>]'
    assert custom_block.render('x') == '[x]'

    wr = io.StringIO()
    tmpl.execute_template(wr, 'row', 4)
    assert wr.getvalue() == '[4]'


def test_parse_files(tmp_path):
    first = tmp_path / 'first.tmpl'
    second = tmp_path / 'second.tmpl'
    first.write_text('first {{template "second.tmpl" .}}')
    second.write_text('second={{.}}')

    tmpl = parse_files(str(first), str(second))
    assert tmpl.name == first.name
    assert tmpl.render(3) == 'first second=3'


def test_builtins():
    assert _render('{{index . 1}}', ['a', 'b']) == 'b'
    assert _render('{{index . "x"}}', {'x': 7}) == '7'
    assert _render('{{slice . 1 3}}', [0, 1, 2, 3]) == '[1 2]'
    assert _render('{{len .}}', 'é') == '2'
    assert _render('{{eq . 2 3}}/{{lt . 3}}', 2) == 'true/true'
    assert _render('{{printf "%q %04d %.2f" "go" 7 1.5}}') == '"go" 0007 1.50'
    assert _render('{{printf "%q %#x %#08x" 10 -127 -127}}') == "'\\n' -0x7f -0x0007f"
    assert _render('{{html .}}', '<a x="y">') == '&lt;a x=&#34;y&#34;&gt;'
    assert _render('{{js .}}', '<a>') == r'\u003Ca\u003E'


@dc.dataclass(frozen=True)
class _Person:
    Name: str

    def Greet(self, prefix):  # noqa: N802 - Go-compatible exported method name.
        return prefix + self.Name


def test_fields_methods_and_call():
    person = _Person('Go')
    assert _render('{{.Name}} {{.Greet "Hi "}}', person) == 'Go Hi Go'
    assert _render('{{call . 2 3}}', lambda a, b: a + b) == '5'


def test_errors_and_missing_keys():
    assert _render('{{.Missing}}', {}) == '<no value>'
    assert _render('{{.Missing}}', {'Present': 1}, options=('missingkey=zero',)) == '0'
    with pytest.raises(ExecError, match='map has no entry'):
        _render('{{.Missing}}', {}, options=('missingkey=error',))
    with pytest.raises(ExecError, match='error calling fail'):
        _render('{{fail}}', funcs={'fail': lambda: (_ for _ in ()).throw(ValueError('boom'))})


def test_comparisons_and_defined_templates():
    value = float('nan')
    assert _render('{{lt . .}}/{{le . .}}/{{gt . .}}/{{ge . .}}/{{eq . .}}', value) == ('false/false/true/true/false')
    assert _render('{{printf "%f" 1}}') == '%!f(int=1)'

    tmpl = Template.new('root').parse('{{define "line\\nbreak"}}x{{end}}')
    assert tmpl.defined_templates() == '; defined templates are: "line\\nbreak", "root"'


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        ('<{{.}}>', '<13>'),
        ('{{$x := 2}}{{if true}}{{$x = 3}}{{end}}{{$x}}', '3'),
        ('{{$x := 1}}{{if true}}{{$x := 2}}{{if true}}{{$x = 3}}{{end}}{{end}}{{$x}}', '1'),
        ('{{(1)}}', '1'),
        ('{{if 0}}NON-ZERO{{else}}ZERO{{end}}', 'ZERO'),
        ('{{if 1.5i}}NON-ZERO{{else}}ZERO{{end}}', 'NON-ZERO'),
        ('{{with 1.5i}}{{.}}{{end}}', '(0+1.5i)'),
        ('{{print 1 2 3}}', '1 2 3'),
        ('{{print nil}}', '<nil>'),
        ('{{println 1 2 3}}', '1 2 3\n'),
        ('{{printf "%04x" 127}}', '007f'),
        ('{{printf "%g" 1+7i}}', '(1+7i)'),
        ('{{html "<script>"}}', '&lt;script&gt;'),
        ('{{js .}}', r"It\'d be nice."),
        ('{{"http://www.example.org/" | urlquery}}', 'http%3A%2F%2Fwww.example.org%2F'),
        ('{{not true}} {{not false}}', 'false true'),
        ('{{and false 0}} {{and 1 0}} {{and 0 true}} {{and 1 1}}', 'false 0 0 1'),
        ('{{or 0 0}} {{or 1 0}} {{or 0 true}} {{or 1 1}}', '0 1 true 1'),
        ('{{and 1 .Unknown}}', '<no value>'),
        ('{{or 0 .Unknown}}', '<no value>'),
        ('{{slice . 1}}', '[4 5]'),
        ('{{slice . 1 2}}', '[4]'),
    ],
)
def test_go_exec_table_subset(source, expected):
    data: object = 13
    if source.startswith('{{slice'):
        data = [3, 4, 5]
    elif source == '{{js .}}':
        data = "It'd be nice."
    elif '.Unknown' in source:
        data = None
    assert _render(source, data) == expected


def test_go_exec_function_subset():
    data = {
        'BinaryFunc': lambda a, b: f'[{a}={b}]',
        'ErrFunc': lambda: ('bla', None),
        'Empty0': None,
    }
    assert _render('{{call .BinaryFunc `1` `2`}}', data) == '[1=2]'
    assert _render('{{call .ErrFunc}}', data) == 'bla'
    assert _render('{{.ErrFunc | call}}', data) == 'bla'
    assert _render('{{.Empty0 | call .BinaryFunc `x`}}', data) == '[x=None]'
