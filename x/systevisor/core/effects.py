# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import typing as ta

from ..configs.models import SystevisorSignalScope
from ..configs.snapshots import SystevisorDesiredInstanceSpec
from .identities import SystevisorInstanceId
from .identities import SystevisorRunId
from .states import SystevisorDeadlineKind
from .states import SystevisorSignalReason


class SystevisorEngineEffect:
    pass


@dc.dataclass(frozen=True)
class SystevisorSpawnProcessEffect(SystevisorEngineEffect):
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    spec: SystevisorDesiredInstanceSpec


@dc.dataclass(frozen=True)
class SystevisorSignalProcessEffect(SystevisorEngineEffect):
    run_id: SystevisorRunId
    signal: str
    scope: SystevisorSignalScope
    reason: SystevisorSignalReason


@dc.dataclass(frozen=True)
class SystevisorScheduleDeadlineEffect(SystevisorEngineEffect):
    deadline_id: int
    deadline_at: float
    kind: SystevisorDeadlineKind
    instance_id: SystevisorInstanceId
    run_id: ta.Optional[SystevisorRunId]


@dc.dataclass(frozen=True)
class SystevisorApplyLiveConfigEffect(SystevisorEngineEffect):
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    spec: SystevisorDesiredInstanceSpec
    changed_paths: ta.Sequence[str]
