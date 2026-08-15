"""
The alt-screen surface: fullscreen apps over the same frame/diff machinery as the inline surface.

Simpler in every way that matters: the alt screen is a fixed grid the terminal hands us whole, so movement is
absolute (`cup`), rows never scroll, and there is no commit operation - nothing here ever becomes scrollback, which
is exactly the tradeoff fullscreen apps opt into. The inline surface remains the primary citizen; this exists for the
genuinely-fullscreen cases (the vim clone, a future browse mode).
"""
from omcore import check

from ..screens.cells import EMPTY_FRAME
from ..screens.cells import Frame
from ..screens.cells import Line
from ..screens.cells import render_cells
from ..screens.diffs import LineUpdate
from ..screens.diffs import diff_frames
from ..text.colors import ColorDepth
from ..tty.terminals import Tty
from .bases import Surface
from .writers import TermWriter


##


class AltSurface(Surface):
    def __init__(
            self,
            tty: Tty | None = None,
            *,
            term: str | None = None,
            depth: ColorDepth = ColorDepth.TRUE,
            kitty_keys: bool = False,
            mouse: bool = False,
    ) -> None:
        super().__init__()

        self._tty = tty if tty is not None else Tty()
        self._writer = TermWriter(self._tty, term=term)
        self._depth = depth
        self._kitty_keys = kitty_keys
        self._mouse = mouse

        self._frame: Frame = EMPTY_FRAME
        self._term_height = 0
        self._term_width = 0
        self._cursor_shown = True
        self._prepared = False
        # (col, row) the terminal cursor is known to be at, or None after painting moved it.
        self._cursor: tuple[int, int] | None = None
        self._sync_output = True

    @property
    def tty(self) -> Tty:
        return self._tty

    @property
    def width(self) -> int:
        return self._term_width

    @property
    def height(self) -> int:
        return self._term_height

    @property
    def frame(self) -> Frame:
        return self._frame

    ##
    # Lifecycle

    def prepare(self) -> None:
        check.state(not self._prepared)

        self._tty.enter_raw()
        self._tty.watch_resize()
        self._term_height, self._term_width = self._tty.get_size()

        w = self._writer
        w.alt_screen(True)
        w.autowrap(False)
        w.bracketed_paste(True)
        if self._kitty_keys:
            w.kitty_keys(True)
        if self._mouse:
            w.mouse_tracking(True)
        w.move_to(0, 0)
        w.erase_down()
        w.flush()
        self._cursor = (0, 0)

        self._frame = EMPTY_FRAME
        self._cursor_shown = True
        self._prepared = True

    def restore(self) -> None:
        if not self._prepared:
            return
        self._prepared = False

        w = self._writer
        self._show_cursor()
        if self._mouse:
            w.mouse_tracking(False)
        if self._kitty_keys:
            w.kitty_keys(False)
        w.bracketed_paste(False)
        w.autowrap(True)
        w.alt_screen(False)
        w.flush()

        self._tty.restore()

    ##
    # Painting

    def set_sync_output(self, enabled: bool) -> None:
        self._sync_output = enabled

    def request_sync_output_report(self) -> None:
        w = self._writer
        w.sync_query()
        w.flush()

    def _move_to(self, row: int, col: int) -> None:
        if self._cursor == (col, row):
            return
        self._writer.move_to(row, col)
        self._cursor = (col, row)

    def _hide_cursor(self) -> None:
        if self._cursor_shown:
            self._writer.hide_cursor()
            self._cursor_shown = False

    def _show_cursor(self) -> None:
        if not self._cursor_shown:
            self._writer.show_cursor()
            self._cursor_shown = True

    def _apply_update(self, update: LineUpdate) -> None:
        w = self._writer
        self._move_to(update.y, update.start_x)
        w.text(render_cells(update.cells, self._depth))
        if update.clear_eol:
            w.erase_eol()
        self._cursor = None  # painting moved it

    def _write_full_line(self, line: Line, y: int) -> None:
        w = self._writer
        self._move_to(y, 0)
        w.text(render_cells(line.cells, self._depth))
        w.erase_eol()
        self._cursor = None

    def take_resized(self) -> bool:
        if not self._tty.take_resized():
            return False
        self._term_height, self._term_width = self._tty.get_size()
        w = self._writer
        self._move_to(0, 0)
        w.erase_down()
        self._cursor = None
        self._frame = EMPTY_FRAME
        return True

    def present(self, frame: Frame) -> None:
        check.state(self._prepared)
        check.arg(frame.height <= self._term_height)

        self.take_resized()

        diff = diff_frames(self._frame, frame)

        w = self._writer
        if self._sync_output:
            w.sync_start()

        if not diff.is_empty:
            self._hide_cursor()

            for update in diff.line_updates:
                self._apply_update(update)

            for i, line in enumerate(diff.appended):
                self._write_full_line(line, diff.old_height + i)

            if diff.shrink:
                self._move_to(diff.height, 0)
                w.erase_down()
                self._cursor = None

        cx, cy = frame.cursor
        self._move_to(cy, min(cx, max(self._term_width - 1, 0)))
        if frame.cursor_visible:
            self._show_cursor()
        else:
            self._hide_cursor()

        if self._sync_output:
            w.sync_end()
        w.flush()

        self._frame = frame

    def beep(self) -> None:
        self._writer.bell()
        self._writer.flush()
