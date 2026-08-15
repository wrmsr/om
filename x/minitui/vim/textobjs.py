"""
Text objects: unlike motions they yield a Span directly - there is no "start position + direction", just "the thing
under the cursor". (Adapted from x/vibes/minivim.)
"""
import typing as ta

from omcore import check

from ..docs.documents import Document
from ..docs.positions import Kind
from ..docs.positions import Pos
from ..docs.positions import Span
from .scans import advance
from .scans import char_at
from .scans import char_class
from .scans import first_nonblank
from .scans import llen
from .scans import retreat


##


PAIRS: ta.Mapping[str, str] = {
    '(': '()',
    ')': '()',
    'b': '()',
    '{': '{}',
    '}': '{}',
    'B': '{}',
    '[': '[]',
    ']': '[]',
    '<': '<>',
    '>': '<>',
}

QUOTES: ta.AbstractSet[str] = frozenset(('"', "'", '`'))

TEXTOBJ_KEYS: ta.AbstractSet[str] = frozenset('wW') | set(PAIRS) | QUOTES


def _obj_word(doc: Document, p: Pos, *, around: bool, big: bool, count: int) -> Span | None:
    line = doc.line(p.row)
    if not line:
        return None

    col = min(p.col, len(line) - 1)

    def run(c: int) -> tuple[int, int]:
        """(start, end_exclusive) of the class run containing col c."""

        k = char_class(line[c], big)
        a = c
        while a > 0 and char_class(line[a - 1], big) == k:
            a -= 1
        b = c + 1
        while b < len(line) and char_class(line[b], big) == k:
            b += 1
        return a, b

    a, b = run(col)

    if around:
        # word + trailing blanks (or leading blanks if none trail) - per word
        for _ in range(count):
            if b < len(line) and char_class(line[b], big) == 0:
                _, b = run(b)
            elif count == 1 and a > 0 and char_class(line[a - 1], big) == 0:
                a, _ = run(a - 1)
            if count > 1 and b < len(line):  # extend over next word too
                _, b = run(b)

    else:
        for _ in range(count - 1):  # 2iw = word + space = 2 runs
            if b < len(line):
                _, b = run(b)

    return Span(Kind.EXCLUSIVE, Pos(p.row, a), Pos(p.row, b))


def _obj_pair(doc: Document, p: Pos, *, around: bool, open_ch: str, close_ch: str) -> Span | None:
    # Backward for the unmatched open (cursor sitting ON open matches itself), forward for the unmatched close.
    # Multi-line.
    q: Pos | None
    depth, q, open_pos = 0, p, None
    while q is not None:
        ch = char_at(doc, q)
        if ch == close_ch and q != p:
            depth += 1
        elif ch == open_ch:
            if depth == 0:
                open_pos = q
                break
            depth -= 1
        q = retreat(doc, q)

    if open_pos is None:
        return None

    depth, q, close_pos = 0, p, None
    while q is not None:
        ch = char_at(doc, q)
        if ch == open_ch and q != p and q != open_pos:
            depth += 1
        elif (ch == close_ch and q != p) or (ch == close_ch and q == p and p != open_pos):
            if depth == 0:
                close_pos = q
                break
            depth -= 1
        q = advance(doc, q)

    if close_pos is None:
        return None

    if around:
        end = advance(doc, close_pos) or Pos(close_pos.row, close_pos.col + 1)
        return Span(Kind.EXCLUSIVE, open_pos, end)

    # vim promotes the *inner* object to linewise when the open bracket ends its line and only whitespace precedes
    # the close bracket on its line - this is why `di{` on a code block keeps the braces on their own lines.
    if (
            open_pos.col == llen(doc, open_pos.row) - 1 and
            close_pos.col <= first_nonblank(doc, close_pos.row) and
            close_pos.row > open_pos.row + 1
    ):
        return Span(Kind.LINEWISE, Pos(open_pos.row + 1, 0), Pos(close_pos.row - 1, 0))

    inner = check.not_none(advance(doc, open_pos))
    return Span(Kind.EXCLUSIVE, inner, close_pos)


def _obj_quote(doc: Document, p: Pos, *, around: bool, q: str) -> Span | None:
    # Current line only, like vim. Pair quotes left-to-right; take the pair containing the cursor, else the next pair
    # to the right.
    line = doc.line(p.row)
    idx = [i for i, ch in enumerate(line) if ch == q]
    pairs = list(zip(idx[0::2], idx[1::2]))
    chosen = (
        next((ab for ab in pairs if ab[0] <= p.col <= ab[1]), None) or
        next((ab for ab in pairs if ab[0] > p.col), None)
    )
    if not chosen:
        return None
    a, b = chosen

    if around:  # (vim also swallows trailing whitespace here; omitted)
        return Span(Kind.EXCLUSIVE, Pos(p.row, a), Pos(p.row, b + 1))

    return Span(Kind.EXCLUSIVE, Pos(p.row, a + 1), Pos(p.row, b))


def textobj(doc: Document, p: Pos, *, around: bool, obj: str, count: int) -> Span | None:
    if obj in 'wW':
        return _obj_word(doc, p, around=around, big=obj == 'W', count=count)
    if obj in PAIRS:
        pair = PAIRS[obj]
        return _obj_pair(doc, p, around=around, open_ch=pair[0], close_ch=pair[1])
    if obj in QUOTES:
        return _obj_quote(doc, p, around=around, q=obj)
    return None
