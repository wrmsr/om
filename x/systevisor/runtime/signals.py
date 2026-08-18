# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import os
import signal
import typing as ta

from omcore.io.fdio.handlers import FdioHandler


_SYSTEVISOR_SIGNALS_DEFAULT_SIGNALS = (
    signal.SIGCHLD,
    signal.SIGTERM,
    signal.SIGINT,
    signal.SIGHUP,
    signal.SIGQUIT,
    signal.SIGUSR1,
    signal.SIGUSR2,
)


def _systevisor_signals_python_handler(signal_number: int, frame: ta.Any) -> None:
    pass


@dc.dataclass(frozen=True)
class SystevisorReceivedSignal:
    signal_number: int


class SystevisorSignalFdioHandler(FdioHandler):
    def __init__(
            self,
            callback: ta.Callable[[SystevisorReceivedSignal], None],
            signal_numbers: ta.Iterable[int] = _SYSTEVISOR_SIGNALS_DEFAULT_SIGNALS,
    ) -> None:
        self._callback = callback
        self._signal_numbers = tuple(dict.fromkeys(signal_numbers))
        self._read_fd, self._write_fd = os.pipe()
        os.set_blocking(self._read_fd, False)
        os.set_blocking(self._write_fd, False)
        os.set_inheritable(self._read_fd, False)
        os.set_inheritable(self._write_fd, False)
        self._previous_handlers: ta.Dict[int, ta.Any] = {}
        self._previous_wakeup_fd: ta.Optional[int] = None
        self._installed = False
        self._closed = False

    def fd(self) -> int:
        return self._read_fd

    @property
    def closed(self) -> bool:
        return self._closed

    def install(self) -> None:
        if self._closed:
            raise RuntimeError('signal handler is closed')
        if self._installed:
            raise RuntimeError('signal handler is already installed')
        previous_wakeup_fd = signal.set_wakeup_fd(self._write_fd, warn_on_full_buffer=False)
        try:
            for signal_number in self._signal_numbers:
                self._previous_handlers[signal_number] = signal.getsignal(signal_number)
                signal.signal(signal_number, _systevisor_signals_python_handler)
        except BaseException:  # noqa: BLE001
            for signal_number, previous_handler in self._previous_handlers.items():
                signal.signal(signal_number, previous_handler)
            self._previous_handlers.clear()
            signal.set_wakeup_fd(previous_wakeup_fd)
            raise
        self._previous_wakeup_fd = previous_wakeup_fd
        self._installed = True

    def readable(self) -> bool:
        return self._installed and not self._closed

    def on_readable(self) -> None:
        while not self._closed:
            try:
                data = os.read(self._read_fd, 4096)
            except BlockingIOError:
                return
            if not data:
                return
            for signal_number in data:
                self._callback(SystevisorReceivedSignal(signal_number))

    def close(self) -> None:
        if self._closed:
            return
        if self._installed:
            for signal_number, previous_handler in self._previous_handlers.items():
                signal.signal(signal_number, previous_handler)
            previous_wakeup_fd = self._previous_wakeup_fd
            if previous_wakeup_fd is None:
                raise RuntimeError('installed signal handler lost its previous wakeup fd')
            signal.set_wakeup_fd(previous_wakeup_fd)
            self._previous_handlers.clear()
            self._installed = False
        os.close(self._read_fd)
        os.close(self._write_fd)
        self._closed = True

    def on_error(self, exc: ta.Optional[BaseException] = None) -> None:
        self.close()
