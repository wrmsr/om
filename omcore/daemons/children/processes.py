import abc
import os
import signal
import subprocess
import typing as ta

from ... import check
from ... import lang
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
    def wait(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def send_signal(self, signum: int, *, process_group: bool = False) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def kill(self, *, process_group: bool = False) -> None:
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

    @property
    def pid(self) -> int:
        return self._process.pid

    def _close_owned_files(self) -> None:
        for file in self._owned_files:
            file.close()

    def wait(self) -> int:
        try:
            return self._process.wait()
        finally:
            self._close_owned_files()

    def send_signal(self, signum: int, *, process_group: bool = False) -> None:
        if process_group:
            os.killpg(self.pid, signum)
        else:
            self._process.send_signal(signum)

    def kill(self, *, process_group: bool = False) -> None:
        if process_group:
            os.killpg(self.pid, signal.SIGKILL)
        else:
            self._process.kill()


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
