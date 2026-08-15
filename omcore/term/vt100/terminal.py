"""
A small vt100/xterm terminal emulator, primarily serving as a test oracle for terminal-rendering code: feed it the
actual bytes a renderer emits and assert on the resulting screen, cursor, and - crucially - scrollback.

Deliberately modeled behaviors (the ones renderers depend on):
 - Scrolling: LF ('index') on the bottom row scrolls the screen and pushes the top row into captured scrollback.
 - Autowrap (DECAWM, ``CSI ? 7 h/l``) with proper *deferred* wrap: writing the last column sets a wrap-pending flag
   rather than moving the cursor; with autowrap off the cursor pins and further writes overwrite the last cell.
 - Cursor visibility (DECTCEM, ``CSI ? 25 h/l``).
 - SGR attributes and colors, including 256-indexed (``38;5;n``) and truecolor (``38;2;r;g;b``) forms, stored
   structurally on cells.

Deliberately unmodeled (so far): scroll regions, alt screen, character sets, bce (erases always write plain blank
cells), resize/reflow, OSC handling beyond swallowing.
"""
import dataclasses as dc
import typing as ta

from ...lite.check import check


# None means the terminal default. Otherwise ('named', n), ('idx', n), or ('rgb', r, g, b).
CellColor: ta.TypeAlias = tuple[str, int] | tuple[str, int, int, int] | None


##


@dc.dataclass(frozen=True)
class Cell:
    """One character cell and its graphic attributes."""

    char: str = ' '

    fg: CellColor = None
    bg: CellColor = None

    bold: bool = False
    dim: bool = False
    italic: bool = False
    underline: bool = False
    blink: bool = False
    reverse: bool = False
    strike: bool = False
    hidden: bool = False


BLANK_CELL = Cell()


##


class Vt100Terminal:
    def __init__(
            self,
            rows: int = 24,
            cols: int = 80,
            *,
            max_scrollback: int = 10_000,
    ) -> None:
        super().__init__()

        check.arg(rows > 0 and cols > 0)

        self._rows = rows
        self._cols = cols
        self._max_scrollback = max_scrollback

        self._screen: list[list[Cell]] = [self._blank_row() for _ in range(rows)]
        self._scrollback: list[list[Cell]] = []

        self._cursor_row = 0
        self._cursor_col = 0
        self._wrap_pending = False

        self._attrs = BLANK_CELL

        self._autowrap = True
        self._cursor_visible = True
        self._bells = 0

        self._state: ta.Literal['normal', 'esc', 'csi', 'osc'] = 'normal'
        self._escape_buffer: list[str] = []

    def _blank_row(self) -> list[Cell]:
        return [BLANK_CELL] * self._cols

    ##
    # Introspection

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def cursor_row(self) -> int:
        return self._cursor_row

    @property
    def cursor_col(self) -> int:
        return self._cursor_col

    @property
    def cursor_visible(self) -> bool:
        return self._cursor_visible

    @property
    def autowrap(self) -> bool:
        return self._autowrap

    @property
    def bells(self) -> int:
        return self._bells

    def cell(self, row: int, col: int) -> Cell:
        return self._screen[row][col]

    @staticmethod
    def _row_text(row: ta.Sequence[Cell], *, no_rstrip: bool = False) -> str:
        s = ''.join(cell.char for cell in row)
        if not no_rstrip:
            s = s.rstrip()
        return s

    def screen_lines(self, *, no_rstrip: bool = False) -> list[str]:
        return [self._row_text(row, no_rstrip=no_rstrip) for row in self._screen]

    def scrollback_lines(self, *, no_rstrip: bool = False) -> list[str]:
        return [self._row_text(row, no_rstrip=no_rstrip) for row in self._scrollback]

    def all_lines(self, *, no_rstrip: bool = False) -> list[str]:
        """Scrollback plus screen - the terminal's full visible history."""

        return [
            *self.scrollback_lines(no_rstrip=no_rstrip),
            *self.screen_lines(no_rstrip=no_rstrip),
        ]

    def get_screen_as_strings(self) -> list[str]:
        """Return a list of strings representing each row (ignoring attributes)."""

        return self.screen_lines(no_rstrip=True)

    ##
    # Cursor and scrolling primitives

    def _clamp_cursor(self) -> None:
        self._cursor_row = min(max(self._cursor_row, 0), self._rows - 1)
        self._cursor_col = min(max(self._cursor_col, 0), self._cols - 1)

    def _scroll_up(self) -> None:
        self._scrollback.append(self._screen.pop(0))
        self._screen.append(self._blank_row())
        if len(self._scrollback) > self._max_scrollback:
            del self._scrollback[: len(self._scrollback) - self._max_scrollback]

    def _index(self) -> None:
        """LF: move down one row, scrolling (into scrollback) at the bottom. Column is preserved."""

        if self._cursor_row >= self._rows - 1:
            self._scroll_up()
        else:
            self._cursor_row += 1

    ##
    # Character input

    def _put_char(self, ch: str) -> None:
        if self._wrap_pending:
            # Deferred autowrap: the previous write filled the last column; this one wraps first.
            self._wrap_pending = False
            self._cursor_col = 0
            self._index()

        self._screen[self._cursor_row][self._cursor_col] = dc.replace(self._attrs, char=ch)

        if self._cursor_col >= self._cols - 1:
            if self._autowrap:
                self._wrap_pending = True
            # else: pinned - further writes overwrite the last cell.
        else:
            self._cursor_col += 1

    ##
    # Escape sequence dispatch

    def _dispatch_csi(self, body: str) -> None:
        if not body:
            return

        final = body[-1]
        params_str = body[:-1]

        private = params_str.startswith('?')
        if private:
            params_str = params_str[1:]

        params: list[int | None] = []
        if params_str:
            for part in params_str.split(';'):
                params.append(int(part) if part.isdigit() else None)

        def param(i: int, default: int) -> int:
            if i < len(params) and params[i] is not None:
                return check.not_none(params[i])
            return default

        if private:
            if final in 'hl':
                enabled = final == 'h'
                for p in params:
                    if p == 7:
                        self._autowrap = enabled
                        if not enabled:
                            self._wrap_pending = False
                    elif p == 25:
                        self._cursor_visible = enabled
                    # Other private modes (2004, 2026, 1049, ...) are ignored.
            return

        if final in 'ABCD':
            n = max(param(0, 1), 1)
            self._wrap_pending = False
            if final == 'A':
                self._cursor_row -= n
            elif final == 'B':
                self._cursor_row += n
            elif final == 'C':
                self._cursor_col += n
            else:
                self._cursor_col -= n
            self._clamp_cursor()

        elif final in 'Hf':
            self._wrap_pending = False
            self._cursor_row = param(0, 1) - 1
            self._cursor_col = param(1, 1) - 1
            self._clamp_cursor()

        elif final == 'G':
            self._wrap_pending = False
            self._cursor_col = param(0, 1) - 1
            self._clamp_cursor()

        elif final == 'd':
            self._wrap_pending = False
            self._cursor_row = param(0, 1) - 1
            self._clamp_cursor()

        elif final == 'J':
            self._erase_display(param(0, 0))

        elif final == 'K':
            self._erase_line(param(0, 0))

        elif final == 'm':
            self._select_graphic_rendition([p if p is not None else 0 for p in params] or [0])

    def _erase_display(self, mode: int) -> None:
        if mode == 0:
            self._erase_line(0)
            for r in range(self._cursor_row + 1, self._rows):
                self._screen[r] = self._blank_row()
        elif mode == 1:
            self._erase_line(1)
            for r in range(self._cursor_row):
                self._screen[r] = self._blank_row()
        elif mode in (2, 3):
            for r in range(self._rows):
                self._screen[r] = self._blank_row()
            if mode == 3:
                self._scrollback.clear()

    def _erase_line(self, mode: int) -> None:
        row = self._screen[self._cursor_row]
        if mode == 0:
            for c in range(self._cursor_col, self._cols):
                row[c] = BLANK_CELL
        elif mode == 1:
            for c in range(self._cursor_col + 1):
                row[c] = BLANK_CELL
        elif mode == 2:
            self._screen[self._cursor_row] = self._blank_row()

    _SGR_ATTRS: ta.ClassVar[ta.Mapping[int, str]] = {
        1: 'bold',
        2: 'dim',
        3: 'italic',
        4: 'underline',
        5: 'blink',
        7: 'reverse',
        8: 'hidden',
        9: 'strike',
    }

    _SGR_ATTR_RESETS: ta.ClassVar[ta.Mapping[int, ta.Sequence[str]]] = {
        22: ('bold', 'dim'),
        23: ('italic',),
        24: ('underline',),
        25: ('blink',),
        27: ('reverse',),
        28: ('hidden',),
        29: ('strike',),
    }

    def _select_graphic_rendition(self, params: ta.Sequence[int]) -> None:
        base = self._attrs
        changes: dict[str, ta.Any] = {}
        i = 0
        while i < len(params):
            p = params[i]
            i += 1
            if p == 0:
                base = BLANK_CELL
                changes = {}
            elif p in self._SGR_ATTRS:
                changes[self._SGR_ATTRS[p]] = True
            elif p in self._SGR_ATTR_RESETS:
                for attr in self._SGR_ATTR_RESETS[p]:
                    changes[attr] = False
            elif 30 <= p <= 37:
                changes['fg'] = ('named', p - 30)
            elif 90 <= p <= 97:
                changes['fg'] = ('named', p - 90 + 8)
            elif p == 39:
                changes['fg'] = None
            elif 40 <= p <= 47:
                changes['bg'] = ('named', p - 40)
            elif 100 <= p <= 107:
                changes['bg'] = ('named', p - 100 + 8)
            elif p == 49:
                changes['bg'] = None
            elif p in (38, 48):
                key = 'fg' if p == 38 else 'bg'
                if i < len(params) and params[i] == 5 and i + 1 < len(params):
                    changes[key] = ('idx', params[i + 1])
                    i += 2
                elif i < len(params) and params[i] == 2 and i + 3 < len(params):
                    changes[key] = ('rgb', params[i + 1], params[i + 2], params[i + 3])
                    i += 4
                else:
                    break  # malformed extended color; drop the rest
        self._attrs = dc.replace(base, **changes) if changes else base

    ##
    # Parsing

    def feed(self, data: str | bytes) -> None:
        if isinstance(data, bytes):
            data = data.decode('utf-8', 'replace')
        for c in data:
            self.parse_byte(c)

    def parse_byte(self, byte: int | str) -> None:
        """Parse a single byte of input (as an integer or a single-character string)."""

        if isinstance(byte, int):
            byte = chr(byte)

        if self._state == 'normal':
            if byte == '\x1b':
                self._state = 'esc'
                self._escape_buffer = []
            elif byte == '\r':
                self._cursor_col = 0
                self._wrap_pending = False
            elif byte == '\n':
                self._index()
                self._wrap_pending = False
            elif byte == '\b':
                self._cursor_col = max(self._cursor_col - 1, 0)
                self._wrap_pending = False
            elif byte == '\t':
                self._cursor_col = min((self._cursor_col // 8 + 1) * 8, self._cols - 1)
                self._wrap_pending = False
            elif byte == '\x07':
                self._bells += 1
            elif byte >= ' ' and byte != '\x7f':
                self._put_char(byte)
            # Other control characters are ignored.

        elif self._state == 'esc':
            if byte == '[':
                self._state = 'csi'
                self._escape_buffer = []
            elif byte == ']':
                self._state = 'osc'
                self._escape_buffer = []
            else:
                # Two-character escapes: only RI (reverse index) would matter for renderers using hardware scroll-up,
                # which ours don't yet. Swallow and return to ground.
                self._state = 'normal'

        elif self._state == 'csi':
            # Parameter bytes 0x30-0x3f and intermediate bytes 0x20-0x2f accumulate; a final byte 0x40-0x7e ends the
            # sequence.
            if '\x40' <= byte <= '\x7e':
                self._escape_buffer.append(byte)
                body = ''.join(self._escape_buffer)
                self._state = 'normal'
                self._escape_buffer = []
                self._dispatch_csi(body)
            elif ' ' <= byte <= '?':
                self._escape_buffer.append(byte)
            else:
                # Aborted sequence (control char inside CSI, etc.) - bail to ground.
                self._state = 'normal'
                self._escape_buffer = []

        elif self._state == 'osc':
            # Swallow until BEL or ST (ESC \); we don't emit OSC, but be robust to it.
            if byte == '\x07':
                self._state = 'normal'
                self._escape_buffer = []
            elif byte == '\\' and self._escape_buffer and self._escape_buffer[-1] == '\x1b':
                self._state = 'normal'
                self._escape_buffer = []
            else:
                self._escape_buffer.append(byte)
