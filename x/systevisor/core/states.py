import enum


class SystevisorProcessState(enum.Enum):
    STOPPED = 'stopped'
    STARTING = 'starting'
    RUNNING = 'running'
    BACKOFF = 'backoff'
    STOPPING = 'stopping'
    EXITED = 'exited'
    FATAL = 'fatal'
    UNKNOWN = 'unknown'


class SystevisorDesiredState(enum.Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    REMOVED = 'removed'


class SystevisorDesiredOrigin(enum.Enum):
    CONFIG = 'config'
    MANUAL = 'manual'
    SHUTDOWN = 'shutdown'


class SystevisorDeadlineKind(enum.Enum):
    START_STABLE = 'start_stable'
    BACKOFF = 'backoff'
    STOP_ESCALATION = 'stop_escalation'


class SystevisorUnitChangeKind(enum.Enum):
    NONE = 'none'
    LIVE = 'live'
    RESTART = 'restart'


class SystevisorSignalReason(enum.Enum):
    STOP = 'stop'
    RESTART = 'restart'
    REMOVE = 'remove'
    SHUTDOWN = 'shutdown'
    ESCALATE = 'escalate'
