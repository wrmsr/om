"""Surface: where frames become terminal bytes."""
import abc

from omcore import lang

from ..screens.cells import Frame
from ..tty.terminals import Tty


##


class Surface(lang.Abstract):
    """
    An output target for frames.

    Implementations own the tty lifecycle (raw mode, autowrap, cursor visibility) between `prepare` and `restore` - or
    `suspend` and `resume`, around a process stop - and turn each `present` into a minimal byte stream via
    retained-frame diffing. Coordinates in frames are always surface-relative; nothing above the surface knows absolute
    terminal positions.
    """

    @property
    @abc.abstractmethod
    def tty(self) -> Tty:
        raise NotImplementedError

    @abc.abstractmethod
    def take_resized(self) -> bool:
        """Absorb any pending terminal resize, returning whether one happened (the caller should re-layout)."""

        raise NotImplementedError

    @abc.abstractmethod
    def set_sync_output(self, enabled: bool) -> None:
        """Whether frames are wrapped in synchronized output (DECSET 2026). Defaults on, blind-optimistically."""

        raise NotImplementedError

    @abc.abstractmethod
    def request_sync_output_report(self) -> None:
        """Send the DECRQM query for mode 2026; the answer arrives in the input stream as a ModeReportEvent."""

        raise NotImplementedError

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
    def suspend(self) -> None:
        """Leave application mode for a process stop (ctrl+z): like `restore`, but expecting a `resume`."""

        raise NotImplementedError

    @abc.abstractmethod
    def resume(self) -> None:
        """Re-enter application mode after a stop. The retained frame is forgotten: the next present repaints fully."""

        raise NotImplementedError

    @abc.abstractmethod
    def present(self, frame: Frame) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def beep(self) -> None:
        raise NotImplementedError
