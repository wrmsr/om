"""
SGR ('select graphic rendition') escape emission and parsing.

Emission is always full-reset-plus-rebuild (`\\x1b[0;...m`) - given transition elision by the caller (only emit when
the effective style actually changes) this is both correct and cheap, and avoids the whole class of incremental-SGR
state bugs. Parsing ingests pre-styled ANSI text (subprocess output, etc.) back into structured segments; non-SGR
escape sequences are dropped.
"""
import re
import typing as ta

from omcore import dataclasses as dc

from .colors import Color
from .colors import ColorDepth
from .colors import IndexedColor
from .colors import NamedColor
from .colors import RgbColor
from .colors import downgrade_color
from .segments import Segment
from .styles import EMPTY_STYLE
from .styles import Style


##


def _color_params(color: Color, *, bg: bool) -> ta.Iterator[int]:
    base = 40 if bg else 30
    if isinstance(color, NamedColor):
        if color.index < 8:
            yield base + color.index
        else:
            yield base + 60 + (color.index - 8)
    elif isinstance(color, IndexedColor):
        yield from (base + 8, 5, color.index)
    elif isinstance(color, RgbColor):
        yield from (base + 8, 2, color.r, color.g, color.b)
    else:
        raise TypeError(color)


_ATTR_PARAMS: ta.Sequence[tuple[str, int]] = (
    ('bold', 1),
    ('dim', 2),
    ('italic', 3),
    ('underline', 4),
    ('blink', 5),
    ('reverse', 7),
    ('hidden', 8),
    ('strike', 9),
)


def style_sgr_params(style: Style, depth: ColorDepth = ColorDepth.TRUE) -> list[int]:
    params: list[int] = []
    for attr, param in _ATTR_PARAMS:
        if getattr(style, attr):
            params.append(param)
    if style.fg is not None and (fg := downgrade_color(style.fg, depth)) is not None:
        params.extend(_color_params(fg, bg=False))
    if style.bg is not None and (bg := downgrade_color(style.bg, depth)) is not None:
        params.extend(_color_params(bg, bg=True))
    return params


RESET_SGR = '\x1b[0m'


def style_sgr(style: Style, depth: ColorDepth = ColorDepth.TRUE) -> str:
    """The full escape establishing `style` from any prior state ('' for the empty style)."""

    params = style_sgr_params(style, depth)
    if not params:
        return ''
    return '\x1b[0;' + ';'.join(map(str, params)) + 'm'


def sgr_transition(old: Style, new: Style, depth: ColorDepth = ColorDepth.TRUE) -> str:
    """The escape string taking the terminal from `old` to `new` ('' if no change is needed)."""

    if old == new:
        return ''
    if (escape := style_sgr(new, depth)):
        return escape
    return RESET_SGR


##


ANSI_ESCAPE_PAT = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')

_SGR_NAMED_ATTRS: ta.Mapping[int, str] = {param: attr for attr, param in _ATTR_PARAMS}

_SGR_ATTR_RESETS: ta.Mapping[int, ta.Sequence[str]] = {
    22: ('bold', 'dim'),
    23: ('italic',),
    24: ('underline',),
    25: ('blink',),
    27: ('reverse',),
    28: ('hidden',),
    29: ('strike',),
}


def _parse_extended_color(params: ta.Sequence[int], i: int) -> tuple[Color | None, int]:
    """Parse a 38/48-prefixed color starting at params[i] ('5;n' or '2;r;g;b'); returns (color, params consumed)."""

    if i < len(params) and params[i] == 5 and i + 1 < len(params):
        index = params[i + 1]
        if 0 <= index <= 255:
            return IndexedColor(index), 2
        return None, 2
    if i < len(params) and params[i] == 2 and i + 3 < len(params):
        r, g, b = params[i + 1: i + 4]
        if all(0 <= c <= 255 for c in (r, g, b)):
            return RgbColor(r, g, b), 4
        return None, 4
    return None, len(params) - i


def apply_sgr_params(style: Style, params: ta.Sequence[int]) -> Style:
    if not params:
        return EMPTY_STYLE

    changes: dict[str, ta.Any] = {}
    i = 0
    while i < len(params):
        p = params[i]
        i += 1
        if p == 0:
            style = EMPTY_STYLE
            changes = {}
        elif p in _SGR_NAMED_ATTRS:
            changes[_SGR_NAMED_ATTRS[p]] = True
        elif p in _SGR_ATTR_RESETS:
            for attr in _SGR_ATTR_RESETS[p]:
                changes[attr] = False
        elif 30 <= p <= 37:
            changes['fg'] = NamedColor(p - 30)
        elif 90 <= p <= 97:
            changes['fg'] = NamedColor(p - 90 + 8)
        elif p == 39:
            changes['fg'] = None
        elif 40 <= p <= 47:
            changes['bg'] = NamedColor(p - 40)
        elif 100 <= p <= 107:
            changes['bg'] = NamedColor(p - 100 + 8)
        elif p == 49:
            changes['bg'] = None
        elif p in (38, 48):
            color, consumed = _parse_extended_color(params, i)
            i += consumed
            if color is not None:
                changes['fg' if p == 38 else 'bg'] = color
        # Unknown parameters are ignored.

    if not changes:
        return style
    return dc.replace(style, **changes)


def _parse_sgr_escape(escape: str, style: Style) -> Style:
    body = escape[2:-1]
    if not body:
        return EMPTY_STYLE
    params: list[int] = []
    for part in body.replace(':', ';').split(';'):
        if part.isdigit():
            params.append(int(part))
        elif not part:
            params.append(0)
        else:
            return style  # private-mode or otherwise non-SGR-shaped; ignore
    return apply_sgr_params(style, params)


def parse_ansi_segments(text: str) -> list[Segment]:
    """
    Parse text containing SGR escapes into styled segments.

    Non-SGR CSI sequences are dropped; the caller is responsible for newlines (segments reject them, so split first).
    """

    segments: list[Segment] = []
    style = EMPTY_STYLE
    pos = 0
    for match in ANSI_ESCAPE_PAT.finditer(text):
        if (chunk := text[pos: match.start()]):
            segments.append(Segment(chunk, style if not style.is_plain else None))
        escape = match.group(0)
        if escape.endswith('m'):
            style = _parse_sgr_escape(escape, style)
        pos = match.end()
    if (chunk := text[pos:]):
        segments.append(Segment(chunk, style if not style.is_plain else None))
    return segments
