"""
A terminal reduced to lines: what turns the text a process writes to a pty into `TerminalOutput` lines. Deliberately not
an emulator - there is no screen, and a line once finished is never revisited - but enough of one for programs which
only ever write forward: SGR styling is kept, the carriage return, backspace, tab and in-line cursor and erase
sequences a progress bar rewrites its line with are honored, and every other control sequence is dropped. A program
which takes the screen over (the alternate screen: an editor, a pager) is beyond it, and is reported rather than
rendered.

Text in, lines out, nothing else: no process, no IO, no clock. Each line comes out styled from the plain style on, so
it renders on its own whatever the lines before it left set.
"""
import re
import typing as ta

from omcore import check
from omcore.term import styled as tst
from omcore.text import styled as st


##


# Every character is covered by one of these, so a match never fails. A lone escape falls to `ctl`: either the start of
# a sequence the feed cut short, or noise.
_TOKEN_PAT = re.compile(
    r'(?P<text>[^\x00-\x1f\x7f-\x9f]+)'
    r'|(?P<csi>\x1b\[(?P<params>[0-?]*)[ -/]*(?P<final>[@-~]))'
    r'|(?P<osc>\x1b\][^\x07\x1b]*(?:\x07|\x1b\\))'
    r'|(?P<string>\x1b[PX^_][^\x1b]*\x1b\\)'
    r'|(?P<esc>\x1b(?:[ -/]+[0-~]|[0-OQ-WYZ\\`-~]))'
    r'|(?P<ctl>[\x00-\x1f\x7f-\x9f])',
)

# What a sequence cut short by the end of a feed looks like: held until the rest of it arrives.
_INCOMPLETE_PAT = re.compile(
    r'\x1b(?:'
    r'\[[0-?]*[ -/]*'
    r'|\][^\x07\x1b]*\x1b?'
    r'|[PX^_][^\x1b]*\x1b?'
    r'|[ -/]*'
    r')',
)

_ALT_SCREEN_MODES: ta.AbstractSet[str] = frozenset(['47', '1047', '1049'])


class LineTerminal:
    def __init__(
            self,
            *,
            tab_width: int = 8,
            max_line_chars: int = 8192,
            max_pending_chars: int = 4096,
    ) -> None:
        """
        A line longer than `max_line_chars` is broken there; an unfinished control sequence longer than
        `max_pending_chars` is taken for text after all.
        """

        super().__init__()

        check.arg(tab_width > 0)
        check.arg(max_line_chars > 0)

        self._tab_width = tab_width
        self._max_line_chars = max_line_chars
        self._max_pending_chars = max_pending_chars

        # The line being written, a cell per character - parallel lists, so a run is written or erased in one step.
        self._chars: list[str] = []
        self._styles: list[st.ResolvedStyle] = []
        self._line_is_styled = False
        self._cursor = 0

        self._style = st.PLAIN_STYLE

        # Output repeats itself: the same few escapes select the same few styles, line after line. Keyed by identity,
        # each entry holding the style its key is the id of.
        self._sgr_styles: dict[tuple[int, str], tuple[st.ResolvedStyle, st.ResolvedStyle]] = {}
        self._style_sgrs: dict[int, tuple[st.ResolvedStyle, str]] = {}

        self._pending = ''
        self._in_alt_screen = False

    @property
    def in_alt_screen(self) -> bool:
        """
        Whether the process has switched to the alternate screen - a full-screen program, whose output is discarded
        while it lasts: there is no screen for it to draw on.
        """

        return self._in_alt_screen

    @property
    def has_partial_line(self) -> bool:
        return bool(self._chars)

    ##
    # The line

    def _pad_to_cursor(self) -> None:
        if (n := self._cursor - len(self._chars)) > 0:
            self._chars.extend(' ' * n)
            self._styles.extend([st.PLAIN_STYLE] * n)

    def _write(self, text: str, lines: list[str]) -> None:
        if self._in_alt_screen:
            return

        pos = 0
        while pos < len(text):
            # Whatever does not fit the line breaks it: an endless line is still output a frontend has to hold.
            room = self._max_line_chars - self._cursor
            if room <= 0:
                lines.append(self._take_line())
                continue
            part = text[pos:pos + room]
            pos += len(part)

            self._pad_to_cursor()
            end = self._cursor + len(part)
            self._chars[self._cursor:end] = part
            self._styles[self._cursor:end] = [self._style] * len(part)
            self._cursor = end
            if self._style is not st.PLAIN_STYLE:
                self._line_is_styled = True

    def _style_sgr(self, style: st.ResolvedStyle) -> str:
        try:
            return self._style_sgrs[id(style)][1]
        except KeyError:
            pass
        if len(self._style_sgrs) >= self._MAX_CACHED_STYLES:
            self._style_sgrs.clear()
        sgr = tst.style_sgr(style)
        self._style_sgrs[id(style)] = (style, sgr)
        return sgr

    def _encode_line(self, *, is_finished: bool) -> str:
        chars = self._chars
        styles = self._styles

        # Trailing plain blanks on a finished line are what an erased or overwritten tail leaves behind. On one still
        # being written they are the space after a prompt.
        n = len(chars)
        if is_finished:
            while n and chars[n - 1] == ' ' and styles[n - 1] is st.PLAIN_STYLE:
                n -= 1

        if not self._line_is_styled:
            return ''.join(chars[:n])

        # Each run is established from scratch and the line ends reset: it stands on its own.
        parts: list[str] = []
        active = ''
        i = 0
        while i < n:
            style = styles[i]
            j = i + 1
            while j < n and styles[j] is style:
                j += 1
            if (sgr := self._style_sgr(style)) != active:
                parts.append(sgr or tst.RESET_SGR)
                active = sgr
            parts.append(''.join(chars[i:j]))
            i = j
        if active:
            parts.append(tst.RESET_SGR)
        return ''.join(parts)

    def _take_line(self, *, is_finished: bool = True) -> str:
        line = self._encode_line(is_finished=is_finished)
        self._chars = []
        self._styles = []
        self._line_is_styled = False
        self._cursor = 0
        return line

    def _move_cursor(self, cursor: int) -> None:
        self._cursor = min(max(cursor, 0), self._max_line_chars)

    def _erase_in_line(self, mode: int) -> None:
        if mode == 0:
            del self._chars[self._cursor:]
            del self._styles[self._cursor:]
        elif mode == 1:
            n = min(self._cursor + 1, len(self._chars))
            self._chars[:n] = ' ' * n
            self._styles[:n] = [st.PLAIN_STYLE] * n
        elif mode == 2:
            self._chars = []
            self._styles = []

    ##
    # Control sequences

    _MAX_CACHED_STYLES: ta.ClassVar[int] = 256

    def _select_graphic_rendition(self, params: str) -> None:
        key = (id(self._style), params)
        try:
            self._style = self._sgr_styles[key][1]
            return
        except KeyError:
            pass

        if (ps := self._parse_params(params)) is None:
            return
        style = tst.apply_sgr_params(self._style, ps)
        if style.is_plain:
            style = st.PLAIN_STYLE  # the one plain style, so that being plain is an identity check

        if len(self._sgr_styles) >= self._MAX_CACHED_STYLES:
            self._sgr_styles.clear()
        self._sgr_styles[key] = (self._style, style)
        self._style = style

    @staticmethod
    def _parse_params(params: str) -> list[int] | None:
        """The numeric parameters of a control sequence, defaults as 0; None for a private or malformed one."""

        out: list[int] = []
        for part in params.replace(':', ';').split(';'):
            if not part:
                out.append(0)
            elif part.isdigit():
                out.append(int(part))
            else:
                return None
        return out

    def _handle_csi(self, params: str, final: str) -> None:
        if final in 'hl' and params.startswith('?'):
            if any(mode in _ALT_SCREEN_MODES for mode in params[1:].split(';')):
                self._in_alt_screen = final == 'h'
            return

        if final == 'm':
            self._select_graphic_rendition(params)
            return

        if self._in_alt_screen or (ps := self._parse_params(params)) is None:
            return

        n = ps[0]
        if final == 'K':
            self._erase_in_line(n)
        elif final == 'C':
            self._move_cursor(self._cursor + max(n, 1))
        elif final == 'D':
            self._move_cursor(self._cursor - max(n, 1))
        elif final == 'G':
            self._move_cursor(max(n, 1) - 1)

    def _handle_control(self, c: str, lines: list[str]) -> None:
        if self._in_alt_screen:
            return

        if c == '\n':
            lines.append(self._take_line())
        elif c == '\r':
            self._cursor = 0
        elif c == '\b':
            self._move_cursor(self._cursor - 1)
        elif c == '\t':
            self._move_cursor((self._cursor // self._tab_width + 1) * self._tab_width)

    ##

    def feed(self, text: str) -> list[str]:
        """The lines `text` finished, in order, without their newlines. What it left unfinished stays, for more."""

        if self._pending:
            text = self._pending + text
            self._pending = ''

        lines: list[str] = []
        pos = 0
        while pos < len(text):
            m = check.not_none(_TOKEN_PAT.match(text, pos))
            kind = m.lastgroup

            if kind == 'text':
                self._write(m.group(), lines)

            elif kind == 'csi':
                self._handle_csi(m.group('params'), m.group('final'))

            elif kind == 'ctl':
                if (c := m.group()) == '\x1b':
                    rest = text[pos:]
                    if len(rest) <= self._max_pending_chars and _INCOMPLETE_PAT.fullmatch(rest) is not None:
                        self._pending = rest
                        break
                else:
                    self._handle_control(c, lines)

            # Everything else - an operating system command, a device control string, a charset selection - is dropped.

            pos = m.end()

        return lines

    def flush(self) -> str | None:
        """Take the line still being written, as far as it has got; None when there is none."""

        if not self._chars:
            return None
        return self._take_line(is_finished=False)
