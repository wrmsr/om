"""
The alt-screen surface: fullscreen apps over the same frame/diff machinery as the inline surface.

Simpler in every way that matters: the alt screen is a fixed grid the terminal hands us whole, so movement is absolute
(`cup`), rows never scroll, and there is no commit operation - nothing here ever becomes scrollback, which is exactly
the tradeoff fullscreen apps opt into. The inline surface remains the primary citizen; this exists for the
genuinely-fullscreen cases (the vim clone), and its painting half - `AltPainter` - doubles as the inline surface's
alt-screen excursion (browse mode: the same app, fullscreen for a while, then back to the live region untouched).
"""
from omcore import check
from omcore.term.styled import ColorDepth
from omcore.term.styled import detect_color_depth

from ..screens.cells import EMPTY_FRAME
from ..screens.cells import Frame
from ..screens.cells import Line
from ..screens.cells import render_cells
from ..screens.diffs import LineUpdate
from ..screens.diffs import diff_frames
from ..tty.terminals import Tty
from .base import Surface
from .writers import TermWriter


##


class AltPainter:
    """
    Retained-frame painting onto a fixed grid with absolute addressing - the alt screen's half of `AltSurface`, and the
    inline surface's alt-screen excursion.

    Pure painting: the owner decides when the grid is ours (screen switching, raw mode, the modes), brackets `paint` in
    synchronized output, and flushes. Cursor visibility is a terminal-global mode rather than per screen, so a painter
    is seeded with the physical state it inherits and reports where it left it.
    """

    def __init__(
            self,
            writer: TermWriter,
            *,
            depth: ColorDepth,
            cursor_shown: bool = True,
    ) -> None:
        super().__init__()

        self._writer = writer
        self._depth = depth

        self._frame: Frame = EMPTY_FRAME
        # (col, row) the terminal cursor is known to be at, or None after painting moved it.
        self._cursor: tuple[int, int] | None = None
        self._cursor_shown = cursor_shown

    @property
    def frame(self) -> Frame:
        return self._frame

    @property
    def cursor_shown(self) -> bool:
        return self._cursor_shown

    def _move_to(self, row: int, col: int) -> None:
        if self._cursor == (col, row):
            return
        self._writer.move_to(row, col)
        self._cursor = (col, row)

    def hide_cursor(self) -> None:
        if self._cursor_shown:
            self._writer.hide_cursor()
            self._cursor_shown = False

    def show_cursor(self) -> None:
        if not self._cursor_shown:
            self._writer.show_cursor()
            self._cursor_shown = True

    def clear(self) -> None:
        """Home and erase the whole grid, forgetting the retained frame: on entry, and after a resize."""

        self._move_to(0, 0)
        self._writer.erase_down()
        self._frame = EMPTY_FRAME

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

    def paint(self, frame: Frame, *, width: int) -> None:
        """Diff `frame` against the retained one, emit the changes, place the cursor, and retain it."""

        diff = diff_frames(self._frame, frame)

        if not diff.is_empty:
            self.hide_cursor()

            for update in diff.line_updates:
                self._apply_update(update)

            for i, line in enumerate(diff.appended):
                self._write_full_line(line, diff.old_height + i)

            if diff.shrink:
                self._move_to(diff.height, 0)
                self._writer.erase_down()
                self._cursor = None

        cx, cy = frame.cursor
        self._move_to(cy, min(cx, max(width - 1, 0)))
        if frame.cursor_visible:
            self.show_cursor()
        else:
            self.hide_cursor()

        self._frame = frame


##


class AltSurface(Surface):
    def __init__(
            self,
            tty: Tty | None = None,
            *,
            term: str | None = None,
            depth: ColorDepth | None = None,
            kitty_keys: bool = False,
            mouse: bool = False,
    ) -> None:
        super().__init__()

        self._tty = tty if tty is not None else Tty()
        self._writer = TermWriter(self._tty, term=term)
        self._depth = depth if depth is not None else detect_color_depth()
        self._kitty_keys = kitty_keys
        self._mouse = mouse

        self._painter = AltPainter(self._writer, depth=self._depth)
        self._term_height = 0
        self._term_width = 0
        self._prepared = False
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
        return self._painter.frame

    def frame_row(self, terminal_row: int) -> int:
        return terminal_row  # the frame is the screen

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
            # Both extended-key protocols: kitty (modern) and xterm modifyOtherKeys (iTerm2, xterm, mintty, and the
            # format tmux's extended-keys forwards). Terminals honor whichever they speak; both are ignored elsewhere.
            w.kitty_keys(True)
            w.kitty_keys_query()
            w.modify_other_keys(True)
        if self._mouse:
            w.mouse_tracking(True)
        self._painter = AltPainter(self._writer, depth=self._depth)  # the cursor is shown again after any restore
        self._painter.clear()
        w.flush()

        self._prepared = True

    def restore(self) -> None:
        if not self._prepared:
            return
        self._prepared = False

        w = self._writer
        self._painter.show_cursor()
        if self._mouse:
            w.mouse_tracking(False)
        if self._kitty_keys:
            w.modify_other_keys(False)
            w.kitty_keys(False)
        w.bracketed_paste(False)
        w.autowrap(True)
        w.alt_screen(False)
        w.flush()

        self._tty.restore()

    def suspend(self) -> None:
        self.restore()  # leaving the alt screen brings the main screen back by itself; nothing of ours survives

    def resume(self) -> None:
        self.prepare()

    ##
    # Painting

    def set_sync_output(self, enabled: bool) -> None:
        self._sync_output = enabled

    def request_sync_output_report(self) -> None:
        w = self._writer
        w.sync_query()
        w.flush()

    def request_terminal_version(self) -> None:
        w = self._writer
        w.terminal_version_query()
        w.flush()

    def take_resized(self) -> bool:
        if not self._tty.take_resized():
            return False
        self._term_height, self._term_width = self._tty.get_size()
        self._painter.clear()
        return True

    def present(self, frame: Frame) -> None:
        check.state(self._prepared)
        check.arg(frame.height <= self._term_height)

        self.take_resized()

        w = self._writer
        if self._sync_output:
            w.sync_start()

        self._painter.paint(frame, width=self._term_width)

        if self._sync_output:
            w.sync_end()
        w.flush()

    def beep(self) -> None:
        self._writer.bell()
        self._writer.flush()
