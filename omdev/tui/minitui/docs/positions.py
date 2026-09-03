"""Positions and spans over documents. Row/col are 0-based; col may equal the line length (the 'newline slot')."""
import enum

from omcore import dataclasses as dc
from omcore import lang


##


@dc.dataclass(frozen=True, order=True)
class Pos(lang.Final):
    row: int
    col: int


class SpanKind(enum.Enum):
    """How a motion/span characterizes the text it covers (vim: :help inclusive)."""

    EXCLUSIVE = enum.auto()  # charwise, target char NOT covered (w, b, h, 0, F, T)
    INCLUSIVE = enum.auto()  # charwise, target char covered     (e, f, t, $)
    LINEWISE = enum.auto()   # whole lines                       (j, k, G, gg, dd)
    BLOCK = enum.auto()      # rectangular (blockwise visual: ctrl+v)


@dc.dataclass(frozen=True)
class Span(lang.Final):
    """
    A range over a document.

    Charwise (EXCLUSIVE kind after resolution): [start, end), end.col may equal the line length. LINEWISE: whole rows
    start.row..end.row inclusive, cols ignored. BLOCK: rows start.row..end.row inclusive, cols [start.col, end.col) on
    each row, clipped to each line's length.
    """

    kind: SpanKind
    start: Pos
    end: Pos

    def contains(self, pos: Pos) -> bool:
        if self.kind is SpanKind.LINEWISE:
            return self.start.row <= pos.row <= self.end.row
        return self.start <= pos < self.end
