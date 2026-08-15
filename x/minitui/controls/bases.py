"""
Controls: the small retained layer between app state and frames.

A `Control` renders *rows of styled segments* for a width - semantic content, no theme applied, no cells yet. The
composition point (see `stacks.py`) resolves themes, builds cells, and assembles the frame. Height is height-for-width
by construction: it's simply how many rows `render` returns.

Controls are passive: mutate them, then ask the driver to `invalidate()`. Event routing is a plain focus pointer held
by the app - there is no tree walk, no bubbling, no implicit dispatch.
"""
import abc
import typing as ta

from omcore import lang

from ..events.types import Event
from ..screens.cells import CursorXY
from ..text.segments import Segments


##


class Control(lang.Abstract):
    @abc.abstractmethod
    def render(self, width: int) -> ta.Sequence[Segments]:
        """Render to rows of segments, each fitting in `width` display columns. May be empty."""

        raise NotImplementedError

    def cursor(self, width: int) -> CursorXY | None:
        """Where this control wants the terminal cursor, relative to its own rows - or None."""

        return None

    def handle_event(self, event: Event) -> bool:
        """Handle an event routed to this control (focus is the app's concern). Returns whether it was consumed."""

        return False
