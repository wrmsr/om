# @om-precheck-allow-any-unicode
from ..controls.stacks import stack_frame
from ..controls.statics import Static
from ..controls.status import StatusBar
from ..runtime.timers import Timers
from ..text.segments import Segment
from ..text.segments import segments_text
from ..text.styles import EMPTY_THEME
from ..text.wraps import wrap_segments


##


def row_texts(rows):
    return [segments_text(row) for row in rows]


def test_wrap_segments_basic():
    assert row_texts(wrap_segments([Segment('a bb ccc dddd')], 6)) == ['a bb', 'ccc', 'dddd']
    assert row_texts(wrap_segments([], 10)) == ['']
    assert row_texts(wrap_segments([Segment('short')], 10)) == ['short']


def test_wrap_segments_hard_break_and_styles():
    rows = wrap_segments([Segment('abcdefgh', 'x')], 3)
    assert row_texts(rows) == ['abc', 'def', 'gh']
    assert all(seg.style == 'x' for row in rows for seg in row)

    # A style boundary mid-word survives wrapping.
    rows = wrap_segments([Segment('aa'), Segment('bb', 'x'), Segment(' cc')], 4)
    assert row_texts(rows) == ['aabb', 'cc']
    assert [seg.style for seg in rows[0]] == [None, 'x']


def test_wrap_segments_wide_chars():
    # Each CJK char is 2 columns; three fit in 6, not 7 chars.
    assert row_texts(wrap_segments([Segment('漢字漢字')], 6)) == ['漢字漢', '字']


def test_wrap_preserves_interior_spaces():
    assert row_texts(wrap_segments([Segment('a  b')], 10)) == ['a  b']


def test_static_multiline():
    s = Static([('one\ntwo three', None)])
    assert row_texts(s.render(20)) == ['one', 'two three']
    assert row_texts(s.render(4)) == ['one', 'two', 'thre', 'e']


def test_status_bar_right_alignment():
    sb = StatusBar(left=[('L', None)], right=[('R', None)])
    (row,) = sb.render(10)
    assert segments_text(row) == 'L        R'

    # Too narrow: stacks instead.
    sb.set_left([('leftleft', None)])
    sb.set_right([('rightright', None)])
    rows = sb.render(10)
    assert row_texts(rows) == ['leftleft', 'rightright']


def test_stack_frame_and_truncation():
    a = Static([('aaa\nbbb', None)])
    b = Static([('ccc', None)])

    frame = stack_frame([a, b], width=10, max_height=10, theme=EMPTY_THEME)
    assert [line.text for line in frame.lines] == ['aaa', 'bbb', 'ccc']
    assert not frame.cursor_visible

    # Over budget: rows drop from the top; the bottom stays.
    frame = stack_frame([a, b], width=10, max_height=2, theme=EMPTY_THEME)
    assert [line.text for line in frame.lines] == ['bbb', 'ccc']


def test_timers_deterministic():
    now = [0.0]
    t = Timers(lambda: now[0])
    fired: list[str] = []

    t.call_later(1.0, lambda: fired.append('once'))
    every = t.call_every(0.5, lambda: fired.append('tick'))

    assert t.next_fire_at() == 0.5
    now[0] = 0.6
    assert t.fire_due() == 1
    assert fired == ['tick']

    # The repeating timer rescheduled from its fire time (0.6 + 0.5 = 1.1) - no catch-up bursts.
    now[0] = 1.05
    assert t.fire_due() == 1
    assert fired == ['tick', 'once']

    now[0] = 1.2
    assert t.fire_due() == 1
    assert fired == ['tick', 'once', 'tick']

    every.cancel()
    now[0] = 10.0
    assert t.fire_due() == 0
    assert t.next_fire_at() is None
