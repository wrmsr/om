from ...text.styles import EMPTY_THEME
from ...text.styles import Style
from ..base import Control
from ..overlays import Overlay
from ..stacks import stack_layout
from ..static import Static


##


class Nothing(Control):
    def render(self, width):
        return []


class Cursory(Static):
    def cursor(self, width):
        return (1, 1)


def _texts(frame):
    return [line.text for line in frame.lines]


def _hit(layout, x, y):
    if (hit := layout.hit_at(x, y)) is None:
        return None
    return (hit.control, hit.x, hit.y)


##


def test_overlay_composites_and_hits():
    a = Static([('aaaaaaaa', None)])
    b = Static([('bbbbbbbb\nbbbbbbbb', None)])
    pop = Static([('XY\nZ', None)])
    layout = stack_layout([a, b], width=8, max_height=10, theme=EMPTY_THEME, overlays=[Overlay(pop, 2, 1, 3)])

    assert _texts(layout.frame) == ['aaaaaaaa', 'bbXY bbb', 'bbZ  bbb']
    [region] = layout.overlays
    assert (region.control, region.x, region.y, region.width, region.height) == (pop, 2, 1, 3, 2)

    assert _hit(layout, 3, 1) == (pop, 1, 0)
    assert _hit(layout, 4, 2) == (pop, 2, 1)
    assert _hit(layout, 0, 1) == (b, 0, 0)
    assert _hit(layout, 5, 2) == (b, 5, 1)  # just right of the box
    assert _hit(layout, 3, 0) == (a, 3, 0)  # just above it
    assert _hit(layout, 0, 7) is None
    assert layout.hit(1) == (b, 0)  # the row-only query sees the stack alone


def test_overlay_clamps_into_frame():
    base = Static([('12345678\n12345678', None)])
    pop = Static([('XYZ\nXYZ', None)])
    layout = stack_layout([base], width=8, max_height=2, theme=EMPTY_THEME, overlays=[Overlay(pop, 7, 1, 3)])

    # Slid left to fit the width and up to fit the height, rather than clipped.
    assert _texts(layout.frame) == ['12345XYZ', '12345XYZ']
    [region] = layout.overlays
    assert (region.x, region.y) == (5, 0)
    assert _hit(layout, 7, 1) == (pop, 2, 1)


def test_overlay_grows_frame_toward_budget():
    base = Static([('base', None)])
    pop = Static([('X\nX\nX', None)])

    layout = stack_layout([base], width=6, max_height=5, theme=EMPTY_THEME, overlays=[Overlay(pop, 1, 0, 1)])
    assert _texts(layout.frame) == ['bXse', ' X', ' X']

    # A box taller than the whole budget shows what fits, from its top.
    layout = stack_layout([base], width=6, max_height=2, theme=EMPTY_THEME, overlays=[Overlay(pop, 1, 0, 1)])
    assert _texts(layout.frame) == ['bXse', ' X']
    [region] = layout.overlays
    assert region.height == 2


def test_overlay_wider_than_frame_clips_and_empty_lands_nowhere():
    base = Static([('abc', None)])
    pop = Static([('WXYZ', None)])
    layout = stack_layout(
        [base],
        width=3,
        max_height=1,
        theme=EMPTY_THEME,
        overlays=[Overlay(pop, 0, 0, 10), Overlay(Nothing(), 0, 0, 2)],
    )
    assert _texts(layout.frame) == ['WXY']
    assert len(layout.overlays) == 1

    layout = stack_layout(
        [base],
        width=3,
        max_height=1,
        theme=EMPTY_THEME,
        overlays=[Overlay(pop, 0, 0, 2, max_height=0)],
    )
    assert _texts(layout.frame) == ['abc']
    assert layout.overlays == ()


def test_overlay_focus_places_cursor():
    pop = Cursory([('ab\ncd', None)])
    layout = stack_layout(
        [Static([('xxxxx', None)])],
        width=5,
        max_height=3,
        theme=EMPTY_THEME,
        focus=pop,
        overlays=[Overlay(pop, 2, 0, 2)],
    )
    assert _texts(layout.frame) == ['xxabx', '  cd']
    assert (layout.frame.cursor, layout.frame.cursor_visible) == ((3, 1), True)

    # Not focused: the cursor parks, hidden, as for any stack without one.
    layout = stack_layout(
        [Static([('xxxxx', None)])],
        width=5,
        max_height=3,
        theme=EMPTY_THEME,
        overlays=[Overlay(pop, 2, 0, 2)],
    )
    assert not layout.frame.cursor_visible


def test_overlay_fill_style_and_order():
    fill = Style(bold=True)
    pop = Static([('X', None)])
    layout = stack_layout(
        [Static([('abcd', None)])],
        width=4,
        max_height=1,
        theme=EMPTY_THEME,
        overlays=[Overlay(pop, 1, 0, 2, fill=fill)],
    )
    [line] = layout.frame.lines
    assert line.text == 'aX d'
    assert line.cells[2].style == fill

    # Later overlays paint over earlier ones, and win hits.
    under = Static([('UU\nUU', None)])
    over = Static([('O', None)])
    layout = stack_layout(
        [Static([('......', None)])],
        width=6,
        max_height=2,
        theme=EMPTY_THEME,
        overlays=[Overlay(under, 1, 0, 2), Overlay(over, 2, 0, 1)],
    )
    assert _texts(layout.frame) == ['.UO...', ' UU']
    assert _hit(layout, 2, 0) == (over, 0, 0)
    assert _hit(layout, 1, 0) == (under, 0, 0)
