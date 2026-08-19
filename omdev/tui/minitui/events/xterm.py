"""
The xterm input parser: characters in, typed events out.

Hardcoded xterm-compatible sequences plus runtime-negotiable extensions (SGR mouse, bracketed paste, kitty keyboard
protocol), per the modern consensus - terminfo is not consulted for input. Structural decoding is preferred over big
sequence tables: modifier parameters (CSI 1;5A etc.) are decoded arithmetically rather than enumerated.

The bare-ESC-vs-sequence ambiguity is resolved by a read timeout (the classic `ttimeoutlen`); bracketed paste
bodies bypass per-character parsing entirely.
"""
import typing as ta

from .keys import Key
from .keys import key_from_char
from .keys import key_text
from .parsing import EventParser
from .parsing import ParseGenerator
from .parsing import ParseTimeoutError
from .parsing import Read1
from .types import CursorPositionEvent
from .types import FocusEvent
from .types import KeyEvent
from .types import KittyFlagsEvent
from .types import ModeReportEvent
from .types import MouseEvent
from .types import MouseEventKind
from .types import PasteEvent
from .types import UnknownSequenceEvent


##


# The ESC byte is fundamentally overloaded on the legacy wire: the escape KEY, the intro of every escape sequence, and
# the alt prefix - and only elapsed time can tell them apart. Every program picks a timeout and thereby picks its
# failure mode: vim waits ~1000ms for key codes by default (sequence-favoring; the famous "delay after ESC"), neovim
# picks ttimeoutlen=50 (ESC-favoring; splits break on laggy links), tmux's escape-time (historically 500ms) makes it the
# classic splitter of sequences it misjudged. The kitty keyboard protocol deletes the ambiguity entirely - the escape
# key arrives as CSI 27u - so when the terminal confirms it (see `set_escape_unambiguous`) these timeouts stop applying
# and escape parsing waits indefinitely, like the CSI path always has.

# How long a lone ESC waits for a following byte before resolving as the escape key. The default sides with sequence
# integrity over ESC latency (closer to vim's ~1000ms than neovim's 50) - the sole cost is bare-ESC resolution latency
# (the visible mode-change lag vim users tune with ttimeoutlen), and on any kitty-confirmed terminal the timeout stops
# applying anyway. Injectable per-instance via `XtermEventParser(escape_timeout_s=...)` for laggy legacy links (mosh
# into tmux, bad wifi).
ESCAPE_TIMEOUT_S = .5

# How long an SS3 intro (ESC O) waits for its final byte. Kept at least as long as the bare-ESC timeout (vim waits
# ~1000ms here): the CSI path waits indefinitely for its final, and an SS3 tail delayed past a too-short window silently
# breaks F1-F4 while F5+ (CSI-form) keep working. The fallback meaning of a lone ESC O on the legacy wire is
# alt+shift+o, so that's what a timeout resolves to. Injectable per-instance like the escape timeout.
SS3_TIMEOUT_S = .5


_MAX_CSI_LENGTH = 64


_CSI_LETTER_BASES: ta.Mapping[str, str] = {
    'A': 'up',
    'B': 'down',
    'C': 'right',
    'D': 'left',
    'E': 'kp5',
    'F': 'end',
    'H': 'home',
    'P': 'f1',
    'Q': 'f2',
    'R': 'f3',
    'S': 'f4',
}

_CSI_TILDE_BASES: ta.Mapping[int, str] = {
    1: 'home',
    2: 'insert',
    3: 'delete',
    4: 'end',
    5: 'pageup',
    6: 'pagedown',
    7: 'home',
    8: 'end',
    11: 'f1',
    12: 'f2',
    13: 'f3',
    14: 'f4',
    15: 'f5',
    17: 'f6',
    18: 'f7',
    19: 'f8',
    20: 'f9',
    21: 'f10',
    23: 'f11',
    24: 'f12',
    29: 'menu',
}

_SS3_BASES: ta.Mapping[str, str] = {
    'A': 'up',
    'B': 'down',
    'C': 'right',
    'D': 'left',
    'F': 'end',
    'H': 'home',
    'P': 'f1',
    'Q': 'f2',
    'R': 'f3',
    'S': 'f4',
    'M': 'enter',
}

# Extended-key codepoints that aren't just unicode characters (shared by the kitty protocol and xterm's modifyOtherKeys;
# the full kitty functional-key ranges can land when something needs them).
_KITTY_SPECIAL_BASES: ta.Mapping[int, str] = {
    9: 'tab',
    13: 'enter',
    27: 'escape',
    32: 'space',
    127: 'backspace',
    # The kitty protocol's numeric functional-key codes (F1-F12) - sent instead of the legacy CSI/SS3 forms by
    # report-all-keys implementations.
    **{57364 + i: f'f{i + 1}' for i in range(12)},
}

# Legacy-wire control aliases. On the plain-bytes wire these chords ARE the named keys (ctrl+[ = 0x1b, ctrl+m = 0x0d,
# ctrl+i = 0x09) and modal editing leans on that - ctrl+[ is vim's escape. The extended protocols disambiguate them as
# ctrl+letter instead; fold them back so bindings behave identically on every negotiated wire. (ctrl+h and ctrl+j
# already agree across wires - 0x08/0x0a decode to ctrl+h/ctrl+j - so they are deliberately absent.)
_CTRL_ALIAS_BASES: ta.Mapping[int, str] = {
    91: 'escape',  # ctrl+[
    105: 'tab',    # ctrl+i
    109: 'enter',  # ctrl+m
}


def _decode_modifiers(m: int) -> dict[str, bool]:
    bits = max(m - 1, 0)
    return {
        'shift': bool(bits & 1),
        'alt': bool(bits & 2),
        'ctrl': bool(bits & 4),
        'super_': bool(bits & 8),
    }


def _int_params(params: str) -> list[int | None]:
    out: list[int | None] = []
    for part in params.split(';'):
        head = part.split(':')[0]
        out.append(int(head) if head.isdigit() else None)
    return out


class XtermEventParser(EventParser):
    def __init__(
            self,
            *,
            escape_timeout_s: float = ESCAPE_TIMEOUT_S,
            ss3_timeout_s: float = SS3_TIMEOUT_S,
    ) -> None:
        super().__init__()

        self._expect_cpr = False

        self.escape_timeout_s = escape_timeout_s
        self.ss3_timeout_s = max(ss3_timeout_s, escape_timeout_s)
        self._escape_unambiguous = False

    @property
    def escape_unambiguous(self) -> bool:
        return self._escape_unambiguous

    def set_escape_unambiguous(self, unambiguous: bool) -> None:
        """
        The terminal confirmed the kitty keyboard protocol's disambiguation is (in)active. When active, the escape
        key arrives as `CSI 27u`, so a bare ESC byte can only begin a sequence - escape parsing waits indefinitely
        (like the CSI path) and the escape key itself gains zero-latency delivery. Applies to reads begun after the
        change.
        """

        self._escape_unambiguous = unambiguous

    def _escape_wait_s(self) -> float | None:
        return None if self._escape_unambiguous else self.escape_timeout_s

    def _ss3_wait_s(self) -> float | None:
        return None if self._escape_unambiguous else self.ss3_timeout_s

    def expect_cursor_position_report(self) -> None:
        """
        Mark that a CPR query (DSR 6) was just sent.

        This disambiguates the response (CSI row;col R) from a modified F3 (CSI 1;m R); the flag clears on the next
        R-final sequence.
        """

        self._expect_cpr = True

    #

    def _emit_key(self, key: Key) -> None:
        self.emit(KeyEvent(key, text=key_text(key)))

    def _emit_char(self, c: str, *, alt: bool = False) -> None:
        self._emit_key(key_from_char(c, alt=alt))

    #

    def _run(self) -> ParseGenerator:
        while True:
            c = yield Read1()
            if c == '\x1b':
                yield from self._parse_escape()
            else:
                self._emit_char(c)

    def _parse_escape(self) -> ParseGenerator:
        while True:
            try:
                c = yield Read1(self._escape_wait_s())
            except ParseTimeoutError:
                self._emit_char('\x1b')
                return

            if c == '\x1b':
                # ESC ESC: resolve the first as the escape key, keep waiting on the second.
                self._emit_char('\x1b')
                continue

            if c == '[':
                yield from self._parse_csi()
            elif c == 'O':
                yield from self._parse_ss3()
            else:
                self._emit_char(c, alt=True)
            return

    def _parse_ss3(self) -> ParseGenerator:
        try:
            c = yield Read1(self._ss3_wait_s())
        except ParseTimeoutError:
            self._emit_key(Key('O', alt=True))
            return

        if (base := _SS3_BASES.get(c)) is not None:
            self._emit_key(Key(base))
        else:
            self.emit(UnknownSequenceEvent('\x1bO' + c))

    def _parse_csi(self) -> ParseGenerator:
        params = ''
        intermediates = ''
        while True:
            c = yield Read1()
            if '0' <= c <= '?':
                if intermediates:
                    # Parameter bytes after intermediates are malformed; bail.
                    self.emit(UnknownSequenceEvent('\x1b[' + params + intermediates + c))
                    return
                params += c
            elif ' ' <= c <= '/':
                intermediates += c
            elif '@' <= c <= '~':
                if c == '~' and params == '200' and not intermediates:
                    yield from self._parse_paste()
                else:
                    self._dispatch_csi(params, intermediates, c)
                return
            else:
                # A control character mid-sequence aborts it.
                self.emit(UnknownSequenceEvent('\x1b[' + params + intermediates + c))
                return
            if len(params) + len(intermediates) > _MAX_CSI_LENGTH:
                self.emit(UnknownSequenceEvent('\x1b[' + params + intermediates))
                return

    #

    def _dispatch_csi(self, params: str, intermediates: str, final: str) -> None:  # noqa: C901
        raw = '\x1b[' + params + intermediates + final

        if intermediates == '$' and final == 'y' and params.startswith('?'):
            ints = _int_params(params[1:])
            if len(ints) == 2 and ints[0] is not None and ints[1] is not None:
                self.emit(ModeReportEvent(ints[0], ints[1]))
            else:
                self.emit(UnknownSequenceEvent(raw))
            return

        if intermediates:
            self.emit(UnknownSequenceEvent(raw))
            return

        if params.startswith('<') and final in 'Mm':
            self._dispatch_mouse(params[1:], release=final == 'm', raw=raw)
            return

        if params.startswith('?'):
            if final == 'u':
                ints = _int_params(params[1:])
                if ints and ints[0] is not None:
                    self.emit(KittyFlagsEvent(ints[0]))
                    return
            self.emit(UnknownSequenceEvent(raw))
            return

        if final == 'I' and not params:
            self.emit(FocusEvent(True))
            return
        if final == 'O' and not params:
            self.emit(FocusEvent(False))
            return

        if final == 'Z':
            self._emit_key(Key('tab', shift=True))
            return

        ints = _int_params(params)

        if final == 'R':
            expect_cpr = self._expect_cpr
            self._expect_cpr = False
            if expect_cpr:
                if len(ints) == 2 and ints[0] is not None and ints[1] is not None:
                    self.emit(CursorPositionEvent(ints[1] - 1, ints[0] - 1))
                else:
                    self.emit(UnknownSequenceEvent(raw))
                return
            # Otherwise fall through: an unrequested R is a modified F3.

        if final == 'u':
            self._dispatch_kitty_key(params, raw=raw)
            return

        if final == '~' and len(ints) == 3 and ints[0] == 27:
            # xterm modifyOtherKeys (formatOtherKeys=0): CSI 27 ; modifier ; codepoint ~
            if ints[1] is not None and ints[2] is not None:
                self._emit_codepoint_key(ints[2], _decode_modifiers(ints[1]), raw=raw)
            else:
                self.emit(UnknownSequenceEvent(raw))
            return

        if final == '~':
            if ints and ints[0] is not None and (base := _CSI_TILDE_BASES.get(ints[0])) is not None:
                mods = _decode_modifiers(ints[1]) if len(ints) > 1 and ints[1] is not None else {}
                self._emit_key(Key(base, **mods))
            else:
                self.emit(UnknownSequenceEvent(raw))
            return

        if (base := _CSI_LETTER_BASES.get(final)) is not None:
            mods = _decode_modifiers(ints[1]) if len(ints) > 1 and ints[1] is not None else {}
            self._emit_key(Key(base, **mods))
            return

        self.emit(UnknownSequenceEvent(raw))

    def _dispatch_mouse(self, params: str, *, release: bool, raw: str) -> None:
        ints = _int_params(params)
        if len(ints) != 3 or any(i is None for i in ints):
            self.emit(UnknownSequenceEvent(raw))
            return
        b, px, py = ta.cast('list[int]', ints)

        mods = {
            'shift': bool(b & 4),
            'alt': bool(b & 8),
            'ctrl': bool(b & 16),
        }

        if b & 64:
            kind = (
                MouseEventKind.SCROLL_UP,
                MouseEventKind.SCROLL_DOWN,
                MouseEventKind.SCROLL_LEFT,
                MouseEventKind.SCROLL_RIGHT,
            )[b & 3]
            button = 0
        else:
            button = b & 3
            if b & 32:
                kind = MouseEventKind.MOVE
            elif release:
                kind = MouseEventKind.UP
            else:
                kind = MouseEventKind.DOWN

        self.emit(MouseEvent(
            kind,
            px - 1,
            py - 1,
            button=button,
            **mods,
        ))

    def _dispatch_kitty_key(self, params: str, *, raw: str) -> None:
        parts = params.split(';')
        code_part = parts[0].split(':')[0]
        if not code_part.isdigit():
            self.emit(UnknownSequenceEvent(raw))
            return
        code = int(code_part)

        mods: dict[str, bool] = {}
        if len(parts) > 1:
            mod_fields = parts[1].split(':')
            if mod_fields[0].isdigit():
                mods = _decode_modifiers(int(mod_fields[0]))
            if len(mod_fields) > 1 and mod_fields[1] == '3':
                return  # key release - ignored

        self._emit_codepoint_key(code, mods, raw=raw)

    def _emit_codepoint_key(self, code: int, mods: dict[str, bool], *, raw: str) -> None:
        """Shared by the kitty protocol and modifyOtherKeys: a unicode codepoint plus modifier flags."""

        if (base := _KITTY_SPECIAL_BASES.get(code)) is not None:
            # Named keys keep explicit shift; a shifted printable would already be its shifted character.
            self._emit_key(Key(base, **mods))
            return

        if (
            mods.get('ctrl') and
            not mods.get('shift') and
            not mods.get('super_') and
            (base := _CTRL_ALIAS_BASES.get(code)) is not None
        ):
            # The ctrl folds into the named key exactly as the legacy wire would have reported it; alt survives.
            self._emit_key(Key(base, alt=mods.get('alt', False)))
            return

        if 0 < code < 0x110000 and (c := chr(code)).isprintable():
            if mods.pop('shift', False):
                c = c.upper()
            self._emit_key(Key(c if c != ' ' else 'space', **mods))
            return

        if 0 < code < 0x20:
            # A modified control character (modifyOtherKeys reports e.g. ctrl+enter-with-shift this way too).
            self._emit_key(key_from_char(chr(code), alt=mods.get('alt', False)))
            return

        self.emit(UnknownSequenceEvent(raw))

    #

    def _parse_paste(self) -> ParseGenerator:
        chunks: list[str] = []
        while True:
            c = yield Read1()
            chunks.append(c)
            # The terminator is ESC[201~; only do the (cheap, bounded) tail check when a '~' arrives.
            if c == '~' and len(chunks) >= 6 and ''.join(chunks[-6:]) == '\x1b[201~':
                text = ''.join(chunks[:-6])
                text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\x00', '')
                self.emit(PasteEvent(text))
                return
