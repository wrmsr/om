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
from omcore.text import styled as st

from .styles import EMPTY_THEME
from .styles import Style
from .styles import StyleLike
from .styles import Theme


type Segments = ta.Sequence[Segment]

type SegmentRows = ta.Sequence[ta.Sequence[Segment]]


##


@dc.dataclass(frozen=True)
class Segment(lang.Final):
    text: str
    style: StyleLike | None = None

    def __post_init__(self) -> None:
        check.arg('\x1b' not in self.text and '\n' not in self.text and '\r' not in self.text)


def segments_text(segments: Segments) -> str:
    return ''.join(segment.text for segment in segments)


def segments_to_styled_text(segments: Segments) -> st.StyledText:
    """
    Lift segments to styled text without resolving: a tag becomes a style name, a patch stays a patch, and a concrete
    style becomes a complete patch so it reproduces exactly over any base.
    """

    builder = st.StyledTextBuilder()
    for segment in segments:
        style: st.StyleLike | None
        if isinstance(segment.style, st.ResolvedStyle):
            style = segment.style.to_patch()
        else:
            style = segment.style
        builder.append(segment.text, style)
    return builder.build()


def styled_text_to_segments(text: st.StyledText) -> list[Segment]:
    """
    Lower single-layer styled text (highlighter output, lifted segments) to segments without resolving: one segment
    per run, a style name becoming its tag string and a complete patch becoming the concrete style it denotes, so
    lifting and lowering round-trip. Text with layered styles has no single-style segment form and must resolve
    through `styled_text_to_segment_lines`.
    """

    out: list[Segment] = []
    for run in text.runs():
        check.arg(len(run.styles) <= 1)
        style: StyleLike | None = None
        if run.styles:
            (ref,) = run.styles
            if isinstance(ref, st.StyleName):
                style = ref.name
            elif isinstance(ref, st.StylePatch) and ref.is_complete:
                style = ref.resolve()
            else:
                style = ref
        out.append(Segment(run.text, style))
    return out


def split_segment_lines(
        parts: ta.Iterable[tuple[str, StyleLike | None]],
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


def styled_text_to_segment_lines(
        text: st.StyledText,
        *,
        theme: Theme = EMPTY_THEME,
        base: Style | None = None,
) -> list[list[Segment]]:
    """Resolve target-neutral styled text into driver-free minitui segment rows."""

    parts: list[tuple[str, StyleLike | None]] = []
    for run in text.runs():
        style = theme.resolve_refs(run.styles, base)
        segment_style = None if style.is_plain else style
        if parts and parts[-1][1] == segment_style:
            previous_text, _ = parts[-1]
            parts[-1] = (previous_text + run.text, segment_style)
        else:
            parts.append((run.text, segment_style))
    return split_segment_lines(parts)
