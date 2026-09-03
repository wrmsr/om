"""Partial and resolved styles, semantic names, and themes."""
import enum
import typing as ta

from ... import dataclasses as dc
from ... import lang
from .colors import Color


##


class ColorDefault(enum.Enum):
    """An explicit request to clear an inherited color to the output target's default."""

    DEFAULT = 'default'


DEFAULT_COLOR = ColorDefault.DEFAULT


type StyleColor = Color | ColorDefault


_STYLE_FLAG_NAMES: ta.Final[ta.Sequence[str]] = (
    'bold',
    'dim',
    'italic',
    'underline',
    'blink',
    'reverse',
    'strike',
    'hidden',
)

_STYLE_FLAG_NAME_SET: ta.Final[ta.AbstractSet[str]] = frozenset(_STYLE_FLAG_NAMES)


def _check_style_color(value: StyleColor | None) -> None:
    if value is not None and not isinstance(value, (Color, ColorDefault)):
        raise TypeError(value)


def _check_style_flag(value: bool | None) -> None:
    if value is not None and not isinstance(value, bool):
        raise TypeError(value)


def _overlay_value(base: ta.Any, overlay: ta.Any) -> ta.Any:
    return base if overlay is None else overlay


def _resolve_color(value: StyleColor | None, inherited: Color | None) -> Color | None:
    if value is None:
        return inherited
    if value is DEFAULT_COLOR:
        return None
    return value


def _resolve_flag(value: bool | None, inherited: bool) -> bool:
    return inherited if value is None else value


@dc.dataclass(frozen=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class StylePatch(lang.Final):
    """
    A partial style layered over another style.

    `None` means inherit. Boolean `False` explicitly disables an inherited attribute, while `DEFAULT_COLOR` explicitly
    clears an inherited foreground or background color.
    """

    fg: StyleColor | None = None
    bg: StyleColor | None = None

    bold: bool | None = None
    dim: bool | None = None
    italic: bool | None = None
    underline: bool | None = None
    blink: bool | None = None
    reverse: bool | None = None
    strike: bool | None = None
    hidden: bool | None = None

    def __post_init__(self) -> None:
        _check_style_color(self.fg)
        _check_style_color(self.bg)
        for name in _STYLE_FLAG_NAMES:
            _check_style_flag(getattr(self, name))

    @property
    def is_empty(self) -> bool:
        return (
            self.fg is None and
            self.bg is None and
            all(getattr(self, name) is None for name in _STYLE_FLAG_NAMES)
        )

    def overlay(self, other: StylePatch) -> StylePatch:
        """Apply `other` over this patch, with its specified properties taking priority."""

        if not isinstance(other, StylePatch):
            raise TypeError(other)
        if other.is_empty:
            return self
        if self.is_empty:
            return other

        return StylePatch(
            fg=_overlay_value(self.fg, other.fg),
            bg=_overlay_value(self.bg, other.bg),
            bold=_overlay_value(self.bold, other.bold),
            dim=_overlay_value(self.dim, other.dim),
            italic=_overlay_value(self.italic, other.italic),
            underline=_overlay_value(self.underline, other.underline),
            blink=_overlay_value(self.blink, other.blink),
            reverse=_overlay_value(self.reverse, other.reverse),
            strike=_overlay_value(self.strike, other.strike),
            hidden=_overlay_value(self.hidden, other.hidden),
        )

    def resolve(self, base: ResolvedStyle | None = None) -> ResolvedStyle:
        """Resolve this patch over a concrete base style, or over the plain style when omitted."""

        if base is None:
            base = ResolvedStyle()
        elif not isinstance(base, ResolvedStyle):
            raise TypeError(base)

        return ResolvedStyle(
            fg=_resolve_color(self.fg, base.fg),
            bg=_resolve_color(self.bg, base.bg),
            bold=_resolve_flag(self.bold, base.bold),
            dim=_resolve_flag(self.dim, base.dim),
            italic=_resolve_flag(self.italic, base.italic),
            underline=_resolve_flag(self.underline, base.underline),
            blink=_resolve_flag(self.blink, base.blink),
            reverse=_resolve_flag(self.reverse, base.reverse),
            strike=_resolve_flag(self.strike, base.strike),
            hidden=_resolve_flag(self.hidden, base.hidden),
        )


EMPTY_STYLE_PATCH = StylePatch()


@dc.dataclass(frozen=True)
@dc.extra_class_params(default_repr_fn=lang.truthy_repr)
class ResolvedStyle(lang.Final):
    """A concrete target-neutral style with no inherited properties remaining."""

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

    def __post_init__(self) -> None:
        for color in (self.fg, self.bg):
            if color is not None and not isinstance(color, Color):
                raise TypeError(color)
        for name in _STYLE_FLAG_NAMES:
            if not isinstance(getattr(self, name), bool):
                raise TypeError(getattr(self, name))

    @property
    def is_plain(self) -> bool:
        return (
            self.fg is None and
            self.bg is None and
            not any(getattr(self, name) for name in _STYLE_FLAG_NAMES)
        )

    def apply(self, patch: StylePatch) -> ResolvedStyle:
        """Resolve `patch` over this style."""

        if not isinstance(patch, StylePatch):
            raise TypeError(patch)
        return patch.resolve(self)


PLAIN_STYLE = ResolvedStyle()


##


@dc.dataclass(frozen=True)
class StyleName(lang.Final):
    """A semantic name resolved to a style patch by an output target's theme."""

    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError(self.name)
        if not self.name or any(c.isspace() for c in self.name):
            raise ValueError(self.name)

    def __str__(self) -> str:
        return self.name


type StyleRef = StylePatch | StyleName
type StyleLike = StylePatch | StyleName | str
type StyleNameLike = StyleName | str


def as_style_ref(style: StyleLike) -> StyleRef:
    """Normalize an ergonomic style value to its canonical stored representation."""

    if isinstance(style, StylePatch):
        return style
    if isinstance(style, StyleName):
        return style
    if isinstance(style, str):
        return StyleName(style)
    raise TypeError(style)


def _style_name_string(name: StyleNameLike) -> str:
    if isinstance(name, StyleName):
        return name.name
    if isinstance(name, str):
        return StyleName(name).name
    raise TypeError(name)


class StyleTheme(lang.Final):
    """An immutable-by-interface mapping from semantic names to style patches."""

    def __init__(
            self,
            styles: ta.Mapping[ta.Any, StylePatch] | None = None,
    ) -> None:
        super().__init__()

        normalized: dict[str, StylePatch] = {}
        for name, style in (styles or {}).items():
            if not isinstance(style, StylePatch):
                raise TypeError(style)
            normalized[_style_name_string(name)] = style
        self._styles = normalized

    def __len__(self) -> int:
        return len(self._styles)

    def __contains__(self, name: object) -> bool:
        if isinstance(name, StyleName):
            return name.name in self._styles
        if isinstance(name, str):
            return name in self._styles
        return False

    def as_dict(self) -> dict[str, StylePatch]:
        """Return a copy of the theme mapping."""

        return dict(self._styles)

    def resolve(self, style: StyleRef) -> StylePatch:
        """Resolve a direct patch or semantic name; unknown names deliberately resolve to an empty patch."""

        if isinstance(style, StylePatch):
            return style
        if isinstance(style, StyleName):
            return self._styles.get(style.name, EMPTY_STYLE_PATCH)
        raise TypeError(style)

    def resolve_refs(
            self,
            styles: ta.Iterable[StyleRef],
            base: ResolvedStyle | None = None,
    ) -> ResolvedStyle:
        """Compose ordered style references and resolve them over a concrete base style."""

        patch = EMPTY_STYLE_PATCH
        for style in styles:
            patch = patch.overlay(self.resolve(style))
        return patch.resolve(base)

    def extend(self, styles: ta.Mapping[ta.Any, StylePatch]) -> StyleTheme:
        """Return a theme with `styles` replacing entries from this theme."""

        merged = self.as_dict()
        for name, style in styles.items():
            merged[_style_name_string(name)] = style
        return StyleTheme(merged)


EMPTY_STYLE_THEME = StyleTheme()
