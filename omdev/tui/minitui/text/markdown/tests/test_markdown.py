# @om-precheck-allow-any-unicode
from omcore.text.highlights import highlight_code
from omcore.text.widths import str_width

from ...segments import segments_text
from ..base import MarkdownStream
from ..base import MdCode
from ..base import MdHeading
from ..base import MdList
from ..base import MdListItem
from ..base import MdParagraph
from ..base import MdQuote
from ..base import MdRule
from ..base import MdTable
from ..base import MdTableAlign
from ..base import parse_markdown
from ..base import parse_markdown_inlines
from ..base import render_markdown_block
from ..base import render_markdown_blocks


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
    segs = parse_markdown_inlines('plain **bold** and `code` plus [x](http://y)')
    assert segments_text(segs) == 'plain bold and code plus x (http://y)'
    styles = [seg.style for seg in segs]
    assert 'md.bold' in styles
    assert 'md.code.inline' in styles
    assert 'md.link' in styles


def test_render_paragraph_wraps():
    (block,) = parse_markdown('some **bold** words that wrap')
    rows = render_markdown_block(block, 12)
    assert all(sum(len(seg.text) for seg in row) <= 12 for row in rows)
    assert 'md.bold' in {seg.style for row in rows for seg in row}


def test_render_list_hanging_indent():
    (block,) = parse_markdown('- a rather long item that wraps around')
    rows = render_markdown_block(block, 16)
    assert segments_text(rows[0]).startswith('• ')
    assert segments_text(rows[1]).startswith('  ')


def test_render_code_highlighted():
    (block,) = parse_markdown('```python\ndef f():\n    return "s"  # c\n```')
    rows = render_markdown_block(block, 40, highlighter=highlight_code)
    styles = {seg.style for row in rows for seg in row}
    assert 'code.keyword' in styles
    assert 'code.def' in styles
    assert 'code.string' in styles
    assert 'code.comment' in styles
    # Full-width fill for background themes.
    assert all(sum(len(seg.text) for seg in row) == 40 for row in rows)


def test_render_blocks_spacing():
    rows = render_markdown_blocks(parse_markdown('a\n\nb'), 10)
    assert [segments_text(r) for r in rows] == ['a', '', 'b']


def test_heading_tags_reach_h6():
    for level in range(1, 7):
        blk = MdHeading.of(level, 'title')
        tags = [seg.style for seg in blk.spans]
        assert tags == [f'md.h{level}'], (level, tags)
    # Beyond-spec levels clamp to h6.
    assert [seg.style for seg in MdHeading.of(9, 'x').spans] == ['md.h6']


def test_nested_list_depths():
    blocks = parse_markdown('- a\n- b\n  - b1\n  - b2\n    - deep\n- c\n')
    (lst,) = blocks
    assert isinstance(lst, MdList)
    assert [(it.marker, it.depth) for it in lst.items] == [
        ('-', 0), ('-', 0), ('-', 1), ('-', 1), ('-', 2), ('-', 0),
    ]


def test_nested_list_renders_indented():
    blocks = parse_markdown('- a\n  - b\n    - c\n')
    rows = [''.join(seg.text for seg in row) for row in render_markdown_block(blocks[0], 40)]
    assert rows == ['• a', '  ◦ b', '    ▪ c']


def test_nested_list_wrapped_lines_align_under_content():
    blocks = parse_markdown('- ' + 'word ' * 12 + '\n  - ' + 'nest ' * 12 + '\n')
    rows = [''.join(seg.text for seg in row) for row in render_markdown_block(blocks[0], 24)]
    conts = [r for r in rows if not r.lstrip().startswith(('•', '◦'))]
    assert conts, rows
    # Continuations hang under the item's content, past its indent + marker.
    assert all(r.startswith('  ') for r in conts), rows


##
# Tables


def test_parse_table():
    blocks = parse_markdown(
        'Intro line\n'
        '| Name | Value |\n'
        '|:-----|------:|\n'
        '| **a** | 1 |\n'
        '| b | `2` |\n'
        '\n'
        'after\n',
    )
    assert blocks == [
        MdParagraph.of('Intro line'),
        MdTable.of(
            ['Name', 'Value'],
            [['**a**', '1'], ['b', '`2`']],
            [MdTableAlign.LEFT, MdTableAlign.RIGHT],
        ),
        MdParagraph.of('after'),
    ]


def test_parse_table_requires_matching_alignment_row():
    assert parse_markdown('| a | b |\n| --- |\n| c |') == [MdParagraph.of('| a | b | | --- | | c |')]
    assert parse_markdown('| a | b |') == [MdParagraph.of('| a | b |')]
    # A bare `---` is a rule, not a one-column alignment row.
    assert parse_markdown('| a |\n---') == [MdParagraph.of('| a |'), MdRule()]
    # A list marker wins over a delimiter row (as in pdcmark).
    assert [type(b) for b in parse_markdown('a | b\n- | -\n')] == [MdParagraph, MdList]


def test_parse_table_cells_escapes_and_ragged_rows():
    (tbl,) = parse_markdown('| a \\| b | c |\n|---|---|\n| only |\n| 1 | 2 | 3 |\n')
    assert tbl == MdTable.of(['a | b', 'c'], [['only', ''], ['1', '2']], [MdTableAlign.NONE, MdTableAlign.NONE])


def test_parse_table_terminators():
    blocks = parse_markdown('| a |\n|---|\n| 1 |\n# head\n| b |\n|---|\n|\ntext\n')
    assert blocks == [
        MdTable.of(['a'], [['1']], [MdTableAlign.NONE]),
        MdHeading.of(1, 'head'),
        MdTable.of(['b'], [], [MdTableAlign.NONE]),  # a lone `|` is not a row
        MdParagraph.of('| text'),
    ]


def test_stream_table_settles_on_terminator():
    s = MarkdownStream()
    s.feed('| a | b |\n|---|---|\n| 1 | 2 |\n')
    assert s.pop_settled() == []  # still open: the next line may be another row
    assert [type(b) for b in s.tail_blocks()] == [MdTable]
    s.feed('\n')
    assert s.pop_settled() == [MdTable.of(['a', 'b'], [['1', '2']], [MdTableAlign.NONE] * 2)]
    assert s.finalize() == []


def test_stream_table_head_splits_off_paragraph():
    s = MarkdownStream()
    s.feed('intro\n| a | b |\n')
    assert s.pop_settled() == []  # the pipe line may still turn out to be a table header
    s.feed('|---|---|\n')
    assert s.pop_settled() == [MdParagraph.of('intro')]
    assert [type(b) for b in s.tail_blocks()] == [MdTable]


def test_render_table_columns_and_alignment():
    (tbl,) = parse_markdown('| Name | N |\n|:-----|--:|\n| ab | 1 |\n| c | 22 |\n')
    rows = render_markdown_block(tbl, 40)
    assert [segments_text(r) for r in rows] == [
        'Name │  N',
        '─────┼───',
        'ab   │  1',
        'c    │ 22',
    ]
    assert {seg.style for seg in rows[0] if seg.text.strip()} == {'md.table.head', 'md.table.border'}
    assert all(seg.style == 'md.table.border' for seg in rows[1])


def test_render_table_center_and_wide_chars():
    (tbl,) = parse_markdown('| x | 名前 |\n|:-:|---|\n| abcde | ✓ |\n')
    rows = [segments_text(r) for r in render_markdown_block(tbl, 40)]
    assert rows == [
        '  x   │ 名前',
        '──────┼─────',
        'abcde │ ✓',
    ]


def test_render_table_wraps_wide_cells():
    (tbl,) = parse_markdown('| k | description |\n|---|---|\n| x | ' + 'word ' * 10 + '|\n')
    rows = render_markdown_block(tbl, 30)
    assert all(str_width(segments_text(row)) <= 30 for row in rows)
    texts = [segments_text(r) for r in rows]
    assert len(texts) > 3  # the wide cell wrapped onto several display rows
    assert all('│' in t for t in texts if '┼' not in t)  # continuation rows keep the column separator


def test_render_table_too_narrow_falls_back_to_joined_rows():
    (tbl,) = parse_markdown('| a | b | c | d |\n|---|---|---|---|\n| 1 | 2 | 3 | 4 |\n')
    rows = [segments_text(r) for r in render_markdown_block(tbl, 8)]
    assert all(len(r) <= 8 for r in rows)
    text = ' '.join(rows)
    assert all(cell in text for cell in 'abcd1234')


def test_render_blocks_table_between_paragraphs():
    rows = render_markdown_blocks(parse_markdown('a\n\n| h |\n|---|\n| 1 |\n\nb'), 10)
    assert [segments_text(r) for r in rows] == ['a', '', 'h', '─', '1', '', 'b']
