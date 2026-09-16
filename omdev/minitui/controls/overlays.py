"""
Floating controls over the stacked frame: popups, menus, dialogs.

An `Overlay` floats a control at a frame position, `width` columns wide and opaque (rows pad to the width with `fill`).
Placement clamps the box into the frame - a popup anchored near the right or bottom edge slides left or up rather than
clipping - after growing the frame toward its height budget when the box needs rows the base does not have (the inline
live region grows while a popup is open; a fullscreen frame already fills the terminal). The cell splice itself is
`screens.overlays`; the frame's cursor follows a focused overlay; hit-testing is by point (`StackLayout.hit_at`),
overlays topmost-first before the stacked controls.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..screens.cells import EMPTY_LINE
from ..screens.cells import Line
from ..screens.cells import line_from_segments
from ..screens.overlays import overlay_line
from ..text.styles import StyleLike
from ..text.styles import Theme
from .base import Control


##


@dc.dataclass(frozen=True)
class Overlay(lang.Final):
    control: Control
    x: int
    y: int
    width: int

    _: dc.KW_ONLY

    fill: StyleLike | None = None  # the style of the padding that squares rows off to `width`
    max_height: int | None = None  # rows beyond are clipped before placement


@dc.dataclass(frozen=True)
class OverlayRegion(lang.Final):
    """Where an overlay landed after clamping: its box in frame coordinates."""

    overlay: Overlay
    x: int
    y: int
    width: int
    height: int

    @property
    def control(self) -> Control:
        return self.overlay.control

    def contains(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height


def place_overlays(
        lines: list[Line],
        overlays: ta.Iterable[Overlay],
        *,
        width: int,
        max_height: int,
        theme: Theme,
) -> list[OverlayRegion]:
    """
    Composite `overlays` onto `lines` in order (later ones on top), growing `lines` toward `max_height` as boxes need,
    and return where each landed. An overlay whose control renders nothing lands nowhere.
    """

    regions: list[OverlayRegion] = []
    for overlay in overlays:
        box_width = min(overlay.width, width)
        if box_width <= 0:
            continue
        rows = overlay.control.render(box_width)
        if overlay.max_height is not None:
            rows = rows[:overlay.max_height]
        top = [line_from_segments(row, theme) for row in rows]
        if not top:
            continue

        while len(lines) < min(overlay.y + len(top), max_height):
            lines.append(EMPTY_LINE)
        top = top[:len(lines)]  # taller than the whole frame: what fits, from the top
        height = len(top)

        x = max(min(overlay.x, width - box_width), 0)
        y = max(min(overlay.y, len(lines) - height), 0)
        fill = theme.resolve(overlay.fill)
        for i, row in enumerate(top):
            lines[y + i] = overlay_line(lines[y + i], row, x, box_width, fill=fill)
        regions.append(OverlayRegion(overlay, x, y, box_width, height))
    return regions
