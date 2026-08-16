"""
Ex-line built-ins: ranges, `:s[ubstitute]`, and line jumps - parsed and applied over the document layer.

Vim-flavored surface, python-regex heart (documented divergence: patterns are `re` syntax, not vim's dialect - no
magicness levels, use `(...)` not `\\(...\\)`). Supported:

    [range]s[ubstitute]<sep>pattern<sep>[replacement[<sep>[flags]]]

 - Ranges: `%`, `N`, `N,M` (1-based), `.`, `$`, `'<`/`'>` (the last visual selection), in any combination.
 - Separator: any punctuation character after the command name (`/`, `#`, `,`, ...), escapable inside parts.
 - Replacement conveniences: `&` = whole match (escape as `\\&`), `\\1`.. group refs, `\\r` inserts a line break.
 - Flags: `g` (every occurrence per line; default is first-per-line, like vim), `i` (ignore case).
 - Empty pattern reuses the last `/` search (escaped literally, since engine search is literal).

Also: a bare range (`:42`, `:$`, `:%`) jumps to its last line. Anything unrecognized falls through to the app's ex
handler untouched. Not (yet) here: the `c` confirm flag, `:g//`, counts, `~`/case sugar in replacements.
"""
import re

from omcore import dataclasses as dc
from omcore import lang

from ..docs.documents import Document
from ..docs.positions import Pos


##


class SubstituteError(Exception):
    """Carries the user-facing message for a failed substitute."""


@dc.dataclass(frozen=True)
class ExRange(lang.Final):
    start_row: int  # 0-based, inclusive
    end_row: int    # 0-based, inclusive


@dc.dataclass(frozen=True)
class SubstituteResult(lang.Final):
    replaced: int
    lines: int
    last_row: int

    @property
    def message(self) -> str:
        n, m = self.replaced, self.lines
        return f'{n} substitution{"s" if n != 1 else ""} on {m} line{"s" if m != 1 else ""}'


##
# Range parsing


_ADDRESS_PAT = re.compile(r"\d+|\.|\$|'<|'>")


def _parse_address(
        text: str,
        *,
        current_row: int,
        last_row: int,
        visual: tuple[int, int] | None,
) -> tuple[int | None, str]:
    if (m := _ADDRESS_PAT.match(text)) is None:
        return (None, text)
    tok = m.group(0)
    rest = text[m.end():]
    if tok.isdigit():
        return (min(max(int(tok) - 1, 0), last_row), rest)
    if tok == '.':
        return (current_row, rest)
    if tok == '$':
        return (last_row, rest)
    if visual is None:
        return (None, text)  # '< / '> with no prior visual selection
    return (visual[0] if tok == "'<" else visual[1], rest)


def parse_ex_range(
        text: str,
        *,
        current_row: int,
        last_row: int,
        visual: tuple[int, int] | None = None,
) -> tuple[ExRange | None, str]:
    """Parse an optional leading range, returning (range, remaining text)."""

    if text.startswith('%'):
        return (ExRange(0, last_row), text[1:])

    first, rest = _parse_address(text, current_row=current_row, last_row=last_row, visual=visual)
    if first is None:
        return (None, text)

    if rest.startswith(','):
        second, rest2 = _parse_address(rest[1:], current_row=current_row, last_row=last_row, visual=visual)
        if second is None:
            return (None, text)
        lo, hi = sorted((first, second))
        return (ExRange(lo, hi), rest2)

    return (ExRange(first, first), rest)


##
# Substitute parsing


_SUBSTITUTE_NAME_PAT = re.compile(r's(?:u(?:b(?:s(?:t(?:i(?:t(?:u(?:t(?:e)?)?)?)?)?)?)?)?)?')


@dc.dataclass(frozen=True)
class SubstituteSpec(lang.Final):
    pattern: str
    replacement: str
    every: bool = False       # the g flag
    ignore_case: bool = False  # the i flag


def _split_on_separator(text: str, sep: str) -> tuple[list[str], str]:
    """Split on unescaped separators (backslash escapes pass through); returns (parts, unused='')."""

    parts: list[str] = ['']
    i = 0
    while i < len(text):
        c = text[i]
        if c == '\\' and i + 1 < len(text):
            nxt = text[i + 1]
            if nxt == sep:
                parts[-1] += sep  # escaped separator becomes literal
            else:
                parts[-1] += c + nxt
            i += 2
            continue
        if c == sep:
            parts.append('')
        else:
            parts[-1] += c
        i += 1
    return (parts, '')


def parse_substitute(text: str) -> SubstituteSpec | None:
    """Parse `s<sep>pat<sep>repl<sep>flags` (after any range). None if this isn't a substitute command."""

    if (m := _SUBSTITUTE_NAME_PAT.match(text)) is None:
        return None
    rest = text[m.end():]
    if not rest or rest[0].isalnum() or rest[0] in ' \\"|':
        return None  # not a valid separator: not (our) substitute - let the app's ex handler see it
    sep = rest[0]

    parts, _ = _split_on_separator(rest[1:], sep)
    pattern = parts[0]
    replacement = parts[1] if len(parts) > 1 else ''
    flags = parts[2] if len(parts) > 2 else ''

    return SubstituteSpec(
        pattern=pattern,
        replacement=replacement,
        every='g' in flags,
        ignore_case='i' in flags,
    )


def _python_replacement(repl: str) -> str:
    """Translate vim replacement conventions to a python `re.sub` template."""

    out = ''
    i = 0
    while i < len(repl):
        c = repl[i]
        if c == '\\' and i + 1 < len(repl):
            nxt = repl[i + 1]
            if nxt == 'r':
                out += '\n'  # vim's \r: insert a line break
            elif nxt == '&':
                out += '&'   # literal ampersand
            elif nxt == 'n':
                out += ' '   # vim inserts NUL; a space is the least-bad line-model equivalent
            else:
                out += c + nxt  # group refs (\1, \g<..>), literal backslashes, etc. pass to re
            i += 2
            continue
        if c == '&':
            out += '\\g<0>'  # vim's &: the whole match
        else:
            out += c
        i += 1
    return out


##
# Application


def apply_substitute(
        doc: Document,
        rows: ExRange,
        spec: SubstituteSpec,
        *,
        last_search: str | None = None,
) -> SubstituteResult:
    """
    Apply a substitute over the row range, editing through the document (the caller owns the undo group).

    Raises SubstituteError with a user-facing message on bad patterns or no matches.
    """

    pattern = spec.pattern
    if not pattern:
        if not last_search:
            raise SubstituteError('No previous search pattern')
        pattern = re.escape(last_search)

    try:
        compiled = re.compile(pattern, re.IGNORECASE if spec.ignore_case else 0)
    except re.error as e:
        raise SubstituteError(f'Invalid pattern: {e}') from e

    template = _python_replacement(spec.replacement)

    replaced = 0
    lines_changed = 0
    last_changed = rows.start_row
    row_offset = 0  # replacements containing \r grow the document; later rows shift down

    for base_row in range(rows.start_row, rows.end_row + 1):
        row = base_row + row_offset
        if row >= doc.line_count():
            break
        line = doc.line(row)
        try:
            new_line, n = compiled.subn(template, line, count=0 if spec.every else 1)
        except re.error as e:
            raise SubstituteError(f'Invalid replacement: {e}') from e
        if not n:
            continue
        doc.replace(Pos(row, 0), Pos(row, len(line)), new_line)
        replaced += n
        lines_changed += 1
        last_changed = row
        row_offset += new_line.count('\n')

    if not replaced:
        raise SubstituteError(f'Pattern not found: {pattern}')

    return SubstituteResult(replaced=replaced, lines=lines_changed, last_row=last_changed)
