"""
Scan space over a document: iterate as if lines ended in a virtual "newline slot" at col == len(line).

That slot is blank-class, which is exactly why word runs never merge across lines; an empty line is a single newline
slot. Includes vim's three character classes (blank / punctuation / word; "big" words collapse to two) and the word
and find-char motions built on them. (Adapted from x/vibes/minivim, retargeted from its Buffer protocol onto
docs.Document.)
"""
from ..docs.documents import Document
from ..docs.positions import Pos


##


def llen(doc: Document, row: int) -> int:
    return len(doc.line(row))


def char_at(doc: Document, p: Pos) -> str | None:
    line = doc.line(p.row)
    return line[p.col] if p.col < len(line) else None  # None == newline slot


def advance(doc: Document, p: Pos) -> Pos | None:
    if p.col < llen(doc, p.row):
        return Pos(p.row, p.col + 1)
    if p.row + 1 < doc.line_count():
        return Pos(p.row + 1, 0)
    return None


def retreat(doc: Document, p: Pos) -> Pos | None:
    if p.col > 0:
        return Pos(p.row, p.col - 1)
    if p.row > 0:
        return Pos(p.row - 1, llen(doc, p.row - 1))
    return None


def first_nonblank(doc: Document, row: int) -> int:
    line = doc.line(row)
    stripped = line.lstrip(' \t')
    return len(line) - len(stripped) if stripped else 0


def clamp_col(doc: Document, p: Pos) -> Pos:
    """Normal-mode cursor may not rest on the newline slot."""

    return Pos(p.row, min(p.col, max(0, llen(doc, p.row) - 1)))


##
# Word machinery. vim's three char classes: 0 blank, 1 punctuation, 2 word. For W/B/E ("big" words) every non-blank
# is one class.


def char_class(ch: str | None, big: bool) -> int:  # noqa
    if ch is None or ch in ' \t':
        return 0
    if big:
        return 2
    return 2 if (ch == '_' or ch.isalnum()) else 1


def word_fwd(doc: Document, p: Pos, count: int, big: bool) -> Pos:  # noqa
    """`w`/`W`: start of next word. An empty line counts as a word."""

    for _ in range(count):
        c0 = char_class(char_at(doc, p), big)
        q = p
        if c0 != 0:  # step off the current word run first
            while True:
                nq = advance(doc, q)
                if nq is None:
                    return q
                q = nq
                if char_class(char_at(doc, q), big) != c0:
                    break
        else:
            nq = advance(doc, q)
            if nq is None:
                return q
            q = nq
        while char_class(char_at(doc, q), big) == 0:  # skip blanks...
            if llen(doc, q.row) == 0:  # ...but an empty line is a word
                break
            nq = advance(doc, q)
            if nq is None:
                break
            q = nq
        p = q
    return p


def word_end(doc: Document, p: Pos, count: int, big: bool) -> Pos:  # noqa
    """`e`/`E`: end of word, inclusive. (Skips empty lines, as vim's e does.)"""

    for _ in range(count):
        q = p
        while True:  # move at least one, skip blanks
            nq = advance(doc, q)
            if nq is None:
                return q
            q = nq
            if char_class(char_at(doc, q), big) != 0:
                break
        c0 = char_class(char_at(doc, q), big)
        while True:  # run to end of this class run
            nq = advance(doc, q)
            if nq is None or char_class(char_at(doc, nq), big) != c0:
                break
            q = nq
        p = q
    return p


def word_back(doc: Document, p: Pos, count: int, big: bool) -> Pos:  # noqa
    """`b`/`B`: back to start of word. Empty line counts as a word."""

    for _ in range(count):
        q = retreat(doc, p)
        if q is None:
            return p
        while char_class(char_at(doc, q), big) == 0:
            if llen(doc, q.row) == 0:
                break
            nq = retreat(doc, q)
            if nq is None:
                return q
            q = nq
        if llen(doc, q.row) == 0:
            p = q
            continue
        c0 = char_class(char_at(doc, q), big)
        while True:
            nq = retreat(doc, q)
            if nq is None or char_class(char_at(doc, nq), big) != c0:
                break
            q = nq
        p = q
    return p


def find_char(
        doc: Document,
        p: Pos,
        ch: str,
        count: int,
        *,
        forward: bool,
        till: bool,
        repeat: bool = False,
) -> Pos | None:
    """
    `f t F T` (current line only, like vim). `repeat` handles the classic `;`-after-`t` stickiness: skip a target
    we're already sitting against.
    """

    line = doc.line(p.row)
    col = p.col
    if repeat and till:
        col = col + 1 if forward else col - 1
    for _ in range(count):
        i = line.find(ch, col + 1) if forward else line.rfind(ch, 0, max(col, 0))
        if i < 0:
            return None
        col = i
    if till:
        col += -1 if forward else 1
    if col < 0 or col >= max(len(line), 1):
        return None
    return Pos(p.row, col)
