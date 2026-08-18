"""
Structured text styling.

A `Style` is a plain frozen dataclass - never an SGR string, never a stylesheet entry. Content-producing code should
usually emit *semantic tags* (plain strings like 'status.mode' or 'syntax.keyword') and let a `Theme` resolve them to
concrete styles at render time; concrete `Style` values are for when the content really does mean a specific look.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .colors import Color


##


@dc.dataclass(frozen=True, kw_only=True)
class Style(lang.Final):
    fg: Color | None = None
    bg: Color | None = None

    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False
    blink: bool = False
    reverse: bool = False
    strike: bool = False
    hidden: bool = False

    @property
    def is_plain(self) -> bool:
        return self == EMPTY_STYLE

    def overlay(self, other: Style) -> Style:
        """
        Return this style with `other`'s set fields applied over it.

        Colors overlay when non-None; attribute flags are or'd. This is the merge rule used when compositing style spans
        from multiple producers (syntax under selection under search, etc.).
        """

        if other.is_plain:
            return self
        if self.is_plain:
            return other
        return Style(
            fg=other.fg if other.fg is not None else self.fg,
            bg=other.bg if other.bg is not None else self.bg,
            bold=self.bold or other.bold,
            dim=self.dim or other.dim,
            italic=self.italic or other.italic,
            underline=self.underline or other.underline,
            blink=self.blink or other.blink,
            reverse=self.reverse or other.reverse,
            strike=self.strike or other.strike,
            hidden=self.hidden or other.hidden,
        )


EMPTY_STYLE = Style()


# What content code may attach to text: nothing, a concrete style, or a semantic theme tag.
StyleLike: ta.TypeAlias = Style | str | None


##


class Theme:
    """Resolves semantic tags to concrete styles. Unknown tags resolve to the empty style, deliberately."""

    def __init__(self, styles: ta.Mapping[str, Style] | None = None) -> None:
        super().__init__()

        self._styles: dict[str, Style] = dict(styles or {})

    def resolve(self, style: StyleLike) -> Style:
        if style is None:
            return EMPTY_STYLE
        if isinstance(style, Style):
            return style
        return self._styles.get(style, EMPTY_STYLE)

    def extend(self, styles: ta.Mapping[str, Style]) -> Theme:
        """A new Theme with `styles` layered over this one's entries (whole-entry replacement per tag)."""

        return Theme({**self._styles, **styles})


EMPTY_THEME = Theme()
