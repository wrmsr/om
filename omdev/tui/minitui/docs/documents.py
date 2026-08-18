"""
The mutable document: lines of text, mutated only through range edits.

Every mutation goes through `replace()`, which validates, applies, bumps `version`, computes the inverse, and notifies
listeners with the `AppliedEdit` - the one channel renderers, highlighters, and undo machinery all hang off. A never-
empty invariant holds: a document always has at least one (possibly empty) line.
"""
import typing as ta

from omcore import check

from .edits import AppliedEdit
from .edits import TextEdit
from .positions import Pos


DocumentListener: ta.TypeAlias = ta.Callable[['Document', AppliedEdit], None]


##


class Document:
    def __init__(self, text: str = '') -> None:
        super().__init__()

        self._lines: list[str] = text.split('\n') if text else ['']
        self._version = 0
        self._listeners: list[DocumentListener] = []

    ##
    # Introspection

    @property
    def version(self) -> int:
        return self._version

    def line_count(self) -> int:
        return len(self._lines)

    def line(self, row: int) -> str:
        return self._lines[row]

    def lines(self) -> ta.Sequence[str]:
        return tuple(self._lines)

    def text(self) -> str:
        return '\n'.join(self._lines)

    def end_pos(self) -> Pos:
        return Pos(len(self._lines) - 1, len(self._lines[-1]))

    def clamp(self, pos: Pos, *, allow_newline_slot: bool = True) -> Pos:
        """Clamp to a valid position; without `allow_newline_slot`, also off the one-past-end column (normal mode)."""

        row = min(max(pos.row, 0), len(self._lines) - 1)
        max_col = len(self._lines[row])
        if not allow_newline_slot:
            max_col = max(max_col - 1, 0)
        return Pos(row, min(max(pos.col, 0), max_col))

    def get_text(self, start: Pos, end: Pos) -> str:
        """The charwise text of [start, end)."""

        check.arg(start <= end)
        if start.row == end.row:
            return self._lines[start.row][start.col: end.col]
        parts = [self._lines[start.row][start.col:]]
        parts.extend(self._lines[start.row + 1: end.row])
        parts.append(self._lines[end.row][: end.col])
        return '\n'.join(parts)

    def _check_pos(self, pos: Pos) -> None:
        check.arg(0 <= pos.row < len(self._lines))
        check.arg(0 <= pos.col <= len(self._lines[pos.row]))

    ##
    # Listeners

    def add_listener(self, listener: DocumentListener) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener: DocumentListener) -> None:
        self._listeners.remove(listener)

    ##
    # Mutation

    def replace(self, start: Pos, end: Pos, text: str) -> AppliedEdit:
        """Replace the charwise range [start, end) with `text`. The one and only mutation primitive."""

        self._check_pos(start)
        self._check_pos(end)
        edit = TextEdit(start, end, text)

        old_text = self.get_text(start, end)

        prefix = self._lines[start.row][: start.col]
        suffix = self._lines[end.row][end.col:]
        new_lines = (prefix + text + suffix).split('\n')
        self._lines[start.row: end.row + 1] = new_lines

        self._version += 1
        applied = AppliedEdit(edit, TextEdit(start, edit.new_end, old_text))
        for listener in list(self._listeners):
            listener(self, applied)
        return applied

    def apply(self, edit: TextEdit) -> AppliedEdit:
        return self.replace(edit.start, edit.end, edit.text)

    def insert(self, pos: Pos, text: str) -> AppliedEdit:
        return self.replace(pos, pos, text)

    def delete(self, start: Pos, end: Pos) -> AppliedEdit:
        return self.replace(start, end, '')

    def set_text(self, text: str) -> AppliedEdit:
        return self.replace(Pos(0, 0), self.end_pos(), text)
