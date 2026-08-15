"""
Vertical stacking of controls into a frame - the live region's layout.

Deliberately simple for now: full width, natural heights, stacked top to bottom. When the total exceeds the height
budget, rows are dropped *from the top* - the bottom of the live region (input, status) is the part that must stay
visible. Weighted height distribution (the Dimension model) arrives when a control actually needs to flex; nothing
depends on the current truncation policy.
"""
import typing as ta

from ..screens.cells import Frame
from ..screens.cells import Line
from ..screens.cells import line_from_segments
from ..text.styles import Theme
from .bases import Control


##


def stack_frame(
        controls: ta.Sequence[Control],
        *,
        width: int,
        max_height: int,
        theme: Theme,
        focus: Control | None = None,
) -> Frame:
    """
    Render `controls` top-to-bottom into a frame fitting `max_height`.

    The cursor comes from `focus` (offset to its rows); if focus is None or its cursor is None (or truncated away),
    the frame's cursor is parked at the end with the cursor hidden.
    """

    lines: list[Line] = []
    cursor: tuple[int, int] | None = None

    for control in controls:
        rows = control.render(width)
        if control is focus and (c := control.cursor(width)) is not None:
            cursor = (c[0], c[1] + len(lines))
        lines.extend(line_from_segments(row, theme) for row in rows)

    if len(lines) > max_height:
        drop = len(lines) - max_height
        lines = lines[drop:]
        if cursor is not None:
            cursor = (cursor[0], cursor[1] - drop)
            if cursor[1] < 0:
                cursor = None

    if cursor is None:
        return Frame(
            tuple(lines),
            cursor=(0, max(len(lines) - 1, 0)),
            cursor_visible=False,
        )

    return Frame(
        tuple(lines),
        cursor=cursor,
        cursor_visible=True,
    )
