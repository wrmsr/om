"""
Rewrites a pattern written for the standard library's `re` into one PCRE2 reads the same way.

The two dialects agree on nearly everything, so this is a single pass which copies a pattern through and steps in only
where they part: escapes PCRE2 does not have or gives another meaning, the character classes whose Unicode membership
differs, the flag letters PCRE2 does not know, and a `[` inside a class, which PCRE2 would take as the start of a POSIX
one. On the way it notes where each capturing group closes, which is what `Match.lastindex` is worked out from.
"""
import re
import typing as ta
import unicodedata

from .... import dataclasses as dc


##


@dc.dataclass(frozen=True)
class TranslatedPattern:
    pattern: str

    # For each capturing group, by its number less one, where among all of them its closing parenthesis comes.
    group_close_ranks: ta.Sequence[int]

    # The flags the pattern turns on for the whole of itself, which `re` reports and PCRE2 does not.
    inline_flags: int = 0


#


# What `\s` and `\w` match for a str pattern in `re`, which is not quite what they match in PCRE2: `re` counts the four
# information separators as whitespace and PCRE2 does not, PCRE2 counts U+180E as whitespace and `re` does not, and
# PCRE2 counts marks and connector punctuation as word characters where `re` only counts letters, numbers, and the
# underscore. So for such a pattern each is written out as the class `re` means by it.
_UNICODE_CLASS_ITEMS: ta.Mapping[str, str] = {
    's': r'\x09-\x0d\x1c-\x20\x{85}\x{a0}\x{1680}\x{2000}-\x{200a}\x{2028}\x{2029}\x{202f}\x{205f}\x{3000}',
    'w': r'\p{L}\p{N}_',
}

# A word boundary is wherever a word character meets something which is not one, so it has to mean the same characters
# as `\w` does: spelled out, it is a word character behind and none ahead, or none behind and one ahead.
_UNICODE_WORD = f'[{_UNICODE_CLASS_ITEMS["w"]}]'
_UNICODE_BOUNDARIES: ta.Mapping[str, str] = {
    'b': f'(?:(?<={_UNICODE_WORD})(?!{_UNICODE_WORD})|(?<!{_UNICODE_WORD})(?={_UNICODE_WORD}))',
    'B': f'(?:(?<={_UNICODE_WORD})(?={_UNICODE_WORD})|(?<!{_UNICODE_WORD})(?!{_UNICODE_WORD}))',
}

_HEX_ESCAPE_LENGTHS: ta.Mapping[str, int] = {
    'u': 4,
    'U': 8,
}

_FLAG_LETTERS = frozenset('aiLmsux')

_FLAGS_BY_LETTER: ta.Mapping[str, int] = {
    'a': re.ASCII,
    'i': re.IGNORECASE,
    'm': re.MULTILINE,
    's': re.DOTALL,
    'u': re.UNICODE,
    'x': re.VERBOSE,
}

_INLINE_ASCII_PAT = re.compile(r'\(\?[a-zA-Z]*a')


class _Translator:
    def __init__(
            self,
            pattern: str,
            *,
            is_str: bool,
            unicode_classes: bool = False,
            verbose: bool = False,
    ) -> None:
        super().__init__()

        self._pattern = pattern
        self._is_str = is_str
        # An inline flag can turn ASCII matching on for part of a pattern, which rewritten classes would not follow.
        self._unicode_classes = unicode_classes and _INLINE_ASCII_PAT.search(pattern) is None
        self._verbose = verbose

        self._pos = 0
        self._out: list[str] = []

        self._num_groups = 0
        self._open_groups: list[int | None] = []
        self._group_close_ranks: dict[int, int] = {}
        self._inline_flags = 0

    def _error(self, msg: str, pos: int) -> re.PatternError:
        return re.PatternError(msg, self._pattern, pos)

    #

    def _translate_escape(self, *, in_class: bool) -> None:
        p = self._pattern
        start = self._pos
        if start + 1 >= len(p):
            # Left as it is for PCRE2 to refuse.
            self._out.append(p[start:])
            self._pos = len(p)
            return

        c = p[start + 1]
        self._pos = start + 2

        if c == 'Z' and not in_class:
            # The end of the subject and nowhere else, which PCRE2 spells with the other case.
            self._out.append(r'\z')

        elif c == 'v':
            # A vertical tab, where PCRE2's is any vertical whitespace.
            self._out.append(r'\x0b')

        elif c in _HEX_ESCAPE_LENGTHS and self._is_str:
            end = self._pos + _HEX_ESCAPE_LENGTHS[c]
            digits = p[self._pos:end]
            if len(digits) != end - self._pos or not all(d in '0123456789abcdefABCDEF' for d in digits):
                raise self._error(f'incomplete escape {p[start:end]}', start)
            self._out.append(rf'\x{{{digits}}}')
            self._pos = end

        elif c == 'N' and self._is_str and p.startswith('{', self._pos):
            end = p.find('}', self._pos)
            if end < 0:
                raise self._error('missing }, unterminated name', self._pos)
            name = p[self._pos + 1:end]
            try:
                char = unicodedata.lookup(name)
            except KeyError:
                raise self._error(f'undefined character name {name!r}', start) from None
            self._out.append(rf'\x{{{ord(char):x}}}')
            self._pos = end + 1

        elif c in _UNICODE_BOUNDARIES and self._unicode_classes and not in_class:
            self._out.append(_UNICODE_BOUNDARIES[c])

        elif c in _UNICODE_CLASS_ITEMS and self._unicode_classes:
            items = _UNICODE_CLASS_ITEMS[c]
            self._out.append(items if in_class else f'[{items}]')

        elif c.lower() in _UNICODE_CLASS_ITEMS and self._unicode_classes and not in_class:
            # A negated class has no spelling as items of another, so within one it is left as PCRE2 has it.
            self._out.append(f'[^{_UNICODE_CLASS_ITEMS[c.lower()]}]')

        else:
            self._out.append(p[start:self._pos])

    def _translate_class(self) -> None:
        p = self._pattern
        start = self._pos
        self._out.append('[')
        self._pos += 1

        if p.startswith('^', self._pos):
            self._out.append('^')
            self._pos += 1

        # A `]` which comes first is a member of the class and not its end.
        if p.startswith(']', self._pos):
            self._out.append(']')
            self._pos += 1

        while self._pos < len(p):
            c = p[self._pos]
            if c == ']':
                self._out.append(']')
                self._pos += 1
                return
            elif c == '\\':
                self._translate_escape(in_class=True)
            elif c == '[':
                # Only ever itself in `re`, where to PCRE2 it can open a POSIX class.
                self._out.append(r'\[')
                self._pos += 1
            else:
                self._out.append(c)
                self._pos += 1

        raise self._error('unterminated character set', start)

    def _translate_flags(self, end: int) -> None:
        # `(?flags)` or `(?flags:` - with the letters `re` has and PCRE2 does not taken out.
        p = self._pattern
        start = self._pos
        letters = p[start + 2:end]

        if 'L' in letters:
            raise self._error('bad inline flags: the LOCALE flag is not supported', start)
        if 'u' in letters and not self._is_str:
            raise self._error("bad inline flags: cannot use 'u' flag with a bytes pattern", start)
        if 'a' in letters and 'u' in letters:
            raise self._error("bad inline flags: flags 'a', 'u' and 'L' are incompatible", start)

        closer = p[end]
        if closer == ')':
            for letter in letters.partition('-')[0]:
                self._inline_flags |= _FLAGS_BY_LETTER[letter]

        letters = letters.replace('u', '')
        if closer == ':':
            self._open_groups.append(None)
            self._out.append(f'(?{letters}:')
        elif letters.strip('-'):
            self._out.append(f'(?{letters})')
        self._pos = end + 1

    def _translate_open(self) -> None:
        p = self._pattern
        start = self._pos

        if not p.startswith('?', start + 1):
            if p.startswith('*', start + 1):
                # One of PCRE2's verbs, which is not a group but does close like one.
                self._open_groups.append(None)
                self._out.append('(')
                self._pos += 1
                return

            self._num_groups += 1
            self._open_groups.append(self._num_groups)
            self._out.append('(')
            self._pos += 1
            return

        if p.startswith('#', start + 2):
            end = p.find(')', start)
            if end < 0:
                raise self._error('missing ), unterminated comment', start)
            self._out.append(p[start:end + 1])
            self._pos = end + 1
            return

        if p.startswith('(', start + 2):
            # A conditional, whose condition is parenthesized but is not a group.
            end = p.find(')', start)
            if end < 0:
                raise self._error('missing ), unterminated name', start)
            self._open_groups.append(None)
            self._out.append(p[start:end + 1])
            self._pos = end + 1
            return

        if p.startswith('P<', start + 2) or (
                p.startswith('<', start + 2) and
                not p.startswith(('<=', '<!'), start + 2)
        ):
            self._num_groups += 1
            self._open_groups.append(self._num_groups)
            self._out.append('(?')
            self._pos += 2
            return

        end = start + 2
        while end < len(p) and (p[end] in _FLAG_LETTERS or p[end] == '-'):
            end += 1
        if end > start + 2 and end < len(p) and p[end] in ':)':
            self._translate_flags(end)
            return

        # Any other kind of group - non-capturing, a lookaround, a reference - is PCRE2's to read as it stands.
        if not p.startswith(('P=', 'P>'), start + 2):
            self._open_groups.append(None)
            self._out.append('(?')
            self._pos += 2
        else:
            end = p.find(')', start)
            if end < 0:
                raise self._error('missing ), unterminated name', start)
            self._out.append(p[start:end + 1])
            self._pos = end + 1

    def _translate_close(self) -> None:
        if self._open_groups:
            group = self._open_groups.pop()
            if group is not None:
                self._group_close_ranks[group] = len(self._group_close_ranks)
        self._out.append(')')
        self._pos += 1

    def translate(self) -> TranslatedPattern:
        p = self._pattern
        while self._pos < len(p):
            c = p[self._pos]
            if c == '\\':
                self._translate_escape(in_class=False)
            elif c == '[':
                self._translate_class()
            elif c == '(':
                self._translate_open()
            elif c == ')':
                self._translate_close()
            elif c == '#' and self._verbose:
                end = p.find('\n', self._pos)
                end = len(p) if end < 0 else end
                self._out.append(p[self._pos:end])
                self._pos = end
            else:
                self._out.append(c)
                self._pos += 1

        # A group left open is PCRE2's to report, but still has to be accounted for here.
        return TranslatedPattern(
            ''.join(self._out),
            [
                self._group_close_ranks.get(group, self._num_groups)
                for group in range(1, self._num_groups + 1)
            ],
            self._inline_flags,
        )


def translate_pattern(
        pattern: str,
        *,
        is_str: bool,
        unicode_classes: bool = False,
        verbose: bool = False,
) -> TranslatedPattern:
    """
    Translates a pattern, given as a str whether it is one or - each byte a character - bytes.

    Raises `re.PatternError` for what is wrong with a pattern in ways only this translation would notice. Everything
    else wrong with one is left for PCRE2 to find.
    """

    return _Translator(
        pattern,
        is_str=is_str,
        unicode_classes=unicode_classes,
        verbose=verbose,
    ).translate()
