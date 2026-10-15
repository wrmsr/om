# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import fcntl
import os
import socket
import stat
import typing as ta

from ....streambufs.types import BytesLike
from ...errors import UnsupportedIoPipelineError
from .core import IoPipelineFdioTransport


##


class DescriptorIoPipelineFdioTransport(IoPipelineFdioTransport):
    """
    A transport over a read descriptor and a write descriptor, which may be the same one: a pipe pair, a process's own
    standard streams, a terminal, or a socket by number.

    Both descriptors are switched to nonblocking mode on construction and restored on release. Descriptors the caller
    opened are the caller's: they are never closed unless `owned`. Output shutdown on a socket descriptor shuts down
    the socket's output half without closing the descriptor; a non-socket write descriptor can only be half-closed by
    closing it, which `owned` or `close_write_fd_on_output_shutdown` permits - its original flags are restored first,
    and the closed number is never touched again - and a single non-socket descriptor used for both directions can
    never be half-closed.
    """

    def __init__(
            self,
            read_fd: int,
            write_fd: int,
            *,
            owned: bool = False,
            close_write_fd_on_output_shutdown: bool = False,
    ) -> None:
        super().__init__()

        self._read_fd = read_fd
        self._write_fd = write_fd
        self._owned = owned
        self._close_write_fd_on_output_shutdown = close_write_fd_on_output_shutdown

        self._open_fds: ta.Set[int] = {read_fd, write_fd}
        self._original_flags: ta.Dict[int, int] = {}
        self._closed = False

        # Both descriptors may share one open file description (dups of a terminal, say), whose flags are shared too:
        # every original is recorded before any is changed, or the second would record the first's change as its
        # original and restore the description to nonblocking.
        for fd in self._open_fds:
            self._original_flags[fd] = fcntl.fcntl(fd, fcntl.F_GETFL)

        for fd in self._open_fds:
            flags = self._original_flags[fd]
            if not (flags & os.O_NONBLOCK):
                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def __repr__(self) -> str:
        return f'{type(self).__name__}@{id(self):x}<{self._read_fd}, {self._write_fd}>'

    @property
    def read_fd(self) -> int:
        return self._read_fd

    @property
    def write_fd(self) -> int:
        return self._write_fd

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def write_fd_closed(self) -> bool:
        return self._write_fd not in self._open_fds

    #

    def read_into(self, buf: memoryview) -> int:
        data = os.read(self._read_fd, len(buf))
        n = len(data)
        buf[:n] = data
        return n

    def write(self, data: BytesLike) -> int:
        return os.write(self._write_fd, data)

    def shutdown_output(self) -> None:
        fd = self._write_fd

        if stat.S_ISSOCK(os.fstat(fd).st_mode):
            # Shutdown acts on the socket, not the descriptor, so a temporary duplicate reaches it without taking
            # ownership of the caller's descriptor.
            sock = socket.socket(fileno=os.dup(fd))
            try:
                sock.shutdown(socket.SHUT_WR)
            finally:
                sock.close()
            return

        if fd == self._read_fd:
            raise UnsupportedIoPipelineError('a single non-socket descriptor cannot be half-closed')

        if not (self._owned or self._close_write_fd_on_output_shutdown):
            raise UnsupportedIoPipelineError('closing the caller-owned write descriptor was not permitted')

        self._release_fd(fd, close=True)

        # The read descriptor may share that open file description - as dups of one terminal do - and is still in use,
        # so it is made nonblocking again. Its original flags are restored when the transport is done with it.
        rfl = fcntl.fcntl(self._read_fd, fcntl.F_GETFL)
        if not rfl & os.O_NONBLOCK:
            fcntl.fcntl(self._read_fd, fcntl.F_SETFL, rfl | os.O_NONBLOCK)

    def _release_fd(self, fd: int, *, close: bool) -> None:
        # The nonblocking flag lives on the open file description, which other descriptors may share, so restore it
        # before closing. The descriptor number may be reused once closed, so it must never be touched again.
        self._open_fds.discard(fd)
        if (flags := self._original_flags.pop(fd, None)) is not None:
            try:
                fcntl.fcntl(fd, fcntl.F_SETFL, flags)
            except OSError:
                pass
        if close:
            try:
                os.close(fd)
            except OSError:
                pass

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True

        for fd in sorted(self._open_fds):
            self._release_fd(fd, close=self._owned)
