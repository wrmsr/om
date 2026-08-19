"""
Turning a spec's `Stdio` into file descriptors: which fds the child gets as 0/1/2, which ends we keep (and for what),
and which must be closed in the parent once the child exists. Pure fd plumbing, shared by every manager implementation.
"""
import os
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ..types.specs import ProcessStdio
from ..types.specs import PtyStdio
from ..types.specs import Stdio
from . import pty as _pty


##


def close_fds_quietly(fds: ta.Iterable[int]) -> None:
    for fd in fds:
        try:
            os.close(fd)
        except OSError:
            pass


@dc.dataclass(frozen=True, kw_only=True)
class StdioSetup:
    """
    The result of `setup_stdio`. Ownership: `child_fds` are closed in the parent right after the fork; `parent_fds` are
    all of ours (including `pty_master_fd` and the pty dups) and must each end up owned by a connection or closed.
    """

    # The child's 0/1/2 (-1 inherits ours).
    stdin_fd: int
    stdout_fd: int
    stderr_fd: int

    child_fds: ta.Sequence[int]
    parent_fds: ta.Sequence[int]

    # Our write end of the child's stdin, if any.
    stdin_w: int | None

    # (spool fd number, our read end) for each output stream.
    output_reads: ta.Sequence[tuple[int, int]]

    # The pty master control fd (kept by the handle for winsize / final close), if a pty was made.
    pty_master_fd: int | None = None

    @property
    def is_pty(self) -> bool:
        return self.pty_master_fd is not None

    def close_all(self) -> None:
        close_fds_quietly(self.child_fds)
        close_fds_quietly(self.parent_fds)


def setup_stdio(stdio: Stdio) -> StdioSetup:
    """Creates the pipes / pty for `stdio`. On any failure everything created so far is closed before re-raising."""

    parent_fds: list[int] = []
    child_fds: list[int] = []

    def _pipe(*, child_reads: bool) -> tuple[int, int]:
        r, w = os.pipe()
        if child_reads:
            child_fds.append(r)
            parent_fds.append(w)
            return r, w
        child_fds.append(w)
        parent_fds.append(r)
        return w, r

    def _devnull() -> int:
        fd = os.open(os.devnull, os.O_RDWR)
        child_fds.append(fd)
        return fd

    try:
        if isinstance(stdio, PtyStdio):
            master, slave = _pty.open_pty()
            parent_fds.append(master)
            child_fds.append(slave)
            _pty.set_winsize(slave, stdio.rows, stdio.cols)
            # Separate dups for reading and writing, each owned by its own connection; the master itself stays with the
            # handle. Output is one merged stream, presented as fd 1.
            pty_read_fd = os.dup(master)
            os.set_inheritable(pty_read_fd, False)
            parent_fds.append(pty_read_fd)
            pty_write_fd = os.dup(master)
            os.set_inheritable(pty_write_fd, False)
            parent_fds.append(pty_write_fd)
            return StdioSetup(
                stdin_fd=slave,
                stdout_fd=slave,
                stderr_fd=slave,
                child_fds=tuple(child_fds),
                parent_fds=tuple(parent_fds),
                stdin_w=pty_write_fd,
                output_reads=((_pty.PTY_OUTPUT_FD, pty_read_fd),),
                pty_master_fd=master,
            )

        stdio = check.isinstance(stdio, ProcessStdio)

        stdin_fd = -1
        stdin_w: int | None = None
        if stdio.stdin == 'pipe':
            stdin_fd, stdin_w = _pipe(child_reads=True)
        elif stdio.stdin == 'devnull':
            stdin_fd = _devnull()
        elif stdio.stdin == 'inherit':
            stdin_fd = -1
        else:
            stdin_fd = check.isinstance(stdio.stdin, int)

        stdout_fd = -1
        stdout_r: int | None = None
        if stdio.stdout == 'pipe':
            stdout_fd, stdout_r = _pipe(child_reads=False)
        elif stdio.stdout == 'devnull':
            stdout_fd = _devnull()
        elif stdio.stdout == 'inherit':
            stdout_fd = -1
        else:
            stdout_fd = check.isinstance(stdio.stdout, int)

        stderr_fd = -1
        stderr_r: int | None = None
        if stdio.stderr == 'pipe':
            stderr_fd, stderr_r = _pipe(child_reads=False)
        elif stdio.stderr == 'devnull':
            stderr_fd = _devnull()
        elif stdio.stderr == 'inherit':
            stderr_fd = -1
        elif stdio.stderr == 'stdout':
            # OS-level merge: whatever the child's stdout is (ours, if inherited).
            stderr_fd = stdout_fd if stdout_fd != -1 else 1
        else:
            stderr_fd = check.isinstance(stdio.stderr, int)

        return StdioSetup(
            stdin_fd=stdin_fd,
            stdout_fd=stdout_fd,
            stderr_fd=stderr_fd,
            child_fds=tuple(child_fds),
            parent_fds=tuple(parent_fds),
            stdin_w=stdin_w,
            output_reads=tuple((fd, r) for fd, r in ((1, stdout_r), (2, stderr_r)) if r is not None),
        )

    except BaseException:
        close_fds_quietly(child_fds)
        close_fds_quietly(parent_fds)
        raise
