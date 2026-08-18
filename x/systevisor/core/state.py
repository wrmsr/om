# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import typing as ta

from ..configs.models import SystevisorHealthRole
from ..configs.snapshots import SystevisorConfigSnapshot
from ..configs.snapshots import SystevisorDesiredInstanceSpec
from .identities import SystevisorCollectionName
from .identities import SystevisorHealthCheckId
from .identities import SystevisorInstanceId
from .identities import SystevisorRunId
from .identities import SystevisorUnitName
from .states import SystevisorCollectionStatus
from .states import SystevisorDeadlineKind
from .states import SystevisorDesiredOrigin
from .states import SystevisorDesiredState
from .states import SystevisorHealthStatus
from .states import SystevisorProcessState


@dc.dataclass
class SystevisorHealthProbeState:
    name: str
    role: SystevisorHealthRole
    config_digest: str
    status: SystevisorHealthStatus = SystevisorHealthStatus.UNKNOWN
    consecutive_successes: int = 0
    consecutive_failures: int = 0
    last_started_at: ta.Optional[float] = None
    last_completed_at: ta.Optional[float] = None
    last_success_at: ta.Optional[float] = None
    last_message: ta.Optional[str] = None
    last_data: ta.Mapping[str, ta.Any] = dc.field(default_factory=dict)
    scheduled_deadline_id: ta.Optional[int] = None
    next_check_at: ta.Optional[float] = None
    in_flight_check_id: ta.Optional[SystevisorHealthCheckId] = None
    recovery_applied: bool = False


@dc.dataclass
class SystevisorCollectionState:
    name: SystevisorCollectionName
    desired_active: bool
    desired_origin: SystevisorDesiredOrigin
    status: SystevisorCollectionStatus = SystevisorCollectionStatus.INACTIVE
    activation_sequence: int = 0
    failure_instance_id: ta.Optional[SystevisorInstanceId] = None
    failure_reason: ta.Optional[str] = None


@dc.dataclass
class SystevisorInstanceState:
    instance_id: SystevisorInstanceId
    unit_name: SystevisorUnitName
    slot: int
    desired_spec: SystevisorDesiredInstanceSpec
    desired_state: SystevisorDesiredState
    desired_origin: SystevisorDesiredOrigin
    process_state: SystevisorProcessState = SystevisorProcessState.STOPPED
    run_id: ta.Optional[SystevisorRunId] = None
    applied_spec_digest: ta.Optional[str] = None
    spawn_confirmed: bool = False
    start_failures: int = 0
    started_at: ta.Optional[float] = None
    ready: bool = False
    completed_successfully: bool = False
    last_return_code: ta.Optional[int] = None
    deadline_id: ta.Optional[int] = None
    deadline_kind: ta.Optional[SystevisorDeadlineKind] = None
    deadline_at: ta.Optional[float] = None
    restart_requested: bool = False
    blocked_reason: ta.Optional[str] = None
    start_stable: bool = False
    health: ta.MutableMapping[str, SystevisorHealthProbeState] = dc.field(default_factory=dict)


@dc.dataclass
class SystevisorEngineState:
    state_schema_version: int = 2
    snapshot: ta.Optional[SystevisorConfigSnapshot] = None
    config_generation: int = 0
    instances: ta.MutableMapping[SystevisorInstanceId, SystevisorInstanceState] = dc.field(default_factory=dict)
    collections: ta.MutableMapping[SystevisorCollectionName, SystevisorCollectionState] = dc.field(default_factory=dict)
    unit_desired_overrides: ta.MutableMapping[SystevisorUnitName, bool] = dc.field(default_factory=dict)
    startup_collection: ta.Optional[SystevisorCollectionName] = None
    shutting_down: bool = False
    next_run_id: int = 1
    next_deadline_id: int = 1
    event_sequence: int = 0
    last_now: float = 0.
    next_health_check_id: int = 1
