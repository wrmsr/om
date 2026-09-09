"""
The structured key model.

A `Key` is a frozen dataclass - base name plus modifier flags - never a raw escape string. Keymap declarations may be
written as specs like 'ctrl+alt+x' for convenience, but they parse to `Key` values immediately; nothing downstream
matches on strings.

Conventions:
 - Printable characters are their own base ('a', 'A', '?', ...) and never carry `shift` - the shift is already in the
   character. `shift` appears only on special keys (shift+tab, shift+up, ...).
 - Space is the named base 'space' (a bare ' ' is illegible in specs); its KeyEvent still carries text ' '.
 - Control characters normalize to ctrl+letter ('ctrl+a'), except the universally-named ones: tab, enter, escape,
   backspace.
"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang


##


@dc.dataclass(frozen=True)
class Key(lang.Final):
    base: str

    _: dc.KW_ONLY

    ctrl: bool = False
    alt: bool = False
    shift: bool = False
    super_: bool = False

    def __post_init__(self) -> None:
        check.non_empty_str(self.base)

    @property
    def spec(self) -> str:
        parts: list[str] = []
        if self.ctrl:
            parts.append('ctrl')
        if self.alt:
            parts.append('alt')
        if self.shift:
            parts.append('shift')
        if self.super_:
            parts.append('super')
        parts.append(self.base)
        return '+'.join(parts)

    def __str__(self) -> str:
        return self.spec


class KeySpecError(Exception):
    pass


_MODIFIER_NAMES: ta.Mapping[str, str] = {
    'ctrl': 'ctrl',
    'control': 'ctrl',
    'alt': 'alt',
    'meta': 'alt',
    'shift': 'shift',
    'super': 'super_',
    'cmd': 'super_',
}


def parse_key(spec: str) -> Key:
    """Parse a 'ctrl+alt+x' style spec. The base is everything after the last '+' ('ctrl++' means ctrl-plus)."""

    if not spec:
        raise KeySpecError(spec)

    parts = spec.split('+')
    if parts[-1] == '' and len(parts) >= 2 and parts[-2] == '':
        # A trailing '++' means the base is the '+' character itself.
        parts = [*parts[:-2], '+']

    base = parts[-1]
    if not base:
        raise KeySpecError(spec)

    mods: dict[str, bool] = {}
    for part in parts[:-1]:
        if (name := _MODIFIER_NAMES.get(part.lower())) is None:
            raise KeySpecError(spec)
        mods[name] = True

    if base == ' ':
        base = 'space'
    return Key(base, **mods)


##


# The base names of keys that exist as ascii control characters, indexed by code point.
_CONTROL_CHAR_BASES: ta.Mapping[int, str] = {
    0x00: 'space',  # ^@ - ctrl+space in practice
    0x09: 'tab',
    0x0d: 'enter',
    0x1b: 'escape',
    0x1c: '\\',
    0x1d: ']',
    0x1e: '^',
    0x1f: '_',
    0x7f: 'backspace',
}

# Codes whose names above are already the full story (no implied ctrl).
_PLAIN_CONTROL_CODES: ta.AbstractSet[int] = frozenset([0x09, 0x0d, 0x1b, 0x7f])


def key_from_char(c: str, *, alt: bool = False) -> Key:
    """The Key for a single input character - printable or ascii control."""

    code = ord(c)
    if (base := _CONTROL_CHAR_BASES.get(code)) is not None:
        return Key(base, ctrl=code not in _PLAIN_CONTROL_CODES, alt=alt)
    if 0x01 <= code <= 0x1a:
        return Key(chr(code + 0x60), ctrl=True, alt=alt)
    if c == ' ':
        return Key('space', alt=alt)
    return Key(c, alt=alt)


def key_text(key: Key) -> str | None:
    """The insertable text for a key, or None if it isn't a plain printable."""

    if key.ctrl or key.alt or key.super_:
        return None
    if key.base == 'space':
        return ' '
    if len(key.base) == 1 and key.base.isprintable():
        return key.base
    return None
