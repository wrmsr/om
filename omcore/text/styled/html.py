"""HTML fragment rendering."""
import html

from .colors import Color
from .colors import RgbColor
from .documents import StyledContent
from .documents import StyledDocument
from .styles import EMPTY_STYLE_THEME
from .styles import PLAIN_STYLE
from .styles import ResolvedStyle
from .styles import StyleTheme
from .text import StyledText


##


def _color_css(color: Color | None) -> str | None:
    if color is None:
        return None
    if isinstance(color, RgbColor):
        return color.hex
    raise TypeError(color)


def _visual_colors(style: ResolvedStyle) -> tuple[str | None, str | None]:
    fg = _color_css(style.fg)
    bg = _color_css(style.bg)
    if style.reverse:
        return (
            bg if bg is not None else 'Canvas',
            fg if fg is not None else 'CanvasText',
        )
    return fg, bg


def _append_css_difference(
        declarations: list[tuple[str, str]],
        name: str,
        value: str | None,
        base_value: str | None,
) -> None:
    if value != base_value:
        declarations.append((name, 'initial' if value is None else value))


def _text_decoration(style: ResolvedStyle) -> str:
    lines: list[str] = []
    if style.underline:
        lines.append('underline')
    if style.blink:
        lines.append('blink')
    if style.strike:
        lines.append('line-through')
    return ' '.join(lines) if lines else 'none'


def style_to_css(
        style: ResolvedStyle,
        *,
        base: ResolvedStyle = PLAIN_STYLE,
) -> str:
    """Render the effective differences between `style` and the ambient `base` as inline CSS."""

    if not isinstance(style, ResolvedStyle):
        raise TypeError(style)
    if not isinstance(base, ResolvedStyle):
        raise TypeError(base)

    declarations: list[tuple[str, str]] = []

    fg, bg = _visual_colors(style)
    base_fg, base_bg = _visual_colors(base)
    _append_css_difference(declarations, 'color', fg, base_fg)
    _append_css_difference(declarations, 'background-color', bg, base_bg)

    if style.bold != base.bold:
        declarations.append(('font-weight', 'bold' if style.bold else 'normal'))
    if style.dim != base.dim:
        declarations.append(('opacity', '.5' if style.dim else '1'))
    if style.italic != base.italic:
        declarations.append(('font-style', 'italic' if style.italic else 'normal'))

    decorations = _text_decoration(style)
    base_decorations = _text_decoration(base)
    if decorations != base_decorations:
        declarations.append(('text-decoration-line', decorations))

    if style.hidden != base.hidden:
        declarations.append(('visibility', 'hidden' if style.hidden else 'visible'))

    return ';'.join(f'{name}:{value}' for name, value in declarations)


def render_html(
        text: StyledContent,
        *,
        theme: StyleTheme = EMPTY_STYLE_THEME,
        base: ResolvedStyle = PLAIN_STYLE,
) -> str:
    """
    Render styled text as an escaped HTML fragment with deterministic inline CSS.

    Literal whitespace is preserved in the fragment. Its containing element should use `white-space: pre-wrap` when
    the browser must display that whitespace exactly.
    """

    value = text.text if isinstance(text, StyledDocument) else StyledText.of(text)
    rendered: list[str] = []
    for run in value.resolved_runs(theme, base):
        escaped = html.escape(run.text, quote=False)
        if css := style_to_css(run.style, base=base):
            rendered.append(f'<span style="{css}">{escaped}</span>')
        else:
            rendered.append(escaped)
    return ''.join(rendered)
