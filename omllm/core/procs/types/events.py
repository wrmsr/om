"""
Lifecycle events published by a `ProcessManager`. Output is *not* an event here - live output is consumed via
`OutputSpool.subscribe()`. Explicitly not a marshal polymorphism.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .ids import ProcessId
from .states import ProcessState


##


@dc.dataclass(frozen=True)
class ProcessEvent(lang.Abstract):
    pass


@dc.dataclass(frozen=True, kw_only=True)
class ProcessLifecycleEvent(ProcessEvent, lang.Abstract):
    process_id: ProcessId
    pid: int
    scope_path: ta.Sequence[str]


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ProcessSpawnedEvent(ProcessLifecycleEvent):
    argv: ta.Sequence[str]
    name: str | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ProcessExitedEvent(ProcessLifecycleEvent):
    returncode: int


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ProcessReapedEvent(ProcessLifecycleEvent):
    returncode: int


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ProcessAbandonedEvent(ProcessLifecycleEvent):
    state: ProcessState


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ProcessPoisonedEvent(ProcessLifecycleEvent):
    reason: str


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ProcessReparentedEvent(ProcessLifecycleEvent):
    old_scope_path: ta.Sequence[str]


#


@dc.dataclass(frozen=True, kw_only=True)
class ScopeEvent(ProcessEvent, lang.Abstract):
    scope_path: ta.Sequence[str]


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScopeOpenedEvent(ScopeEvent):
    pass


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class ScopeClosedEvent(ScopeEvent):
    num_processes: int
    num_abandoned: int = 0
