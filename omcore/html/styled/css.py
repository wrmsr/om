"""Inline css for resolved styles."""
from ...text import styled as st


##


def _color_css(color: st.Color | None) -> str | None:
    if color is None:
        return None
    if isinstance(color, st.RgbColor):
        return color.hex
    raise TypeError(color)


def _visual_colors(style: st.ResolvedStyle) -> tuple[str | None, str | None]:
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


def _text_decoration(style: st.ResolvedStyle) -> str:
    lines: list[str] = []
    if style.underline:
        lines.append('underline')
    if style.blink:
        lines.append('blink')
    if style.strike:
        lines.append('line-through')
    return ' '.join(lines) if lines else 'none'


def style_to_css(
        style: st.ResolvedStyle,
        *,
        base: st.ResolvedStyle = st.PLAIN_STYLE,
) -> str:
    """Render the effective differences between `style` and the ambient `base` as inline css."""

    if not isinstance(style, st.ResolvedStyle):
        raise TypeError(style)
    if not isinstance(base, st.ResolvedStyle):
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
