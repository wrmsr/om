"""
The inline surface: minitui's reason to exist.

The terminal viewport is [ ...native scrollback... | committed tail | LIVE REGION ]. The live region is the bottom
rows of our output: a retained `Frame`, diffed and redrawn in place. `commit()` freezes lines out of the top of the
live region into the terminal's own scrollback - immutable once emitted, visible after exit, tmux-native - and
re-anchors the live region below them. A message that finalizes exactly as displayed commits for zero bytes.

All cursor tracking is relative to the live region origin (row 0); there are no absolute coordinates anywhere.
Downward motion is always the literal '\\r\\n' pair - never cud - because only '\\r\\n' scrolls the terminal when the
cursor is on the bottom row, which is exactly how the live region grows and how commits push history upward. Autowrap
is disabled while active so a width-exact line can never desync the relative tracking.
"""
import typing as ta

from omcore import check

from ..screens.cells import EMPTY_FRAME
from ..screens.cells import CursorXY
from ..screens.cells import Frame
from ..screens.cells import Line
from ..screens.cells import render_cells
from ..screens.diffs import LineUpdate
from ..screens.diffs import diff_frames
from ..screens.diffs import diff_lines
from ..text.colors import ColorDepth
from ..tty.terminals import Tty
from .bases import Surface
from .writers import TermWriter


##


_REDRAW_DEBUG_PALETTE: ta.Sequence[str] = (
    '\x1b[41m',
    '\x1b[42m',
    '\x1b[43m',
    '\x1b[44m',
    '\x1b[45m',
    '\x1b[46m',
)


class InlineSurface(Surface):
    def __init__(
            self,
            tty: Tty | None = None,
            *,
            term: str | None = None,
            depth: ColorDepth = ColorDepth.TRUE,
            visualize_redraws: bool = False,
            kitty_keys: bool = False,
            mouse: bool = False,
    ) -> None:
        super().__init__()

        self._tty = tty if tty is not None else Tty()
        self._writer = TermWriter(self._tty, term=term)
        self._depth = depth
        self._visualize_redraws = visualize_redraws
        self._kitty_keys = kitty_keys
        self._mouse = mouse

        self._frame: Frame = EMPTY_FRAME
        self._cursor: CursorXY = (0, 0)
        self._term_height = 0
        self._term_width = 0
        self._cursor_shown = True
        self._prepared = False
        self._debug_cycle = 0

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
        """The currently-displayed (retained) live region frame."""

        return self._frame

    ##
    # Lifecycle

    def prepare(self) -> None:
        check.state(not self._prepared)

        self._tty.enter_raw()
        self._tty.watch_resize()
        self._term_height, self._term_width = self._tty.get_size()

        w = self._writer
        w.autowrap(False)
        w.bracketed_paste(True)
        if self._kitty_keys:
            w.kitty_keys(True)
        if self._mouse:
            w.mouse_tracking(True)
        # Normalize to column 0 of the current row; this becomes the live region origin. (A shell that left a partial
        # line gets overwritten - CPR-based column detection can improve this once the input layer exists.)
        w.cr()
        w.flush()

        self._frame = EMPTY_FRAME
        self._cursor = (0, 0)
        self._cursor_shown = True
        self._prepared = True

    def restore(self) -> None:
        if not self._prepared:
            return
        self._prepared = False

        w = self._writer
        # Leave the shell on a fresh line below everything we drew.
        self._move(0, max(self._frame.height - 1, 0))
        w.crlf()
        self._show_cursor()
        if self._mouse:
            w.mouse_tracking(False)
        if self._kitty_keys:
            w.kitty_keys(False)
        w.bracketed_paste(False)
        w.autowrap(True)
        w.flush()

        self._tty.restore()

    ##
    # Movement (relative to the live region origin)

    def _move(self, x: int, y: int) -> None:
        w = self._writer
        cx, cy = self._cursor
        if y < cy:
            w.up(cy - y)
        elif y > cy:
            w.crlf(y - cy)
            cx = 0
        if x != cx:
            if x == 0:
                w.cr()
            elif x > cx:
                w.right(x - cx)
            else:
                w.left(cx - x)
        self._cursor = (x, y)

    def _hide_cursor(self) -> None:
        if self._cursor_shown:
            self._writer.hide_cursor()
            self._cursor_shown = False

    def _show_cursor(self) -> None:
        if not self._cursor_shown:
            self._writer.show_cursor()
            self._cursor_shown = True

    ##
    # Painting

    def _debug_style(self) -> str | None:
        if not self._visualize_redraws:
            return None
        style = _REDRAW_DEBUG_PALETTE[self._debug_cycle % len(_REDRAW_DEBUG_PALETTE)]
        self._debug_cycle += 1
        return style

    def _resync_margin(self, y: int) -> None:
        # With autowrap off the terminal pins the cursor at the last column, so a write reaching the right margin
        # leaves the physical cursor short of where naive width-addition says. A CR makes tracking exact again.
        if self._cursor[0] >= self._term_width:
            self._writer.cr()
            self._cursor = (0, y)

    def _apply_update(self, update: LineUpdate, debug_style: str | None) -> None:
        self._move(update.start_x, update.y)
        self._writer.text(render_cells(update.cells, self._depth, debug_style=debug_style))
        if update.clear_eol:
            self._writer.erase_eol()
        self._cursor = (update.start_x + update.width, update.y)
        self._resync_margin(update.y)

    def _write_line_onto_new_row(self, line: Line, y: int, debug_style: str | None) -> None:
        """Write a full line onto row `y`, which must be created by moving down from row y-1 (or be the origin row)."""

        if y > 0:
            self._move(self._cursor[0], y - 1)
            self._writer.crlf()
            self._cursor = (0, y)
        else:
            self._move(0, 0)
        self._writer.text(render_cells(line.cells, self._depth, debug_style=debug_style))
        self._cursor = (line.width, y)
        self._resync_margin(y)

    def _handle_resize(self) -> None:
        self._term_height, self._term_width = self._tty.get_size()
        # Erase and forget the live region; redrawn from scratch by the caller's next frame. Committed content above
        # is the terminal's problem (native rewrap), as it should be.
        self._move(0, 0)
        self._writer.erase_down()
        self._frame = EMPTY_FRAME

    def take_resized(self) -> bool:
        """
        Return whether the terminal was resized since last asked, absorbing the change.

        When true, the live region has been erased and forgotten - the caller should re-layout to the new size and
        present a fresh frame.
        """

        if not self._tty.take_resized():
            return False
        self._handle_resize()
        return True

    def present(self, frame: Frame) -> None:
        check.state(self._prepared)
        # The live region must fit the terminal: rows scrolled off the top would break relative cursor tracking. The
        # layout layer is responsible for producing frames that fit.
        check.arg(frame.height <= self._term_height)
        cx, cy = frame.cursor
        check.arg(0 <= cy <= max(frame.height - 1, 0) and cx >= 0)

        self.take_resized()

        diff = diff_frames(self._frame, frame)

        w = self._writer
        w.sync_start()
        debug_style = self._debug_style() if not diff.is_empty else None

        if not diff.is_empty:
            self._hide_cursor()

            for update in diff.line_updates:
                self._apply_update(update, debug_style)

            for i, line in enumerate(diff.appended):
                self._write_line_onto_new_row(line, diff.old_height + i, debug_style)

            if diff.shrink:
                self._move(0, diff.height)
                w.erase_down()

        self._move(min(cx, max(self._term_width - 1, 0)), cy)
        if frame.cursor_visible:
            self._show_cursor()
        else:
            self._hide_cursor()

        w.sync_end()
        w.flush()

        self._frame = frame

    ##
    # Committing

    def commit(self, lines: ta.Sequence[Line]) -> None:
        """
        Freeze `lines` into the terminal's scrollback above the live region and re-anchor below them.

        The lines are drawn over the top rows of the live region (diffed against what is displayed there - identical
        content costs nothing), then the origin advances past them. The retained frame becomes whatever displayed rows
        remain below; the caller's next `present` re-fills the live region.
        """

        check.state(self._prepared)
        if not lines:
            return

        self.take_resized()

        w = self._writer
        w.sync_start()
        self._hide_cursor()

        old = self._frame
        n = len(lines)

        for i, line in enumerate(lines):
            if i < old.height:
                if (update := diff_lines(old.lines[i], line, i)) is not None:
                    self._apply_update(update, None)
            else:
                self._write_line_onto_new_row(line, i, None)

        # Advance the origin to the row after the last committed line, creating it if the commit consumed the whole
        # live region (which may scroll).
        if n < old.height:
            self._move(0, n)
            remaining = old.lines[n:]
        else:
            self._move(self._cursor[0], n - 1)
            w.crlf()
            remaining = ()

        # Rebase: everything below the committed lines shifts up by n in live-region coordinates.
        self._cursor = (0, 0)
        self._frame = Frame(remaining, cursor=(0, 0), cursor_visible=old.cursor_visible)

        w.sync_end()
        w.flush()

    ##
    # Misc

    def beep(self) -> None:
        self._writer.bell()
        self._writer.flush()
