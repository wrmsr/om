# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import enum
import typing as ta

from .effects import SystevisorEngineEffect
from .identities import SystevisorInstanceId
from .identities import SystevisorRunId


class SystevisorEventKind(enum.Enum):
    CONFIG_APPLIED = 'config_applied'
    CONFIG_UNCHANGED = 'config_unchanged'
    INSTANCE_ADDED = 'instance_added'
    INSTANCE_REMOVED = 'instance_removed'
    STATE_CHANGED = 'state_changed'
    DESIRED_CHANGED = 'desired_changed'
    PROCESS_EXITED = 'process_exited'
    PROCESS_SPAWN_FAILED = 'process_spawn_failed'
    PROCESS_CONFIG_UPDATED = 'process_config_updated'
    DEPENDENCY_BLOCKED = 'dependency_blocked'
    DEPENDENCY_UNBLOCKED = 'dependency_unblocked'
    COMMAND_REJECTED = 'command_rejected'
    STALE_FACT_IGNORED = 'stale_fact_ignored'
    SHUTDOWN_STARTED = 'shutdown_started'
    SIGNAL_FORWARDED = 'signal_forwarded'
    HEALTH_PROBE_STARTED = 'health_probe_started'
    HEALTH_PROBE_RESULT = 'health_probe_result'
    HEALTH_CHANGED = 'health_changed'
    READINESS_CHANGED = 'readiness_changed'
    HEALTH_RECOVERY_REQUESTED = 'health_recovery_requested'
    COLLECTION_ADDED = 'collection_added'
    COLLECTION_REMOVED = 'collection_removed'
    COLLECTION_DESIRED_CHANGED = 'collection_desired_changed'
    COLLECTION_STATUS_CHANGED = 'collection_status_changed'
    COLLECTION_STOP_TOGETHER = 'collection_stop_together'


@dc.dataclass(frozen=True)
class SystevisorEvent:
    sequence: int
    at: float
    kind: SystevisorEventKind
    instance_id: ta.Optional[SystevisorInstanceId] = None
    run_id: ta.Optional[SystevisorRunId] = None
    request_id: ta.Optional[str] = None
    data: ta.Mapping[str, ta.Any] = dc.field(default_factory=dict)


@dc.dataclass(frozen=True)
class SystevisorEngineOutput:
    effects: ta.Sequence[SystevisorEngineEffect] = ()
    events: ta.Sequence[SystevisorEvent] = ()
