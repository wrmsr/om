# ruff: noqa: UP006 UP007 UP037 UP045
import abc
import dataclasses as dc
import enum
import hashlib
import json
import math
import os
import os.path
import tempfile
import typing as ta

from omcore.io.fdio.handlers import FdioHandler
from omcore.io.fdio.manager import FdioManager
from omcore.lite.abstract import Abstract

from ..configs.models import SystevisorScheduleActionConfig
from ..configs.models import SystevisorScheduleActionKind
from ..configs.models import SystevisorScheduleConcurrencyPolicy
from ..configs.models import SystevisorScheduleConfig
from ..configs.models import SystevisorScheduleMissedPolicy
from ..configs.models import SystevisorScheduleTargetKind
from ..configs.snapshots import SystevisorConfigSnapshot
from ..control.configs import SystevisorConfigController
from ..control.configs import SystevisorConfigParticipant
from ..control.configs import SystevisorConfigPreparedChange
from ..control.operations import SystevisorOperation
from ..control.operations import SystevisorOperationStatus
from ..control.service import SystevisorControlService
from ..runtime.clocks import SystevisorClock
from ..runtime.events import SystevisorEventBus
from .cron import SystevisorCronExpression
from .cron import systevisor_parse_cron


_SYSTEVISOR_SCHEDULER_STATE_SCHEMA_VERSION = 1
_SYSTEVISOR_SCHEDULER_WALL_RECHECK_SECS = 60.
_SYSTEVISOR_SCHEDULER_MAX_DUE_SCAN = 5_000_000


class SystevisorScheduleEventKind(enum.Enum):
    FIRED = 'fired'
    SKIPPED = 'skipped'


@dc.dataclass(frozen=True)
class SystevisorScheduleEvent:
    kind: SystevisorScheduleEventKind
    schedule_name: str
    scheduled_wall_time: float
    operation_id: ta.Optional[str] = None
    reason: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class SystevisorSchedulePersistentState:
    fingerprint: str
    last_due_wall_time: float
    last_fired_wall_time: ta.Optional[float] = None
    fire_count: int = 0
    skip_count: int = 0


@dc.dataclass
class SystevisorScheduleState:
    name: str
    config: SystevisorScheduleConfig
    fingerprint: str
    last_due_wall_time: float
    next_due_wall_time: float
    last_fired_wall_time: ta.Optional[float] = None
    last_operation_id: ta.Optional[str] = None
    fire_count: int = 0
    skip_count: int = 0

    def persistent(self) -> SystevisorSchedulePersistentState:
        return SystevisorSchedulePersistentState(
            fingerprint=self.fingerprint,
            last_due_wall_time=self.last_due_wall_time,
            last_fired_wall_time=self.last_fired_wall_time,
            fire_count=self.fire_count,
            skip_count=self.skip_count,
        )


class SystevisorScheduleStateStore(Abstract):
    @abc.abstractmethod
    def load(self, path: str) -> ta.Mapping[str, SystevisorSchedulePersistentState]:
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, path: str, states: ta.Mapping[str, SystevisorSchedulePersistentState]) -> None:
        raise NotImplementedError


class SystevisorJsonScheduleStateStore(SystevisorScheduleStateStore):
    def load(self, path: str) -> ta.Mapping[str, SystevisorSchedulePersistentState]:
        try:
            with open(path) as state_file:
                value = json.load(state_file)
        except FileNotFoundError:
            return {}
        if not isinstance(value, dict) or value.get('schema_version') != _SYSTEVISOR_SCHEDULER_STATE_SCHEMA_VERSION:
            raise ValueError('invalid schedule state schema')
        raw_states = value.get('schedules')
        if not isinstance(raw_states, dict):
            raise TypeError('invalid schedule state mapping')
        states: ta.Dict[str, SystevisorSchedulePersistentState] = {}
        for name, raw_state in raw_states.items():
            if not isinstance(name, str) or not isinstance(raw_state, dict):
                raise TypeError('invalid schedule state record')
            states[name] = SystevisorSchedulePersistentState(
                fingerprint=str(raw_state['fingerprint']),
                last_due_wall_time=float(raw_state['last_due_wall_time']),
                last_fired_wall_time=(
                    None if raw_state.get('last_fired_wall_time') is None else
                    float(raw_state['last_fired_wall_time'])
                ),
                fire_count=int(raw_state.get('fire_count', 0)),
                skip_count=int(raw_state.get('skip_count', 0)),
            )
        return states

    def save(self, path: str, states: ta.Mapping[str, SystevisorSchedulePersistentState]) -> None:
        directory = os.path.dirname(path)
        os.makedirs(directory, mode=0o700, exist_ok=True)
        value = {
            'schema_version': _SYSTEVISOR_SCHEDULER_STATE_SCHEMA_VERSION,
            'schedules': {
                name: dc.asdict(state)
                for name, state in sorted(states.items())
            },
        }
        fd, temporary_path = tempfile.mkstemp(prefix='.schedules.', dir=directory)
        try:
            data = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')
            offset = 0
            while offset < len(data):
                offset += os.write(fd, data[offset:])
            os.fsync(fd)
            os.close(fd)
            fd = -1
            os.replace(temporary_path, path)
            directory_fd = os.open(directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if fd >= 0:
                os.close(fd)
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def systevisor_schedule_fingerprint(config: SystevisorScheduleConfig) -> str:
    action = config.action
    source = '|'.join((
        config.cron,
        config.timezone,
        config.missed.value,
        str(config.max_catch_up),
        config.concurrency.value,
        action.kind.value,
        action.target_kind.value if action.target_kind is not None else '',
        action.target or '',
    ))
    return hashlib.sha256(source.encode('utf-8')).hexdigest()


class SystevisorPreparedSchedulerChange(SystevisorConfigPreparedChange):
    def __init__(
            self,
            scheduler: 'SystevisorScheduler',
            states: ta.Mapping[str, SystevisorScheduleState],
            crons: ta.Mapping[str, SystevisorCronExpression],
            state_path: ta.Optional[str],
    ) -> None:
        self._scheduler = scheduler
        self._states = states
        self._crons = crons
        self._state_path = state_path
        self._finished = False

    def commit(self) -> None:
        if self._finished:
            raise RuntimeError('scheduler change is already finished')
        self._scheduler._commit(self._states, self._crons, self._state_path)  # noqa: SLF001
        self._finished = True

    def rollback(self) -> None:
        self._finished = True


class SystevisorScheduler(FdioHandler, SystevisorConfigParticipant):
    def __init__(
            self,
            config_controller: SystevisorConfigController,
            control: SystevisorControlService,
            operations_clock: SystevisorClock,
            fdio_manager: FdioManager,
            event_bus: SystevisorEventBus,
            state_store: SystevisorScheduleStateStore,
    ) -> None:
        self._control = control
        self._clock = operations_clock
        self._event_bus = event_bus
        self._state_store = state_store
        self._states: ta.Dict[str, SystevisorScheduleState] = {}
        self._crons: ta.Dict[str, SystevisorCronExpression] = {}
        self._state_path: ta.Optional[str] = None
        self._state_directory_override: ta.Optional[str] = None
        self._closed = False
        config_controller.add_participant(self)
        fdio_manager.register(self)

    @property
    def states(self) -> ta.Mapping[str, SystevisorScheduleState]:
        return self._states

    def fd(self) -> int:
        return -1

    def set_state_directory_override(self, state_directory: ta.Optional[str]) -> None:
        if self._states:
            raise RuntimeError('scheduler state directory override must be set before configuration')
        self._state_directory_override = state_directory

    @property
    def closed(self) -> bool:
        return self._closed

    def _persistent_states(self) -> ta.Mapping[str, SystevisorSchedulePersistentState]:
        return {name: state.persistent() for name, state in self._states.items()}

    def prepare(self, snapshot: SystevisorConfigSnapshot) -> SystevisorConfigPreparedChange:
        state_directory = (
            self._state_directory_override
            if self._state_directory_override is not None else
            snapshot.config.manager.state_directory
        )
        state_path = os.path.join(state_directory, 'schedules.json') if state_directory is not None else None
        persisted = (
            self._persistent_states() if self._states else
            self._state_store.load(state_path) if state_path is not None else
            {}
        )
        now = self._clock.wall_time()
        baseline = math.floor(now / 60.) * 60.
        states: ta.Dict[str, SystevisorScheduleState] = {}
        crons: ta.Dict[str, SystevisorCronExpression] = {}
        for name, config in snapshot.config.schedules.items():
            if not config.enabled:
                continue
            cron = systevisor_parse_cron(config.cron)
            fingerprint = systevisor_schedule_fingerprint(config)
            previous = persisted.get(name)
            if previous is None or previous.fingerprint != fingerprint:
                previous = SystevisorSchedulePersistentState(fingerprint, baseline)
            current = self._states.get(name)
            states[name] = SystevisorScheduleState(
                name=name,
                config=config,
                fingerprint=fingerprint,
                last_due_wall_time=previous.last_due_wall_time,
                next_due_wall_time=cron.next_after(previous.last_due_wall_time),
                last_fired_wall_time=previous.last_fired_wall_time,
                last_operation_id=(
                    current.last_operation_id
                    if current is not None and current.fingerprint == fingerprint else
                    None
                ),
                fire_count=previous.fire_count,
                skip_count=previous.skip_count,
            )
            crons[name] = cron
        return SystevisorPreparedSchedulerChange(self, states, crons, state_path)

    def _commit(
            self,
            states: ta.Mapping[str, SystevisorScheduleState],
            crons: ta.Mapping[str, SystevisorCronExpression],
            state_path: ta.Optional[str],
    ) -> None:
        self._states = dict(states)
        self._crons = dict(crons)
        self._state_path = state_path
        self._persist()

    def _persist(self) -> None:
        if self._state_path is not None:
            try:
                self._state_store.save(self._state_path, self._persistent_states())
            except OSError as exc:
                self._event_bus.publish('schedule.persistence_failed', {
                    'path': self._state_path,
                    'message': str(exc),
                }, self._clock.monotonic())

    def next_deadline(self) -> ta.Optional[float]:
        if self._closed or not self._states:
            return None
        monotonic = self._clock.monotonic()
        wall_time = self._clock.wall_time()
        due_at = min(state.next_due_wall_time for state in self._states.values())
        return min(
            monotonic + max(0., due_at - wall_time),
            monotonic + _SYSTEVISOR_SCHEDULER_WALL_RECHECK_SECS,
        )

    def _operation_active(self, state: SystevisorScheduleState) -> bool:
        if state.last_operation_id is None:
            return False
        operation = self._control.operations.get(state.last_operation_id)
        return operation is not None and operation.status is SystevisorOperationStatus.PENDING

    def _execute_action(self, action: SystevisorScheduleActionConfig) -> SystevisorOperation:
        if action.kind is SystevisorScheduleActionKind.SHUTDOWN:
            return self._control.shutdown()
        target = ta.cast(str, action.target)
        target_kind = ta.cast(SystevisorScheduleTargetKind, action.target_kind)
        if action.kind is SystevisorScheduleActionKind.RESTART:
            return (
                self._control.restart_unit(target)
                if target_kind is SystevisorScheduleTargetKind.UNIT else
                self._control.restart_instance(target)
            )
        active = action.kind is SystevisorScheduleActionKind.START
        if target_kind is SystevisorScheduleTargetKind.UNIT:
            return self._control.set_unit(target, active)
        if target_kind is SystevisorScheduleTargetKind.COLLECTION:
            return self._control.set_collection(target, active)
        return self._control.set_instance(target, active)

    def _publish(
            self,
            kind: SystevisorScheduleEventKind,
            state: SystevisorScheduleState,
            scheduled_wall_time: float,
            *,
            operation_id: ta.Optional[str] = None,
            reason: ta.Optional[str] = None,
    ) -> None:
        self._event_bus.publish('schedule', SystevisorScheduleEvent(
            kind=kind,
            schedule_name=state.name,
            scheduled_wall_time=scheduled_wall_time,
            operation_id=operation_id,
            reason=reason,
        ), self._clock.monotonic())

    def _run_state(self, state: SystevisorScheduleState, now: float) -> None:
        cron = self._crons[state.name]
        catch_up: ta.List[float] = []
        due_count = 0
        latest_due: ta.Optional[float] = None
        next_due = state.next_due_wall_time
        while next_due <= now and due_count < _SYSTEVISOR_SCHEDULER_MAX_DUE_SCAN:
            due_count += 1
            latest_due = next_due
            if len(catch_up) < state.config.max_catch_up:
                catch_up.append(next_due)
            next_due = cron.next_after(next_due)
        if latest_due is None:
            return
        if next_due <= now:
            raise RuntimeError(f'schedule backlog exceeds {_SYSTEVISOR_SCHEDULER_MAX_DUE_SCAN} occurrences')

        latest_is_current = now - latest_due < 60.
        if due_count == 1 and latest_is_current:
            selected = [latest_due]
        elif state.config.missed is SystevisorScheduleMissedPolicy.SKIP:
            selected = [latest_due] if latest_is_current else []
        elif state.config.missed is SystevisorScheduleMissedPolicy.LATEST:
            selected = [latest_due]
        else:
            selected = catch_up

        fired_count = 0
        for scheduled_wall_time in selected:
            if (
                    state.config.concurrency is SystevisorScheduleConcurrencyPolicy.SKIP and
                    self._operation_active(state)
            ):
                self._publish(
                    SystevisorScheduleEventKind.SKIPPED,
                    state,
                    scheduled_wall_time,
                    reason='previous operation is still pending',
                )
                continue
            operation = self._execute_action(state.config.action)
            state.last_operation_id = operation.operation_id
            state.last_fired_wall_time = scheduled_wall_time
            state.fire_count += 1
            fired_count += 1
            self._publish(
                SystevisorScheduleEventKind.FIRED,
                state,
                scheduled_wall_time,
                operation_id=operation.operation_id,
            )
        skipped_count = due_count - fired_count
        state.skip_count += skipped_count
        missed_policy_skips = due_count - len(selected)
        if missed_policy_skips:
            self._publish(
                SystevisorScheduleEventKind.SKIPPED,
                state,
                latest_due,
                reason=f'missed-run policy skipped {missed_policy_skips} occurrence(s)',
            )
        state.last_due_wall_time = latest_due
        state.next_due_wall_time = next_due

    def on_timeout(self) -> None:
        now = self._clock.wall_time()
        for state in self._states.values():
            self._run_state(state, now)
        self._persist()

    def close(self) -> None:
        self._closed = True
        self._states.clear()
        self._crons.clear()
