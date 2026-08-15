"""
HTML entity reference scanner.

CommonMark §6.2: three entity forms,

  * named: `&name;`            (e.g. `&copy;`)
  * decimal: `&#NNNN;`         (e.g. `&#35;` → `#`)
  * hexadecimal: `&#xHHHH;` / `&#XHHHH;`

We delegate decoding to the stdlib's HTML5 named-entity table (`html.entities.html5`) - far larger and more current
than pulldown-cmark's generated 2125-row `entities.rs`. Lookups use the exact semicolon-terminated name: CommonMark
recognizes only `&name;` forms, never the legacy semicolon-less entities (`&copy` is plain text), and never partial
matches (`&notanentity;` must not decode its `&not` prefix - which is exactly what `html.unescape` would do, so it
must not be used here).
"""
import html.entities
import re

from .... import dataclasses as dc


##


# CM-spec entity shapes. Note: numeric forms must have 1..7 digits and must be followed by `;`.
_RE_NAMED = re.compile(r'&([A-Za-z][A-Za-z0-9]{0,31});')
_RE_DECIMAL = re.compile(r'&#([0-9]{1,7});')
_RE_HEX = re.compile(r'&#[xX]([0-9A-Fa-f]{1,6});')


@dc.dataclass(frozen=True)
class EntityMatch:
    end: int      # one past the closing `;`
    decoded: str  # the decoded character(s)


# pulldown-cmark/src/scanners.rs::scan_entity - same shape but we lean on the stdlib's HTML5 entity table.
def scan_entity(text: str, start: int) -> EntityMatch | None:
    if start >= len(text) or text[start] != '&':
        return None

    # Try each form in fixed precedence: hex (most specific), then decimal, then named.
    m = _RE_HEX.match(text, start)
    if m is not None:
        code = int(m.group(1), 16)
        if not _is_valid_codepoint(code):
            return EntityMatch(end=m.end(), decoded='�')
        return EntityMatch(end=m.end(), decoded=chr(code))

    m = _RE_DECIMAL.match(text, start)
    if m is not None:
        code = int(m.group(1))
        if not _is_valid_codepoint(code):
            return EntityMatch(end=m.end(), decoded='�')
        return EntityMatch(end=m.end(), decoded=chr(code))

    m = _RE_NAMED.match(text, start)
    if m is not None:
        # Exact lookup of the semicolon-terminated name only. (NOT `html.unescape`: it also resolves legacy
        # semicolon-less entities embedded as prefixes, turning `&notanentity;` into `\u00acanentity;`.)
        decoded = html.entities.html5.get(m.group(1) + ';')
        if decoded is None:
            return None
        return EntityMatch(end=m.end(), decoded=decoded)

    return None


def _is_valid_codepoint(code: int) -> bool:
    # Per CM §6.2: NUL is forbidden; values out of the Unicode range fall back to U+FFFD.
    if code == 0:
        return False
    if code > 0x10FFFF:
        return False
    # Surrogates are also invalid.
    if 0xD800 <= code <= 0xDFFF:
        return False
    return True
