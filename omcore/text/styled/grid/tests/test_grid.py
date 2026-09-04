# @om-precheck-allow-any-unicode
import pytest

from ...documents import StyledDocument
from ...styles import StyleName
from ...styles import StylePatch
from ...text import StyledText
from ...text import StyleSpan
from ..fitting import fit
from ..fitting import pad_left
from ..fitting import pad_right
from ..fitting import truncate
from ..indents import expand_tabs
from ..indents import indent_guides
from ..measuring import cell_width
from ..measuring import fit_offset
from ..rules import rule
from ..wrapping import wrap
from ..wrapping import wrap_document


BOLD = StylePatch(bold=True)


##


def test_measuring():
    assert cell_width('abc') == 3
    assert cell_width('漢字') == 4
    assert cell_width(StyledText('a漢').styled(BOLD)) == 3
    assert cell_width('') == 0

    assert fit_offset('abc', 2) == 2
    assert fit_offset('abc', 5) == 3
    assert fit_offset('漢字', 3) == 1
    assert fit_offset('漢字', 0) == 0


def test_truncate():
    text = StyledText('abcdef').styled(BOLD, 2, 6)

    assert truncate(text, 10) == text
    assert truncate(text, 3) == StyledText('abc', (StyleSpan(2, 3, BOLD),))
    assert truncate(text, 0) == StyledText()
    assert truncate('漢字漢', 3) == StyledText('漢')

    assert truncate(text, 4, ellipsis='…') == StyledText('abc…', (StyleSpan(2, 3, BOLD),))
    assert truncate('abcdef', 1, ellipsis='…') == StyledText('a')
    assert truncate('abcdef', 5, ellipsis='...') == StyledText('ab...')


def test_pad_and_fit():
    assert pad_left('a', 2) == StyledText('  a')
    assert pad_right('a', 2, fill='.') == StyledText('a..')
    assert pad_left('a', 0) == StyledText('a')
    assert pad_right('a', 1, style='pad') == StyledText('a ', (StyleSpan.of(1, 2, 'pad'),))

    assert fit('ab', 5) == StyledText('ab   ')
    assert fit('ab', 5, align='right') == StyledText('   ab')
    assert fit('ab', 5, align='center') == StyledText(' ab  ')
    assert fit('abcdef', 3) == StyledText('abc')
    assert fit('abcdef', 3, ellipsis='…') == StyledText('ab…')
    assert fit('漢字', 3, align='right') == StyledText(' 漢')

    styled = fit(StyledText('a').styled(BOLD), 3, style='base')
    assert styled.text == 'a  '
    assert [run.styles for run in styled.runs()] == [(StyleName('base'), BOLD), (StyleName('base'),)]

    with pytest.raises(ValueError):  # noqa: PT011
        fit('a', 3, align='middle')  # type: ignore[arg-type]
    with pytest.raises(Exception):  # noqa: B017 PT011
        fit('a', 3, fill='漢')


##


def _texts(lines):
    return [line.text for line in lines]


def test_wrap_basic():
    assert _texts(wrap('a bb ccc dddd', 6)) == ['a bb', 'ccc', 'dddd']
    assert _texts(wrap('', 10)) == ['']
    assert _texts(wrap('short', 10)) == ['short']
    assert _texts(wrap('a b', 0)) == ['a b']


def test_wrap_hard_break_and_styles():
    lines = wrap(StyledText('abcdefgh').styled('x'), 3)
    assert _texts(lines) == ['abc', 'def', 'gh']
    assert all(line.style_at(0) == (StyleName('x'),) for line in lines)

    lines = wrap(StyledText.assemble('aa', ('bb', 'x'), ' cc'), 4)
    assert _texts(lines) == ['aabb', 'cc']
    assert lines[0].style_at(1) == ()
    assert lines[0].style_at(2) == (StyleName('x'),)
    assert lines[1].style_at(0) == ()


def test_wrap_wide_chars_and_interior_whitespace():
    assert _texts(wrap('漢字漢字', 6)) == ['漢字漢', '字']
    assert _texts(wrap('a  b', 10)) == ['a  b']
    assert _texts(wrap('a  b', 2)) == ['a', 'b']
    assert _texts(wrap('a ', 1)) == ['a']


def test_wrap_rejects_newlines_and_wraps_documents():
    with pytest.raises(ValueError):  # noqa: PT011
        wrap('a\nb', 10)

    document = wrap_document(StyledDocument.of_text('a bb ccc\n\ndddd\n'), 4)
    assert [line.text for line in document.lines] == ['a bb', 'ccc', '', 'dddd']
    assert document.trailing_newline


##


def test_rule():
    assert rule(5) == StyledText('─────')
    assert rule(5, character='=', style='r') == StyledText('=====', (StyleSpan.of(0, 5, 'r'),))
    assert rule(0) == StyledText()

    titled = rule(9, title=StyledText('hi').styled(BOLD), style='r')
    assert titled.text == '── hi ───'
    assert titled.style_at(3) == (BOLD,)
    assert titled.style_at(0) == (StyleName('r'),)
    assert titled.style_at(2) == (StyleName('r'),)

    assert rule(4, title='toolong').text == ' to '


##


def test_expand_tabs():
    assert expand_tabs('a\tb', 4) == StyledText('a   b')
    assert expand_tabs('\t\tx', 2) == StyledText('    x')
    assert expand_tabs('漢\tb', 4) == StyledText('漢  b')
    assert expand_tabs('a\n\tb', 4) == StyledText('a\n    b')

    styled = expand_tabs(StyledText('a\tb').styled(BOLD, 1, 2), 4)
    assert styled == StyledText('a   b', (StyleSpan(1, 4, BOLD),))
    assert expand_tabs(StyledText('ab').styled(BOLD), 4) == StyledText('ab').styled(BOLD)


def test_indent_guides():
    assert indent_guides('  x', 4, style='g') == StyledText('  x')

    guided = indent_guides(StyledText('        x').styled(BOLD), 4, style='g')
    assert guided.text == '│   │   x'
    assert guided.style_at(0) == (BOLD, StyleName('g'))
    assert guided.style_at(4) == (BOLD, StyleName('g'))
    assert guided.style_at(1) == (BOLD,)
