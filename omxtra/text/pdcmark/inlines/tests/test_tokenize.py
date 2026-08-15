"""Inline tokenizer tests (pre-emphasis-resolution)."""
from ...blocks.leaves import BufferedLine
from ..nodes import AutolinkNode
from ..nodes import CodeNode
from ..nodes import DelimNode
from ..nodes import HardBreakNode
from ..nodes import HtmlNode
from ..nodes import SoftBreakNode
from ..nodes import TextNode
from ..tokenize import tokenize_inline


def _line(text: str, line_start: int = 0) -> BufferedLine:
    return BufferedLine(text=text, line_start=line_start, line_next=line_start + len(text) + 1)


def _tokens(text: str):
    return tokenize_inline((_line(text),))


def test_plain_text():
    out = _tokens('hello world')
    assert len(out) == 1
    assert isinstance(out[0], TextNode) and out[0].text == 'hello world'


def test_backslash_escape():
    out = _tokens(r'a\*b')
    # Tokenizer accumulates `a`, `*`, `b` into the same buffer (escape consumes backslash, emits the punct as text).
    text_parts = [t.text for t in out if isinstance(t, TextNode)]
    assert ''.join(text_parts) == 'a*b'
    # No DelimNode produced.
    assert not any(isinstance(t, DelimNode) for t in out)


def test_entity_decoded():
    out = _tokens('a &amp; b')
    text_parts = [t.text for t in out if isinstance(t, TextNode)]
    assert ''.join(text_parts) == 'a & b'


def test_unknown_entity_kept_literal():
    out = _tokens('a &bogus; b')
    text_parts = [t.text for t in out if isinstance(t, TextNode)]
    assert ''.join(text_parts) == 'a &bogus; b'


def test_code_span():
    out = _tokens('a `foo` b')
    codes = [t for t in out if isinstance(t, CodeNode)]
    assert len(codes) == 1
    assert codes[0].text == 'foo'


def test_code_span_strips_surrounding_spaces():
    out = _tokens('` foo `')
    codes = [t for t in out if isinstance(t, CodeNode)]
    assert codes[0].text == 'foo'


def test_code_span_double_backtick():
    out = _tokens('``foo`bar``')
    codes = [t for t in out if isinstance(t, CodeNode)]
    assert codes[0].text == 'foo`bar'


def test_unmatched_backtick_is_text():
    out = _tokens('`unmatched')
    assert not any(isinstance(t, CodeNode) for t in out)
    text_parts = [t.text for t in out if isinstance(t, TextNode)]
    assert ''.join(text_parts) == '`unmatched'


def test_autolink_uri():
    out = _tokens('<http://x.test>')
    auts = [t for t in out if isinstance(t, AutolinkNode)]
    assert len(auts) == 1 and not auts[0].is_email
    assert auts[0].target == 'http://x.test'


def test_autolink_email():
    out = _tokens('<a@b.test>')
    auts = [t for t in out if isinstance(t, AutolinkNode)]
    assert auts[0].is_email and auts[0].target == 'a@b.test'


def test_inline_html_tag():
    out = _tokens('hi <span>x</span>')
    htmls = [t for t in out if isinstance(t, HtmlNode)]
    assert len(htmls) == 2  # <span> and </span>


def test_inline_html_comment():
    out = _tokens('<!-- x -->')
    htmls = [t for t in out if isinstance(t, HtmlNode)]
    assert len(htmls) == 1 and htmls[0].text == '<!-- x -->'


def test_emph_delim_simple():
    out = _tokens('*foo*')
    delims = [t for t in out if isinstance(t, DelimNode)]
    assert len(delims) == 2
    assert delims[0].char == '*' and delims[0].count == 1 and delims[0].can_open
    assert delims[1].char == '*' and delims[1].count == 1 and delims[1].can_close


def test_emph_strong_run():
    out = _tokens('**foo**')
    delims = [t for t in out if isinstance(t, DelimNode)]
    assert len(delims) == 2 and all(d.count == 2 for d in delims)


def test_emph_intraword_underscore_no_open():
    out = _tokens('foo_bar')
    # The `_` is between two word chars → neither open nor close.
    delims = [t for t in out if isinstance(t, DelimNode)]
    assert len(delims) == 1
    assert not delims[0].can_open and not delims[0].can_close


def test_softbreak_between_lines():
    out = tokenize_inline((_line('hello', 0), _line('world', 6)))
    breaks = [t for t in out if isinstance(t, SoftBreakNode)]
    assert len(breaks) == 1


def test_hardbreak_via_trailing_spaces():
    out = tokenize_inline((_line('hello  ', 0), _line('world', 8)))
    assert any(isinstance(t, HardBreakNode) for t in out)


def test_hardbreak_via_trailing_backslash():
    out = tokenize_inline((_line('hello\\', 0), _line('world', 7)))
    assert any(isinstance(t, HardBreakNode) for t in out)


# Multi-line whitespace / break semantics (lines are joined verbatim; breaks are decided in the walk).


def test_double_backslash_at_eol_is_soft_break():
    # The escape consumes the pair into a literal backslash; the newline is then an ordinary soft break.
    out = tokenize_inline((_line('foo\\\\', 0), _line('bar', 6)))
    kinds = [type(n).__name__ for n in out]
    assert kinds == ['TextNode', 'SoftBreakNode', 'TextNode']
    assert isinstance(out[0], TextNode) and out[0].text == 'foo\\'


def test_triple_backslash_at_eol_is_hard_break():
    out = tokenize_inline((_line('foo\\\\\\', 0), _line('bar', 7)))
    kinds = [type(n).__name__ for n in out]
    assert kinds == ['TextNode', 'HardBreakNode', 'TextNode']
    assert isinstance(out[0], TextNode) and out[0].text == 'foo\\'


def test_code_span_keeps_interior_trailing_spaces():
    out = tokenize_inline((_line('`code  ', 0), _line('span`', 8)))
    assert len(out) == 1
    assert isinstance(out[0], CodeNode) and out[0].text == 'code   span'


def test_code_span_keeps_interior_leading_spaces():
    out = tokenize_inline((_line('`a', 0), _line('   b`', 3)))
    assert isinstance(out[0], CodeNode) and out[0].text == 'a    b'


def test_raw_html_keeps_interior_whitespace():
    out = tokenize_inline((_line('<a href="x  ', 0), _line('y">', 13)))
    assert len(out) == 1
    assert isinstance(out[0], HtmlNode) and out[0].text == '<a href="x  \ny">'


def test_soft_break_swallows_next_line_leading_spaces():
    out = tokenize_inline((_line('aaa', 0), _line('   bbb', 4)))
    kinds = [type(n).__name__ for n in out]
    assert kinds == ['TextNode', 'SoftBreakNode', 'TextNode']
    assert isinstance(out[2], TextNode) and out[2].text == 'bbb'


def test_tab_before_newline_is_soft_break():
    out = tokenize_inline((_line('a\t', 0), _line('b', 3)))
    kinds = [type(n).__name__ for n in out]
    assert kinds == ['TextNode', 'SoftBreakNode', 'TextNode']
    assert isinstance(out[0], TextNode) and out[0].text == 'a'
