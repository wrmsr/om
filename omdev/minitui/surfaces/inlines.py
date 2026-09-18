"""
The inline surface: minitui's reason to exist.

The terminal viewport is [ ...native scrollback... | committed tail | LIVE REGION ]. The live region is the bottom rows
of our output: a retained `Frame`, diffed and redrawn in place. `commit()` freezes lines out of the top of the live
region into the terminal's own scrollback - immutable once emitted, visible after exit, tmux-native - and re-anchors the
live region below them. A message that finalizes exactly as displayed commits for zero bytes.

All cursor tracking is relative to the live region origin (row 0); there are no absolute coordinates anywhere in the
painting. Downward motion is always the literal '\\r\\n' pair - never cud - because only '\\r\\n' scrolls the terminal
when the cursor is on the bottom row, which is exactly how the live region grows and how commits push history upward.
Autowrap is disabled while active so a width-exact line can never desync the relative tracking.

The one absolute quantity kept on the side is the origin's terminal row, learned from the startup CPR and moved up by
every bottom-row line feed - solely so mouse reports, which are absolute, can be translated into frame rows.

The alt-screen excursion (`set_alt_screen`): the terminal's alternate screen saves the main screen and cursor on entry
and restores both on exit, so the live region and its relative tracking survive a fullscreen interlude untouched - a
browse mode over the same app draws with an `AltPainter` meanwhile, and nothing it draws propagates back. Commits are
impossible while in the excursion (they would land on the alt screen); the driver buffers them until the return.
"""
import typing as ta

from omcore import check
from omcore.term.styled import ColorDepth
from omcore.term.styled import detect_color_depth

from ..screens.cells import EMPTY_FRAME
from ..screens.cells import CursorXY
from ..screens.cells import Frame
from ..screens.cells import Line
from ..screens.cells import render_cells
from ..screens.diffs import LineUpdate
from ..screens.diffs import diff_frames
from ..screens.diffs import diff_lines
from ..tty.terminals import Tty
from .alts import AltPainter
from .base import Surface
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
            depth: ColorDepth | None = None,
            visualize_redraws: bool = False,
            kitty_keys: bool = False,
            mouse: bool = False,
    ) -> None:
        super().__init__()

        self._tty = tty if tty is not None else Tty()
        self._writer = TermWriter(self._tty, term=term)
        self._depth = depth if depth is not None else detect_color_depth()
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
        # Blind-optimistic until negotiated: unknown DECSETs are ignored by terminals that lack them.
        self._sync_output = True

        # The origin's terminal row, when known (see `frame_row`). None until the CPR answers, and again after a resize:
        # the terminal reflowed the main screen under us and the row is anyone's guess.
        self._origin_row: int | None = None

        # The alt-screen excursion: a painter while requested; the switch itself is written by the first present, so
        # entry and first paint share one synchronized-output bracket (no blank alt screen in between).
        self._alt: AltPainter | None = None
        self._alt_entered = False
        self._alt_entry_size: tuple[int, int] = (0, 0)

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
        """The currently-displayed (retained) live region frame - on the main screen, alt excursion or not."""

        return self._frame

    @property
    def alt_screen(self) -> bool:
        return self._alt is not None

    @property
    def origin_row(self) -> int | None:
        """The live region origin's terminal row, if known."""

        return self._origin_row

    def frame_row(self, terminal_row: int) -> int:
        """
        In the alt excursion the frame is the screen. Otherwise the live region sits at its tracked origin - or, when
        that is unknown (no CPR answer, or a resize since), is assumed to hug the bottom of the terminal, where it ends
        up once anything has scrolled.
        """

        if self._alt is not None:
            return terminal_row
        if (origin := self._origin_row) is None:
            origin = max(self._term_height - self._frame.height, 0)
        return terminal_row - origin

    ##
    # Lifecycle

    def prepare(self, *, defer_origin: bool = False) -> None:
        """
        Enter raw mode and establish the live region origin.

        By default the origin is column 0 of the current row (a bare CR - a shell's partial line gets overwritten). With
        `defer_origin`, nothing positional is written: the caller (a driver) sends a CPR query via `request_origin` and
        later calls `resolve_origin`/`resolve_origin_fallback` - which moves to a *fresh* line when the shell left the
        cursor mid-line, the polite behavior. No present/commit may happen in between.
        """

        check.state(not self._prepared)

        self._tty.enter_raw()
        self._tty.watch_resize()
        self._term_height, self._term_width = self._tty.get_size()

        w = self._writer
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
        if not defer_origin:
            w.cr()
        w.flush()

        self._frame = EMPTY_FRAME
        self._cursor = (0, 0)
        self._cursor_shown = True
        self._origin_row = None
        self._alt = None
        self._alt_entered = False
        self._prepared = True

    def set_sync_output(self, enabled: bool) -> None:
        self._sync_output = enabled

    def request_sync_output_report(self) -> None:
        """Send the DECRQM query for synchronized output; the answer arrives as a ModeReportEvent(2026, ...)."""

        w = self._writer
        w.sync_query()
        w.flush()

    def request_terminal_version(self) -> None:
        """Send the XTVERSION query; a tmux in front of us answers for itself (a TerminalVersionEvent)."""

        w = self._writer
        w.terminal_version_query()
        w.flush()

    def request_origin(self, parser: ta.Any) -> None:
        """Send a CPR query (DSR 6); `parser` is armed to recognize the response (expect_cursor_position_report)."""

        w = self._writer
        w.raw(b'\x1b[6n')
        w.flush()
        parser.expect_cursor_position_report()

    def resolve_origin(self, col: int, row: int | None = None) -> None:
        """
        The CPR answer arrived: start on a fresh line if the shell left the cursor mid-line. With the reported `row`,
        the origin's terminal row becomes known (a fresh line on the bottom row scrolls, and stays the bottom row).
        """

        w = self._writer
        if col > 0:
            w.crlf()
            if row is not None:
                row = min(row + 1, max(self._term_height - 1, 0))
        else:
            w.cr()  # col 0 already, but normalize defensively
        w.flush()
        self._cursor = (0, 0)
        self._origin_row = row

    def resolve_origin_fallback(self) -> None:
        """No CPR answer (unsupported terminal): fall back to the overwrite-in-place behavior."""

        w = self._writer
        w.cr()
        w.flush()
        self._cursor = (0, 0)
        self._origin_row = None

    def _leave(self) -> None:
        w = self._writer
        self._show_cursor()
        if self._mouse:
            w.mouse_tracking(False)
        if self._kitty_keys:
            w.modify_other_keys(False)
            w.kitty_keys(False)
        w.bracketed_paste(False)
        w.autowrap(True)
        w.flush()

        self._tty.restore()

    def restore(self) -> None:
        if not self._prepared:
            return
        self.set_alt_screen(False)
        self._prepared = False

        # Leave the shell on a fresh line below everything we drew.
        self._move(0, max(self._frame.height - 1, 0))
        self._crlf()
        self._leave()

    def suspend(self) -> None:
        """
        Leave application mode for a process stop. The live region is erased rather than left behind: it is transient
        by definition, and the shell's job-control chatter should land where it was, not below a stale copy. Committed
        content above is untouched. The driver re-establishes the origin on resume exactly as at startup.
        """

        if not self._prepared:
            return
        self.set_alt_screen(False)
        self._prepared = False

        self._move(0, 0)
        self._writer.erase_down()
        self._frame = EMPTY_FRAME
        self._leave()

    def resume(self) -> None:
        self.prepare(defer_origin=True)

    ##
    # The alt-screen excursion

    def set_alt_screen(self, enabled: bool) -> None:
        """
        Enter or leave the fullscreen excursion. Entry is idempotent and cheap: the screen switch itself happens with
        the first present. Leaving restores the main screen as it was (the terminal's doing) and re-marks a resize that
        happened meanwhile, so the owner's usual resize path erases and repaints the live region it can no longer trust.
        """

        check.state(self._prepared)
        if enabled == (self._alt is not None):
            return

        if enabled:
            self._alt = AltPainter(self._writer, depth=self._depth, cursor_shown=self._cursor_shown)
            self._alt_entered = False
            self._alt_entry_size = (self._term_height, self._term_width)
            return

        painter = check.not_none(self._alt)
        self._alt = None
        if self._alt_entered:
            self._alt_entered = False
            w = self._writer
            w.alt_screen(False)
            if not self._mouse:
                w.mouse_tracking(False)
            w.flush()
            self._cursor_shown = painter.cursor_shown  # one terminal-global mode, wherever it was last set

        if self._tty.take_resized() or (self._term_height, self._term_width) != self._alt_entry_size:
            self._tty.mark_resized()

    def _enter_alt(self, painter: AltPainter) -> None:
        w = self._writer
        if not self._mouse:
            w.mouse_tracking(True)  # the wheel is the point of browsing; the live region's setting returns on leave
        w.alt_screen(True)
        painter.clear()
        self._alt_entered = True

    def _present_alt(self, painter: AltPainter, frame: Frame) -> None:
        check.arg(frame.height <= self._term_height)

        w = self._writer
        if self._sync_output:
            w.sync_start()

        if not self._alt_entered:
            self._enter_alt(painter)

        painter.paint(frame, width=self._term_width)

        if self._sync_output:
            w.sync_end()
        w.flush()

    ##
    # Movement (relative to the live region origin)

    def _crlf(self, n: int = 1) -> None:
        """
        The literal pair, `n` times, from the current tracked row - the only thing that ever scrolls the terminal. Each
        line feed from the bottom row moves everything above it up one, the origin included; the caller then records the
        new cursor row. (A commit taller than the terminal legitimately drives the origin negative here: the rebase that
        follows brings it back onto the screen.)
        """

        self._writer.crlf(n)
        if (origin := self._origin_row) is not None:
            row = self._cursor[1]
            for _ in range(n):
                if origin + row >= self._term_height - 1:
                    origin -= 1
                row += 1
            self._origin_row = origin

    def _move(self, x: int, y: int) -> None:
        w = self._writer
        cx, cy = self._cursor
        if y < cy:
            w.up(cy - y)
        elif y > cy:
            self._crlf(y - cy)
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
        # With autowrap off the terminal pins the cursor at the last column, so a write reaching the right margin leaves
        # the physical cursor short of where naive width-addition says. A CR makes tracking exact again.
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
            self._crlf()
            self._cursor = (0, y)
        else:
            self._move(0, 0)
        self._writer.text(render_cells(line.cells, self._depth, debug_style=debug_style))
        self._cursor = (line.width, y)
        self._resync_margin(y)

    def _handle_resize(self) -> None:
        self._term_height, self._term_width = self._tty.get_size()
        # Erase and forget the live region; redrawn from scratch by the caller's next frame. Committed content above is
        # the terminal's problem (native rewrap), as it should be - and so is where our origin ended up.
        self._move(0, 0)
        self._writer.erase_down()
        self._frame = EMPTY_FRAME
        self._origin_row = None

    def take_resized(self) -> bool:
        """
        Return whether the terminal was resized since last asked, absorbing the change.

        When true, the live region has been erased and forgotten - the caller should re-layout to the new size and
        present a fresh frame. In the alt excursion the alt grid is cleared instead; the live region's turn comes on
        leaving.
        """

        if not self._tty.take_resized():
            return False
        if (painter := self._alt) is not None:
            self._term_height, self._term_width = self._tty.get_size()
            if self._alt_entered:
                painter.clear()
            return True
        self._handle_resize()
        return True

    def present(self, frame: Frame) -> None:
        check.state(self._prepared)

        self.take_resized()

        if (painter := self._alt) is not None:
            self._present_alt(painter, frame)
            return

        # The live region must fit the terminal: rows scrolled off the top would break relative cursor tracking. The
        # layout layer is responsible for producing frames that fit.
        check.arg(frame.height <= self._term_height)
        cx, cy = frame.cursor
        check.arg(0 <= cy <= max(frame.height - 1, 0) and cx >= 0)

        diff = diff_frames(self._frame, frame)

        w = self._writer
        if self._sync_output:
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

        if self._sync_output:
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
        check.state(self._alt is None)  # the alt screen is not scrollback; the driver holds commits until the return
        if not lines:
            return

        self.take_resized()

        w = self._writer
        if self._sync_output:
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

        # Advance the origin to the row after the last committed line, creating it if the commit consumed the whole live
        # region (which may scroll).
        if n < old.height:
            self._move(0, n)
            remaining = old.lines[n:]
        else:
            self._move(self._cursor[0], n - 1)
            self._crlf()
            remaining = ()

        # Rebase: everything below the committed lines shifts up by n in live-region coordinates - and the origin moves
        # down past them on the terminal (onto the bottom row at most: the tracking above already counted the scrolls).
        self._cursor = (0, 0)
        self._frame = Frame(remaining, cursor=(0, 0), cursor_visible=old.cursor_visible)
        if (origin := self._origin_row) is not None:
            self._origin_row = min(max(origin + n, 0), max(self._term_height - 1, 0))

        if self._sync_output:
            w.sync_end()
        w.flush()

    ##
    # Misc

    def beep(self) -> None:
        self._writer.bell()
        self._writer.flush()
