import os.path

import pytest

from omcore.text import styled as st

from ..highlights import JsHighlighter


##


def _highlight(lines):
    result = JsHighlighter().highlight(lines)
    assert [line.text for line in result] == lines
    for line in result:
        end = 0
        for span in line.spans:
            assert end <= span.start < span.end <= len(line.text)
            end = span.end
            assert isinstance(span.style, st.StyleName)
            assert span.style.name in {
                'code.comment', 'code.string', 'code.number', 'code.keyword', 'code.builtin', 'code.def',
            }
    return result


def _assert_style(line, text, style):
    start = line.text.index(text)
    expected = (st.StyleName(style),) if style is not None else ()
    assert all(line.style_at(i) == expected for i in range(start, start + len(text)))


def test_javascript_highlighter():
    lines = _highlight([
        'export async function greet(name) {',
        '  const answer = Math.max(42, 1.5); // a comment',
        '  return "hello";',
        '}',
        'class Greeter extends Object {}',
    ])
    _assert_style(lines[0], 'export', 'code.keyword')
    _assert_style(lines[0], 'async', 'code.keyword')
    _assert_style(lines[0], 'function', 'code.keyword')
    _assert_style(lines[0], 'greet', 'code.def')
    _assert_style(lines[0], 'name', None)
    _assert_style(lines[1], 'Math', 'code.builtin')
    _assert_style(lines[1], 'max', None)
    _assert_style(lines[1], '42', 'code.number')
    _assert_style(lines[1], '// a comment', 'code.comment')
    _assert_style(lines[2], '"hello"', 'code.string')
    _assert_style(lines[4], 'Greeter', 'code.def')
    _assert_style(lines[4], 'extends', 'code.keyword')
    _assert_style(lines[4], 'Object', 'code.builtin')


def test_generators_and_declaration_comments():
    lines = _highlight(['function /* note */ *', '  generate() {}', 'class /* note */ Thing {}'])
    _assert_style(lines[0], 'function', 'code.keyword')
    _assert_style(lines[0], '/* note */', 'code.comment')
    assert lines[0].style_at(len(lines[0].text) - 1) == ()
    _assert_style(lines[1], 'generate', 'code.def')
    _assert_style(lines[2], 'Thing', 'code.def')


def test_anonymous_declarations_and_builtin_names():
    lines = _highlight([
        'const F = function* () {};',
        'const C = class extends Object {};',
        'function Array() {}',
    ])
    _assert_style(lines[1], 'extends', 'code.keyword')
    _assert_style(lines[1], 'Object', 'code.builtin')
    _assert_style(lines[2], 'Array', 'code.def')


def test_properties_are_not_keywords_or_builtins():
    line = _highlight(['obj.default; obj?.return; obj.Math; obj?. /* c */ Array; obj.function(name)'])[0]
    for name in ('default', 'return', 'Math', 'Array', 'function', 'name'):
        _assert_style(line, name, None)


def test_nested_templates_and_regex():
    line = _highlight(['const x = `outer ${`inner ${/a[}]/gi.test("a") ? 12 : 0}`} tail`;'])[0]
    for chunk in ('`outer ', '`inner ', ' tail`', '/a[}]/gi', '"a"'):
        _assert_style(line, chunk, 'code.string')
    _assert_style(line, '12', 'code.number')
    _assert_style(line, 'test', None)
    _assert_style(line, '${', None)
    _assert_style(line, '?', None)


def test_multiline_comments_templates_and_shebang():
    lines = _highlight([
        '#!/usr/bin/env node',
        '/* first',
        '\tsecond */ const s = `hello',
        'world ${',
        '  123 + Math.PI',
        '} tail`;',
        '',
    ])
    _assert_style(lines[0], lines[0].text, 'code.comment')
    _assert_style(lines[1], '/* first', 'code.comment')
    _assert_style(lines[2], '\tsecond */', 'code.comment')
    _assert_style(lines[2], '`hello', 'code.string')
    _assert_style(lines[3], 'world ', 'code.string')
    _assert_style(lines[3], '${', None)
    _assert_style(lines[4], '123', 'code.number')
    _assert_style(lines[4], 'Math', 'code.builtin')
    _assert_style(lines[5], '}', None)
    _assert_style(lines[5], ' tail`', 'code.string')


@pytest.mark.parametrize('number', ['0', '12.5', '.5', '1e-3', '0xff', '0b101', '0o77', '123n', '1_000'])
def test_numbers(number):
    line = _highlight([f'const n = {number};'])[0]
    _assert_style(line, number, 'code.number')


@pytest.mark.parametrize(('source', 'fragment', 'style'), [
    ('const s = "unfinished', '"unfinished', 'code.string'),
    ("const s = 'unfinished", "'unfinished", 'code.string'),
    ('const r = /unfinished[', '/unfinished[', 'code.string'),
    ('const s = `unfinished', '`unfinished', 'code.string'),
    ('/* unfinished', '/* unfinished', 'code.comment'),
    ('const s = `x ${42 +', '42', 'code.number'),
])
def test_incomplete_literals(source, fragment, style):
    _assert_style(_highlight([source])[0], fragment, style)


@pytest.mark.parametrize('lines', [
    [], [''], ['', ''], ['\tconst π = "🌍";\r', '', '\tπ?.default'],
    ['function broken(:', '  "unfinished', '  @@@'],
    ['`a', '', '${', '/* incomplete', ''],
    ['`' + '${`' * 1500],
    ['(' * 5000 + '0' + ')' * 5000],
])
def test_source_preservation_and_editor_input(lines):
    _highlight(lines)


def test_vendored_marked_source():
    path = os.path.join(
        os.path.dirname(__file__), '..', '..', '..',
        'omllm', 'ui', 'web', 'resources', 'vendor', 'packages', 'marked', 'index.js',
    )
    with open(path) as f:
        source = f.read()
    _highlight(source.split('\n'))
