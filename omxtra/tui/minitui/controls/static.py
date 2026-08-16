"""Static text controls."""
import typing as ta

from ..text.segments import Segment
from ..text.styles import StyleLike
from ..text.wraps import wrap_segments
from .base import Control


TextParts: ta.TypeAlias = ta.Sequence[tuple[str, StyleLike]]


##


def parts_to_segment_lines(parts: TextParts) -> list[list[Segment]]:
    """Split styled (text, style) parts on newlines into per-line segment lists."""

    lines: list[list[Segment]] = [[]]
    for text, style in parts:
        first = True
        for chunk in text.split('\n'):
            if not first:
                lines.append([])
            first = False
            if chunk:
                lines[-1].append(Segment(chunk, style))
    return lines


class Static(Control):
    """Styled, word-wrapped text. Mutate via `set_parts`/`set_text` (then invalidate the driver)."""

    def __init__(
            self,
            parts: TextParts = (),
    ) -> None:
        super().__init__()

        self._lines: list[list[Segment]] = parts_to_segment_lines(parts)

    def set_parts(self, parts: TextParts) -> None:
        self._lines = parts_to_segment_lines(parts)

    def set_text(self, text: str, style: StyleLike = None) -> None:
        self.set_parts([(text, style)])

    def render(self, width: int) -> ta.Sequence[ta.Sequence[Segment]]:
        rows: list[ta.Sequence[Segment]] = []
        for line in self._lines:
            rows.extend(wrap_segments(line, width))
        return rows
