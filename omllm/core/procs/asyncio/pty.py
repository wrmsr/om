"""
Pseudo-terminal helpers. A pty is a single bidirectional char device: the child's stdin/stdout/stderr are the slave,
and the master is both the child's output (read) and its input (write) - so there is no separate stderr, and output
is one interleaved stream. Winsize changes on the master are delivered to the child's foreground group as SIGWINCH.
"""
import fcntl
import os
import struct
import termios
import typing as ta


##


# The pty output stream is presented in the spool under this fd number (a tty has no separate stderr).
PTY_OUTPUT_FD: ta.Final[int] = 1


class Winsize(ta.NamedTuple):
    rows: int
    cols: int


def open_pty() -> tuple[int, int]:
    """Returns (master, slave). The master is set non-inheritable; the slave is passed to the child."""

    master, slave = os.openpty()
    os.set_inheritable(master, False)
    os.set_inheritable(slave, True)
    return master, slave


def set_winsize(fd: int, rows: int, cols: int) -> None:
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))


def get_winsize(fd: int) -> Winsize:
    packed = fcntl.ioctl(fd, termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0))
    rows, cols, _, _ = struct.unpack('HHHH', packed)
    return Winsize(rows, cols)
