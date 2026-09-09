"""Headless terminal rendering for styled segments. Styled text and documents render through `omcore.term.styled`."""
from omcore.term import styled as tst
from omcore.text import styled as st

from .segments import SegmentRows
from .segments import Segments
from .styles import EMPTY_THEME
from .styles import Style
from .styles import Theme


##


def render_ansi_segments(
        segments: Segments,
        *,
        theme: Theme = EMPTY_THEME,
        base: Style | None = None,
        depth: tst.ColorDepth = tst.ColorDepth.TRUE,
) -> str:
    """Render one segment row to ANSI without a screen, surface, driver, or event loop."""

    return tst.render_ansi_runs(
        (
            st.ResolvedStyledTextRun(segment.text, theme.resolve(segment.style, base))
            for segment in segments
            if segment.text
        ),
        depth=depth,
    )


def render_ansi_segment_rows(
        rows: SegmentRows,
        *,
        theme: Theme = EMPTY_THEME,
        base: Style | None = None,
        depth: tst.ColorDepth = tst.ColorDepth.TRUE,
        trailing_newline: bool = False,
) -> str:
    """Render already-split segment rows as a newline-delimited ANSI string."""

    rendered = '\n'.join(
        render_ansi_segments(row, theme=theme, base=base, depth=depth)
        for row in rows
    )
    if trailing_newline and rows:
        rendered += '\n'
    return rendered
