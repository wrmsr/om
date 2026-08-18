# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import typing as ta

from ..configs.snapshots import SystevisorConfigSnapshot
from .identities import SystevisorCollectionName
from .identities import SystevisorHealthCheckId
from .identities import SystevisorInstanceId
from .identities import SystevisorRunId
from .identities import SystevisorUnitName


class SystevisorEngineInput:
    pass


class SystevisorEngineCommand(SystevisorEngineInput):
    pass


class SystevisorEngineFact(SystevisorEngineInput):
    pass


@dc.dataclass(frozen=True)
class SystevisorApplySnapshotCommand(SystevisorEngineCommand):
    snapshot: SystevisorConfigSnapshot
    request_id: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class SystevisorSetUnitDesiredCommand(SystevisorEngineCommand):
    unit_name: SystevisorUnitName
    active: bool
    request_id: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class SystevisorSetCollectionDesiredCommand(SystevisorEngineCommand):
    collection_name: SystevisorCollectionName
    active: bool
    request_id: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class SystevisorSetInstanceDesiredCommand(SystevisorEngineCommand):
    instance_id: SystevisorInstanceId
    active: bool
    request_id: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class SystevisorRestartInstanceCommand(SystevisorEngineCommand):
    instance_id: SystevisorInstanceId
    request_id: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class SystevisorShutdownCommand(SystevisorEngineCommand):
    request_id: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class SystevisorSpawnSucceededFact(SystevisorEngineFact):
    run_id: SystevisorRunId


@dc.dataclass(frozen=True)
class SystevisorSpawnFailedFact(SystevisorEngineFact):
    run_id: SystevisorRunId
    message: str


@dc.dataclass(frozen=True)
class SystevisorProcessExitedFact(SystevisorEngineFact):
    run_id: SystevisorRunId
    return_code: int


@dc.dataclass(frozen=True)
class SystevisorDeadlineReachedFact(SystevisorEngineFact):
    deadline_id: int


@dc.dataclass(frozen=True)
class SystevisorHealthProbeResultFact(SystevisorEngineFact):
    check_id: SystevisorHealthCheckId
    run_id: SystevisorRunId
    success: bool
    message: ta.Optional[str] = None
    data: ta.Mapping[str, ta.Any] = dc.field(default_factory=dict)
