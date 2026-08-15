"""
Styled text segments - the currency of content production.

A `Segment` is a run of text with one style (concrete or semantic tag); controls render to sequences of segments, one
line per sequence. Segments are *plain text only*: no escape sequences, no newlines inside a segment (splitting
multi-line text is the producer's job, via `split_segment_lines`). Widths and wrapping live downstream in the screens
layer, which turns segments into cells.
"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from .styles import StyleLike


Segments: ta.TypeAlias = ta.Sequence['Segment']


##


@dc.dataclass(frozen=True)
class Segment(lang.Final):
    text: str
    style: StyleLike = None

    def __post_init__(self) -> None:
        check.arg('\x1b' not in self.text and '\n' not in self.text and '\r' not in self.text)


def segments_text(segments: Segments) -> str:
    return ''.join(segment.text for segment in segments)


def split_segment_lines(
        parts: ta.Iterable[tuple[str, StyleLike]],
) -> list[list[Segment]]:
    """Split (text, style) runs which may contain newlines into per-line segment lists."""

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
