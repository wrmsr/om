"""
Cell-level overlay compositing: splicing one line over another at a column - the mechanism under floating controls
(popups, menus, dialogs). Pure functions over `Line`s; placement policy (where a box goes, clamping into the frame)
lives in the controls layer.

The one subtlety is wide characters: a cell cannot be half-covered. A wide cell of the base straddling either edge of
the overlaid span is replaced by plain spaces in its style over its exposed columns, and a wide cell of the overlay that
would run past the span's end is dropped for fill - so the composite is exactly the base's columns with a
`width`-column box punched in.
"""
import typing as ta

from omcore import check

from ..text.styles import EMPTY_STYLE
from ..text.styles import Style
from .cells import Cell
from .cells import Line


##


def _spaces(n: int, style: Style) -> list[Cell]:
    return [Cell(' ', 1, style) for _ in range(n)]


def fit_cells(cells: ta.Iterable[Cell], width: int, fill: Style = EMPTY_STYLE) -> list[Cell]:
    """
    Exactly `width` columns of `cells`: clipped (a wide cell straddling the end is dropped), then padded with fill.
    """

    out: list[Cell] = []
    used = 0
    for cell in cells:
        if used + cell.width > width:
            break
        out.append(cell)
        used += cell.width
    out.extend(_spaces(width - used, fill))
    return out


def overlay_line(base: Line, top: Line, x: int, width: int, *, fill: Style = EMPTY_STYLE) -> Line:
    """`base` with columns [x, x + width) replaced by `top` fitted to `width` - an opaque box over the row."""

    check.arg(x >= 0)
    check.arg(width > 0)

    left: list[Cell] = []
    right: list[Cell] = []
    end = x + width
    pos = 0
    for cell in base.cells:
        cell_end = pos + cell.width
        if cell_end <= x:
            left.append(cell)
        elif pos < x:
            left.extend(_spaces(x - pos, cell.style))  # straddles the left edge: its exposed columns stay, blank
        elif pos >= end:
            right.append(cell)
        elif cell_end > end:
            right.extend(_spaces(cell_end - end, cell.style))  # straddles the right edge
        pos = cell_end
    if pos < x:
        left.extend(_spaces(x - pos, EMPTY_STYLE))  # the base ends short of the box

    return Line.from_cells([*left, *fit_cells(top.cells, width, fill), *right])


def overlay_lines(
        base: ta.Sequence[Line],
        top: ta.Sequence[Line],
        x: int,
        y: int,
        width: int,
        *,
        fill: Style = EMPTY_STYLE,
) -> list[Line]:
    """`base` with `top` boxed in at (x, y); rows of `top` falling outside `base` are dropped."""

    out = list(base)
    for i, row in enumerate(top):
        if 0 <= (j := y + i) < len(out):
            out[j] = overlay_line(out[j], row, x, width, fill=fill)
    return out
