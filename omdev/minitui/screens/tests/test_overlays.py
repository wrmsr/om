# @om-precheck-allow-any-unicode
from ...text.segments import Segment
from ...text.styles import EMPTY_STYLE
from ...text.styles import EMPTY_THEME
from ...text.styles import Style
from ..cells import Cell
from ..cells import line_from_segments
from ..overlays import fit_cells
from ..overlays import overlay_line
from ..overlays import overlay_lines


##


WIDE = '日'  # a two-column CJK character


def _line(*parts):
    return line_from_segments(
        [Segment(p) if isinstance(p, str) else Segment(*p) for p in parts],
        EMPTY_THEME,
    )


def test_overlay_line_middle():
    out = overlay_line(_line('abcdefgh'), _line('XY'), 2, 2)
    assert out.text == 'abXYefgh'
    assert out.width == 8


def test_overlay_line_pads_with_fill():
    fill = Style(bold=True)
    out = overlay_line(_line('abcdefgh'), _line('X'), 2, 3, fill=fill)
    assert out.text == 'abX  fgh'
    assert [c.style for c in out.cells[2:5]] == [EMPTY_STYLE, fill, fill]


def test_overlay_line_beyond_base_end():
    out = overlay_line(_line('ab'), _line('XY'), 4, 2)
    assert out.text == 'ab  XY'
    assert all(c == Cell(' ', 1, EMPTY_STYLE) for c in out.cells[2:4])


def test_overlay_line_wide_base_straddles_left_edge():
    styled = Style(italic=True)
    base = _line('a', (WIDE, styled), 'b')  # columns: a=0, wide=1-2, b=3
    out = overlay_line(base, _line('X'), 2, 1)
    assert out.text == 'a Xb'
    assert out.cells[1] == Cell(' ', 1, styled)  # the exposed half keeps the cell's style


def test_overlay_line_wide_base_straddles_right_edge():
    base = _line('a', WIDE, 'b')
    out = overlay_line(base, _line('XY'), 0, 2)
    assert out.text == 'XY b'
    assert out.width == 4


def test_overlay_line_wide_top_clipped_to_box():
    out = overlay_line(_line('abc'), _line(WIDE), 1, 1)
    assert out.text == 'a c'


def test_overlay_line_covers_base_fully():
    out = overlay_line(_line('ab'), _line('WXYZ'), 0, 4)
    assert out.text == 'WXYZ'


def test_fit_cells():
    cells = _line('ab', WIDE, 'c').cells
    assert ''.join(c.text for c in fit_cells(cells, 3)) == 'ab '  # the wide cell would run past: fill instead
    assert ''.join(c.text for c in fit_cells(cells, 4)) == 'ab' + WIDE
    assert ''.join(c.text for c in fit_cells(cells, 7)) == 'ab' + WIDE + 'c  '
    assert fit_cells((), 2) == [Cell(' ', 1, EMPTY_STYLE)] * 2


def test_overlay_lines_offsets_and_clipping():
    base = [_line('r0'), _line('r1'), _line('r2')]
    top = [_line('A'), _line('B')]

    out = overlay_lines(base, top, 1, 1, 1)
    assert [line.text for line in out] == ['r0', 'rA', 'rB']

    out = overlay_lines(base, top, 0, 2, 1)
    assert [line.text for line in out] == ['r0', 'r1', 'A2']  # the second row falls off the bottom

    out = overlay_lines(base, top, 0, -1, 1)
    assert [line.text for line in out] == ['B0', 'r1', 'r2']  # the first row falls off the top

    assert [line.text for line in base] == ['r0', 'r1', 'r2']  # inputs untouched
