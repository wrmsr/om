"""
A process on a pseudo-terminal, as an interpreter which drives one needs it: bytes each way, a window size, an
interrupt, and an end.
Like the executors and runners this is a seam, and a loop-neutral one - there is no implementation here. Where such a
process runs (this machine, a container, the far side of a connection) and what looks after it is the host's business:
it adapts its own process infrastructure to this interface rather than the other way round.
"""
import abc
import typing as ta

from omcore import lang


##


class PtyProcess(lang.Abstract):
    @abc.abstractmethod
    def write(self, data: bytes) -> ta.Awaitable[None]:
        """
        Write to the terminal, as its keyboard would: control characters included. Raises BrokenPipeError when the
        process is no longer there to take it.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def read(self, timeout: float | None = None) -> ta.Awaitable[bytes | None]:
        """
        What the process has written since the last read, waiting for some when there is none yet: empty once there
        will never be more (the process exited, or was lost), None when `timeout` seconds pass first.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def resize(self, rows: int, cols: int) -> ta.Awaitable[None]:
        raise NotImplementedError

    @abc.abstractmethod
    def interrupt(self) -> ta.Awaitable[None]:
        """
        SIGINT to the process itself - which is not what the terminal's interrupt character does: that reaches the
        foreground job, and a shell with job control is not in it. Raises BrokenPipeError when the process is no longer
        there.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def aclose(self) -> ta.Awaitable[None]:
        """Stop the process, and whatever it started, if it is still running. Idempotent, and bounded."""

        raise NotImplementedError


class PtySpawner(lang.Abstract):
    @abc.abstractmethod
    def spawn(
            self,
            argv: ta.Sequence[str],
            *,
            rows: int,
            cols: int,
    ) -> ta.Awaitable[PtyProcess]:
        """
        Start `argv` as the session leader of a new terminal of the given size, in whatever directory and environment
        the host has for it. Raises when it cannot be started.
        """

        raise NotImplementedError
