"""
The menu: a floating list of actions - a context menu over a transcript row, a small command palette - shown through
an `Overlay`. One row per item with the selection highlighted; up/down (or j/k) move over the enabled items, wrapping;
enter or space activates; escape or q closes; a click activates the row under it. The menu knows nothing about where
it floats: the app opens it (an Overlay at the click, `width` columns wide), and closes it on `on_close` - which the
menu also calls after an activation, since a menu that has done its job goes away.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore.text.widths import str_width

from ..events.keys import Key
from ..events.types import Event
from ..events.types import KeyEvent
from ..events.types import MouseEvent
from ..events.types import MouseEventKind
from ..text.segments import Segment
from .base import Control


##


@dc.dataclass(frozen=True)
class MenuItem(lang.Final):
    label: str

    _: dc.KW_ONLY

    on_select: ta.Callable[[], None] | None = None
    disabled: bool = False


class Menu(Control):
    def __init__(
            self,
            items: ta.Iterable[MenuItem] = (),
            *,
            on_close: ta.Callable[[], None] | None = None,
            min_width: int = 0,
    ) -> None:
        super().__init__()

        self._on_close = on_close
        self._min_width = min_width

        self._items: tuple[MenuItem, ...] = ()
        self._selected: int | None = None
        self.set_items(items)

    @property
    def items(self) -> ta.Sequence[MenuItem]:
        return self._items

    @property
    def selected_index(self) -> int | None:
        return self._selected

    @property
    def selected(self) -> MenuItem | None:
        return self._items[self._selected] if self._selected is not None else None

    @property
    def width(self) -> int:
        """The natural box width: the widest label plus a space either side, at least `min_width`."""

        labels = max((str_width(item.label) for item in self._items), default=0)
        return max(labels + 2, self._min_width)

    def set_items(self, items: ta.Iterable[MenuItem]) -> None:
        self._items = tuple(items)
        self._selected = next((i for i, item in enumerate(self._items) if not item.disabled), None)

    ##
    # Selection

    def select(self, index: int) -> None:
        if 0 <= index < len(self._items) and not self._items[index].disabled:
            self._selected = index

    def move(self, delta: int) -> None:
        """Step the selection over the enabled items, wrapping."""

        n = len(self._items)
        if not n or self._selected is None:
            return
        i = self._selected
        for _ in range(n):
            i = (i + delta) % n
            if not self._items[i].disabled:
                self._selected = i
                return

    def activate(self) -> bool:
        """Run the selected item's action (then close). False when there is nothing enabled to run."""

        if (item := self.selected) is None or item.disabled:
            return False
        if item.on_select is not None:
            item.on_select()
        self.close()
        return True

    def close(self) -> None:
        if self._on_close is not None:
            self._on_close()

    ##
    # Rendering

    def render(self, width: int) -> ta.Sequence[ta.Sequence[Segment]]:
        inner = max(width - 2, 0)
        rows: list[ta.Sequence[Segment]] = []
        for i, item in enumerate(self._items):
            if i == self._selected:
                tag = 'menu.selected'
            elif item.disabled:
                tag = 'menu.disabled'
            else:
                tag = 'menu.item'
            label = item.label
            while label and str_width(label) > inner:
                label = label[:-1]
            rows.append([Segment(f' {label}{" " * (inner - str_width(label))} ', tag)])
        return rows

    ##
    # Events (the app routes; local coordinates arrive in the event)

    def handle_event(self, event: Event) -> bool:
        if isinstance(event, MouseEvent):
            if event.kind is MouseEventKind.DOWN and 0 <= event.y < len(self._items):
                if self._items[event.y].disabled:
                    return False  # not the selected item's click
                self.select(event.y)
                return self.activate()
            return False

        if isinstance(event, KeyEvent):
            key = event.key
            if key in (Key('up'), Key('k')):
                self.move(-1)
            elif key in (Key('down'), Key('j')):
                self.move(1)
            elif key in (Key('enter'), Key('space')):
                self.activate()
            elif key in (Key('escape'), Key('q')):
                self.close()
            else:
                return False
            return True

        return False
