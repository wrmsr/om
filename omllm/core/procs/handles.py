"""
The process handle, split into narrow roles so that code can depend on exactly the capability it needs (a tool that
only reads output takes a `ProcessOutput`; a supervisor takes a `ProcessControl`). `Process` composes them.

All methods are async and loop-agnostic in signature; the only implementation today is asyncio-based.
"""
import abc
import typing as ta

from omcore import lang

from .spool.spool import OutputSpool
from .types.ids import ProcessId
from .types.options import ProcOptions
from .types.options import TerminationPolicy
from .types.specs import ProcessSpec
from .types.states import ProcessState


if ta.TYPE_CHECKING:
    from .scopes.scope import ProcessScope


##


class ProcessInfo(lang.Abstract):
    @property
    @abc.abstractmethod
    def id(self) -> ProcessId:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def pid(self) -> int:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def spec(self) -> ProcessSpec:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def options(self) -> ProcOptions:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def state(self) -> ProcessState:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def returncode(self) -> int | None:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def scope(self) -> ProcessScope:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def created_at(self) -> float:
        """Wall-clock time (time.time()) at which the process was spawned."""

        raise NotImplementedError

    @property
    def name(self) -> str | None:
        return self.spec.name


class ProcessControl(lang.Abstract):
    @abc.abstractmethod
    def signal(self, sig: int, *, process_group: bool | None = None) -> ta.Awaitable[None]:
        """
        Sends a signal to the process (or, by default per its TerminationPolicy, its process group). Only ever
        reaches processes we own: raises ProcessNotAliveError once reaped or poisoned.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def terminate(self) -> ta.Awaitable[None]:
        raise NotImplementedError

    @abc.abstractmethod
    def kill(self) -> ta.Awaitable[None]:
        raise NotImplementedError

    @abc.abstractmethod
    def aclose(self, policy: TerminationPolicy | None = None) -> ta.Awaitable[None]:
        """
        Full teardown: stop the process if alive (signal -> grace -> SIGKILL -> hard timeout), sweep its group,
        drain/close output, reap, unregister. Idempotent. Never hangs beyond the policy's bounds; a process that
        survives SIGKILL is abandoned (or raises StuckProcessError per policy).
        """

        raise NotImplementedError


class ProcessStdin(lang.Abstract):
    @property
    @abc.abstractmethod
    def has_stdin(self) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def stdin_closed(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, data: bytes) -> ta.Awaitable[None]:
        """Writes to stdin, applying backpressure. Raises BrokenPipeError if the child has closed it."""

        raise NotImplementedError

    @abc.abstractmethod
    def write_eof(self) -> ta.Awaitable[None]:
        raise NotImplementedError


class ProcessOutput(lang.Abstract):
    @property
    @abc.abstractmethod
    def spool(self) -> OutputSpool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def output_ended(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def wait_output_ended(self, timeout: float | None = None) -> ta.Awaitable[bool]:
        raise NotImplementedError


class ProcessPty(lang.Abstract):
    @property
    @abc.abstractmethod
    def has_pty(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def resize(self, rows: int, cols: int) -> ta.Awaitable[None]:
        """
        Sets the terminal window size, delivering SIGWINCH to the child's foreground group. Raises NotAPtyError
        if the process was not started under a pty.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def get_winsize(self) -> tuple[int, int] | None:
        """Current (rows, cols), or None if there is no pty (or it has been torn down)."""

        raise NotImplementedError


class ProcessWaiter(lang.Abstract):
    @property
    @abc.abstractmethod
    def exited(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def wait(self, timeout: float | None = None) -> ta.Awaitable[int]:
        """
        Waits for exit and returns the return code (negative signal number if signaled). Raises
        ProcessTimeoutError on timeout; the process is left as-is. Cancellation-safe.
        """

        raise NotImplementedError


##


class Process(
    ProcessInfo,
    ProcessControl,
    ProcessStdin,
    ProcessOutput,
    ProcessPty,
    ProcessWaiter,
    lang.Abstract,
):
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(id={self.id!r}, pid={self.pid}, state={self.state.name}, argv={list(self.spec.argv)!r})'  # noqa

    async def __aenter__(self) -> ta.Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.aclose()
