"""
Driving a demo app end to end under a real pty: a subprocess on a pseudo-terminal of a fixed size, keys written to it,
its output accumulated - and terminal queries it makes (the startup CPR) answered the way a terminal would, so the run
is not timeout-delayed. Waits are for specific output, never for time.
"""
import fcntl
import os
import pty
import select
import struct
import subprocess
import termios
import time
import typing as ta


##


CPR_QUERY = b'\x1b[6n'


class PtyRun:
    def __init__(
            self,
            argv: ta.Sequence[str],
            *,
            rows: int = 24,
            cols: int = 80,
            cwd: str | None = None,
    ) -> None:
        super().__init__()

        self.master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('hhhh', rows, cols, 0, 0))
        self.proc = subprocess.Popen(  # noqa: S603
            argv,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            cwd=cwd,
            env={**os.environ, 'TERM': 'xterm-256color'},
            start_new_session=True,
        )
        os.close(slave)

        self.output = bytearray()
        self._mark = 0
        self._answered_cprs = 0

    def send(self, data: bytes) -> None:
        os.write(self.master, data)

    def _pump(self, timeout_s: float) -> bool:
        """Read what is available within `timeout_s`, answering new CPR queries; False at EOF."""

        ready, _, _ = select.select([self.master], [], [], max(timeout_s, 0))
        if not ready:
            return True
        try:
            data = os.read(self.master, 65536)
        except OSError:
            data = b''
        if not data:
            return False
        self.output.extend(data)
        queries = self.output.count(CPR_QUERY)
        while self._answered_cprs < queries:
            self.send(b'\x1b[1;1R')
            self._answered_cprs += 1
        return True

    def read_until(self, needle: bytes, *, timeout_s: float = 10.) -> None:
        """Wait for `needle` to appear in the output past the last thing waited for."""

        deadline = time.monotonic() + timeout_s
        while True:
            if (idx := self.output.find(needle, self._mark)) >= 0:
                self._mark = idx + len(needle)
                return
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f'{needle!r} not seen in {timeout_s}s; output tail: {bytes(self.output[-400:])!r}')
            if not self._pump(remaining):
                raise EOFError(f'process ended before {needle!r}; output tail: {bytes(self.output[-400:])!r}')

    def finish(self, *, timeout_s: float = 10.) -> int:
        """Drain the output to EOF and reap the process, returning its exit code."""

        deadline = time.monotonic() + timeout_s
        while self._pump(deadline - time.monotonic()):
            if time.monotonic() >= deadline:
                break
        try:
            return self.proc.wait(timeout=max(deadline - time.monotonic(), .1))
        finally:
            os.close(self.master)

    def kill(self) -> None:
        if self.proc.poll() is None:
            self.proc.kill()
            self.proc.wait()
        try:
            os.close(self.master)
        except OSError:
            pass
