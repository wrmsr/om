# @om-lite
# ruff: noqa: UP006 UP007 UP037 UP045
import dataclasses as dc
import enum
import sys
import typing as ta

from omcore.io.fdio.handlers import FdioHandler
from omcore.io.fdio.manager import FdioManager

from ..configs.models import SystevisorObservationConfig
from ..configs.snapshots import SystevisorConfigSnapshot
from ..control.configs import SystevisorConfigController
from ..control.configs import SystevisorConfigParticipant
from ..control.configs import SystevisorConfigPreparedChange
from ..core.identities import SystevisorInstanceId
from ..core.identities import SystevisorRunId
from ..runtime.clocks import SystevisorClock
from ..runtime.events import SystevisorEventBus
from ..runtime.processes import SystevisorOwnedProcessPurpose
from ..runtime.processes import SystevisorOwnedProcessState
from ..runtime.processes import SystevisorOwnedProcessStatus
from ..runtime.processes import SystevisorProcessManager
from .cgroups import SystevisorCgroupCounters
from .cgroups import SystevisorCgroupManager
from .namespaces import systevisor_namespace_flags
from .sampling import SystevisorProcessResourceCounters
from .sampling import SystevisorProcessResourceSampler
from .sockets import SystevisorInheritedSocketRegistry


class SystevisorResourceEventKind(enum.Enum):
    SAMPLED = 'sampled'
    FAILED = 'failed'
    RECOVERED = 'recovered'
    ENDED = 'ended'


@dc.dataclass(frozen=True)
class SystevisorResourceRates:
    cpu_percent: ta.Optional[float] = None
    read_bytes_per_sec: ta.Optional[float] = None
    write_bytes_per_sec: ta.Optional[float] = None


@dc.dataclass(frozen=True)
class SystevisorResourceSample:
    sample_schema_version: int
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    pid: int
    monotonic_at: float
    wall_time: float
    process: SystevisorProcessResourceCounters
    rates: SystevisorResourceRates
    cgroup: ta.Optional[SystevisorCgroupCounters] = None


@dc.dataclass(frozen=True)
class SystevisorResourceRunState:
    state_schema_version: int
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    active: bool
    first_observed_at: float
    last_observed_at: ta.Optional[float]
    ended_at: ta.Optional[float]
    sample_count: int
    failure_count: int
    consecutive_failures: int
    last_error: ta.Optional[str]
    sample: ta.Optional[SystevisorResourceSample]


@dc.dataclass(frozen=True)
class SystevisorResourceEvent:
    kind: SystevisorResourceEventKind
    run_id: SystevisorRunId
    instance_id: SystevisorInstanceId
    sample_count: int
    failure_count: int
    message: ta.Optional[str] = None


def _systevisor_resource_rate(
        current: ta.Optional[ta.Union[int, float]],
        previous: ta.Optional[ta.Union[int, float]],
        elapsed: float,
) -> ta.Optional[float]:
    if current is None or previous is None or elapsed <= 0 or current < previous:
        return None
    return (float(current) - float(previous)) / elapsed


def _systevisor_resource_rates(
        counters: SystevisorProcessResourceCounters,
        previous: ta.Optional[SystevisorResourceSample],
        now: float,
) -> SystevisorResourceRates:
    if previous is None:
        return SystevisorResourceRates()
    elapsed = now - previous.monotonic_at
    current_cpu = (
        None if counters.cpu_user_secs is None or counters.cpu_system_secs is None else
        counters.cpu_user_secs + counters.cpu_system_secs
    )
    previous_counters = previous.process
    previous_cpu = (
        None if previous_counters.cpu_user_secs is None or previous_counters.cpu_system_secs is None else
        previous_counters.cpu_user_secs + previous_counters.cpu_system_secs
    )
    cpu_rate = _systevisor_resource_rate(current_cpu, previous_cpu, elapsed)
    return SystevisorResourceRates(
        cpu_percent=None if cpu_rate is None else cpu_rate * 100.,
        read_bytes_per_sec=_systevisor_resource_rate(
            counters.read_bytes,
            previous_counters.read_bytes,
            elapsed,
        ),
        write_bytes_per_sec=_systevisor_resource_rate(
            counters.write_bytes,
            previous_counters.write_bytes,
            elapsed,
        ),
    )


class SystevisorPreparedResourceChange(SystevisorConfigPreparedChange):
    def __init__(
            self,
            owner: 'SystevisorResourceObserver',
            config: SystevisorObservationConfig,
    ) -> None:
        self._owner = owner
        self._config = config
        self._finished = False

    def commit(self) -> None:
        if self._finished:
            raise RuntimeError('resource configuration change is already finished')
        self._owner._cgroup_manager.commit_config()  # noqa: SLF001
        self._owner._apply_config(self._config)  # noqa: SLF001
        self._finished = True

    def rollback(self) -> None:
        if self._finished:
            return
        self._owner._cgroup_manager.rollback_config()  # noqa: SLF001
        self._finished = True


class SystevisorResourceObserver(FdioHandler, SystevisorConfigParticipant):
    def __init__(
            self,
            config_controller: SystevisorConfigController,
            process_manager: SystevisorProcessManager,
            process_sampler: SystevisorProcessResourceSampler,
            cgroup_manager: SystevisorCgroupManager,
            socket_registry: SystevisorInheritedSocketRegistry,
            clock: SystevisorClock,
            fdio_manager: FdioManager,
            event_bus: SystevisorEventBus,
    ) -> None:
        self._process_manager = process_manager
        self._process_sampler = process_sampler
        self._cgroup_manager = cgroup_manager
        self._socket_registry = socket_registry
        self._clock = clock
        self._event_bus = event_bus
        self._config = SystevisorObservationConfig(enabled=False)
        self._states: ta.Dict[SystevisorRunId, SystevisorResourceRunState] = {}
        self._next_sample_at: ta.Optional[float] = None
        self._closed = False
        cgroup_manager.set_wake_callback(self._wake_for_cgroup_cleanup)
        config_controller.add_participant(self)
        fdio_manager.register(self)

    @property
    def states(self) -> ta.Mapping[SystevisorRunId, SystevisorResourceRunState]:
        return self._states

    @property
    def cgroup_states(self) -> ta.Mapping[SystevisorRunId, ta.Any]:
        return self._cgroup_manager.states

    @property
    def inherited_sockets(self) -> ta.Mapping[str, ta.Any]:
        return self._socket_registry.sockets

    def fd(self) -> int:
        return -1

    @property
    def closed(self) -> bool:
        return self._closed

    def close(self) -> None:
        self._closed = True
        self._next_sample_at = None

    def prepare(self, snapshot: SystevisorConfigSnapshot) -> SystevisorConfigPreparedChange:
        if sys.platform != 'linux' and any(
                systevisor_namespace_flags(unit.resources.namespaces)
                for unit in snapshot.config.units.values()
        ):
            raise RuntimeError('namespace isolation is supported only on Linux')
        self._socket_registry.require(
            socket_name
            for unit in snapshot.config.units.values()
            for socket_name in unit.resources.inherited_sockets
        )
        self._cgroup_manager.prepare_config(snapshot)
        return SystevisorPreparedResourceChange(self, snapshot.config.manager.observation)

    def _apply_config(self, config: SystevisorObservationConfig) -> None:
        was_enabled = self._config.enabled
        self._config = config
        if config.enabled:
            if not was_enabled or self._next_sample_at is None:
                self._next_sample_at = self._clock.monotonic()
        else:
            self._next_sample_at = (
                self._clock.monotonic()
                if self._cgroup_manager.needs_sweep() else
                None
            )

    def _wake_for_cgroup_cleanup(self) -> None:
        if not self._closed:
            self._next_sample_at = self._clock.monotonic()

    def next_deadline(self) -> ta.Optional[float]:
        return None if self._closed else self._next_sample_at

    def _publish(
            self,
            kind: SystevisorResourceEventKind,
            state: SystevisorResourceRunState,
            message: ta.Optional[str] = None,
    ) -> None:
        self._event_bus.publish('resource', SystevisorResourceEvent(
            kind=kind,
            run_id=state.run_id,
            instance_id=state.instance_id,
            sample_count=state.sample_count,
            failure_count=state.failure_count,
            message=message,
        ), self._clock.monotonic())

    def _sample_process(self, process: SystevisorOwnedProcessState, now: float, wall_time: float) -> None:
        previous_state = self._states.get(process.run_id)
        try:
            counters = self._process_sampler.sample(process)
            cgroup = self._cgroup_manager.sample(process.run_id)
        except Exception as exc:  # noqa: BLE001
            state = SystevisorResourceRunState(
                state_schema_version=1,
                run_id=process.run_id,
                instance_id=process.instance_id,
                active=True,
                first_observed_at=(now if previous_state is None else previous_state.first_observed_at),
                last_observed_at=(None if previous_state is None else previous_state.last_observed_at),
                ended_at=None,
                sample_count=(0 if previous_state is None else previous_state.sample_count),
                failure_count=(0 if previous_state is None else previous_state.failure_count) + 1,
                consecutive_failures=(0 if previous_state is None else previous_state.consecutive_failures) + 1,
                last_error=f'{type(exc).__name__}: {exc}',
                sample=(None if previous_state is None else previous_state.sample),
            )
            self._states[process.run_id] = state
            if state.consecutive_failures == 1:
                self._publish(SystevisorResourceEventKind.FAILED, state, state.last_error)
            return

        previous_sample = None if previous_state is None else previous_state.sample
        sample = SystevisorResourceSample(
            sample_schema_version=1,
            run_id=process.run_id,
            instance_id=process.instance_id,
            pid=process.pid,
            monotonic_at=now,
            wall_time=wall_time,
            process=counters,
            rates=_systevisor_resource_rates(counters, previous_sample, now),
            cgroup=cgroup,
        )
        state = SystevisorResourceRunState(
            state_schema_version=1,
            run_id=process.run_id,
            instance_id=process.instance_id,
            active=True,
            first_observed_at=(now if previous_state is None else previous_state.first_observed_at),
            last_observed_at=now,
            ended_at=None,
            sample_count=(0 if previous_state is None else previous_state.sample_count) + 1,
            failure_count=(0 if previous_state is None else previous_state.failure_count),
            consecutive_failures=0,
            last_error=None,
            sample=sample,
        )
        self._states[process.run_id] = state
        if previous_state is not None and previous_state.consecutive_failures:
            self._publish(SystevisorResourceEventKind.RECOVERED, state)
        if self._config.emit_events:
            self._publish(SystevisorResourceEventKind.SAMPLED, state)

    def _mark_ended(self, live_run_ids: ta.AbstractSet[SystevisorRunId], now: float) -> None:
        for run_id, state in tuple(self._states.items()):
            if state.active and run_id not in live_run_ids:
                ended = dc.replace(state, active=False, ended_at=now)
                self._states[run_id] = ended
                self._publish(SystevisorResourceEventKind.ENDED, ended)

        ended_states = sorted(
            (state for state in self._states.values() if not state.active),
            key=lambda state: (state.ended_at or 0., int(state.run_id)),
            reverse=True,
        )
        for state in ended_states[self._config.retained_runs:]:
            self._states.pop(state.run_id, None)
        self._cgroup_manager.prune(frozenset(self._states))

    def sample_now(self) -> None:
        if self._closed:
            return
        now = self._clock.monotonic()
        wall_time = self._clock.wall_time()
        processes = tuple(
            process
            for process in self._process_manager.snapshot_states()
            if (
                process.run_id > 0 and
                process.purpose is SystevisorOwnedProcessPurpose.SERVICE and
                process.status in {SystevisorOwnedProcessStatus.SPAWNING, SystevisorOwnedProcessStatus.RUNNING} and
                process.observe_resources
            )
        )
        live_run_ids = {process.run_id for process in processes}
        for process in processes:
            self._sample_process(process, now, wall_time)
        self._mark_ended(live_run_ids, now)
        self._cgroup_manager.sweep()

    def on_timeout(self) -> None:
        if self._config.enabled:
            self.sample_now()
        else:
            self._cgroup_manager.sweep()
        if not self._closed and (self._config.enabled or self._cgroup_manager.needs_sweep()):
            self._next_sample_at = self._clock.monotonic() + self._config.interval_secs
        else:
            self._next_sample_at = None
