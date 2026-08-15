"""Surface: where frames become terminal bytes."""
import abc

from omcore import lang

from ..screens.cells import Frame


##


class Surface(lang.Abstract):
    """
    An output target for frames.

    Implementations own the tty lifecycle (raw mode, autowrap, cursor visibility) between `prepare` and `restore`, and
    turn each `present` into a minimal byte stream via retained-frame diffing. Coordinates in frames are always
    surface-relative; nothing above the surface knows absolute terminal positions.
    """

    @property
    @abc.abstractmethod
    def width(self) -> int:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def height(self) -> int:
        """The maximum useful frame height - for an inline surface, the terminal height."""

        raise NotImplementedError

    @abc.abstractmethod
    def prepare(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def restore(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def present(self, frame: Frame) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def beep(self) -> None:
        raise NotImplementedError
