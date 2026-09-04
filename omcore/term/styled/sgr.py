"""
SGR ('select graphic rendition') escape emission.

Emission is always full-reset-plus-rebuild (`\\x1b[0;...m`) - given transition elision by the caller (only emit when the
effective style actually changes) this is both correct and cheap, and avoids the whole class of incremental-SGR state
bugs.
"""
import typing as ta

from ...text import styled as st
from .. import codes
from .colors import ColorDepth
from .colors import IndexedColor
from .colors import NamedColor
from .colors import downgrade_color


##


def _color_params(color: st.Color, *, bg: bool) -> ta.Iterator[int]:
    plane: ta.Any = codes.SGRs.Bg if bg else codes.SGRs.Fg
    if isinstance(color, NamedColor):
        if color.index < 8:
            yield plane.BLACK.value + color.index
        else:
            yield plane.BRIGHT_BLACK.value + (color.index - 8)
    elif isinstance(color, IndexedColor):
        yield from (plane.EXTENDED.value, codes.SGRs.EXTENDED_INDEXED, color.index)
    elif isinstance(color, st.RgbColor):
        yield from (plane.EXTENDED.value, codes.SGRs.EXTENDED_RGB, color.r, color.g, color.b)
    else:
        raise TypeError(color)


ATTR_PARAMS: ta.Sequence[tuple[str, int]] = (
    ('bold', codes.SGRs.Attr.BOLD.value),
    ('dim', codes.SGRs.Attr.DIM.value),
    ('italic', codes.SGRs.Attr.ITALIC.value),
    ('underline', codes.SGRs.Attr.UNDERLINE.value),
    ('blink', codes.SGRs.Attr.SLOW_BLINK.value),
    ('reverse', codes.SGRs.Attr.REVERSE.value),
    ('hidden', codes.SGRs.Attr.CONCEAL.value),
    ('strike', codes.SGRs.Attr.STRIKE.value),
)


def style_sgr_params(style: st.ResolvedStyle, depth: ColorDepth = ColorDepth.TRUE) -> list[int]:
    params: list[int] = []
    for attr, param in ATTR_PARAMS:
        if getattr(style, attr):
            params.append(param)
    if style.fg is not None and (fg := downgrade_color(style.fg, depth)) is not None:
        params.extend(_color_params(fg, bg=False))
    if style.bg is not None and (bg := downgrade_color(style.bg, depth)) is not None:
        params.extend(_color_params(bg, bg=True))
    return params


RESET_SGR = codes.SGR(codes.SGRs.RESET)


def style_sgr(style: st.ResolvedStyle, depth: ColorDepth = ColorDepth.TRUE) -> str:
    """The full escape establishing `style` from any prior state ('' for the plain style)."""

    params = style_sgr_params(style, depth)
    if not params:
        return ''
    return codes.SGR(';'.join(map(str, (codes.SGRs.RESET, *params))))


def sgr_transition(old: st.ResolvedStyle, new: st.ResolvedStyle, depth: ColorDepth = ColorDepth.TRUE) -> str:
    """The escape string taking the terminal from `old` to `new` ('' if no change is needed)."""

    if old == new:
        return ''
    if (escape := style_sgr(new, depth)):
        return escape
    return RESET_SGR
