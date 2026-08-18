import typing as ta

from omcore import dataclasses as dc


##


class ProcessError(Exception):
    pass


##


@dc.dataclass()
class SpawnError(ProcessError):
    """The child failed before exec (or the exec itself failed). `stage` names the shim step that failed."""

    stage: str
    errno: int | None
    message: str

    argv: ta.Sequence[str] | None = None

    def __str__(self) -> str:
        return f'{self.stage}: [errno {self.errno}] {self.message}' + (f' (argv={self.argv!r})' if self.argv else '')


class ProcessTimeoutError(ProcessError, TimeoutError):
    pass


class ProcessNotAliveError(ProcessError):
    pass


class ProcessPoisonedError(ProcessError):
    pass


class StuckProcessError(ProcessError):
    pass


class ScopeClosedError(ProcessError):
    pass


class NotAPtyError(ProcessError):
    pass


class ManagerClosedError(ProcessError):
    pass


class ManagerNotStartedError(ProcessError):
    pass


class UnsafeChildSignalDispositionError(ProcessError):
    """
    SIGCHLD is ignored (or otherwise makes children auto-reap) in this process - pid ownership cannot be guaranteed, so
    the manager refuses to start.
    """
