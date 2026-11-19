# @om-precheck-allow-any-unicode
import builtins
import glob
import os.path
import random
import subprocess
import sys
import textwrap

import pytest

from omcore.text import styled as st

from ..core import specials
from ..highlights import HyHighlighter
from ..models import Integer
from ..reader import read_many
from ..reader import unmangle
from ..reader.hyreader import HyReader
from ..reader.hyreader import _as_number
from ..runtime import HyRuntime


##


def _check_lines(source, highlighted):
    lines = source.split('\n')
    assert [line.text for line in highlighted] == lines
    assert len(highlighted) == len(lines)
    for line in highlighted:
        end = 0
        for span in line.spans:
            assert 0 <= span.start < span.end <= len(line.text)
            assert span.start >= end
            end = span.end
            assert isinstance(span.style, st.StyleName)
            assert span.style.name.startswith('code.')
    return highlighted


def _highlight(source, **kwargs):
    return _check_lines(source, HyHighlighter(**kwargs).highlight(source.split('\n')))


def _assert_style(line, text, name, *, start=0):
    left = line.text.index(text, start)
    expected = () if name is None else (st.StyleName('code.' + name),)
    assert all(line.style_at(i) == expected for i in range(left, left + len(text))), (line.text, text, name)


def test_shared_styles_and_token_boundaries():
    line, = _highlight('(defn greet [name] (print :hello 42 "hi")) ; goodbye')
    for token, name in [
        ('defn', 'keyword'),
        ('greet', 'def'),
        ('name', None),
        ('print', 'builtin'),
        (':hello', 'keyword'),
        ('42', 'number'),
        ('"hi"', 'string'),
        ('; goodbye', 'comment'),
        ('(', None),
        (')', None),
        (' ', None),
    ]:
        _assert_style(line, token, name)


@pytest.mark.parametrize('token', [
    '0', '-0', '+42', '123456789012345678901234567890', '0xff', '-0XFF', '0o755', '0b101',
    '1_000', '0x_ff', '1,000', '1.25', '.5', '-.5', '1.', '1e3', '-1.2e-3', '1_2.3_4',
    'Inf', '-Inf', 'NaN', 'inf', 'nan', '1j', '-2J', '1+2j', '3.5-4.2j', '+j', '-j',
    'j', 'J', '42abc', '0x', '0b102', '1e', '1e+', '1/2', '1.2.3', '123-name', '3jtail',
    'NaNthing', 'Infinity', '1__0', '1,2,3', '１',
])
def test_numbers_are_whole_reader_tokens(token):
    line, = _highlight(f'[{token}]')
    _assert_style(line, token, 'number' if _as_number(token) is not None else None)
    _assert_style(line, '[', None)
    _assert_style(line, ']', None)


@pytest.mark.parametrize('source', [
    '"plain ; #_ 42 {not-a-field}"',
    r'"escaped \" quote and \\ slash"',
    r'r"raw \n {not-a-field}"',
    r'b"bytes \xff {not-a-field}"',
    r'br"raw bytes \n"',
    r'rb"raw bytes \n"',
    '#[[plain "quotes" ; comment #_ {braces}]]',
    '#[tag[wrong ]other] and ]] then ]tag]',
    '#[faux[{(+ 1 2)}]faux]',
    '#[b[bytes-looking but a string]b]',
])
def test_strings_include_prefixes_and_bracket_delimiters(source):
    assert len(list(read_many(source))) == 1
    line, = _highlight(source + ' 27')
    _assert_style(line, source, 'string')
    _assert_style(line, '27', 'number')


def test_multiline_strings_preserve_empty_lines_and_columns():
    source = '(setv s #[long[\n\tλ ; not a comment\n\n]wrong] still string\n]long])\n(print 9)\n'
    lines = _highlight(source)
    _assert_style(lines[0], '#[long[', 'string')
    for row in (1, 3):
        _assert_style(lines[row], lines[row].text, 'string')
    assert not lines[2].spans
    _assert_style(lines[4], ']long]', 'string')
    _assert_style(lines[4], ')', None)
    _assert_style(lines[5], 'print', 'builtin')
    assert not lines[-1].spans


def test_quote_is_not_a_python_string():
    line, = _highlight("'foo `(~bar ~@baz) '42 '\"hello\"")
    for token in ("'", '`', '~', '~@'):
        _assert_style(line, token, 'keyword')
    for token in ('foo', 'bar', 'baz'):
        _assert_style(line, token, None)
    _assert_style(line, '42', 'number')
    _assert_style(line, '"hello"', 'string')


@pytest.mark.parametrize('prefix', ['f', 'fr', 'rf', 't', 'tr', 'rt'])
def test_interpolation_uses_hy_symbols_keywords_and_builtins(prefix):
    source = prefix + '"before {hy-name} {hy-name!r} {:key} {(if True (len [1]) None)} after"'
    assert len(list(read_many(source))) == 1
    line, = _highlight(source)
    _assert_style(line, prefix + '"before {', 'string')
    _assert_style(line, 'hy-name', None)
    # Without whitespace, !r belongs to the Hy symbol, not a conversion.
    _assert_style(line, 'hy-name!r', None)
    for token in (':key', 'if', 'True', 'None'):
        _assert_style(line, token, 'keyword')
    _assert_style(line, 'len', 'builtin')
    _assert_style(line, '1', 'number')
    _assert_style(line, '} after"', 'string')


@pytest.mark.parametrize('prefix', ['f', 't'])
def test_nested_interpolation_same_quotes_dict_braces_and_comments(prefix):
    source = prefix + '"outer {(get {"key" f"inner {(+ 2 3)}"} "key")} {' + '\n; field comment\n(len [4])} end"'
    assert len(list(read_many(source))) == 1
    lines = _highlight(source)
    for token, name in [('get', 'keyword'), ('"key"', 'string'), ('f"inner {', 'string'), ('+', 'keyword')]:
        _assert_style(lines[0], token, name)
    _assert_style(lines[0], '2', 'number')
    _assert_style(lines[0], '3', 'number')
    _assert_style(lines[1], '; field comment', 'comment')
    _assert_style(lines[2], 'len', 'builtin')
    _assert_style(lines[2], '4', 'number')
    _assert_style(lines[2], '} end"', 'string')


@pytest.mark.parametrize('prefix', ['f', 't'])
@pytest.mark.parametrize('suffix', [' = }', ' !r}', ' !s}', ' !a}', ' = !r:>{width}.{precision}f}'])
def test_interpolation_debug_conversion_and_nested_format_specs(prefix, suffix):
    source = prefix + '"{value' + suffix + '"'
    assert len(list(read_many(source))) == 1
    line, = _highlight(source)
    _assert_style(line, 'value', None)
    if 'width' in source:
        _assert_style(line, 'width', None)
        _assert_style(line, 'precision', None)
        _assert_style(line, '= !r:>{', 'string')
        _assert_style(line, 'f}', 'string')
    else:
        _assert_style(line, suffix.strip(), 'string')


@pytest.mark.parametrize('source', [
    'f"{{literal}} {{{(+ 1 2)}}}"',
    't"{{literal}} {{{(+ 1 2)}}}"',
    r'f"\N{SNOWMAN} {(+ 1 2)}"',
    r'fr"\{(+ 1 2)}"',
    r'f"\{(+ 1 2)}"',
])
def test_literal_braces_named_escapes_and_backslash_before_field(source):
    # A backslash before { doesn't escape the interpolation in Hy.
    if source != r'f"\{(+ 1 2)}"':
        assert len(list(read_many(source))) == 1
    line, = _highlight(source)
    if 'literal' in source:
        _assert_style(line, '{{literal}}', 'string')
    if 'SNOWMAN' in source:
        _assert_style(line, r'\N{SNOWMAN}', 'string')
    _assert_style(line, '+', 'keyword')
    _assert_style(line, '1', 'number')
    _assert_style(line, '2', 'number')


@pytest.mark.parametrize('delimiter', ['f', 'f-long', 't', 't-long', 'template'])
@pytest.mark.parametrize('enabled', [False, True])
def test_bracketed_interpolation_modes(delimiter, enabled):
    source = '#[' + delimiter + '[literal {(+ 1 2)}]' + delimiter + ']'
    assert len(list(read_many(source, reader=HyReader(bracketed_templates=enabled)))) == 1
    line, = _highlight(source, bracketed_templates=enabled)
    interpolate = delimiter.startswith('f') or (enabled and delimiter in ('t', 't-long'))
    if interpolate:
        _assert_style(line, '+', 'keyword')
        _assert_style(line, '1', 'number')
        _assert_style(line, '#[' + delimiter + '[literal {', 'string')
        _assert_style(line, '}]' + delimiter + ']', 'string')
    else:
        _assert_style(line, source, 'string')


@pytest.mark.parametrize('discarded', [
    '#_ 42',
    '#_ (print [1 {"x" 2}] #{3} #(4 5))',
    '#_ "string ; #_ not syntax"',
    '#_ #[tag[a ]other] b]tag]',
    '#_ f"{(+ 1 2)}"',
    '#_ #_ 1 2',
    "#_ '#_ 1 2",
    '#_ #^int value',
    '#_ ; skip this comment\n[1\n 2]',
])
def test_discard_comments_cover_one_surviving_reader_form(discarded):
    source = discarded + ' 99'
    models = list(read_many(source))
    assert models == [Integer(99)]
    lines = _highlight(source)
    for line in lines[:-1]:
        if line.text:
            _assert_style(line, line.text, 'comment')
    last = lines[-1]
    _assert_style(last, last.text[:-3], 'comment')
    _assert_style(last, '99', 'number')


@pytest.mark.parametrize('source', [
    '(defn target [] 1)',
    '(defn [decorator (factory 1)] target [] 1)',
    '(defn :async target [] 1)',
    '(defn :tp [T] target [] 1)',
    '(defn [decorator] :async :tp [T] target [] 1)',
    '(defn #^int target [] 1)',
    '(defn #^ int|None target [] 1)',
    '(defn (annotate target int) [] 1)',
    '(defn ; between head and name\n #_ ignored target [] 1)',
    '(defmacro target [] 1)',
    '(defclass [decorator] target [])',
    '(deftype :tp [T] target T)',
    '(defreader target 1)',
])
def test_definition_names_survive_modifiers_decorators_and_annotations(source):
    assert len(list(read_many(source))) == 1
    lines = _highlight(source)
    row = next(line for line in lines if 'target' in line.text)
    _assert_style(row, 'target', 'def')
    for line in lines:
        if 'decorator' in line.text:
            _assert_style(line, 'decorator', None)
        if ':async' in line.text:
            _assert_style(line, ':async', 'keyword')
        if ':tp' in line.text:
            _assert_style(line, ':tp', 'keyword')


@pytest.mark.parametrize('annotation', [
    'int', 'int|None', 'dict[str int]', 'ta.Sequence[int]|None',
    'ta.Mapping[str ta.Sequence[int|None]]|None', 'ta.Callable[[int str] ta.Awaitable[None]]',
    'tuple[#* Ts]', '(| int None)', '"Forward"',
])
def test_annotations_and_nested_unions(annotation):
    source = '#^' + annotation + ' variable 17'
    assert len(list(read_many(source))) == 2
    line, = _highlight(source)
    _assert_style(line, '#^', 'keyword')
    _assert_style(line, 'variable', None)
    _assert_style(line, '17', 'number')
    for token in ('int', 'str', 'dict', 'tuple'):
        if token in annotation:
            _assert_style(line, token, 'builtin')
    if 'None' in annotation:
        _assert_style(line, 'None', 'keyword')
    for i, c in enumerate(line.text):
        if c == '|':
            assert line.style_at(i) == (st.StyleName('code.keyword'),)


def test_annotation_syntax_does_not_leak_into_normal_symbols():
    line, = _highlight('#^int x int|None a|b len-more my:keyword foo#tag :12')
    for token in ('x', 'int|None', 'a|b', 'len-more', 'my:keyword', 'foo#tag'):
        _assert_style(line, token, None)
    _assert_style(line, ':12', 'keyword')


def test_shebang_unicode_tabs_arbitrary_symbols_and_dispatch_tags():
    lines = _highlight(
        '#!/usr/bin/env hy\n'
        '\t(print λ 雪 foo-bar? foo/bar a!b $value len-more)\n'
        '#custom-tag #* xs #** mapping #{1} #(2)\n',
    )
    _assert_style(lines[0], lines[0].text, 'comment')
    _assert_style(lines[1], '\t', None)
    _assert_style(lines[1], 'print', 'builtin')
    for token in ('λ', '雪', 'foo-bar?', 'foo/bar', 'a!b', '$value', 'len-more'):
        _assert_style(lines[1], token, None)
    for token in ('#custom-tag', '#*', '#**', '#{', '#('):
        _assert_style(lines[2], token, 'keyword')
    _assert_style(lines[2], '1', 'number')
    _assert_style(lines[2], '2', 'number')


@pytest.mark.parametrize('source', [
    '', '\n', '\t\n\n ', '(', ')]}', '(defn', '(defn target [', '"unterminated',
    'r"ends in slash\\', '#[missing', '#[bad]delimiter[', '#[x[unterminated',
    '#', '#_', '#_ (1 [2', '#^', '#^dict[str', 'f"{', 't"{(get {"key"',
    'f"{value !', 'f"{value :>{', 'f"single } brace"', '\x00 λ \r\t',
    '(' * 1500 + '1', '#_ ' * 1500 + '1',
])
def test_malformed_and_deep_editor_input_is_preserved(source):
    _highlight(source)


def test_stateless_calls_and_input_not_mutated():
    highlighter = HyHighlighter()
    source = ['(print 7)', '', 'λ']
    before = list(source)
    expected = highlighter.highlight(source)
    for interrupted in [['"unfinished'], ['#_ ('], ['f"{'], [], ['(defn']]:
        highlighter.highlight(interrupted)
        assert highlighter.highlight(source) == expected
    assert source == before
    assert highlighter.highlight([]) == []
    assert [line.text for line in highlighter.highlight(('',))] == ['']


def test_hy_fixture_corpus_preserves_text_and_span_bounds():
    package_dir = os.path.dirname(os.path.dirname(__file__))
    paths = sorted(glob.glob(os.path.join(package_dir, '**', '*.hy'), recursive=True))
    assert paths
    highlighter = HyHighlighter()
    for path in paths:
        with open(path, encoding='utf-8', newline='') as f:
            source = f.read()
        _check_lines(source, highlighter.highlight(source.split('\n')))


def test_no_external_dependencies_or_source_execution():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    code = textwrap.dedent(f"""
        import sys
        from {__package__.rpartition('.')[0]}.highlights import HyHighlighter

        source = [
            '(defreader dangerous (raise (RuntimeError "reader executed")))',
            '#dangerous (raise (RuntimeError "source executed"))',
            '(eval-and-compile (raise (RuntimeError "compiler executed")))',
            '(defmacro dangerous [] (raise (RuntimeError "macro executed")))',
            '(dangerous)',
            'f"{{(raise (RuntimeError "interpolation executed"))}}"',
        ]
        result = HyHighlighter().highlight(source)
        assert [line.text for line in result] == source
        assert not any(name == 'pygments' or name.startswith('pygments.') for name in sys.modules)
        assert 'site' not in sys.modules
    """)
    result = subprocess.run(
        [sys.executable, '-S', '-c', code],
        cwd=root,
        env={'PYTHONPATH': root},
        capture_output=True,
        check=False,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_all_core_specials_macros_and_mangled_aliases():
    names = set(specials._hy_macros) | set(HyRuntime().hy._hy_macros)  # noqa: SLF001
    for name in names:
        for spelling in (name, unmangle(name)):
            line, = _highlight(spelling)
            _assert_style(line, spelling, 'keyword')


def test_builtins_mangling_and_dotted_access():
    for name in vars(builtins):
        if name in ('True', 'False', 'None'):
            continue
        line, = _highlight(unmangle(name))
        _assert_style(line, unmangle(name), 'builtin')
    line, = _highlight('hy.eval str.join .join foo.print')
    _assert_style(line, 'hy', 'builtin')
    _assert_style(line, 'str', 'builtin')
    for token in ('.eval', '.join', 'foo.print'):
        _assert_style(line, token, None)


def test_only_ascii_whitespace_terminates_identifiers():
    line, = _highlight('len\u00a0name 12,34 ,42 _42 foo:bar foo#tag')
    for token in ('len\u00a0name', ',42', '_42', 'foo:bar', 'foo#tag'):
        _assert_style(line, token, None)
    _assert_style(line, '12,34', 'number')


def test_deterministic_malformed_snippets():
    rng = random.Random(0)
    alphabet = '()[]{};"\'`~#_^*|:!@bftrN\\ abc0123\n\t\u00a0\x00\ue000\u0378'
    for _ in range(500):
        _highlight(''.join(rng.choices(alphabet, k=rng.randrange(150))))


@pytest.mark.parametrize('container', ['[#_ 1]', '(#_ 1)', '{#_ 1}', '#{#_ 1}', '#(#_ 1)'])
def test_trailing_discard_does_not_consume_container_closer(container):
    source = '#_ ' + container + ' 99'
    assert list(read_many(source)) == [Integer(99)]
    line, = _highlight(source)
    _assert_style(line, '#_ ' + container, 'comment')
    _assert_style(line, '99', 'number')
    line, = _highlight('f"{(len ' + container + ')} {(+ 2 3)}"')
    _assert_style(line, 'len', 'builtin')
    _assert_style(line, '+', 'keyword')
    _assert_style(line, '2', 'number')


@pytest.mark.parametrize('prefix', ['f', 't'])
def test_named_escape_recognition_is_independent_of_backslash_parity(prefix):
    source = prefix + r'"\\N{(+ 1 2)}"'
    assert len(list(read_many(source))) == 1
    line, = _highlight(source)
    _assert_style(line, source, 'string')


@pytest.mark.parametrize('annotation', [
    'f"{list[int]}"', 'f"{int|None}"', 't"{int|None}"',
    '#(int)[str|None]', '#{int}[str|None]', '#[[Foo]]|None',
])
def test_annotation_context_applies_to_all_reader_forms(annotation):
    source = '#^' + annotation + ' variable int|None 17'
    assert len(list(read_many(source))) == 3
    line, = _highlight(source)
    for token in ('list', 'int', 'str'):
        if token in annotation:
            _assert_style(line, token, 'builtin')
    if 'None' in annotation:
        _assert_style(line, 'None', 'keyword')
    _assert_style(line, 'int|None', None, start=len('#^' + annotation))
    _assert_style(line, '17', 'number')


def test_flat_annotation_union_does_not_exhaust_recursion():
    source = '#^' + '|'.join(['int'] * 1500) + ' variable\n(print 42)'
    assert len(list(read_many(source))) == 2
    lines = _highlight(source)
    _assert_style(lines[0], 'int', 'builtin', start=lines[0].text.rindex('int'))
    _assert_style(lines[1], 'print', 'builtin')
    _assert_style(lines[1], '42', 'number')
