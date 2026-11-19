import os.path

import pytest

from ..lexing import JsLexError
from ..lexing import JsPosition
from ..lexing import JsScanner
from ..lexing import JsSourceMap
from ..vendor.parsing import parse_module


##


def _scan(source, **kwargs):
    tokens = JsScanner(source, **kwargs).scan()
    assert ''.join(token.value for token in tokens) == source
    offset = 0
    for token in tokens:
        assert token.start == offset
        assert token.start < token.end <= len(source)
        assert token.value == source[token.start:token.end]
        offset = token.end
    assert offset == len(source)
    return tokens


def _significant(source):
    return [(t.kind, t.value) for t in _scan(source) if t.kind not in ('whitespace', 'comment')]


def test_lossless_token_stream():
    source = '#!/usr/bin/env node\r\n/* hi */ const π = "🌍"; // tail\n'
    assert [(t.kind, t.value) for t in _scan(source)] == [
        ('comment', '#!/usr/bin/env node'), ('whitespace', '\r\n'), ('comment', '/* hi */'),
        ('whitespace', ' '), ('identifier', 'const'), ('whitespace', ' '), ('identifier', 'π'),
        ('whitespace', ' '), ('punctuation', '='), ('whitespace', ' '), ('string', '"🌍"'),
        ('punctuation', ';'), ('whitespace', ' '), ('comment', '// tail'), ('whitespace', '\n'),
    ]


def test_source_locations():
    source = 'π🌍\r\n\tq\rα\u2028b\u2029'
    locations = JsSourceMap(source)
    for offset in range(len(source) + 1):
        assert locations.position(offset).byte_offset == len(source[:offset].encode('utf-8'))
    assert locations.position(2) == JsPosition(2, 6, 1, 2)
    assert locations.position(4) == JsPosition(4, 8, 2, 0)
    assert locations.position(5) == JsPosition(5, 9, 2, 1)
    assert locations.position(7) == JsPosition(7, 11, 3, 0)
    assert locations.position(9) == JsPosition(9, 16, 4, 0)
    assert locations.position(len(source)).line == 5
    with pytest.raises(ValueError, match='-1'):
        locations.position(-1)
    with pytest.raises(ValueError, match=str(len(source) + 1)):
        locations.position(len(source) + 1)
    assert JsSourceMap('').position(0) == JsPosition(0, 0, 1, 0)


def test_token_locations_are_opt_in():
    source = '/* 🌍 */\nconst π = 3;'
    token = next(t for t in _scan(source) if t.value == 'π')
    locations = JsSourceMap(source)
    assert locations.position(token.start).line == 2
    assert locations.position(token.start).column == 6
    assert locations.position(token.end).column == 7
    assert locations.position(token.end).byte_offset - locations.position(token.start).byte_offset == 2


@pytest.mark.parametrize('source', [
    '0', '12', '12.5', '.5', '1.', '1.e+3', '1e-3', '0xff', '0XAB_CD', '0b101', '0B10_01',
    '0o77', '0O7_1', '123n', '0xffn', '0b1n', '0o7n', '1_000.2_5e1_0',
])
def test_numbers(source):
    assert _significant(source) == [('number', source)]


@pytest.mark.parametrize('source', [
    'foo', '_x', '$a', 'π', 'a\u0301', 'a\u200c', 'a\u200d', r'\u0061bc', r'a\u{62}',
])
def test_identifiers(source):
    assert _significant(source) == [('identifier', source)]


def test_longest_punctuation_and_numeric_boundaries():
    assert [v for _, v in _significant('a>>>=2;b**=3;c&&=d;e??=f;g?.x;...y;i++/2')] == [
        'a', '>>>=', '2', ';', 'b', '**=', '3', ';', 'c', '&&=', 'd', ';', 'e', '??=', 'f', ';',
        'g', '?.', 'x', ';', '...', 'y', ';', 'i', '++', '/', '2',
    ]
    assert _significant('a?.3:0') == [
        ('identifier', 'a'), ('punctuation', '?'), ('number', '.3'), ('punctuation', ':'), ('number', '0'),
    ]
    assert _significant('1..toString()')[:3] == [('number', '1.'), ('punctuation', '.'), ('identifier', 'toString')]


@pytest.mark.parametrize('source', [
    "'a\\'b'", '"a\\"b"', '"a\\\nb"', '"a\\\r\nb"', '"\u2028\u2029"',
])
def test_strings(source):
    assert _significant(source) == [('string', source)]


def test_nested_templates_are_ordered_and_nonoverlapping():
    source = '`a${foo({x: `b${import("dep")}`})}c` / 2'
    tokens = _scan(source)
    assert [t.value for t in tokens if t.kind == 'template'] == ['`a', '`b', '`', 'c`']
    assert [t.value for t in tokens if t.kind == 'template_boundary'] == ['${', '${', '}', '}']
    assert all(t.embedded for t in tokens if t.value in ('foo', 'x', 'import', '"dep"', '`b'))
    assert not tokens[0].embedded
    assert not next(t for t in tokens if t.value == 'c`').embedded
    assert tokens[-3].value == '/'
    assert tokens[-3].kind == 'punctuation'


def test_escaped_template_boundaries():
    source = r'`a\${b}\`c`'
    assert _significant(source) == [('template', source)]


@pytest.mark.parametrize('source', [
    'x / 2', 'x /= 2', '1 / 2', 'x++ / 2', '(x) / 2', 'f(x) / 2', '({x:1}) / 2',
    'const x = {} / 2', '`a${x}` / 2', '`${{x:1} / 2}`', '`${{x:1}/2}${{y:2}/3}`',
    'obj.return / 2', 'obj?.delete / 2', 'obj.if(x) / 2', 'obj?.while(x) / 2',
    'this.#return / 2',
])
def test_division_context(source):
    tokens = _scan(source)
    assert all(t.kind != 'regex' for t in tokens)
    assert any(t.kind == 'punctuation' and t.value in ('/', '/=') for t in tokens)


@pytest.mark.parametrize('source', [
    'const x = /a[\\/]b/giu', 'return /a/', 'x => /a/', 'x ? /a/ : /a/', 'x && /a/', 'x ?? /a/',
    'x === /a/', 'x ** /a/', 'x ||= /a/', 'if (x) /a/', 'while (x) /a/', 'for (;;) /a/',
    'switch (x) {} /a/', 'try {} catch (e) /a/', 'function f() {} /a/',
    '`${/a/}`', '`${ {x:/a/} }`',
])
def test_regular_expression_context(source):
    assert any(t.kind == 'regex' for t in _scan(source))


def test_comments_do_not_change_context():
    assert _significant('if /* c */ (x) // c\n /a/')[-1] == ('regex', '/a/')
    assert _significant('obj. /* c */ return // c\n / 2')[-2:] == [('punctuation', '/'), ('number', '2')]
    assert [(t.kind, t.value) for t in _scan('// a\u2028x// b\u2029y') if t.kind != 'whitespace'] == [
        ('comment', '// a'), ('identifier', 'x'), ('comment', '// b'), ('identifier', 'y'),
    ]


@pytest.mark.parametrize(('source', 'kind'), [
    ('"unfinished', 'string'), ("'unfinished\\", 'string'), ('/* unfinished', 'comment'),
    ('/unfinished[', 'regex'), ('`unfinished', 'template'), ('`${x', 'identifier'), ('@', 'error'),
])
def test_strict_errors_and_tolerant_input(source, kind):
    with pytest.raises(JsLexError) as exc:
        JsScanner(source).scan()
    assert 0 <= exc.value.offset <= len(source)
    assert _scan(source, tolerant=True)[-1].kind == kind


def test_tolerant_recovery_at_newlines():
    tokens = _scan('"unfinished\nconst x = 1;\n/a\nlet y = 2', tolerant=True)
    assert any(t.kind == 'identifier' and t.value == 'const' for t in tokens)
    assert any(t.kind == 'identifier' and t.value == 'let' for t in tokens)


def test_scanner_can_be_reused_without_mutating_prior_results():
    scanner = JsScanner('`${f()}`')
    first = scanner.scan()
    second = scanner.scan()
    assert first == second
    assert first is not second
    assert JsScanner('').scan() == []


def test_vendored_marked_strict_scan_and_vendor_parsing():
    path = os.path.join(
        os.path.dirname(__file__), '..', '..', '..',
        'omllm', 'ui', 'web', 'resources', 'vendor', 'packages', 'marked', 'index.js',
    )
    with open(path) as f:
        source = f.read()
    tokens = _scan(source)
    assert {'regex', 'number', 'identifier', 'string', 'template', 'comment'} <= {t.kind for t in tokens}
    result = parse_module(source)
    assert result.specifiers == ()
    assert not result.dynamic_import
    with_import = source + '\nimport "scanner-regression";'
    result = parse_module(with_import)
    assert [s.value for s in result.specifiers] == ['scanner-regression']
    assert with_import[result.specifiers[0].start:result.specifiers[0].end] == 'scanner-regression'
