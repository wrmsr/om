import pytest

from omcore import marshal as msh
from omcore.text import diffs
from omcore.text import styled as st

from ..diffdocs import render_diff_text_doc
from ..html import HtmlTextRenderer
from ..rendering import TextRenderingOptions
from ..styled import StyledTextBlock
from ..styled import StyledTextRenderer
from ..types import DiffText
from ..types import StrText
from ..types import Text


def test_diff_text():
    d = DiffText(
        old='a\nb\nc\n',
        new='a\nB\nc\n',
        path='f.py',
    )

    s = str(d)
    assert '--- f.py' in s
    assert '-b' in s
    assert '+B' in s

    rendered = StyledTextRenderer().render(d)
    assert rendered.parts == (StyledTextBlock(d),)

    m = msh.marshal(d, Text)
    d2 = msh.unmarshal(m, Text)
    assert d2 == d
    assert msh.marshal(d2, Text) == m


def test_empty_diff_is_falsey():
    d = DiffText(old='a\n', new='a\n')

    assert not d
    assert str(d) == ''
    assert Text.of('x', d, 'y') == StrText('xy')


def test_diff_marshal_omits_none_path():
    d = DiffText(old='x\n', new='y\n')

    m = msh.marshal(d, Text)
    assert m == {'diff': {'old': 'x\n', 'new': 'y\n'}}
    assert msh.unmarshal(m, Text) == d


def test_diff_text_composes():
    t = Text.of([
        'changing f.py:\n',
        DiffText(old='x\n', new='y\n'),
    ])

    s = str(t)
    assert s.startswith('changing f.py:\n')
    assert '-x' in s
    assert '+y' in s


##


@pytest.mark.parametrize(('old', 'new'), [('a\nb', 'a\nc'), ('a\nb\n', 'a\nb'), ('a\nb', 'a\nb\n')])
def test_texts_without_a_final_newline_make_a_valid_patch(old, new):
    d = DiffText(old=old, new=new, path='f.txt')

    # Each line ends in a newline: one that the text lacked is marked as missing instead of running on to the next.
    assert all(line.endswith('\n') for line in d.diff_lines)

    [hunk] = diffs.parse_patch(''.join(d.diff_lines)).files[0].hunks
    marked = {(line.kind, line.text) for line in hunk.lines if line.has_no_newline_marker}
    expected = {
        *([(diffs.HunkLineKind.REMOVE, old.split('\n')[-1])] if not old.endswith('\n') else []),
        *([(diffs.HunkLineKind.ADD, new.split('\n')[-1])] if not new.endswith('\n') else []),
    }
    assert marked == expected

    assert render_diff_text_doc(d, width=60)


def test_a_form_feed_stays_within_its_line():
    d = DiffText(old='a\x0cb\nc\n', new='a\x0cb\nC\n')

    [hunk] = diffs.parse_patch(''.join(d.diff_lines)).files[0].hunks
    assert [line.text for line in hunk.lines] == ['a\x0cb', 'c', 'C']


def test_diff_docs_highlight_hunks_with_the_whole_file():
    old = '\n'.join(['def f():', '    """', *[f'    line {i}' for i in range(10)], '    """', ''])
    d = DiffText(old=old, new=old.replace('line 6', 'LINE 6'), path='/w/f.py')

    def changed_row_is_string(**kwargs):
        options = TextRenderingOptions(diff_layout='unified', **kwargs)
        document = render_diff_text_doc(d, width=80, options=options)
        row = next(line for line in document.lines if 'LINE 6' in line.text)
        return st.StyleName('code.string') in row.style_at(row.text.index('LINE 6'))

    assert changed_row_is_string()

    # Past the context limits the hunks are highlighted on their own, and this one cannot tell it is in a string.
    assert not changed_row_is_string(diff_context_limits=diffs.DiffContextLimits(max_lines=10))
    assert not changed_row_is_string(diff_context_limits=diffs.DiffContextLimits(max_bytes=100))
    assert changed_row_is_string(diff_context_limits=diffs.DiffContextLimits(max_lines=None, max_bytes=None))


def test_html_shows_a_diff_that_will_not_lay_out_as_plain_text():
    html = HtmlTextRenderer().render(DiffText(old='x\n', new='y\n', path='bad\npath'))

    assert '<pre' in html
    assert '-x' in html
    assert '+y' in html
