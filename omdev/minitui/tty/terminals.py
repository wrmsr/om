"""
Tty plumbing: fds, raw mode, size, resize signal.

`Tty` owns the file descriptors and the termios state dance; it knows nothing about escape sequences or frames. Signal
handling note: SIGWINCH installation is inherently process-global - the previous handler is saved on install and
restored on `restore()`, pyrepl-style.
"""
import fcntl
import os
import signal
import struct
import termios
import typing as ta

from omcore import check
from omcore.term.termstate import TermState
from omcore.term.termstate import get_term_state
from omcore.term.termstate import set_term_state


##


class Tty:
    def __init__(
            self,
            *,
            input_fd: int = 0,
            output_fd: int = 1,
    ) -> None:
        super().__init__()

        self._input_fd = input_fd
        self._output_fd = output_fd

        self._saved_state: TermState | None = None
        self._saved_sigwinch: ta.Any = None
        self._resized = False

    @property
    def input_fd(self) -> int:
        return self._input_fd

    @property
    def output_fd(self) -> int:
        return self._output_fd

    #

    def write_bytes(self, data: bytes) -> None:
        pos = 0
        while pos < len(data):
            pos += os.write(self._output_fd, data[pos:])

    #

    def get_size(self) -> tuple[int, int]:
        """Return (height, width) in character cells."""

        try:
            raw = fcntl.ioctl(self._input_fd, termios.TIOCGWINSZ, b'\x00' * 8)
        except OSError:
            return 25, 80
        height, width = struct.unpack('hhhh', raw)[:2]
        if not height:
            return 25, 80
        return height, width

    #

    def enter_raw(self, *, keep_signals: bool = True) -> None:
        """
        Put the input fd into raw-ish mode: no echo, no canonical buffering, no flow control, no output processing.

        With `keep_signals` (the default) ISIG stays on, so ctrl-c/ctrl-z still raise/suspend - the app decides whether
        to take those over later by rebinding at the signal level.
        """

        check.state(self._saved_state is None)
        self._saved_state = get_term_state(self._input_fd)

        raw = self._saved_state.copy()
        # ICRNL et al must go too: otherwise the Enter key's '\r' arrives as '\n' (ctrl+j). (pyrepl leaves them set and
        # instead binds both ctrl+j and ctrl+m to accept - we want the distinction.)
        raw.iflag &= ~(termios.INPCK | termios.ISTRIP | termios.IXON | termios.ICRNL | termios.INLCR | termios.IGNCR)
        raw.oflag &= ~termios.OPOST
        raw.cflag &= ~(termios.CSIZE | termios.PARENB)
        raw.cflag |= termios.CS8
        raw.iflag |= termios.BRKINT
        raw.lflag &= ~(termios.ICANON | termios.ECHO | termios.IEXTEN)
        if keep_signals:
            raw.lflag |= termios.ISIG
        else:
            raw.lflag &= ~termios.ISIG
        raw.cc[termios.VMIN] = 1  # type: ignore[call-overload]
        raw.cc[termios.VTIME] = 0  # type: ignore[call-overload]
        set_term_state(self._input_fd, raw, termios.TCSADRAIN)

    def restore(self) -> None:
        if (saved := self._saved_state) is not None:
            self._saved_state = None
            set_term_state(self._input_fd, saved, termios.TCSADRAIN)

        if self._saved_sigwinch is not None:
            try:
                signal.signal(signal.SIGWINCH, self._saved_sigwinch)
            except ValueError:
                pass  # not the main thread
            self._saved_sigwinch = None

    def probe_foreground(self) -> bool:
        """
        A no-op termios round trip: from the foreground it succeeds; from a job continued with `bg` it either stops us
        again (SIGTTOU's default action) or fails outright - so a resume path learns it may not touch the terminal
        before writing escape sequences over the shell's screen.
        """

        try:
            set_term_state(self._input_fd, get_term_state(self._input_fd))
        except (termios.error, OSError):
            return False
        return True

    #

    def watch_resize(self) -> None:
        check.state(self._saved_sigwinch is None)

        def handler(signum: int, frame: ta.Any) -> None:
            self._resized = True

        self._saved_sigwinch = signal.signal(signal.SIGWINCH, handler)

    def mark_resized(self) -> None:
        """For drivers that own signal handling themselves (asyncio's add_signal_handler replaces ours)."""

        self._resized = True

    def take_resized(self) -> bool:
        """Return whether a resize happened since the last call, clearing the flag."""

        resized = self._resized
        self._resized = False
        return resized
