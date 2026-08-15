"""
Fenced code block open / close scanners.

CommonMark §4.5. A code fence is three or more backticks or three or more tildes, optionally preceded by up to 3 spaces,
followed by an optional info string. A backtick fence's info string must not contain backticks.
"""
from .... import dataclasses as dc
from .entities import scan_entity
from .whitespace import is_ascii_punctuation
from .whitespace import scan_ch_repeat


##


@dc.dataclass(frozen=True)
class FenceOpen:
    fence_char: str    # '`' or '~'
    fence_length: int  # number of fence chars
    indent: int        # leading-space count (0..3)
    info: str          # info string after the fence; trimmed of surrounding whitespace
    # Position in the input line just past the EOL/end (caller uses to determine remainder).


# pulldown-cmark/src/scanners.rs::scan_code_fence
def scan_fence_open(line: str) -> FenceOpen | None:
    i = 0
    n = len(line)
    while i < n and line[i] == ' ' and i < 3:
        i += 1
    if i >= n:
        return None
    c = line[i]
    if c != '`' and c != '~':
        return None
    length = scan_ch_repeat(line, i, c)
    if length < 3:
        return None
    info_start = i + length
    # Take the rest of the line as info, trimming leading / trailing whitespace.
    raw_info = line[info_start:].strip()
    # Backtick fences may not contain a backtick in the info string.
    if c == '`' and '`' in raw_info:
        return None
    return FenceOpen(fence_char=c, fence_length=length, indent=i, info=_decode_info(raw_info))


def _decode_info(raw: str) -> str:
    """CM §4.5: backslash escapes and entity references are decoded in info strings."""

    if '\\' not in raw and '&' not in raw:
        return raw
    out: list[str] = []
    i = 0
    n = len(raw)
    while i < n:
        c = raw[i]
        if c == '\\' and i + 1 < n and is_ascii_punctuation(raw[i + 1]):
            out.append(raw[i + 1])
            i += 2
            continue
        if c == '&' and (em := scan_entity(raw, i)) is not None:
            out.append(em.decoded)
            i = em.end
            continue
        out.append(c)
        i += 1
    return ''.join(out)


# pulldown-cmark/src/scanners.rs::scan_closing_code_fence
def is_fence_close(line: str, fence_char: str, fence_length: int) -> bool:
    """
    Recognize a closing fence: optional up-to-3-space indent + at least `fence_length` of `fence_char` + optional
    trailing whitespace + EOL. No info string allowed.
    """

    i = 0
    n = len(line)
    while i < n and line[i] == ' ' and i < 3:
        i += 1
    count = scan_ch_repeat(line, i, fence_char)
    if count < fence_length:
        return False
    j = i + count
    while j < n and (line[j] == ' ' or line[j] == '\t'):
        j += 1
    return j == n
