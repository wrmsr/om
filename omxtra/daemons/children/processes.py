import abc
import errno
import os
import signal
import subprocess
import sys
import threading
import typing as ta

from omcore import check
from omcore import lang

from .configs import ChildProcessConfig
from .configs import ChildProcessInput
from .configs import ChildProcessOutput
from .configs import ChildProcessOutputMode


##


class ChildProcess(lang.Abstract):
    @property
    @abc.abstractmethod
    def pid(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def wait_exited(self) -> int:
        """
        Blocks until the child has exited and returns its returncode, without reaping it: until `reap`, its pid - and so
        its process group id - cannot be reused, and remains safe to signal.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def reap(self) -> int:
        """
        Waits for the child to exit, then releases it - after which its pid may name something else - and returns its
        returncode.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def send_signal(self, signum: int, *, process_group: bool = False) -> None:
        """Raises ProcessLookupError once the child has been reaped."""

        raise NotImplementedError

    @abc.abstractmethod
    def kill(self, *, process_group: bool = False) -> None:
        """Raises ProcessLookupError once the child has been reaped."""

        raise NotImplementedError


class ChildProcessFactory(lang.Abstract):
    @abc.abstractmethod
    def spawn(self, config: ChildProcessConfig) -> ChildProcess:
        raise NotImplementedError


##


class PopenChildProcess(ChildProcess):
    def __init__(
            self,
            process: subprocess.Popen,
            owned_files: ta.Iterable[ta.IO[bytes]],
    ) -> None:
        super().__init__()

        self._process = process
        self._owned_files = tuple(owned_files)

        # Held across each signal and the reap, so that a signal can never race the release of the pid.
        self._lock = threading.Lock()
        self._reaped = False

    @property
    def pid(self) -> int:
        return self._process.pid

    def _close_owned_files(self) -> None:
        for file in self._owned_files:
            file.close()

    def _returncode_if_reaped(self) -> int | None:
        with self._lock:
            if self._reaped:
                return check.not_none(self._process.returncode)
            return None

    def wait_exited(self) -> int:
        if (returncode := self._returncode_if_reaped()) is not None:
            return returncode
        # Not through the Popen, whose own waits reap - and not under the lock, which held through a wait for a live
        # child would shut out the very signals that might end it.
        try:
            result = check.not_none(os.waitid(os.P_PID, self.pid, os.WEXITED | os.WNOWAIT))
        except ChildProcessError:
            # Reaped out from under the wait, by a `reap` that saw the exit first: its result stands.
            if (returncode := self._returncode_if_reaped()) is not None:
                return returncode
            raise
        if result.si_code == os.CLD_EXITED:
            return result.si_status
        return -result.si_status

    def reap(self) -> int:
        # Exited first, outside the lock: holding it through a wait for a live child would shut out the very signals
        # that might end it.
        self.wait_exited()
        with self._lock:
            try:
                return self._process.wait()
            finally:
                self._reaped = True
                self._close_owned_files()

    def _leader_alive(self) -> bool:
        """Non-reaping: whether the leader has neither exited nor been reaped."""

        try:
            return os.waitid(os.P_PID, self.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is None
        except ChildProcessError:
            return False

    def _signal_group(self, signum: int) -> None:
        try:
            os.killpg(self.pid, signum)
        except PermissionError as e:
            # Darwin fails a group signal with EPERM rather than ESRCH when every member of the group is a zombie - as
            # it is once the leader, held unreaped, has exited and nothing else in it lives. Only a leader still alive,
            # and so one we may not signal, makes it a genuine permission error.
            if sys.platform != 'darwin' or self._leader_alive():
                raise
            raise ProcessLookupError(errno.ESRCH, f'process group {self.pid} has no live members') from e

    def _signal(self, signum: int, *, process_group: bool) -> None:
        with self._lock:
            if self._reaped:
                # Its pid is released, and may already name something else.
                raise ProcessLookupError(errno.ESRCH, f'child process {self.pid} has been reaped')
            # Unreaped, neither the pid nor the group id can have been reused. Both are signaled directly rather than
            # through the Popen, whose signaling first polls - and so may reap.
            if process_group:
                self._signal_group(signum)
            else:
                os.kill(self.pid, signum)

    def send_signal(self, signum: int, *, process_group: bool = False) -> None:
        self._signal(signum, process_group=process_group)

    def kill(self, *, process_group: bool = False) -> None:
        self._signal(signal.SIGKILL, process_group=process_group)


class PopenChildProcessFactory(ChildProcessFactory):
    @staticmethod
    def _resolve_output(
            output: ChildProcessOutput,
            *,
            owned_files: list[ta.IO[bytes]],
            open_files: dict[tuple[str, bool], ta.IO[bytes]],
    ) -> ta.Any:
        if output.mode is ChildProcessOutputMode.INHERIT:
            return None
        if output.mode is ChildProcessOutputMode.DEVNULL:
            return subprocess.DEVNULL
        if output.mode is ChildProcessOutputMode.STDOUT:
            return subprocess.STDOUT
        if output.mode is ChildProcessOutputMode.FILE:
            path = os.path.expanduser(check.not_none(output.path))
            key = (os.path.abspath(path), output.append)
            if (file := open_files.get(key)) is None:
                file = open(path, 'ab' if output.append else 'wb', buffering=0)  # noqa: SIM115
                open_files[key] = file
                owned_files.append(file)
            return file
        raise ValueError(output.mode)

    def spawn(self, config: ChildProcessConfig) -> ChildProcess:
        owned_files: list[ta.IO[bytes]] = []
        open_files: dict[tuple[str, bool], ta.IO[bytes]] = {}
        try:
            stdout = self._resolve_output(
                config.stdout,
                owned_files=owned_files,
                open_files=open_files,
            )
            stderr = self._resolve_output(
                config.stderr,
                owned_files=owned_files,
                open_files=open_files,
            )

            process = subprocess.Popen(
                list(config.cmd),
                cwd=config.resolved_cwd(),
                env=config.resolved_env(),
                stdin=(
                    None
                    if config.stdin is ChildProcessInput.INHERIT
                    else subprocess.DEVNULL
                ),
                stdout=stdout,
                stderr=stderr,
                close_fds=True,
                pass_fds=tuple(config.pass_fds),
                start_new_session=config.start_new_session,
            )

        except BaseException:
            for file in owned_files:
                file.close()
            raise

        return PopenChildProcess(process, owned_files)


DEFAULT_CHILD_PROCESS_FACTORY = PopenChildProcessFactory()
