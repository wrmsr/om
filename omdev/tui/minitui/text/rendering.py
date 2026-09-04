"""Headless terminal rendering for styled segments and documents."""

from omcore.text import styled as st

from .colors import ColorDepth
from .segments import SegmentRows
from .segments import Segments
from .segments import styled_text_to_segment_lines
from .sgr import RESET_SGR
from .sgr import style_sgr
from .styles import EMPTY_THEME
from .styles import Style
from .styles import Theme


##


def render_ansi_segments(
        segments: Segments,
        *,
        theme: Theme = EMPTY_THEME,
        base: Style | None = None,
        depth: ColorDepth = ColorDepth.TRUE,
) -> str:
    """Render one segment row to ANSI without a screen, surface, driver, or event loop."""

    active = ''
    rendered: list[str] = []
    for segment in segments:
        style = theme.resolve(segment.style, base)
        target = style_sgr(style, depth)
        if target != active:
            rendered.append(target or RESET_SGR)
            active = target
        rendered.append(segment.text)

    if active:
        rendered.append(RESET_SGR)
    return ''.join(rendered)


def render_ansi_segment_rows(
        rows: SegmentRows,
        *,
        theme: Theme = EMPTY_THEME,
        base: Style | None = None,
        depth: ColorDepth = ColorDepth.TRUE,
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


def render_ansi_styled_text(
        text: st.StyledTextLike,
        *,
        theme: Theme = EMPTY_THEME,
        base: Style | None = None,
        depth: ColorDepth = ColorDepth.TRUE,
) -> str:
    """Resolve and render target-neutral styled text directly to an ANSI string."""

    return render_ansi_segment_rows(
        styled_text_to_segment_lines(st.StyledText.of(text), theme=theme, base=base),
        theme=EMPTY_THEME,
        depth=depth,
    )


def render_ansi_styled_document(
        document: st.StyledDocument,
        *,
        theme: Theme = EMPTY_THEME,
        base: Style | None = None,
        depth: ColorDepth = ColorDepth.TRUE,
) -> str:
    """Resolve and render a target-neutral styled document directly to an ANSI string."""

    if not isinstance(document, st.StyledDocument):
        raise TypeError(document)

    rows = [
        styled_text_to_segment_lines(line, theme=theme, base=base)[0]
        for line in document.lines
    ]
    return render_ansi_segment_rows(
        rows,
        theme=EMPTY_THEME,
        depth=depth,
        trailing_newline=document.trailing_newline,
    )
