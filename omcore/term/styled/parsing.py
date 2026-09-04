"""
SGR escape parsing: pre-styled ANSI text (subprocess output, etc.) back into styled text.

Non-SGR escape sequences are dropped. The parsed styles are concrete, so they are recorded as complete style patches:
a styled run reproduces exactly the style the terminal would have shown, over any base. Runs the escapes leave plain
carry no style at all and so inherit whatever base the text is later placed under, as they would have taken the
terminal's own defaults.
"""
import re
import typing as ta

from ... import dataclasses as dc
from ...text import styled as st
from .. import codes
from .colors import IndexedColor
from .colors import NamedColor
from .sgr import ATTR_PARAMS


##


ANSI_ESCAPE_PAT = re.compile(r'\x1b\[[0-?]*[ -/]*[@-~]')


def strip_ansi_escapes(text: str) -> str:
    """Remove every CSI escape sequence, SGR or otherwise."""

    return ANSI_ESCAPE_PAT.sub('', text)


##


_SGR_NAMED_ATTRS: ta.Mapping[int, str] = {param: attr for attr, param in ATTR_PARAMS}

_SGR_ATTR_RESETS: ta.Mapping[int, ta.Sequence[str]] = {
    codes.SGRs.AttrOff.NORMAL_INTENSITY.value: ('bold', 'dim'),
    codes.SGRs.AttrOff.ITALIC.value: ('italic',),
    codes.SGRs.AttrOff.UNDERLINE.value: ('underline',),
    codes.SGRs.AttrOff.BLINK.value: ('blink',),
    codes.SGRs.AttrOff.REVERSE.value: ('reverse',),
    codes.SGRs.AttrOff.CONCEAL.value: ('hidden',),
    codes.SGRs.AttrOff.STRIKE.value: ('strike',),
}

_FG = codes.SGRs.Fg
_BG = codes.SGRs.Bg


def _parse_extended_color(params: ta.Sequence[int], i: int) -> tuple[st.Color | None, int]:
    """Parse a 38/48-prefixed color starting at params[i] ('5;n' or '2;r;g;b'); returns (color, params consumed)."""

    if i < len(params) and params[i] == codes.SGRs.EXTENDED_INDEXED and i + 1 < len(params):
        index = params[i + 1]
        if 0 <= index <= 255:
            return IndexedColor(index), 2
        return None, 2
    if i < len(params) and params[i] == codes.SGRs.EXTENDED_RGB and i + 3 < len(params):
        r, g, b = params[i + 1: i + 4]
        if all(0 <= c <= 255 for c in (r, g, b)):
            return st.RgbColor(r, g, b), 4
        return None, 4
    return None, len(params) - i


def apply_sgr_params(style: st.ResolvedStyle, params: ta.Sequence[int]) -> st.ResolvedStyle:
    """The style after applying one SGR escape's parameters to `style`; an empty parameter list resets."""

    if not params:
        return st.PLAIN_STYLE

    changes: dict[str, ta.Any] = {}
    i = 0
    while i < len(params):
        p = params[i]
        i += 1
        if p == codes.SGRs.RESET:
            style = st.PLAIN_STYLE
            changes = {}
        elif p in _SGR_NAMED_ATTRS:
            changes[_SGR_NAMED_ATTRS[p]] = True
        elif p in _SGR_ATTR_RESETS:
            for attr in _SGR_ATTR_RESETS[p]:
                changes[attr] = False
        elif _FG.BLACK.value <= p <= _FG.WHITE.value:
            changes['fg'] = NamedColor(p - _FG.BLACK.value)
        elif _FG.BRIGHT_BLACK.value <= p <= _FG.BRIGHT_WHITE.value:
            changes['fg'] = NamedColor(p - _FG.BRIGHT_BLACK.value + 8)
        elif p == _FG.DEFAULT.value:
            changes['fg'] = None
        elif _BG.BLACK.value <= p <= _BG.WHITE.value:
            changes['bg'] = NamedColor(p - _BG.BLACK.value)
        elif _BG.BRIGHT_BLACK.value <= p <= _BG.BRIGHT_WHITE.value:
            changes['bg'] = NamedColor(p - _BG.BRIGHT_BLACK.value + 8)
        elif p == _BG.DEFAULT.value:
            changes['bg'] = None
        elif p in (_FG.EXTENDED.value, _BG.EXTENDED.value):
            color, consumed = _parse_extended_color(params, i)
            i += consumed
            if color is not None:
                changes['fg' if p == _FG.EXTENDED.value else 'bg'] = color
        # Unknown parameters are ignored.

    if not changes:
        return style
    return dc.replace(style, **changes)


def _parse_sgr_escape(escape: str, style: st.ResolvedStyle) -> st.ResolvedStyle:
    body = escape[2:-1]
    if not body:
        return st.PLAIN_STYLE
    params: list[int] = []
    for part in body.replace(':', ';').split(';'):
        if part.isdigit():
            params.append(int(part))
        elif not part:
            params.append(0)
        else:
            return style  # private-mode or otherwise non-SGR-shaped; ignore
    return apply_sgr_params(style, params)


def parse_ansi_text(text: str) -> st.StyledText:
    """
    Parse text carrying SGR escapes into styled text whose styled runs carry complete patches of the concrete styles
    seen and whose plain runs carry no style.

    Non-SGR escape sequences are dropped; newlines and other characters pass through as text.
    """

    builder = st.StyledTextBuilder()
    style = st.PLAIN_STYLE
    pos = 0
    for match in ANSI_ESCAPE_PAT.finditer(text):
        if (chunk := text[pos: match.start()]):
            builder.append(chunk, None if style.is_plain else style.to_patch())
        escape = match.group(0)
        if escape.endswith('m'):
            style = _parse_sgr_escape(escape, style)
        pos = match.end()
    if (chunk := text[pos:]):
        builder.append(chunk, None if style.is_plain else style.to_patch())
    return builder.build()
