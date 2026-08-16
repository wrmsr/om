# @om-precheck-allow-any-unicode
from ..text.highlights import highlight_code
from ..text.markdowns import MarkdownStream
from ..text.markdowns import MdCode
from ..text.markdowns import MdHeading
from ..text.markdowns import MdList
from ..text.markdowns import MdListItem
from ..text.markdowns import MdParagraph
from ..text.markdowns import MdQuote
from ..text.markdowns import MdRule
from ..text.markdowns import parse_inlines
from ..text.markdowns import parse_markdown
from ..text.markdowns import render_block
from ..text.markdowns import render_blocks
from ..text.segments import segments_text


##


def test_parse_blocks():
    blocks = parse_markdown(
        '# Title\n'
        '\n'
        'A paragraph\n'
        'continued here.\n'
        '\n'
        '- one\n'
        '- two\n'
        '  wrapped\n'
        '\n'
        '> quoted\n'
        '> stuff\n'
        '\n'
        '```python\n'
        'x = 1\n'
        '```\n'
        '\n'
        '---\n',
    )
    assert blocks == [
        MdHeading.of(1, 'Title'),
        MdParagraph.of('A paragraph continued here.'),
        MdList((
            MdListItem.of('-', 'one'),
            MdListItem.of('-', 'two wrapped'),
        )),
        MdQuote.of('quoted stuff'),
        MdCode('python', ('x = 1',)),
        MdRule(),
    ]


def test_heading_terminates_paragraph():
    blocks = parse_markdown('para\n# head')
    assert blocks == [MdParagraph.of('para'), MdHeading.of(1, 'head')]


def test_stream_settling():
    s = MarkdownStream()

    s.feed('# Title\n\nA paragraph that ')
    settled = s.pop_settled()
    # The heading settled (complete line + terminator semantics: single-line block); the open paragraph did not.
    assert settled == [MdHeading.of(1, 'Title')]
    assert [type(b) for b in s.tail_blocks()] == [MdParagraph]

    s.feed('keeps going.\n\nNext ')
    settled = s.pop_settled()
    assert settled == [MdParagraph.of('A paragraph that keeps going.')]

    # An open fence never settles until closed.
    s.feed('para.\n\n```python\ncode line\n')
    settled = s.pop_settled()
    assert settled == [MdParagraph.of('Next para.')]
    assert [type(b) for b in s.tail_blocks()] == [MdCode]

    s.feed('```\n')
    settled = s.pop_settled()
    assert settled == [MdCode('python', ('code line',))]

    assert s.finalize() == []
    assert s.buffer == ''


def test_stream_partial_line_never_settles():
    s = MarkdownStream()
    s.feed('# almost a heading')
    assert s.pop_settled() == []
    s.feed('\n')
    assert s.pop_settled() == [MdHeading.of(1, 'almost a heading')]


def test_inlines():
    segs = parse_inlines('plain **bold** and `code` plus [x](http://y)')
    assert segments_text(segs) == 'plain bold and code plus x (http://y)'
    styles = [seg.style for seg in segs]
    assert 'md.bold' in styles
    assert 'md.code.inline' in styles
    assert 'md.link' in styles


def test_render_paragraph_wraps():
    (block,) = parse_markdown('some **bold** words that wrap')
    rows = render_block(block, 12)
    assert all(sum(len(seg.text) for seg in row) <= 12 for row in rows)
    assert 'md.bold' in {seg.style for row in rows for seg in row}


def test_render_list_hanging_indent():
    (block,) = parse_markdown('- a rather long item that wraps around')
    rows = render_block(block, 16)
    assert segments_text(rows[0]).startswith('• ')
    assert segments_text(rows[1]).startswith('  ')


def test_render_code_highlighted():
    (block,) = parse_markdown('```python\ndef f():\n    return "s"  # c\n```')
    rows = render_block(block, 40, highlighter=highlight_code)
    styles = {seg.style for row in rows for seg in row}
    assert 'code.keyword' in styles
    assert 'code.def' in styles
    assert 'code.string' in styles
    assert 'code.comment' in styles
    # Full-width fill for background themes.
    assert all(sum(len(seg.text) for seg in row) == 40 for row in rows)


def test_render_blocks_spacing():
    rows = render_blocks(parse_markdown('a\n\nb'), 10)
    assert [segments_text(r) for r in rows] == ['a', '', 'b']


##


def test_python_highlighter_tolerates_garbage():
    rows = highlight_code('python', ['def broken(:', '  "unclosed'])
    assert rows is not None
    assert [segments_text(r) for r in rows] == ['def broken(:', '  "unclosed']


def test_python_highlighter_multiline_string():
    rows = highlight_code('python', ['x = """', 'inside', '"""'])
    assert rows is not None
    assert all(
        seg.style == 'code.string'
        for seg in rows[1]
    )


def test_diff_highlighter():
    rows = highlight_code('diff', ['--- a', '+++ b', '@@ -1 +1 @@', '-old', '+new', ' ctx'])
    assert rows is not None
    styles = [row[0].style if row else None for row in rows]
    assert styles == [
        'code.diff.meta',
        'code.diff.meta',
        'code.diff.hunk',
        'code.diff.del',
        'code.diff.add',
        None,
    ]


def test_unknown_language_returns_none():
    # (Not 'brainfuck' - pygments actually has a lexer for that.)
    assert highlight_code('zz-no-such-lang-zz', ['+++']) is None


def test_pygments_fallback_highlighter():
    import importlib.util  # noqa: PLC0415

    import pytest  # noqa: PLC0415

    if importlib.util.find_spec('pygments') is None:
        pytest.skip('pygments not installed')

    rows = highlight_code('rust', ['fn main() { let x = "s"; } // c'])
    assert rows is not None
    styles = {seg.style for row in rows for seg in row}
    assert 'code.keyword' in styles
    assert 'code.string' in styles

    # Multi-line + row-count invariant.
    rows = highlight_code('json', ['{', '  "k": 1', '}'])
    assert rows is not None
    assert len(rows) == 3

    # Still None for total nonsense.
    assert highlight_code('no-such-language-zzz', ['x']) is None
