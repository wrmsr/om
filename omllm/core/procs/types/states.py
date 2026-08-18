import enum


##


class ProcessState(enum.Enum):
    # Spawned but the exec handshake has not completed.
    SPAWNING = enum.auto()

    # Exec'd and not yet observed to have exited.
    RUNNING = enum.auto()

    # Exit observed (waitid WNOWAIT) but deliberately not yet reaped - the pid and pgid are still ours.
    EXITED = enum.auto()

    # Reaped. Terminal. The pid may be recycled by the OS - never signaled again.
    REAPED = enum.auto()

    # Survived SIGKILL past the hard timeout and was unregistered. Terminal for management purposes; if it ever
    # exits it is reaped by its lingering watcher.
    ABANDONED = enum.auto()

    # Something else reaped our child (SIGCHLD ignored, foreign waitpid, ...). Terminal - never signaled again.
    POISONED = enum.auto()

    @property
    def is_alive(self) -> bool:
        return self in (ProcessState.SPAWNING, ProcessState.RUNNING)

    @property
    def is_terminal(self) -> bool:
        return self in (ProcessState.REAPED, ProcessState.ABANDONED, ProcessState.POISONED)
