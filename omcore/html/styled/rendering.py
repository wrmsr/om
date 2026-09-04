"""Html fragment rendering of styled text."""
import html

from ...text import styled as st
from .css import style_to_css


##


def render_html(
        text: st.StyledContent,
        *,
        theme: st.StyleTheme = st.EMPTY_STYLE_THEME,
        base: st.ResolvedStyle = st.PLAIN_STYLE,
) -> str:
    """
    Render styled text as an escaped html fragment with deterministic inline css.

    Literal whitespace is preserved in the fragment. Its containing element should use `white-space: pre-wrap` when
    the browser must display that whitespace exactly.
    """

    value = text.text if isinstance(text, st.StyledDocument) else st.StyledText.of(text)
    rendered: list[str] = []
    for run in value.resolved_runs(theme, base):
        escaped = html.escape(run.text, quote=False)
        if css := style_to_css(run.style, base=base):
            rendered.append(f'<span style="{css}">{escaped}</span>')
        else:
            rendered.append(escaped)
    return ''.join(rendered)
