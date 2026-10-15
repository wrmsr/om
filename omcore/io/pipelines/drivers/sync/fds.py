# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import fcntl
import os
import socket
import stat
import typing as ta

from ...core import IoPipeline
from ...errors import UnsupportedIoPipelineError
from .core import SyncIoPipelineDriver


##


class FdSyncIoPipelineDriver(SyncIoPipelineDriver):
    """
    Drive a pipeline over a pair of caller-owned file descriptors, such as a pipe pair or a process's own stdio.

    Both descriptors are switched to nonblocking mode while the driver is active and restored afterwards. They may be
    the same descriptor. An optional timeout bounds each readiness wait the same way a socket's timeout would.

    ShutdownOutput on a socket write descriptor shuts down the socket's output half without closing the descriptor. A
    caller-owned non-socket write descriptor (a pipe, a terminal) cannot be half-closed without closing it, so the
    message fails unless `close_write_fd_on_output_shutdown` grants the driver that ownership - in which case the
    descriptor's original flags are restored and it is closed. A single non-socket descriptor used for both directions
    can never be half-closed.
    """

    def __init__(
            self,
            spec: IoPipeline.Spec,
            read_fd: int,
            write_fd: int,
            config: ta.Optional[SyncIoPipelineDriver.Config] = None,
            *,
            timeout_s: ta.Optional[float] = None,
            close_write_fd_on_output_shutdown: bool = False,
    ) -> None:
        super().__init__(spec, config)

        self._read_fd = read_fd
        self._write_fd = write_fd
        self._timeout_s = timeout_s
        self._close_write_fd_on_output_shutdown = close_write_fd_on_output_shutdown

        self._original_flags: ta.Dict[int, int] = {}

    @property
    def read_fd(self) -> int:
        return self._read_fd

    @property
    def write_fd(self) -> int:
        return self._write_fd

    def _prepare_transport(self) -> None:
        fds = {self._read_fd, self._write_fd}

        # Both descriptors may share one open file description (dups of a terminal, say), whose flags are shared too:
        # every original is recorded before any is changed, or the second would record the first's change as its
        # original and restore the description to nonblocking.
        for fd in fds:
            self._original_flags[fd] = fcntl.fcntl(fd, fcntl.F_GETFL)

        for fd in fds:
            flags = self._original_flags[fd]
            if not (flags & os.O_NONBLOCK):
                fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def _restore_transport(self) -> None:
        flags_by_fd = self._original_flags
        self._original_flags = {}
        for fd, flags in flags_by_fd.items():
            try:
                fcntl.fcntl(fd, fcntl.F_SETFL, flags)
            except OSError:
                pass

    def _transport_timeout(self) -> ta.Optional[float]:
        return self._timeout_s

    def _read_fileno(self) -> int:
        return self._read_fd

    def _write_fileno(self) -> int:
        return self._write_fd

    def _read_into(self, buf: memoryview) -> int:
        data = os.read(self._read_fd, len(buf))
        n = len(data)
        buf[:n] = data
        return n

    def _write(self, data: memoryview) -> int:
        return os.write(self._write_fd, data)

    def _shutdown_output(self) -> None:
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

        if not self._close_write_fd_on_output_shutdown:
            raise UnsupportedIoPipelineError('closing the caller-owned write descriptor was not permitted')

        # The nonblocking flag lives on the open file description, which other descriptors may share, so restore it
        # before closing. The descriptor number may be reused once closed, so it must never be touched again.
        if (flags := self._original_flags.pop(fd, None)) is not None:
            fcntl.fcntl(fd, fcntl.F_SETFL, flags)
        os.close(fd)

        # The read descriptor may share that open file description - as dups of one terminal do - and is still in use,
        # so it is made nonblocking again. Its original flags are restored when the driver is done with it.
        rfl = fcntl.fcntl(self._read_fd, fcntl.F_GETFL)
        if not rfl & os.O_NONBLOCK:
            fcntl.fcntl(self._read_fd, fcntl.F_SETFL, rfl | os.O_NONBLOCK)
