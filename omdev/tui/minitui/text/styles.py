"""
Structured text styling.

The target-neutral style values live in `omcore.text.styled`; this module is minitui's compatibility facade and theme
adapter. Content-producing code should usually emit semantic tags and let a `Theme` resolve them at render time.
"""
import typing as ta

from omcore import lang
from omcore.text import styled as st


##


Style = st.ResolvedStyle


EMPTY_STYLE = st.PLAIN_STYLE


type StyleLike = st.ResolvedStyle | st.StyleLike
type ThemeStyle = st.ResolvedStyle | st.StylePatch


def _as_style_patch(style: ThemeStyle) -> st.StylePatch:
    if isinstance(style, st.StylePatch):
        return style
    if not isinstance(style, st.ResolvedStyle):
        raise TypeError(style)
    return st.StylePatch(
        fg=style.fg,
        bg=style.bg,
        bold=True if style.bold else None,
        dim=True if style.dim else None,
        italic=True if style.italic else None,
        underline=True if style.underline else None,
        blink=True if style.blink else None,
        reverse=True if style.reverse else None,
        strike=True if style.strike else None,
        hidden=True if style.hidden else None,
    )


##


class Theme(lang.Final):
    """Resolve minitui style values through a target-neutral `StyleTheme`."""

    def __init__(self, styles: ta.Mapping[ta.Any, ThemeStyle] | None = None) -> None:
        super().__init__()

        self._theme = st.StyleTheme({
            name: _as_style_patch(style)
            for name, style in (styles or {}).items()
        })

    @property
    def style_theme(self) -> st.StyleTheme:
        """The underlying target-neutral theme, for the headless core renderers."""

        return self._theme

    def resolve(self, style: StyleLike | None, base: st.ResolvedStyle | None = None) -> st.ResolvedStyle:
        if style is None:
            return EMPTY_STYLE if base is None else base
        if isinstance(style, st.ResolvedStyle):
            return style
        return self._theme.resolve_refs((st.as_style_ref(style),), base)

    def resolve_refs(
            self,
            styles: ta.Iterable[st.StyleRef],
            base: st.ResolvedStyle | None = None,
    ) -> st.ResolvedStyle:
        return self._theme.resolve_refs(styles, base)

    def extend(self, styles: ta.Mapping[ta.Any, ThemeStyle]) -> Theme:
        """A new Theme with `styles` layered over this one's entries (whole-entry replacement per tag)."""

        return Theme(self._theme.extend({
            name: _as_style_patch(style)
            for name, style in styles.items()
        }).as_dict())


EMPTY_THEME = Theme()
