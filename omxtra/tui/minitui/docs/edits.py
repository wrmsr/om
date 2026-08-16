"""
Range edits: the single mutation primitive and the algebra everything leans on.

A `TextEdit` replaces the charwise range [start, end) with `text` (which may contain newlines) - insert is start==end,
delete is text=''. This is deliberately the same shape as tree-sitter's `edit()` and LSP's TextEdit, so incremental
consumers translate directly. Applying yields an `AppliedEdit` carrying the exact inverse, which is what undo, redo,
and transactional grouping are made of; `remap_pos` moves positions (cursors, match spans, decoration anchors) through
an edit, which is what makes multi-cursor and durable spans possible.
"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from .positions import Pos


##


@dc.dataclass(frozen=True)
class TextEdit(lang.Final):
    start: Pos
    end: Pos
    text: str

    def __post_init__(self) -> None:
        check.arg(self.start <= self.end)

    @property
    def is_insert(self) -> bool:
        return self.start == self.end

    @property
    def new_end(self) -> Pos:
        """Where the replaced range ends after the edit."""

        lines = self.text.split('\n')
        if len(lines) == 1:
            return Pos(self.start.row, self.start.col + len(lines[0]))
        return Pos(self.start.row + len(lines) - 1, len(lines[-1]))


@dc.dataclass(frozen=True)
class AppliedEdit(lang.Final):
    edit: TextEdit
    inverse: TextEdit


def remap_pos(pos: Pos, edit: TextEdit, *, before_bias: bool = False) -> Pos:
    """
    Where `pos` lands after `edit` is applied.

    Positions before the edited range are unchanged; positions after it shift by the edit's size delta; positions
    inside the replaced range clamp to its start (or, with `before_bias` False and an insert at exactly `pos`, stay
    after the inserted text - insertions at the cursor push the cursor forward).
    """

    start = edit.start
    end = edit.end

    if pos < start:
        return pos
    if pos < end or (pos == end and before_bias and not edit.is_insert):
        return start
    if pos == start and before_bias:
        return pos

    # At or after the old end: shift by the delta.
    new_end = edit.new_end
    if pos.row == end.row:
        return Pos(new_end.row, new_end.col + (pos.col - end.col))
    return Pos(pos.row + (new_end.row - end.row), pos.col)


def remap_pos_through(pos: Pos, edits: ta.Iterable[TextEdit], *, before_bias: bool = False) -> Pos:
    for edit in edits:
        pos = remap_pos(pos, edit, before_bias=before_bias)
    return pos
