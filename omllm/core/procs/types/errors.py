import typing as ta

from omcore import dataclasses as dc


##


class ProcsError(Exception):
    pass


##


@dc.dataclass()
class SpawnError(ProcsError):
    """The child failed before exec (or the exec itself failed). `stage` names the shim step that failed."""

    stage: str
    errno: int | None
    message: str

    argv: ta.Sequence[str] | None = None

    def __str__(self) -> str:
        return f'{self.stage}: [errno {self.errno}] {self.message}' + (f' (argv={self.argv!r})' if self.argv else '')


class ProcessTimeoutError(ProcsError, TimeoutError):
    pass


class ProcessNotAliveError(ProcsError):
    pass


class ProcessPoisonedError(ProcsError):
    pass


class StuckProcessError(ProcsError):
    pass


class ScopeClosedError(ProcsError):
    pass


class ManagerClosedError(ProcsError):
    pass


class ManagerNotStartedError(ProcsError):
    pass


class UnsafeChildSignalDispositionError(ProcsError):
    """
    SIGCHLD is ignored (or otherwise makes children auto-reap) in this process - pid ownership cannot be
    guaranteed, so the manager refuses to start.
    """
