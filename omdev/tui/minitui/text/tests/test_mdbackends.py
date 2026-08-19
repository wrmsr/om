# @om-precheck-allow-any-unicode
import importlib.util

import pytest

from ...controls.markdown import get_markdown_stream
from ..markdown import MdCode
from ..markdown import MdHeading
from ..markdown import render_blocks
from ..segments import segments_text


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

    rows = [segments_text(r) for r in render_blocks(blocks, 40)]
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
    tail_text = ' '.join(segments_text(r) for r in render_blocks(s.tail_blocks(), 60))
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
    assert 'md.code.inline' in styles, name


def test_registry_errors():
    with pytest.raises(LookupError):
        get_markdown_stream('no-such-backend')


def test_default_backend_is_pdcmark():
    from ..pdcmark import PdcmarkStream  # noqa: PLC0415
    assert isinstance(get_markdown_stream(), PdcmarkStream)


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
            from ..markdown import MdList  # noqa: PLC0415
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
    return [segments_text(row) for row in render_blocks([block], 40)]
