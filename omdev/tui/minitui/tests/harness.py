import typing as ta

from omcore.term.vt100.terminal import Vt100Terminal

from ..screens.cells import Frame
from ..screens.cells import Line
from ..screens.cells import line_from_segments
from ..surfaces.inlines import InlineSurface
from ..text.colors import ColorDepth
from ..text.segments import Segment
from ..text.styles import EMPTY_THEME
from ..text.styles import StyleLike
from ..text.styles import Theme
from ..tty.terminals import Tty


##


class RecordingTty(Tty):
    """A Tty that records writes instead of touching any fd, with a settable size."""

    def __init__(
            self,
            *,
            height: int = 24,
            width: int = 80,
    ) -> None:
        super().__init__(input_fd=-1, output_fd=-1)

        self._height = height
        self._width = width
        self.writes: list[bytes] = []
        self.foreground = True

    def write_bytes(self, data: bytes) -> None:
        self.writes.append(data)

    def get_size(self) -> tuple[int, int]:
        return self._height, self._width

    def enter_raw(self, *, keep_signals: bool = True) -> None:
        pass

    def restore(self) -> None:
        pass

    def watch_resize(self) -> None:
        pass

    def probe_foreground(self) -> bool:
        return self.foreground

    def resize(self, *, height: int, width: int) -> None:
        self._height = height
        self._width = width
        self._resized = True


class SurfaceHarness:
    """An InlineSurface wired to a recording tty and a vt100 emulator oracle."""

    def __init__(
            self,
            *,
            height: int = 8,
            width: int = 40,
            theme: Theme = EMPTY_THEME,
    ) -> None:
        super().__init__()

        self.tty = RecordingTty(height=height, width=width)
        self.surface = InlineSurface(self.tty, term='xterm-256color', depth=ColorDepth.TRUE)
        self.terminal = Vt100Terminal(rows=height, cols=width)
        self.theme = theme

        self._fed = 0

        self.surface.prepare()
        self.pump()

    def pump(self) -> bytes:
        """Feed any recorded-but-unfed writes into the emulator, returning them."""

        data = b''.join(self.tty.writes[self._fed:])
        self._fed = len(self.tty.writes)
        self.terminal.feed(data)
        return data

    #

    def line(self, *parts: str | tuple[str, StyleLike | None]) -> Line:
        segments = [
            Segment(part) if isinstance(part, str) else Segment(part[0], part[1])
            for part in parts
        ]
        return line_from_segments(segments, self.theme)

    def frame(
            self,
            *lines: str | Line,
            cursor: tuple[int, int] | None = None,
            cursor_visible: bool = True,
    ) -> Frame:
        line_objs = tuple(
            self.line(line) if isinstance(line, str) else line
            for line in lines
        )
        return Frame(
            line_objs,
            cursor=cursor if cursor is not None else (0, max(len(line_objs) - 1, 0)),
            cursor_visible=cursor_visible,
        )

    #

    def present(self, frame: Frame) -> bytes:
        self.surface.present(frame)
        return self.pump()

    def commit(self, lines: ta.Sequence[Line]) -> bytes:
        self.surface.commit(lines)
        return self.pump()

    #

    def screen(self) -> list[str]:
        return self.terminal.screen_lines()

    def scrollback(self) -> list[str]:
        return self.terminal.scrollback_lines()

    def all_lines(self) -> list[str]:
        return self.terminal.all_lines()
