"""
Replacement templates as `re.sub` and `Match.expand` read them: literal text, group references as `\\1` and `\\g<name>`,
and a handful of character escapes. PCRE2 has replacement templates of its own, and they are not these.
"""
import re
import typing as ta

from .... import dataclasses as dc


##


@dc.dataclass(frozen=True)
class Template:
    # Literal text - str whichever kind the template was, each byte of a bytes one a character - and group numbers.
    parts: ta.Sequence[str | int]

    @property
    def is_literal(self) -> bool:
        return all(isinstance(part, str) for part in self.parts)


#


_OCTAL_DIGITS = frozenset('01234567')
_DIGITS = frozenset('0123456789')
_ASCII_LETTERS = frozenset('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')

_CHARACTER_ESCAPES: ta.Mapping[str, str] = {
    'a': '\a',
    'b': '\b',
    'f': '\f',
    'n': '\n',
    'r': '\r',
    't': '\t',
    'v': '\v',
    '\\': '\\',
}


def parse_template(
        template: str | bytes,
        *,
        num_groups: int,
        group_index: ta.Mapping[str, int],
) -> Template:
    """Parses a template, which if it is bytes is read with each byte a character."""

    if isinstance(template, bytes):
        template = template.decode('latin-1')

    parts: list[str | int] = []
    literal: list[str] = []

    def error(msg: str, pos: int) -> re.PatternError:
        return re.PatternError(msg, template, pos)

    def add_group(group: int, pos: int) -> None:
        if group > num_groups:
            raise error(f'invalid group reference {group}', pos)
        if literal:
            parts.append(''.join(literal))
            literal.clear()
        parts.append(group)

    pos = 0
    n = len(template)
    while pos < n:
        c = template[pos]
        if c != '\\':
            literal.append(c)
            pos += 1
            continue

        start = pos
        if pos + 1 >= n:
            raise error('bad escape (end of pattern)', start)
        c = template[pos + 1]
        pos += 2

        if c == 'g':
            if not template.startswith('<', pos):
                raise error('missing <', pos)
            end = template.find('>', pos)
            if end < 0:
                raise error('missing >, unterminated name', pos + 1)
            name = template[pos + 1:end]
            if not name:
                raise error('missing group name', pos + 1)

            if name.isascii() and name.isdigit():
                add_group(int(name), pos + 1)
            elif not name.isidentifier():
                raise error(f'bad character in group name {name!r}', pos + 1)
            else:
                try:
                    group = group_index[name]
                except KeyError:
                    raise IndexError(f'unknown group name {name!r}') from None
                add_group(group, pos + 1)
            pos = end + 1

        elif c == '0':
            # Always an octal escape, of up to three digits.
            end = pos
            while end < n and end < pos + 2 and template[end] in _OCTAL_DIGITS:
                end += 1
            literal.append(chr(int(template[pos - 1:end], 8) & 0xFF))
            pos = end

        elif c in _DIGITS:
            # A group reference of one or two digits - unless it is three octal digits, which is a character.
            if pos < n and template[pos] in _DIGITS:
                if (
                        c in _OCTAL_DIGITS and
                        template[pos] in _OCTAL_DIGITS and
                        pos + 1 < n and
                        template[pos + 1] in _OCTAL_DIGITS
                ):
                    value = int(template[pos - 1:pos + 2], 8)
                    if value > 0o377:
                        raise error(
                            f'octal escape value {template[start:pos + 2]} outside of range 0-0o377',
                            start,
                        )
                    literal.append(chr(value))
                    pos += 2
                else:
                    add_group(int(template[pos - 1:pos + 1]), start + 1)
                    pos += 1
            else:
                add_group(int(c), start + 1)

        elif c in _CHARACTER_ESCAPES:
            literal.append(_CHARACTER_ESCAPES[c])

        elif c in _ASCII_LETTERS:
            raise error(f'bad escape \\{c}', start)

        else:
            # Any other escape is kept exactly as it was written, backslash and all.
            literal.append(template[start:pos])

    if literal:
        parts.append(''.join(literal))
    return Template(parts)


def expand_template(
        template: Template,
        get_group: ta.Callable[[int], ta.Any],
        *,
        is_str: bool,
) -> ta.Any:
    """Fills a template in. A group which took no part in the match is replaced by nothing, as it is in `re`."""

    pieces: list[ta.Any] = []
    for part in template.parts:
        if isinstance(part, int):
            if (value := get_group(part)) is not None:
                pieces.append(value)
        else:
            pieces.append(part if is_str else part.encode('latin-1'))

    return ('' if is_str else b'').join(pieces)
