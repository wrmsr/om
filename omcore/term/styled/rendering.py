"""
Headless ANSI rendering of styled text - no screen, surface, driver, or event loop.

An ANSI byte stream reflows like any other flow text: nothing here measures cells or wraps. Fixed-width layout is a
separate lowering (`omcore.text.styled.grid`) that a screen applies before rendering, and a plain log line never needs.
"""
import typing as ta

from ...text import styled as st
from .colors import ColorDepth
from .sgr import RESET_SGR
from .sgr import style_sgr


##


def render_ansi_runs(
        runs: ta.Iterable[st.ResolvedStyledTextRun],
        *,
        depth: ColorDepth = ColorDepth.TRUE,
) -> str:
    """Render resolved runs as one ANSI string, eliding unchanged style transitions and resetting at the end."""

    active = ''
    rendered: list[str] = []
    for run in runs:
        target = style_sgr(run.style, depth)
        if target != active:
            rendered.append(target or RESET_SGR)
            active = target
        rendered.append(run.text)

    if active:
        rendered.append(RESET_SGR)
    return ''.join(rendered)


def render_ansi(
        text: st.StyledContent,
        *,
        theme: st.StyleTheme = st.EMPTY_STYLE_THEME,
        base: st.ResolvedStyle | None = None,
        depth: ColorDepth = ColorDepth.TRUE,
) -> str:
    """
    Resolve and render styled text or a styled document to an ANSI string.

    Each line is rendered and reset on its own so styles never bleed across newlines.
    """

    document = text if isinstance(text, st.StyledDocument) else st.StyledDocument.of_text(st.StyledText.of(text))
    rendered = '\n'.join(
        render_ansi_runs(line.resolved_runs(theme, base), depth=depth)
        for line in document.lines
    )
    if document.trailing_newline:
        rendered += '\n'
    return rendered
