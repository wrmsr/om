# PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
# --------------------------------------------
#
# 1. This LICENSE AGREEMENT is between the Python Software Foundation ("PSF"), and the Individual or Organization
# ("Licensee") accessing and otherwise using this software ("Python") in source or binary form and its associated
# documentation.
#
# 2. Subject to the terms and conditions of this License Agreement, PSF hereby grants Licensee a nonexclusive,
# royalty-free, world-wide license to reproduce, analyze, test, perform and/or display publicly, prepare derivative
# works, distribute, and otherwise use Python alone or in any derivative version, provided, however, that PSF's License
# Agreement and PSF's notice of copyright, i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
# 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017 Python Software Foundation; All Rights Reserved" are retained in Python
# alone or in any derivative version prepared by Licensee.
#
# 3. In the event Licensee prepares a derivative work that is based on or incorporates Python or any part thereof, and
# wants to make the derivative work available to others as provided herein, then Licensee hereby agrees to include in
# any such work a brief summary of the changes made to Python.
#
# 4. PSF is making Python available to Licensee on an "AS IS" basis.  PSF MAKES NO REPRESENTATIONS OR WARRANTIES,
# EXPRESS OR IMPLIED.  BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND DISCLAIMS ANY REPRESENTATION OR WARRANTY
# OF MERCHANTABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT INFRINGE ANY THIRD PARTY
# RIGHTS.
#
# 5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL
# DAMAGES OR LOSS AS A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON, OR ANY DERIVATIVE THEREOF, EVEN IF
# ADVISED OF THE POSSIBILITY THEREOF.
#
# 6. This License Agreement will automatically terminate upon a material breach of its terms and conditions.
#
# 7. Nothing in this License Agreement shall be deemed to create any relationship of agency, partnership, or joint
# venture between PSF and Licensee.  This License Agreement does not grant permission to use PSF trademarks or trade
# name in a trademark sense to endorse or promote products or services of Licensee, or any third party.
#
# 8. By copying, installing or otherwise using Python, Licensee agrees to be bound by the terms and conditions of this
# License Agreement.
# Derived from x/term/pyrepl/unix/console.py's capability loading and buffered write machinery (itself from cpython's
# _pyrepl). Notable changes: baud-rate tputs delay handling is dropped entirely; capabilities fall back to hardcoded
# xterm sequences when absent from terminfo rather than raising; buffering is bytes-level with one write per flush.
"""
Terminfo-driven escape emission with buffered output.

The writer is pure mechanism: named operations that append bytes to a buffer, and a flush. Movement *policy* (when to
use \\r\\n vs cuu, relative coordinate tracking) lives in the surfaces that drive it. Output capabilities come from our
pure-python terminfo, falling back to hardcoded xterm sequences for anything a terminfo entry lacks; sequences with no
terminfo names at all (synchronized output, bracketed paste, ...) are hardcoded, per the modern consensus.
"""
import typing as ta

from omcore.term import terminfo

from ..tty.terminals import Tty


##


# Fallbacks for capabilities missing from a terminfo entry - the ansi/xterm forms, matching terminfo's parametrized
# cap syntax (processed via tparm just like real entries).
_CAP_FALLBACKS: ta.Mapping[str, bytes] = {
    'bel': b'\x07',
    'civis': b'\x1b[?25l',
    'cnorm': b'\x1b[?25h',
    'cub': b'\x1b[%p1%dD',
    'cub1': b'\x08',
    'cuf': b'\x1b[%p1%dC',
    'cuf1': b'\x1b[C',
    'cuu': b'\x1b[%p1%dA',
    'cuu1': b'\x1b[A',
    'ed': b'\x1b[J',
    'el': b'\x1b[K',
    'rmam': b'\x1b[?7l',
    'smam': b'\x1b[?7h',
}

# No terminfo names exist for these.
_SYNC_START = b'\x1b[?2026h'
_SYNC_END = b'\x1b[?2026l'
_BRACKETED_PASTE_ON = b'\x1b[?2004h'
_BRACKETED_PASTE_OFF = b'\x1b[?2004l'
_KITTY_KEYS_PUSH = b'\x1b[>1u'
_KITTY_KEYS_POP = b'\x1b[<u'
_MOUSE_ON = b'\x1b[?1000h\x1b[?1006h'
_MOUSE_OFF = b'\x1b[?1006l\x1b[?1000l'


class TermWriter:
    def __init__(
            self,
            tty: Tty,
            *,
            term: str | None = None,
            encoding: str = 'utf-8',
    ) -> None:
        super().__init__()

        self._tty = tty
        self._encoding = encoding
        self._terminfo = terminfo.load_term_info(term)
        self._buffer = bytearray()

    def _cap(self, name: str) -> bytes | None:
        if (entry := self._terminfo.get(name)) is not None:
            return entry
        return _CAP_FALLBACKS.get(name)

    #

    def text(self, s: str) -> None:
        self._buffer.extend(s.encode(self._encoding, 'replace'))

    def raw(self, data: bytes) -> None:
        self._buffer.extend(data)

    def cap(self, name: str, *args: int) -> None:
        if (entry := self._cap(name)) is None:
            return
        self._buffer.extend(terminfo.tparm(entry, *args) if args else entry)

    def flush(self) -> None:
        if self._buffer:
            self._tty.write_bytes(bytes(self._buffer))
            self._buffer.clear()

    #

    def up(self, n: int) -> None:
        if n == 1:
            self.cap('cuu1')
        elif n > 1:
            self.cap('cuu', n)

    def right(self, n: int) -> None:
        if n == 1:
            self.cap('cuf1')
        elif n > 1:
            self.cap('cuf', n)

    def left(self, n: int) -> None:
        if n == 1:
            self.cap('cub1')
        elif n > 1:
            self.cap('cub', n)

    def cr(self) -> None:
        self.text('\r')

    def crlf(self, n: int = 1) -> None:
        # With OPOST off this is the literal pair: column 0, then down one row - scrolling the terminal if (and only
        # if) the cursor is on the bottom row. This, not cud, is how the live region grows; see the inline surface.
        self.text('\r\n' * n)

    def erase_eol(self) -> None:
        self.cap('el')

    def erase_down(self) -> None:
        self.cap('ed')

    def hide_cursor(self) -> None:
        self.cap('civis')

    def show_cursor(self) -> None:
        self.cap('cnorm')

    def autowrap(self, enabled: bool) -> None:  # noqa
        self.cap('smam' if enabled else 'rmam')

    def sync_start(self) -> None:
        self.raw(_SYNC_START)

    def sync_end(self) -> None:
        self.raw(_SYNC_END)

    def bracketed_paste(self, enabled: bool) -> None:  # noqa
        self.raw(_BRACKETED_PASTE_ON if enabled else _BRACKETED_PASTE_OFF)

    def kitty_keys(self, enabled: bool) -> None:  # noqa
        self.raw(_KITTY_KEYS_PUSH if enabled else _KITTY_KEYS_POP)

    def mouse_tracking(self, enabled: bool) -> None:  # noqa
        self.raw(_MOUSE_ON if enabled else _MOUSE_OFF)

    def bell(self) -> None:
        self.cap('bel')
