"""The elastic status bar: left and right styled parts, right-aligned when they fit on one row."""
import typing as ta

from ..text.segments import Segment
from ..text.widths import str_width
from ..text.wraps import wrap_segments
from .bases import Control
from .statics import TextParts


##


def _parts_to_segments(parts: TextParts) -> list[Segment]:
    return [Segment(text, style) for text, style in parts if text]


def _segments_width(segments: ta.Sequence[Segment]) -> int:
    return sum(str_width(segment.text) for segment in segments)


class StatusBar(Control):
    """
    Readonly and never focusable. One row when left + right fit (right-aligned filler between); otherwise it grows -
    left content word-wrapped, then right content on its own row(s).
    """

    def __init__(
            self,
            left: TextParts = (),
            right: TextParts = (),
    ) -> None:
        super().__init__()

        self._left = _parts_to_segments(left)
        self._right = _parts_to_segments(right)

    def set_left(self, parts: TextParts) -> None:
        self._left = _parts_to_segments(parts)

    def set_right(self, parts: TextParts) -> None:
        self._right = _parts_to_segments(parts)

    def render(self, width: int) -> ta.Sequence[ta.Sequence[Segment]]:
        left_w = _segments_width(self._left)
        right_w = _segments_width(self._right)

        if not self._right:
            return wrap_segments(self._left, width)

        if left_w + right_w + 1 <= width:
            filler = ' ' * (width - left_w - right_w)
            return [[*self._left, Segment(filler), *self._right]]

        return [
            *wrap_segments(self._left, width),
            *wrap_segments(self._right, width),
        ]
