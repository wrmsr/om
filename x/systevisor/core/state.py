# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import typing as ta

from ..configs.snapshots import SystevisorConfigSnapshot
from ..configs.snapshots import SystevisorDesiredInstanceSpec
from .identities import SystevisorInstanceId
from .identities import SystevisorRunId
from .identities import SystevisorUnitName
from .states import SystevisorDeadlineKind
from .states import SystevisorDesiredOrigin
from .states import SystevisorDesiredState
from .states import SystevisorProcessState


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


@dc.dataclass
class SystevisorEngineState:
    state_schema_version: int = 1
    snapshot: ta.Optional[SystevisorConfigSnapshot] = None
    config_generation: int = 0
    instances: ta.MutableMapping[SystevisorInstanceId, SystevisorInstanceState] = dc.field(default_factory=dict)
    unit_desired_overrides: ta.MutableMapping[SystevisorUnitName, bool] = dc.field(default_factory=dict)
    shutting_down: bool = False
    next_run_id: int = 1
    next_deadline_id: int = 1
    event_sequence: int = 0
    last_now: float = 0.
