"""
Vertical stacking of controls into a frame - the live region's layout - with overlays floated on top.

Deliberately simple for now: full width, natural heights, stacked top to bottom. When the total exceeds the height
budget, rows are dropped *from the top* - the bottom of the live region (input, status) is the part that must stay
visible. Weighted height distribution (the Dimension model) arrives when a control actually needs to flex; nothing
depends on the current truncation policy.

`stack_layout` additionally reports each control's row range within the frame - the hit map for routing mouse clicks
(the app calls `StackLayout.hit(y)` with a frame-relative row and forwards the event, y localized, to the control) -
and, given `overlays`, composites them over the stacked rows (see `overlays.py`) and reports their boxes; an app with
overlays routes by point through `hit_at`, which checks them topmost-first.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..screens.cells import Frame
from ..screens.cells import Line
from ..screens.cells import line_from_segments
from ..text.styles import Theme
from .base import Control
from .overlays import Overlay
from .overlays import OverlayRegion
from .overlays import place_overlays


##


@dc.dataclass(frozen=True)
class StackRegion(lang.Final):
    control: Control
    y_start: int
    y_end: int  # exclusive
    clip_top: int = 0  # leading control rows dropped by truncation


@dc.dataclass(frozen=True)
class LayoutHit(lang.Final):
    """The control under a frame point, with the point in the control's own coordinates."""

    control: Control
    x: int
    y: int


@dc.dataclass(frozen=True)
class StackLayout(lang.Final):
    frame: Frame
    regions: tuple[StackRegion, ...]
    overlays: tuple[OverlayRegion, ...] = ()

    def hit(self, y: int) -> tuple[Control, int] | None:
        """
        The stacked control at frame row `y` and that row's index within the control's own rendering, or None. Sees only
        the stack: with overlays in play, route by point through `hit_at`.
        """

        for region in self.regions:
            if region.y_start <= y < region.y_end:
                return (region.control, y - region.y_start + region.clip_top)
        return None

    def hit_at(self, x: int, y: int) -> LayoutHit | None:
        """The control under frame point (x, y): the topmost overlay covering it, else the stacked control on row y."""

        for region in reversed(self.overlays):
            if region.contains(x, y):
                return LayoutHit(region.control, x - region.x, y - region.y)
        if (found := self.hit(y)) is not None:
            control, local_y = found
            return LayoutHit(control, x, local_y)
        return None


def stack_layout(
        controls: ta.Sequence[Control],
        *,
        width: int,
        max_height: int,
        theme: Theme,
        focus: Control | None = None,
        overlays: ta.Sequence[Overlay] = (),
) -> StackLayout:
    """
    Render `controls` top-to-bottom into a frame fitting `max_height`, with per-control hit regions, then float
    `overlays` over the result (later ones on top; the frame grows toward `max_height` for a box that needs the rows).

    The cursor comes from `focus` (offset to its rows, or to its overlay's box); if focus is None or its cursor is None
    (or truncated away), the frame's cursor is parked at the end with the cursor hidden.
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

    overlay_regions: list[OverlayRegion] = []
    if overlays:
        overlay_regions = place_overlays(
            lines,
            overlays,
            width=width,
            max_height=max_height,
            theme=theme,
        )
        for region in overlay_regions:
            if region.control is focus and (c := focus.cursor(region.width)) is not None:
                cursor = (region.x + c[0], region.y + c[1])

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
    return StackLayout(frame, regions, tuple(overlay_regions))


def stack_frame(
        controls: ta.Sequence[Control],
        *,
        width: int,
        max_height: int,
        theme: Theme,
        focus: Control | None = None,
        overlays: ta.Sequence[Overlay] = (),
) -> Frame:
    return stack_layout(
        controls,
        width=width,
        max_height=max_height,
        theme=theme,
        focus=focus,
        overlays=overlays,
    ).frame
