import abc

from omcore import lang

from ..events.types import Event
from ..screens.cells import Frame


##


class App(lang.Abstract):
    @abc.abstractmethod
    def render(self, width: int, max_height: int) -> Frame:
        """Build the live-region frame. Must fit: height <= max_height, content wrapped to width."""

        raise NotImplementedError

    @abc.abstractmethod
    def handle_event(self, event: Event) -> None:
        raise NotImplementedError
