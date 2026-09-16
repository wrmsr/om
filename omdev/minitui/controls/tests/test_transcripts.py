from ...events.keys import Key
from ...events.types import KeyEvent
from ...events.types import MouseEvent
from ...events.types import MouseEventKind
from ...screens.cells import line_from_segments
from ...text.segments import Segment
from ...text.styles import EMPTY_STYLE
from ...text.styles import EMPTY_THEME
from ...text.styles import Style
from ..cards import Card
from ..static import Static
from ..transcripts import Transcript
from ..transcripts import TranscriptView


##


def _line(*segments):
    return line_from_segments(
        [Segment(s) if isinstance(s, str) else Segment(*s) for s in segments],
        EMPTY_THEME,
    )


def _lines(*texts):
    return [_line(t) for t in texts]


def _texts(rows):
    return [''.join(seg.text for seg in row) for row in rows]


def _filled(transcript, n, prefix=''):
    for i in range(n):
        transcript.record(_lines(f'{prefix}{i}'), tag=i)


def _hit_info(v, y):
    """(document row, block tag, block row, control, control row) under view row y, or None."""

    if (hit := v.hit(y)) is None:
        return None
    return (
        hit.row,
        hit.block.tag if hit.block is not None else None,
        hit.block_row,
        hit.control,
        hit.control_row,
    )


##


def test_transcript_blocks_and_lookup():
    t = Transcript()
    b0 = t.record(_lines('a0', 'a1'), tag='a')
    b1 = t.record(_lines('b0'))
    b2 = t.record(_lines('c0', 'c1', 'c2'), tag='c')
    assert t.height == 6
    assert list(t.blocks) == [b0, b1, b2]

    assert t.block_at(0) == (b0, 0)
    assert t.block_at(1) == (b0, 1)
    assert t.block_at(2) == (b1, 0)
    assert t.block_at(3) == (b2, 0)
    assert t.block_at(5) == (b2, 2)
    assert t.block_at(6) is None
    assert t.block_at(-1) is None

    assert [line.text for line in t.lines(1, 4)] == ['a1', 'b0', 'c0']
    assert [line.text for line in t.lines(-3, 100)] == ['a0', 'a1', 'b0', 'c0', 'c1', 'c2']
    assert t.lines(4, 4) == []


def test_transcript_max_rows_drops_whole_blocks():
    t = Transcript(max_rows=3)
    t.record(_lines('a', 'a'))
    second = t.record(_lines('b', 'b'))
    assert t.height == 2
    assert list(t.blocks) == [second]
    assert t.block_at(1) == (second, 1)

    # The newest block always stays, even alone over the bound.
    big = t.record(_lines('c', 'c', 'c', 'c', 'c'))
    assert list(t.blocks) == [big]
    assert t.height == 5
    assert t.block_at(4) == (big, 4)


##


def test_view_follows_then_unpins():
    t = Transcript()
    _filled(t, 10)
    v = TranscriptView(t, height=4)

    assert _texts(v.render(20)) == ['6', '7', '8', '9']
    assert (v.offset, v.total, v.follow) == (6, 10, True)

    v.scroll_by(-2)
    assert _texts(v.render(20)) == ['4', '5', '6', '7']
    assert (v.offset, v.follow) == (4, False)

    # New content does not move an unpinned view.
    t.record(_lines('10', '11'))
    assert _texts(v.render(20)) == ['4', '5', '6', '7']

    v.scroll_to_bottom()
    assert _texts(v.render(20)) == ['8', '9', '10', '11']
    assert (v.offset, v.follow) == (8, True)

    # Scrolling down onto the bottom re-pins; at the bottom there is nowhere further.
    v.scroll_by(-1)
    v.render(20)
    v.scroll_by(5)
    assert _texts(v.render(20)) == ['8', '9', '10', '11']
    assert (v.offset, v.follow) == (8, True)

    v.scroll_to_top()
    assert _texts(v.render(20)) == ['0', '1', '2', '3']
    assert (v.offset, v.follow) == (0, False)
    v.page_down()
    assert _texts(v.render(20)) == ['3', '4', '5', '6']
    v.page_up()
    assert _texts(v.render(20)) == ['0', '1', '2', '3']


def test_view_pads_and_clips():
    t = Transcript()
    t.record(_lines('abcdef'))
    wide = '\u65e5'  # a two-column CJK character
    t.record([_line('ab', wide, 'c')])
    v = TranscriptView(t, height=4)
    assert _texts(v.render(4)) == ['abcd', f'ab{wide}', '', '']
    assert _texts(v.render(3)) == ['abc', 'ab', '', '']  # the wide character straddling the edge goes, whole
    assert _texts(v.render(5)) == ['abcde', f'ab{wide}c', '', '']


def test_view_merges_styles():
    t = Transcript()
    bold = Style(bold=True)
    t.record([_line(('ab', bold), ('c', None), ('d', None))])
    v = TranscriptView(t, height=1)
    [row] = v.render(20)
    assert list(row) == [Segment('ab', bold), Segment('cd', EMPTY_STYLE)]


def test_view_trailing_controls_and_hits():
    t = Transcript()
    _filled(t, 3)
    live = Static([('l1\nl2', None)])
    v = TranscriptView(t, height=10)
    v.set_trailing([live])

    assert _texts(v.render(20)) == ['0', '1', '2', 'l1', 'l2', '', '', '', '', '']
    assert v.total == 5

    assert _hit_info(v, 0) == (0, 0, 0, None, 0)
    assert _hit_info(v, 3) == (3, None, 0, live, 0)
    assert _hit_info(v, 4) == (4, None, 0, live, 1)
    assert _hit_info(v, 5) is None
    assert _hit_info(v, -1) is None

    # Hits follow the scroll offset.
    v.set_height(2)
    assert _texts(v.render(20)) == ['l1', 'l2']
    assert _hit_info(v, 0) == (3, None, 0, live, 0)
    v.scroll_by(-1)
    assert _texts(v.render(20)) == ['2', 'l1']
    assert _hit_info(v, 0) == (2, 2, 0, None, 0)


def test_view_events():
    t = Transcript()
    _filled(t, 20)
    card = Card([('tool', None)], detail=[[Segment('detail')]])
    clicks = []
    v = TranscriptView(t, height=5, on_click=lambda hit, event: clicks.append((hit.row, event.x)))
    v.set_trailing([card])
    v.render(20)
    assert v.offset == 16

    assert v.handle_event(MouseEvent(MouseEventKind.SCROLL_UP, 0, 0))
    v.render(20)
    assert v.offset == 13
    assert v.handle_event(KeyEvent(Key('k')))
    v.render(20)
    assert v.offset == 12
    assert v.handle_event(KeyEvent(Key('pagedown')))
    v.render(20)
    assert v.offset == 16
    assert v.handle_event(KeyEvent(Key('g')))
    v.render(20)
    assert v.offset == 0
    assert v.handle_event(KeyEvent(Key('G')))
    v.render(20)
    assert (v.offset, v.follow) == (16, True)
    assert not v.handle_event(KeyEvent(Key('x')))

    # A click on history reports the hit; a click on a live control goes to it.
    assert v.handle_event(MouseEvent(MouseEventKind.DOWN, 3, 0))
    assert clicks == [(16, 3)]
    expanded = [card.expanded]
    assert v.handle_event(MouseEvent(MouseEventKind.DOWN, 0, 4))
    expanded.append(card.expanded)
    v.render(20)  # the expanded card is a row taller; following, the view slid down one
    assert not v.handle_event(MouseEvent(MouseEventKind.DOWN, 0, 4))  # the card's detail row: not its expander
    expanded.append(card.expanded)
    assert expanded == [False, True, True]
