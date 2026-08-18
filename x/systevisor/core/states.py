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
    COLLECTION = 'collection'
    COLLECTION_FAILURE = 'collection_failure'
    DEPENDENCY = 'dependency'
    MANUAL = 'manual'
    SHUTDOWN = 'shutdown'
    HEALTH = 'health'


class SystevisorDeadlineKind(enum.Enum):
    START_STABLE = 'start_stable'
    BACKOFF = 'backoff'
    STOP_ESCALATION = 'stop_escalation'
    HEALTH_PROBE = 'health_probe'


class SystevisorHealthStatus(enum.Enum):
    UNKNOWN = 'unknown'
    PENDING = 'pending'
    PASSING = 'passing'
    FAILING = 'failing'


class SystevisorCollectionStatus(enum.Enum):
    INACTIVE = 'inactive'
    STARTING = 'starting'
    READY = 'ready'
    STOPPING = 'stopping'
    DEGRADED = 'degraded'
    FAILED = 'failed'


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
    FORWARD = 'forward'
