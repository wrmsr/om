import typing as ta

from .segments import Segment
from .styles import StyleLike


TextParts: ta.TypeAlias = ta.Sequence[tuple[str, StyleLike | None]]


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
