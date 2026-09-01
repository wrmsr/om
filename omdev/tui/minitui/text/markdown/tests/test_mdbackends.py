# @om-precheck-allow-any-unicode
import importlib.util

import pytest

from ....controls.markdown import get_markdown_stream
from ...segments import segments_text
from ..backends import parse_markdown_with
from ..base import MdCode
from ..base import MdHeading
from ..base import MdList
from ..base import MdTable
from ..base import MdTableAlign
from ..base import render_markdown_blocks
from ..pdcmark import PdcmarkStream


##


SAMPLE = (
    '# Title\n'
    '\n'
    'para **bold** and `code` here\n'
    '\n'
    '- one\n'
    '- two\n'
    '\n'
    '> quoted words\n'
    '\n'
    '```python\n'
    'x = 1\n'
    '```\n'
    '\n'
    '---\n'
    '\n'
    '1. first\n'
    '2. second\n'
    '\n'
    '| col | n |\n'
    '|:----|--:|\n'
    '| **x** | 1 |\n'
    '| yy | 22 |\n'
)

EXPECTED_ROWS = [
    '# Title',
    '',
    'para bold and code here',
    '',
    '• one',
    '• two',
    '',
    '│ quoted words',
    '',
    ' x = 1                                  ',
    '',
    '─' * 40,
    '',
    '1. first',
    '2. second',
    '',
    'col │  n',
    '────┼───',
    'x   │  1',
    'yy  │ 22',
]


def backend_names():
    names = ['internal', 'pdcmark']
    if importlib.util.find_spec('markdown_it') is not None:
        names.append('markdown-it')
    return names


@pytest.mark.parametrize('name', backend_names())
@pytest.mark.parametrize('chunk_size', [1, 7, 4096])
def test_backend_equivalence(name, chunk_size):
    s = get_markdown_stream(name)
    blocks = []
    for i in range(0, len(SAMPLE), chunk_size):
        s.feed(SAMPLE[i: i + chunk_size])
        blocks.extend(s.pop_settled())
    blocks.extend(s.finalize())

    rows = [segments_text(r) for r in render_markdown_blocks(blocks, 40)]
    assert rows == EXPECTED_ROWS, f'{name} (chunk={chunk_size})'


@pytest.mark.parametrize('name', backend_names())
def test_backend_settles_incrementally(name):
    # Backends may settle at different points (markdown-it holds back the last two top-level blocks; the others hold
    # one) - the contract is only: settled blocks are final, the tail always shows the live remainder.
    s = get_markdown_stream(name)
    s.feed('# Done\n\nfiller para\n\nstill going ')
    settled = s.pop_settled()
    assert any(isinstance(b, MdHeading) for b in settled), name

    # The open paragraph shows in the tail, live.
    tail_text = ' '.join(segments_text(r) for r in render_markdown_blocks(s.tail_blocks(), 60))
    assert 'still going' in tail_text

    # An open fence appears in the tail; once closed (and drained) it comes through exactly once.
    s.feed('on.\n\n```py\ncode\n')
    early = s.pop_settled()
    assert not any(isinstance(b, MdCode) for b in early), name  # never settles while open
    assert any(isinstance(b, MdCode) for b in s.tail_blocks()), name
    s.feed('```\n')
    rest = [*s.pop_settled(), *s.finalize()]
    assert sum(isinstance(b, MdCode) for b in rest) == 1, name


@pytest.mark.parametrize('name', backend_names())
def test_backend_inline_styles_survive(name):
    s = get_markdown_stream(name)
    s.feed('mix of **bold** *ital* ~~gone~~ `mono`\n')
    blocks = s.finalize()
    styles = {seg.style for b in blocks for seg in getattr(b, 'spans', ())}
    assert 'md.bold' in styles, name
    assert 'md.italic' in styles, name
    assert 'md.strike' in styles, name
    assert 'md.code.inline' in styles, name


@pytest.mark.parametrize('name', backend_names())
def test_backend_table_alignments(name):
    s = get_markdown_stream(name)
    s.feed('| l | c | r | n |\n|:--|:-:|--:|---|\n| 1 | 2 | 3 | 4 |\n')
    blocks = [*s.pop_settled(), *s.finalize()]
    (tbl,) = [b for b in blocks if isinstance(b, MdTable)]
    assert tbl.aligns == (MdTableAlign.LEFT, MdTableAlign.CENTER, MdTableAlign.RIGHT, MdTableAlign.NONE), name
    assert [segments_text(c) for c in tbl.head.cells] == ['l', 'c', 'r', 'n'], name
    assert [[segments_text(c) for c in r.cells] for r in tbl.rows] == [['1', '2', '3', '4']], name


@pytest.mark.parametrize('name', backend_names())
def test_backend_table_inline_styles_in_cells(name):
    s = get_markdown_stream(name)
    s.feed('| a | b |\n|---|---|\n| **bold** | `code` |\n')
    (tbl,) = [b for b in [*s.pop_settled(), *s.finalize()] if isinstance(b, MdTable)]
    styles = {seg.style for row in tbl.rows for cell in row.cells for seg in cell}
    assert {'md.bold', 'md.code.inline'} <= styles, name


@pytest.mark.parametrize('name', backend_names())
def test_backend_table_in_list_item_not_dropped(name):
    # Only the real parsers nest a table inside an item; either way every cell must remain visible.
    src = '- item\n\n  | a | b |\n  |---|---|\n  | 1 | 2 |\n\n- next\n'
    s = get_markdown_stream(name)
    s.feed(src)
    blocks = [*s.pop_settled(), *s.finalize()]
    text = ' '.join(segments_text(r) for r in render_markdown_blocks(blocks, 40))
    for needle in ('item', 'a', 'b', '1', '2', 'next'):
        assert needle in text, (name, text)
    markers = [it.marker for b in blocks if isinstance(b, MdList) for it in b.items]
    assert markers == ['-', '-'], (name, blocks)


@pytest.mark.parametrize('name', ['pdcmark', *(['markdown-it'] if 'markdown-it' in backend_names() else [])])
def test_backend_code_block_in_list_item_splits_list(name):
    s = get_markdown_stream(name)
    s.feed('1. one\n\n   ```\n   x = 1\n   ```\n\n2. two\n')
    blocks = [*s.pop_settled(), *s.finalize()]
    assert [type(b) for b in blocks] == [MdList, MdCode, MdList], (name, blocks)
    assert [it.marker for b in blocks if isinstance(b, MdList) for it in b.items] == ['1.', '2.'], name


@pytest.mark.parametrize('name', backend_names())
def test_backend_table_streams_live_then_settles_once(name):
    s = get_markdown_stream(name)
    s.feed('| a | b |\n|---|---|\n| 1 | 2 |\n| 3 |')
    early = s.pop_settled()
    assert not any(isinstance(b, MdTable) for b in early), name  # never settles while open
    tail = s.tail_blocks()
    (tbl,) = [b for b in tail if isinstance(b, MdTable)]
    assert len(tbl.rows) == 2, name  # the partial row shows live
    s.feed(' 4 |\n\nafter\n')
    rest = [*s.pop_settled(), *s.finalize()]
    tables = [b for b in rest if isinstance(b, MdTable)]
    assert len(tables) == 1, name
    assert [[segments_text(c) for c in r.cells] for r in tables[0].rows] == [['1', '2'], ['3', '4']], name


@pytest.mark.parametrize('name', backend_names())
def test_parse_markdown_with_matches_streaming(name):
    # One-shot (immediate mode, echoed prompts) must render exactly what the chunked stream would have.
    s = get_markdown_stream(name)
    blocks = []
    for i in range(0, len(SAMPLE), 7):
        s.feed(SAMPLE[i: i + 7])
        blocks.extend(s.pop_settled())
    blocks.extend(s.finalize())
    streamed = [segments_text(r) for r in render_markdown_blocks(blocks, 40)]

    oneshot = [segments_text(r) for r in render_markdown_blocks(parse_markdown_with(get_markdown_stream(name), SAMPLE), 40)]  # noqa: E501
    assert oneshot == streamed == EXPECTED_ROWS, name


def test_parse_markdown_with_default_backend_has_full_fidelity():
    # The default (pdcmark) backend runs a real inline engine: nested emphasis the internal parser can't do.
    blocks = parse_markdown_with(get_markdown_stream(), 'a **bold *and italic* run** here\n')
    styles = [seg.style for b in blocks for seg in getattr(b, 'spans', ())]
    assert 'md.bold' in styles
    assert 'md.italic' in styles


def test_parse_markdown_with_leaves_backend_reusable():
    s = get_markdown_stream()
    assert [type(b) for b in parse_markdown_with(s, '# one\n')] == [MdHeading]
    assert [type(b) for b in parse_markdown_with(s, 'two\n')] != [MdHeading]
    assert s.tail_blocks() == []


def test_registry_errors():
    with pytest.raises(LookupError):
        get_markdown_stream('no-such-backend')


def test_default_backend_is_pdcmark_with_gfm():
    s = get_markdown_stream()
    assert isinstance(s, PdcmarkStream)
    assert s.options.tables
    assert s.options.strikethrough


def test_nested_list_depth_equivalence_across_backends():
    src = '- a\n- b\n  - b1\n    - deep\n- c\n\n1. x\n   1. y\n2. z\n'
    expected = None
    for name in backend_names():
        # Whole-feed and chunked feeds must agree on item depths.
        for chunks in ([src], [src[i:i + 7] for i in range(0, len(src), 7)]):
            s = get_markdown_stream(name)
            blocks = []
            for c in chunks:
                s.feed(c)
                blocks.extend(s.pop_settled())
            blocks.extend(s.finalize())
            items = [(it.marker, it.depth) for b in blocks if isinstance(b, MdList) for it in b.items]
            if expected is None:
                expected = items
            assert items == expected, (name, len(chunks), items, expected)
    assert expected  # at least one backend ran and produced items


@pytest.mark.parametrize('name', backend_names())
def test_backend_reusable_across_finalize_cycles(name):
    # The chat tail is long-lived: it finalizes at every content-block boundary (text, tool call, text, ...) and keeps
    # feeding the same instance. A one-shot backend silently eats every cycle after the first - the "multi-tool turn
    # renders an empty response" bug.
    s = get_markdown_stream(name)

    s.feed('# first\n\nalpha\n')
    first = s.finalize()
    assert any('first' in seg for b in first for seg in _plain_rows(b))

    s.feed('# second\n\nbeta\n')
    second = list(s.pop_settled())
    second.extend(s.finalize())
    rows = [seg for b in second for seg in _plain_rows(b)]
    assert any('second' in r for r in rows)
    assert any('beta' in r for r in rows)
    assert not any('first' in r for r in rows)  # no leakage from the previous cycle

    assert s.tail_blocks() == []


def _plain_rows(block):
    return [segments_text(row) for row in render_markdown_blocks([block], 40)]
