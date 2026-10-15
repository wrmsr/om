# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import socket
import typing as ta

from ...core import IoPipeline
from ...errors import UnsupportedIoPipelineError
from .core import SyncIoPipelineDriver


##


class SocketSyncIoPipelineDriver(SyncIoPipelineDriver):
    """
    Drive a pipeline over a caller-owned socket.

    The driver temporarily makes the socket nonblocking so reads, queued writes, and timers can share one readiness
    wait, then restores the original timeout when the pipeline closes or fails. The socket's original timeout, if any,
    bounds each wait.
    """

    def __init__(
            self,
            spec: IoPipeline.Spec,
            sock: ta.Any,
            config: ta.Optional[SyncIoPipelineDriver.Config] = None,
    ) -> None:
        super().__init__(spec, config)

        self._sock = sock

        self._socket_mode_changed = False
        self._socket_original_timeout: ta.Optional[float] = None

    @property
    def socket(self) -> ta.Any:
        return self._sock

    def _prepare_transport(self) -> None:
        try:
            gettimeout = self._sock.gettimeout
            setblocking = self._sock.setblocking
            _ = self._sock.settimeout
        except AttributeError:
            return

        self._socket_original_timeout = gettimeout()
        setblocking(False)
        self._socket_mode_changed = True

    def _restore_transport(self) -> None:
        if not self._socket_mode_changed:
            return
        self._socket_mode_changed = False

        try:
            self._sock.settimeout(self._socket_original_timeout)
        except OSError:
            pass

    def _transport_timeout(self) -> ta.Optional[float]:
        if self._socket_mode_changed:
            return self._socket_original_timeout

        try:
            return self._sock.gettimeout()
        except AttributeError:
            return None

    def _read_fileno(self) -> int:
        return self._sock.fileno()

    def _write_fileno(self) -> int:
        return self._sock.fileno()

    def _read_into(self, buf: memoryview) -> int:
        return self._sock.recv_into(buf)

    def _write(self, data: memoryview) -> int:
        return self._sock.send(data)

    def _shutdown_output(self) -> None:
        try:
            shutdown = self._sock.shutdown
        except AttributeError:
            raise UnsupportedIoPipelineError(f'{self._sock!r} has no shutdown method') from None

        shutdown(socket.SHUT_WR)
