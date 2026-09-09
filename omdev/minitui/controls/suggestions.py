"""The suggestions popup: a small selectable list stacked above the input (slash commands, completions)."""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..text.segments import Segment
from .base import Control


##


@dc.dataclass(frozen=True)
class SuggestionItem(lang.Final):
    label: str
    description: str = ''


class SuggestionsPopup(Control):
    def __init__(self) -> None:
        super().__init__()

        self._items: tuple[SuggestionItem, ...] = ()
        self._selected: int | None = None

    @property
    def visible(self) -> bool:
        return bool(self._items)

    @property
    def selected(self) -> SuggestionItem | None:
        if self._selected is None or not self._items:
            return None
        return self._items[self._selected]

    def set_items(self, items: ta.Iterable[SuggestionItem]) -> None:
        new = tuple(items)
        if new != self._items:
            self._items = new
            self._selected = None

    def clear(self) -> None:
        self._items = ()
        self._selected = None

    def item_at(self, index: int) -> SuggestionItem | None:
        """The item on rendered row `index` (rows map 1:1 to items) - click selection."""

        if 0 <= index < len(self._items):
            self._selected = index
            return self._items[index]
        return None

    def cycle(self) -> SuggestionItem | None:
        """Advance the selection (wrapping) and return the newly-selected item."""

        if not self._items:
            return None
        self._selected = 0 if self._selected is None else (self._selected + 1) % len(self._items)
        return self._items[self._selected]

    def render(self, width: int) -> ta.Sequence[ta.Sequence[Segment]]:
        if not self._items:
            return []

        label_w = max(len(item.label) for item in self._items)
        rows: list[list[Segment]] = []
        for i, item in enumerate(self._items):
            selected = i == self._selected
            row = [Segment(item.label.ljust(label_w), 'popup.selected' if selected else 'popup.label')]
            if item.description:
                row.append(Segment('  '))
                row.append(Segment(item.description, 'popup.selected.desc' if selected else 'popup.desc'))
            rows.append(row)
        return rows
