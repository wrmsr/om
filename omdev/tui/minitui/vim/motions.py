"""
Motion results and span resolution.

A motion never edits: it *describes* - target + kind + hints. `resolve()` turns (start, MotionResult) into an operable
Span, applying vim's two `:help exclusive` adjustment rules - those two rules alone are why `dw` behaves sanely without
w/b special-casing anything. (Adapted from x/vibes/minivim.)
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..docs.documents import Document
from ..docs.positions import Pos
from ..docs.positions import Span
from ..docs.positions import SpanKind
from .scans import first_nonblank
from .scans import llen


##


# curswant value meaning "end of line, whatever that is"
WANT_EOL = 10 ** 9


@dc.dataclass(frozen=True)
class MotionResult(lang.Final):
    target: Pos
    kind: SpanKind

    _: dc.KW_ONLY

    keeps_curswant: bool = False     # j/k: reuse remembered column
    to_first_nonblank: bool = False  # G/gg place cursor at first non-blank
    curswant_eol: bool = False       # $ pins curswant to "always end of line"


# motion key -> needs a trailing character argument? (vim's NV_NCH flag)
MOTION_NEEDS_ARG: ta.AbstractSet[str] = frozenset('ftFT')

MOTION_KEYS: ta.AbstractSet[str] = frozenset('hljk0^$wWbBeEGnN;,%') | {'gg'} | MOTION_NEEDS_ARG


def resolve(doc: Document, start: Pos, mr: MotionResult) -> Span | None:
    """Resolve (start, motion) into an operable Span, or None for a degenerate (empty) one."""

    if mr.kind is SpanKind.LINEWISE:
        r1, r2 = sorted((start.row, mr.target.row))
        return Span(SpanKind.LINEWISE, Pos(r1, 0), Pos(r2, 0))

    a, b = (start, mr.target) if start <= mr.target else (mr.target, start)
    if mr.kind is SpanKind.INCLUSIVE:
        b = Pos(b.row, min(b.col + 1, llen(doc, b.row)))
    else:
        # vim's two `:help exclusive` adjustments:
        #   * `dw` on the last word of a line deletes to EOL, no line join
        #   * `dw` at/before the first non-blank of a line goes linewise
        if b.col == 0 and b.row > a.row:
            if a.col <= first_nonblank(doc, a.row):
                return Span(SpanKind.LINEWISE, Pos(a.row, 0), Pos(b.row - 1, 0))
            b = Pos(b.row - 1, llen(doc, b.row - 1))
    if not a < b:
        return None
    return Span(SpanKind.EXCLUSIVE, a, b)
