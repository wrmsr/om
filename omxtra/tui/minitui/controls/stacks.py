"""
Vertical stacking of controls into a frame - the live region's layout.

Deliberately simple for now: full width, natural heights, stacked top to bottom. When the total exceeds the height
budget, rows are dropped *from the top* - the bottom of the live region (input, status) is the part that must stay
visible. Weighted height distribution (the Dimension model) arrives when a control actually needs to flex; nothing
depends on the current truncation policy.

`stack_layout` additionally reports each control's row range within the frame - the hit map for routing mouse clicks
(the app calls `StackLayout.hit(y)` with a frame-relative row and forwards the event, y localized, to the control).
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..screens.cells import Frame
from ..screens.cells import Line
from ..screens.cells import line_from_segments
from ..text.styles import Theme
from .bases import Control


##


@dc.dataclass(frozen=True)
class StackRegion(lang.Final):
    control: Control
    y_start: int
    y_end: int  # exclusive
    clip_top: int = 0  # leading control rows dropped by truncation


@dc.dataclass(frozen=True)
class StackLayout(lang.Final):
    frame: Frame
    regions: tuple[StackRegion, ...]

    def hit(self, y: int) -> tuple[Control, int] | None:
        """The control at frame row `y` and that row's index within the control's own rendering, or None."""

        for region in self.regions:
            if region.y_start <= y < region.y_end:
                return (region.control, y - region.y_start + region.clip_top)
        return None


def stack_layout(
        controls: ta.Sequence[Control],
        *,
        width: int,
        max_height: int,
        theme: Theme,
        focus: Control | None = None,
) -> StackLayout:
    """
    Render `controls` top-to-bottom into a frame fitting `max_height`, with per-control hit regions.

    The cursor comes from `focus` (offset to its rows); if focus is None or its cursor is None (or truncated away),
    the frame's cursor is parked at the end with the cursor hidden.
    """

    lines: list[Line] = []
    cursor: tuple[int, int] | None = None
    spans: list[tuple[Control, int, int]] = []

    for control in controls:
        rows = control.render(width)
        if control is focus and (c := control.cursor(width)) is not None:
            cursor = (c[0], c[1] + len(lines))
        start = len(lines)
        lines.extend(line_from_segments(row, theme) for row in rows)
        if len(lines) > start:
            spans.append((control, start, len(lines)))

    drop = 0
    if len(lines) > max_height:
        drop = len(lines) - max_height
        lines = lines[drop:]
        if cursor is not None:
            cursor = (cursor[0], cursor[1] - drop)
            if cursor[1] < 0:
                cursor = None

    regions = tuple(
        StackRegion(
            control,
            max(start - drop, 0),
            end - drop,
            clip_top=max(drop - start, 0),
        )
        for control, start, end in spans
        if end - drop > 0
    )

    if cursor is None:
        frame = Frame(
            tuple(lines),
            cursor=(0, max(len(lines) - 1, 0)),
            cursor_visible=False,
        )
    else:
        frame = Frame(
            tuple(lines),
            cursor=cursor,
            cursor_visible=True,
        )
    return StackLayout(frame, regions)


def stack_frame(
        controls: ta.Sequence[Control],
        *,
        width: int,
        max_height: int,
        theme: Theme,
        focus: Control | None = None,
) -> Frame:
    return stack_layout(
        controls,
        width=width,
        max_height=max_height,
        theme=theme,
        focus=focus,
    ).frame
