# ruff: noqa: UP006 UP007 UP045
import typing as ta

from ..configs.models import SystevisorDependencyCondition
from ..configs.models import SystevisorHealthRecovery
from ..configs.models import SystevisorHealthRole
from ..configs.models import SystevisorRestartMode
from ..configs.models import SystevisorUnitKind
from ..configs.snapshots import SystevisorConfigSnapshot
from ..configs.snapshots import SystevisorDesiredInstanceSpec
from ..configs.snapshots import systevisor_digest_config_object
from .changes import SystevisorUnitChange
from .changes import systevisor_classify_unit_change
from .effects import SystevisorApplyLiveConfigEffect
from .effects import SystevisorEngineEffect
from .effects import SystevisorRunHealthProbeEffect
from .effects import SystevisorScheduleDeadlineEffect
from .effects import SystevisorSignalProcessEffect
from .effects import SystevisorSpawnProcessEffect
from .events import SystevisorEngineOutput
from .events import SystevisorEvent
from .events import SystevisorEventKind
from .identities import SystevisorCollectionName
from .identities import SystevisorHealthCheckId
from .identities import SystevisorInstanceId
from .identities import SystevisorRunId
from .identities import SystevisorUnitName
from .inputs import SystevisorApplySnapshotCommand
from .inputs import SystevisorDeadlineReachedFact
from .inputs import SystevisorEngineInput
from .inputs import SystevisorForwardSignalCommand
from .inputs import SystevisorHealthProbeResultFact
from .inputs import SystevisorProcessExitedFact
from .inputs import SystevisorRestartInstanceCommand
from .inputs import SystevisorSetCollectionDesiredCommand
from .inputs import SystevisorSetInstanceDesiredCommand
from .inputs import SystevisorSetUnitDesiredCommand
from .inputs import SystevisorShutdownCommand
from .inputs import SystevisorSpawnFailedFact
from .inputs import SystevisorSpawnSucceededFact
from .signals import systevisor_normalize_signal_name
from .state import SystevisorCollectionState
from .state import SystevisorEngineState
from .state import SystevisorHealthProbeState
from .state import SystevisorInstanceState
from .states import SystevisorCollectionStatus
from .states import SystevisorDeadlineKind
from .states import SystevisorDesiredOrigin
from .states import SystevisorDesiredState
from .states import SystevisorHealthStatus
from .states import SystevisorProcessState
from .states import SystevisorSignalReason
from .states import SystevisorUnitChangeKind


_SYSTEVISOR_ENGINE_LIVE_PROCESS_STATES = frozenset({
    SystevisorProcessState.STARTING,
    SystevisorProcessState.RUNNING,
    SystevisorProcessState.STOPPING,
})

_SYSTEVISOR_ENGINE_TERMINAL_PROCESS_STATES = frozenset({
    SystevisorProcessState.STOPPED,
    SystevisorProcessState.EXITED,
    SystevisorProcessState.FATAL,
})


class SystevisorEngine:
    def __init__(self, state: ta.Optional[SystevisorEngineState] = None) -> None:
        self._state = state if state is not None else SystevisorEngineState()
        self._effects: ta.List[SystevisorEngineEffect] = []
        self._events: ta.List[SystevisorEvent] = []

    @property
    def state(self) -> SystevisorEngineState:
        return self._state

    def rehydrate(self, state: SystevisorEngineState) -> None:
        if self._state != SystevisorEngineState() or self._effects or self._events:
            raise RuntimeError('engine state can only be rehydrated before use')
        self._state = state

    def step(self, engine_input: SystevisorEngineInput, now: float) -> SystevisorEngineOutput:
        if now < self._state.last_now:
            raise ValueError(now)
        self._state.last_now = now
        self._effects = []
        self._events = []

        if isinstance(engine_input, SystevisorApplySnapshotCommand):
            self._apply_snapshot(engine_input, now)
        elif isinstance(engine_input, SystevisorSetUnitDesiredCommand):
            self._set_unit_desired(engine_input, now)
        elif isinstance(engine_input, SystevisorSetCollectionDesiredCommand):
            self._set_collection_desired(engine_input, now)
        elif isinstance(engine_input, SystevisorSetInstanceDesiredCommand):
            self._set_instance_desired(engine_input, now)
        elif isinstance(engine_input, SystevisorRestartInstanceCommand):
            self._restart_instance(engine_input, now)
        elif isinstance(engine_input, SystevisorForwardSignalCommand):
            self._forward_signal(engine_input, now)
        elif isinstance(engine_input, SystevisorShutdownCommand):
            self._shutdown(engine_input, now)
        elif isinstance(engine_input, SystevisorSpawnSucceededFact):
            self._spawn_succeeded(engine_input, now)
        elif isinstance(engine_input, SystevisorSpawnFailedFact):
            self._spawn_failed(engine_input, now)
        elif isinstance(engine_input, SystevisorProcessExitedFact):
            self._process_exited(engine_input, now)
        elif isinstance(engine_input, SystevisorDeadlineReachedFact):
            self._deadline_reached(engine_input, now)
        elif isinstance(engine_input, SystevisorHealthProbeResultFact):
            self._health_probe_result(engine_input, now)
        else:
            raise TypeError(engine_input)

        self._stabilize(now)
        return SystevisorEngineOutput(effects=tuple(self._effects), events=tuple(self._events))

    def _emit_event(
            self,
            kind: SystevisorEventKind,
            now: float,
            *,
            instance: ta.Optional[SystevisorInstanceState] = None,
            run_id: ta.Optional[SystevisorRunId] = None,
            request_id: ta.Optional[str] = None,
            data: ta.Optional[ta.Mapping[str, ta.Any]] = None,
    ) -> None:
        self._state.event_sequence += 1
        self._events.append(SystevisorEvent(
            sequence=self._state.event_sequence,
            at=now,
            kind=kind,
            instance_id=instance.instance_id if instance is not None else None,
            run_id=run_id if run_id is not None else (instance.run_id if instance is not None else None),
            request_id=request_id,
            data=dict(data or {}),
        ))

    def _transition(
            self,
            instance: SystevisorInstanceState,
            process_state: SystevisorProcessState,
            now: float,
            reason: str,
    ) -> None:
        if instance.process_state is process_state:
            return
        previous = instance.process_state
        instance.process_state = process_state
        self._emit_event(
            SystevisorEventKind.STATE_CHANGED,
            now,
            instance=instance,
            data={'from': previous.value, 'to': process_state.value, 'reason': reason},
        )

    def _change_desired(
            self,
            instance: SystevisorInstanceState,
            desired_state: SystevisorDesiredState,
            desired_origin: SystevisorDesiredOrigin,
            now: float,
            *,
            request_id: ta.Optional[str] = None,
    ) -> None:
        previous = instance.desired_state
        previous_origin = instance.desired_origin
        instance.desired_state = desired_state
        instance.desired_origin = desired_origin
        if previous is not desired_state or previous_origin is not desired_origin:
            self._emit_event(
                SystevisorEventKind.DESIRED_CHANGED,
                now,
                instance=instance,
                request_id=request_id,
                data={
                    'from': previous.value,
                    'to': desired_state.value,
                    'origin': desired_origin.value,
                },
            )

    def _reject_command(self, message: str, now: float, request_id: ta.Optional[str]) -> None:
        self._emit_event(
            SystevisorEventKind.COMMAND_REJECTED,
            now,
            request_id=request_id,
            data={'message': message},
        )

    def _emit_collection_event(
            self,
            kind: SystevisorEventKind,
            collection: SystevisorCollectionState,
            now: float,
            *,
            request_id: ta.Optional[str] = None,
            data: ta.Optional[ta.Mapping[str, ta.Any]] = None,
    ) -> None:
        event_data = {'collection': collection.name}
        event_data.update(data or {})
        self._emit_event(kind, now, request_id=request_id, data=event_data)

    def _find_run(self, run_id: SystevisorRunId) -> ta.Optional[SystevisorInstanceState]:
        for instance in self._state.instances.values():
            if instance.run_id == run_id:
                return instance
        return None

    def _stale_fact(self, fact_name: str, run_id: ta.Optional[SystevisorRunId], now: float) -> None:
        self._emit_event(
            SystevisorEventKind.STALE_FACT_IGNORED,
            now,
            run_id=run_id,
            data={'fact': fact_name},
        )

    def _new_instance(
            self,
            spec: SystevisorDesiredInstanceSpec,
            desired_state: SystevisorDesiredState,
            desired_origin: SystevisorDesiredOrigin,
            now: float,
    ) -> SystevisorInstanceState:
        instance = SystevisorInstanceState(
            instance_id=spec.instance_id,
            unit_name=spec.unit_name,
            slot=spec.slot,
            desired_spec=spec,
            desired_state=desired_state,
            desired_origin=desired_origin,
            health={
                probe.name: self._new_health_probe_state(probe)
                for probe in spec.unit.health
            },
        )
        self._state.instances[spec.instance_id] = instance
        self._emit_event(
            SystevisorEventKind.INSTANCE_ADDED,
            now,
            instance=instance,
            data={'spec_digest': spec.spec_digest},
        )
        return instance

    def _configured_desired_from_snapshot(
            self,
            spec: SystevisorDesiredInstanceSpec,
            snapshot: ta.Optional[SystevisorConfigSnapshot],
    ) -> ta.Tuple[SystevisorDesiredState, SystevisorDesiredOrigin]:
        if self._state.shutting_down:
            return SystevisorDesiredState.INACTIVE, SystevisorDesiredOrigin.SHUTDOWN
        override = self._state.unit_desired_overrides.get(spec.unit_name)
        if override is not None:
            return (
                SystevisorDesiredState.ACTIVE if override else SystevisorDesiredState.INACTIVE,
                SystevisorDesiredOrigin.MANUAL,
            )

        active_collection = False
        if snapshot is not None:
            for collection_name, config in snapshot.config.collections.items():
                if spec.unit_name not in config.units:
                    continue
                collection = self._state.collections.get(SystevisorCollectionName(collection_name))
                if collection is None:
                    continue
                if (
                        not collection.desired_active and
                        collection.desired_origin in {
                            SystevisorDesiredOrigin.MANUAL,
                            SystevisorDesiredOrigin.COLLECTION_FAILURE,
                        }
                ):
                    return SystevisorDesiredState.INACTIVE, SystevisorDesiredOrigin.COLLECTION
                active_collection = active_collection or collection.desired_active

        if active_collection:
            return SystevisorDesiredState.ACTIVE, SystevisorDesiredOrigin.COLLECTION
        if self._state.startup_collection is not None:
            return SystevisorDesiredState.INACTIVE, SystevisorDesiredOrigin.CONFIG
        return (
            SystevisorDesiredState.ACTIVE if spec.unit.autostart else SystevisorDesiredState.INACTIVE,
            SystevisorDesiredOrigin.CONFIG,
        )

    def _sync_collections(self, snapshot: SystevisorConfigSnapshot, now: float) -> None:
        previous_names = set(self._state.collections)
        desired_names = {SystevisorCollectionName(name) for name in snapshot.config.collections}
        for name in sorted(desired_names - previous_names):
            config = snapshot.config.collections[name]
            selected = self._state.startup_collection == name
            desired_active = selected or (self._state.startup_collection is None and config.autostart)
            collection = SystevisorCollectionState(
                name=name,
                desired_active=desired_active,
                desired_origin=(
                    SystevisorDesiredOrigin.MANUAL if selected else SystevisorDesiredOrigin.CONFIG
                ),
                activation_sequence=1 if desired_active else 0,
            )
            self._state.collections[name] = collection
            self._emit_collection_event(
                SystevisorEventKind.COLLECTION_ADDED,
                collection,
                now,
                data={'desired_active': desired_active},
            )

        for name in sorted(desired_names & previous_names):
            collection = self._state.collections[name]
            if collection.desired_origin is SystevisorDesiredOrigin.CONFIG:
                config = snapshot.config.collections[name]
                collection.desired_active = (
                    self._state.startup_collection == name or
                    (self._state.startup_collection is None and config.autostart)
                )

        for name in sorted(previous_names - desired_names):
            collection = self._state.collections.pop(name)
            self._emit_collection_event(SystevisorEventKind.COLLECTION_REMOVED, collection, now)

    def _refresh_configured_desires(self, snapshot: SystevisorConfigSnapshot, now: float) -> None:
        self._reconcile_dependency_desires(snapshot, now)

    def _apply_snapshot(self, command: SystevisorApplySnapshotCommand, now: float) -> None:
        previous_snapshot = self._state.snapshot
        if previous_snapshot is not None and previous_snapshot.digest == command.snapshot.digest:
            self._state.snapshot = command.snapshot
            self._emit_event(
                SystevisorEventKind.CONFIG_UNCHANGED,
                now,
                request_id=command.request_id,
                data={'digest': command.snapshot.digest, 'generation': self._state.config_generation},
            )
            return

        self._sync_collections(command.snapshot, now)

        previous_ids = set(self._state.instances)
        desired_ids = set(command.snapshot.instances)
        added_ids = desired_ids - previous_ids
        removed_ids = previous_ids - desired_ids
        retained_ids = desired_ids & previous_ids

        for instance_id in sorted(added_ids):
            spec = command.snapshot.instances[instance_id]
            desired_state, desired_origin = self._configured_desired_from_snapshot(spec, command.snapshot)
            self._new_instance(spec, desired_state, desired_origin, now)

        for instance_id in sorted(retained_ids):
            instance = self._state.instances[instance_id]
            new_spec = command.snapshot.instances[instance_id]
            change = systevisor_classify_unit_change(instance.desired_spec.unit, new_spec.unit)
            instance.desired_spec = new_spec

            if instance.desired_origin in {
                    SystevisorDesiredOrigin.CONFIG,
                    SystevisorDesiredOrigin.COLLECTION,
            }:
                desired_state, desired_origin = self._configured_desired_from_snapshot(new_spec, command.snapshot)
                self._change_desired(instance, desired_state, desired_origin, now)

            self._apply_unit_change(instance, change, now)

        for instance_id in sorted(removed_ids):
            instance = self._state.instances[instance_id]
            self._change_desired(instance, SystevisorDesiredState.REMOVED, SystevisorDesiredOrigin.CONFIG, now)

        self._state.snapshot = command.snapshot
        self._state.config_generation += 1
        self._emit_event(
            SystevisorEventKind.CONFIG_APPLIED,
            now,
            request_id=command.request_id,
            data={
                'digest': command.snapshot.digest,
                'previous_digest': previous_snapshot.digest if previous_snapshot is not None else None,
                'generation': self._state.config_generation,
                'added': len(added_ids),
                'removed': len(removed_ids),
                'retained': len(retained_ids),
            },
        )

    def _apply_unit_change(
            self,
            instance: SystevisorInstanceState,
            change: SystevisorUnitChange,
            now: float,
    ) -> None:
        if change.kind is SystevisorUnitChangeKind.NONE:
            return

        if change.kind is SystevisorUnitChangeKind.LIVE:
            if 'health' in change.live_paths:
                self._sync_health_config(instance, now)
            if instance.run_id is not None and instance.process_state in _SYSTEVISOR_ENGINE_LIVE_PROCESS_STATES:
                self._effects.append(SystevisorApplyLiveConfigEffect(
                    run_id=instance.run_id,
                    instance_id=instance.instance_id,
                    spec=instance.desired_spec,
                    changed_paths=change.live_paths,
                ))
                self._emit_event(
                    SystevisorEventKind.PROCESS_CONFIG_UPDATED,
                    now,
                    instance=instance,
                    data={'changed_paths': tuple(change.live_paths)},
                )
            instance.applied_spec_digest = instance.desired_spec.spec_digest
            return

        instance.restart_requested = instance.desired_state is SystevisorDesiredState.ACTIVE
        if (
                instance.process_state is SystevisorProcessState.BACKOFF or
                instance.process_state in _SYSTEVISOR_ENGINE_TERMINAL_PROCESS_STATES
        ):
            instance.deadline_id = None
            instance.deadline_kind = None
            instance.deadline_at = None
            instance.run_id = None
            instance.spawn_confirmed = False
            instance.applied_spec_digest = None
            instance.start_failures = 0
            instance.completed_successfully = False
            if instance.desired_state is SystevisorDesiredState.ACTIVE:
                self._transition(instance, SystevisorProcessState.STOPPED, now, 'restart_required_config')

    def _set_unit_desired(self, command: SystevisorSetUnitDesiredCommand, now: float) -> None:
        if self._state.snapshot is None or command.unit_name not in self._state.snapshot.config.units:
            self._reject_command(f'unknown unit: {command.unit_name}', now, command.request_id)
            return
        if command.active and self._state.shutting_down:
            self._reject_command('engine is shutting down', now, command.request_id)
            return

        self._state.unit_desired_overrides[command.unit_name] = command.active
        for instance in self._instances_for_unit(command.unit_name):
            self._set_instance_active(instance, command.active, now, command.request_id)

    def _set_collection_desired(self, command: SystevisorSetCollectionDesiredCommand, now: float) -> None:
        snapshot = self._state.snapshot
        if snapshot is None or command.collection_name not in snapshot.config.collections:
            self._reject_command(f'unknown collection: {command.collection_name}', now, command.request_id)
            return
        if command.active and self._state.shutting_down:
            self._reject_command('engine is shutting down', now, command.request_id)
            return

        collection = self._state.collections[command.collection_name]
        previous_active = collection.desired_active
        previous_origin = collection.desired_origin
        collection.desired_active = command.active
        collection.desired_origin = SystevisorDesiredOrigin.MANUAL
        if command.active:
            collection.activation_sequence += 1
            collection.failure_instance_id = None
            collection.failure_reason = None
        if previous_active != command.active or previous_origin is not collection.desired_origin:
            self._emit_collection_event(
                SystevisorEventKind.COLLECTION_DESIRED_CHANGED,
                collection,
                now,
                request_id=command.request_id,
                data={'from': previous_active, 'to': command.active, 'origin': 'manual'},
            )
        self._refresh_configured_desires(snapshot, now)

    def _set_instance_desired(self, command: SystevisorSetInstanceDesiredCommand, now: float) -> None:
        instance = self._state.instances.get(command.instance_id)
        if instance is None:
            self._reject_command(f'unknown instance: {command.instance_id}', now, command.request_id)
            return
        if command.active and self._state.shutting_down:
            self._reject_command('engine is shutting down', now, command.request_id)
            return
        self._set_instance_active(instance, command.active, now, command.request_id)

    def _set_instance_active(
            self,
            instance: SystevisorInstanceState,
            active: bool,
            now: float,
            request_id: ta.Optional[str],
    ) -> None:
        desired_state = SystevisorDesiredState.ACTIVE if active else SystevisorDesiredState.INACTIVE
        self._change_desired(instance, desired_state, SystevisorDesiredOrigin.MANUAL, now, request_id=request_id)
        if active and instance.process_state in {SystevisorProcessState.EXITED, SystevisorProcessState.FATAL}:
            instance.start_failures = 0
            instance.completed_successfully = False
            self._transition(instance, SystevisorProcessState.STOPPED, now, 'manual_start')
        elif not active and instance.process_state in {
                SystevisorProcessState.BACKOFF,
                SystevisorProcessState.EXITED,
                SystevisorProcessState.FATAL,
        }:
            instance.deadline_id = None
            instance.deadline_kind = None
            instance.deadline_at = None
            self._transition(instance, SystevisorProcessState.STOPPED, now, 'manual_stop')

    def _restart_instance(self, command: SystevisorRestartInstanceCommand, now: float) -> None:
        instance = self._state.instances.get(command.instance_id)
        if instance is None:
            self._reject_command(f'unknown instance: {command.instance_id}', now, command.request_id)
            return
        if self._state.shutting_down:
            self._reject_command('engine is shutting down', now, command.request_id)
            return
        self._change_desired(
            instance,
            SystevisorDesiredState.ACTIVE,
            SystevisorDesiredOrigin.MANUAL,
            now,
            request_id=command.request_id,
        )
        instance.restart_requested = True
        if instance.process_state in _SYSTEVISOR_ENGINE_TERMINAL_PROCESS_STATES or (
                instance.process_state is SystevisorProcessState.BACKOFF
        ):
            instance.deadline_id = None
            instance.deadline_kind = None
            instance.deadline_at = None
            instance.start_failures = 0
            self._transition(instance, SystevisorProcessState.STOPPED, now, 'manual_restart')

    def _shutdown(self, command: SystevisorShutdownCommand, now: float) -> None:
        if self._state.shutting_down:
            return
        self._state.shutting_down = True
        self._emit_event(SystevisorEventKind.SHUTDOWN_STARTED, now, request_id=command.request_id)
        for collection in self._state.collections.values():
            if collection.desired_active:
                collection.desired_active = False
                collection.desired_origin = SystevisorDesiredOrigin.SHUTDOWN
                self._emit_collection_event(
                    SystevisorEventKind.COLLECTION_DESIRED_CHANGED,
                    collection,
                    now,
                    data={'from': True, 'to': False, 'origin': 'shutdown'},
                )
        for instance in self._stop_order():
            self._change_desired(instance, SystevisorDesiredState.INACTIVE, SystevisorDesiredOrigin.SHUTDOWN, now)

    def _forward_signal(self, command: SystevisorForwardSignalCommand, now: float) -> None:
        incoming = systevisor_normalize_signal_name(command.signal)
        for instance in sorted(self._state.instances.values(), key=lambda item: item.instance_id):
            if instance.run_id is None or instance.process_state not in _SYSTEVISOR_ENGINE_LIVE_PROCESS_STATES:
                continue
            signals = instance.desired_spec.unit.signals
            outgoing = next((
                configured_outgoing
                for configured_incoming, configured_outgoing in signals.forward.items()
                if systevisor_normalize_signal_name(configured_incoming) == incoming
            ), None)
            if outgoing is None:
                continue
            outgoing = systevisor_normalize_signal_name(outgoing)
            self._effects.append(SystevisorSignalProcessEffect(
                run_id=instance.run_id,
                signal=outgoing,
                scope=signals.scope,
                reason=SystevisorSignalReason.FORWARD,
            ))
            self._emit_event(
                SystevisorEventKind.SIGNAL_FORWARDED,
                now,
                instance=instance,
                data={
                    'incoming': incoming,
                    'outgoing': outgoing,
                    'scope': signals.scope.value,
                },
            )

    def _spawn_succeeded(self, fact: SystevisorSpawnSucceededFact, now: float) -> None:
        instance = self._find_run(fact.run_id)
        if (
                instance is None or
                instance.process_state is not SystevisorProcessState.STARTING or
                instance.spawn_confirmed
        ):
            self._stale_fact('spawn_succeeded', fact.run_id, now)
            return
        instance.spawn_confirmed = True
        instance.started_at = now
        self._schedule_health_role(instance, SystevisorHealthRole.STARTUP, now)
        start_secs = instance.desired_spec.unit.restart.start_secs
        if start_secs <= 0:
            instance.start_stable = True
            self._maybe_mark_running(instance, now)
        else:
            self._schedule_deadline(instance, SystevisorDeadlineKind.START_STABLE, now + start_secs)

    def _spawn_failed(self, fact: SystevisorSpawnFailedFact, now: float) -> None:
        instance = self._find_run(fact.run_id)
        if instance is None or instance.process_state not in {
                SystevisorProcessState.STARTING,
                SystevisorProcessState.STOPPING,
        }:
            self._stale_fact('spawn_failed', fact.run_id, now)
            return
        self._emit_event(
            SystevisorEventKind.PROCESS_SPAWN_FAILED,
            now,
            instance=instance,
            data={'message': fact.message},
        )
        self._clear_run(instance)
        if instance.process_state is SystevisorProcessState.STOPPING or (
                instance.desired_state is not SystevisorDesiredState.ACTIVE
        ):
            self._transition(instance, SystevisorProcessState.STOPPED, now, 'spawn_failed_while_stopping')
        else:
            self._startup_failed(instance, now, 'spawn_failed')

    def _process_exited(self, fact: SystevisorProcessExitedFact, now: float) -> None:
        instance = self._find_run(fact.run_id)
        if instance is None:
            self._stale_fact('process_exited', fact.run_id, now)
            return

        previous_state = instance.process_state
        instance.last_return_code = fact.return_code
        expected = fact.return_code in instance.desired_spec.unit.restart.expected_exit_codes
        instance.completed_successfully = expected and previous_state is SystevisorProcessState.RUNNING
        self._emit_event(
            SystevisorEventKind.PROCESS_EXITED,
            now,
            instance=instance,
            data={'return_code': fact.return_code, 'expected': expected, 'from_state': previous_state.value},
        )
        self._clear_run(instance)

        if previous_state is SystevisorProcessState.STOPPING or (
                instance.desired_state is not SystevisorDesiredState.ACTIVE
        ):
            self._transition(instance, SystevisorProcessState.STOPPED, now, 'process_stopped')
            return
        if previous_state is SystevisorProcessState.STARTING:
            self._startup_failed(instance, now, 'early_exit')
            return

        self._transition(instance, SystevisorProcessState.EXITED, now, 'process_exited')
        restart_mode = instance.desired_spec.unit.restart.mode
        should_restart = (
            instance.restart_requested or
            restart_mode is SystevisorRestartMode.ALWAYS or
            (restart_mode is SystevisorRestartMode.UNEXPECTED and not expected)
        )
        instance.restart_requested = False
        if should_restart:
            self._transition(instance, SystevisorProcessState.STOPPED, now, 'automatic_restart')

    def _deadline_reached(self, fact: SystevisorDeadlineReachedFact, now: float) -> None:
        instance = next(
            (candidate for candidate in self._state.instances.values() if candidate.deadline_id == fact.deadline_id),
            None,
        )
        if instance is None:
            health_match = next((
                (candidate, health)
                for candidate in self._state.instances.values()
                for health in candidate.health.values()
                if health.scheduled_deadline_id == fact.deadline_id
            ), None)
            if health_match is None:
                self._stale_fact('deadline_reached', None, now)
                return
            self._health_deadline_reached(health_match[0], health_match[1], now)
            return

        deadline_kind = instance.deadline_kind
        instance.deadline_id = None
        instance.deadline_kind = None
        instance.deadline_at = None
        if deadline_kind is SystevisorDeadlineKind.START_STABLE:
            if instance.process_state is SystevisorProcessState.STARTING and instance.spawn_confirmed:
                instance.start_stable = True
                self._maybe_mark_running(instance, now)
            else:
                self._stale_fact('start_stable_deadline', instance.run_id, now)
        elif deadline_kind is SystevisorDeadlineKind.BACKOFF:
            if instance.process_state is SystevisorProcessState.BACKOFF:
                self._transition(instance, SystevisorProcessState.STOPPED, now, 'backoff_elapsed')
            else:
                self._stale_fact('backoff_deadline', instance.run_id, now)
        elif deadline_kind is SystevisorDeadlineKind.STOP_ESCALATION:
            if instance.process_state is SystevisorProcessState.STOPPING and instance.run_id is not None:
                self._effects.append(SystevisorSignalProcessEffect(
                    run_id=instance.run_id,
                    signal=instance.desired_spec.unit.stop.kill_signal,
                    scope=(
                        instance.desired_spec.unit.stop.kill_scope or
                        instance.desired_spec.unit.stop.scope
                    ),
                    reason=SystevisorSignalReason.ESCALATE,
                ))
            else:
                self._stale_fact('stop_escalation_deadline', instance.run_id, now)
        else:
            self._stale_fact('unknown_deadline', instance.run_id, now)

    def _mark_running(self, instance: SystevisorInstanceState, now: float) -> None:
        instance.deadline_id = None
        instance.deadline_kind = None
        instance.deadline_at = None
        instance.start_failures = 0
        self._transition(instance, SystevisorProcessState.RUNNING, now, 'startup_ready')
        self._schedule_health_role(instance, SystevisorHealthRole.READINESS, now)
        self._schedule_health_role(instance, SystevisorHealthRole.LIVENESS, now)
        self._update_readiness(instance, now)

    def _new_health_probe_state(self, probe: ta.Any) -> SystevisorHealthProbeState:
        return SystevisorHealthProbeState(
            name=probe.name,
            role=probe.role,
            config_digest=systevisor_digest_config_object(probe, type(probe)),
        )

    def _reset_health_for_run(self, instance: SystevisorInstanceState) -> None:
        instance.start_stable = False
        instance.ready = False
        instance.health = {
            probe.name: self._new_health_probe_state(probe)
            for probe in instance.desired_spec.unit.health
        }

    def _sync_health_config(self, instance: SystevisorInstanceState, now: float) -> None:
        health: ta.Dict[str, SystevisorHealthProbeState] = {}
        for probe in instance.desired_spec.unit.health:
            config_digest = systevisor_digest_config_object(probe, type(probe))
            previous = instance.health.get(probe.name)
            if previous is not None and previous.config_digest == config_digest:
                health[probe.name] = previous
            else:
                health[probe.name] = self._new_health_probe_state(probe)
        instance.health = health

        if instance.process_state is SystevisorProcessState.STARTING and instance.spawn_confirmed:
            self._schedule_health_role(instance, SystevisorHealthRole.STARTUP, now)
            self._maybe_mark_running(instance, now)
        elif instance.process_state is SystevisorProcessState.RUNNING:
            self._schedule_health_role(instance, SystevisorHealthRole.READINESS, now)
            self._schedule_health_role(instance, SystevisorHealthRole.LIVENESS, now)
            self._update_readiness(instance, now)

    def _probe_config(self, instance: SystevisorInstanceState, name: str) -> ta.Any:
        return next(probe for probe in instance.desired_spec.unit.health if probe.name == name)

    def _schedule_health_role(
            self,
            instance: SystevisorInstanceState,
            role: SystevisorHealthRole,
            now: float,
    ) -> None:
        for probe in instance.desired_spec.unit.health:
            if probe.role is not role:
                continue
            health = instance.health[probe.name]
            if health.scheduled_deadline_id is None and health.in_flight_check_id is None:
                self._schedule_health_probe(instance, health, now + probe.initial_delay_secs)

    def _schedule_health_probe(
            self,
            instance: SystevisorInstanceState,
            health: SystevisorHealthProbeState,
            deadline_at: float,
    ) -> None:
        deadline_id = self._state.next_deadline_id
        self._state.next_deadline_id += 1
        health.scheduled_deadline_id = deadline_id
        health.next_check_at = deadline_at
        self._effects.append(SystevisorScheduleDeadlineEffect(
            deadline_id=deadline_id,
            deadline_at=deadline_at,
            kind=SystevisorDeadlineKind.HEALTH_PROBE,
            instance_id=instance.instance_id,
            run_id=instance.run_id,
        ))

    def _all_startup_passing(self, instance: SystevisorInstanceState) -> bool:
        startup = tuple(
            health
            for health in instance.health.values()
            if health.role is SystevisorHealthRole.STARTUP
        )
        return not startup or all(health.status is SystevisorHealthStatus.PASSING for health in startup)

    def _maybe_mark_running(self, instance: SystevisorInstanceState, now: float) -> None:
        if (
                instance.process_state is SystevisorProcessState.STARTING and
                instance.spawn_confirmed and
                instance.start_stable and
                self._all_startup_passing(instance)
        ):
            self._mark_running(instance, now)

    def _update_readiness(self, instance: SystevisorInstanceState, now: float) -> None:
        readiness = tuple(
            health
            for health in instance.health.values()
            if health.role is SystevisorHealthRole.READINESS
        )
        ready = (
            instance.process_state is SystevisorProcessState.RUNNING and
            (not readiness or all(health.status is SystevisorHealthStatus.PASSING for health in readiness))
        )
        if ready == instance.ready:
            return
        instance.ready = ready
        self._emit_event(
            SystevisorEventKind.READINESS_CHANGED,
            now,
            instance=instance,
            data={'ready': ready},
        )

    def _health_deadline_reached(
            self,
            instance: SystevisorInstanceState,
            health: SystevisorHealthProbeState,
            now: float,
    ) -> None:
        health.scheduled_deadline_id = None
        health.next_check_at = None
        if instance.run_id is None or not self._health_role_active(instance, health.role):
            self._stale_fact('health_probe_deadline', instance.run_id, now)
            return

        check_id = SystevisorHealthCheckId(self._state.next_health_check_id)
        self._state.next_health_check_id += 1
        health.in_flight_check_id = check_id
        health.last_started_at = now
        if health.status is SystevisorHealthStatus.UNKNOWN:
            health.status = SystevisorHealthStatus.PENDING
        probe = self._probe_config(instance, health.name)
        self._emit_event(
            SystevisorEventKind.HEALTH_PROBE_STARTED,
            now,
            instance=instance,
            data={'check_id': check_id, 'probe': health.name, 'role': health.role.value},
        )
        self._effects.append(SystevisorRunHealthProbeEffect(
            check_id=check_id,
            run_id=instance.run_id,
            instance_id=instance.instance_id,
            probe=probe,
            spec=instance.desired_spec,
        ))

    def _health_role_active(
            self,
            instance: SystevisorInstanceState,
            role: SystevisorHealthRole,
    ) -> bool:
        if role is SystevisorHealthRole.STARTUP:
            return instance.process_state is SystevisorProcessState.STARTING
        return instance.process_state is SystevisorProcessState.RUNNING

    def _health_probe_result(self, fact: SystevisorHealthProbeResultFact, now: float) -> None:
        instance = self._find_run(fact.run_id)
        match = None if instance is None else next((
            health
            for health in instance.health.values()
            if health.in_flight_check_id == fact.check_id
        ), None)
        if instance is None or match is None or not self._health_role_active(instance, match.role):
            self._stale_fact('health_probe_result', fact.run_id, now)
            return

        health = match
        health.in_flight_check_id = None
        health.last_completed_at = now
        health.last_message = fact.message
        health.last_data = dict(fact.data)
        probe = self._probe_config(instance, health.name)
        previous_status = health.status
        if fact.success:
            health.consecutive_successes += 1
            health.consecutive_failures = 0
            health.last_success_at = now
            if health.consecutive_successes >= probe.success_threshold:
                health.status = SystevisorHealthStatus.PASSING
                health.recovery_applied = False
        else:
            health.consecutive_failures += 1
            health.consecutive_successes = 0
            if health.consecutive_failures >= probe.failure_threshold:
                health.status = SystevisorHealthStatus.FAILING

        self._emit_event(
            SystevisorEventKind.HEALTH_PROBE_RESULT,
            now,
            instance=instance,
            data={
                'check_id': fact.check_id,
                'probe': health.name,
                'success': fact.success,
                'message': fact.message,
                'consecutive_successes': health.consecutive_successes,
                'consecutive_failures': health.consecutive_failures,
            },
        )
        if health.status is not previous_status:
            self._emit_event(
                SystevisorEventKind.HEALTH_CHANGED,
                now,
                instance=instance,
                data={
                    'probe': health.name,
                    'from': previous_status.value,
                    'to': health.status.value,
                },
            )

        if health.role is SystevisorHealthRole.STARTUP:
            self._maybe_mark_running(instance, now)
        elif health.role is SystevisorHealthRole.READINESS:
            self._update_readiness(instance, now)

        recovered = self._apply_health_recovery(instance, health, probe.recovery, now)
        if not recovered and self._health_role_active(instance, health.role):
            self._schedule_health_probe(instance, health, now + probe.interval_secs)

    def _apply_health_recovery(
            self,
            instance: SystevisorInstanceState,
            health: SystevisorHealthProbeState,
            recovery: SystevisorHealthRecovery,
            now: float,
    ) -> bool:
        if (
                health.status is not SystevisorHealthStatus.FAILING or
                health.recovery_applied or
                recovery is SystevisorHealthRecovery.NONE
        ):
            return False
        health.recovery_applied = True
        self._emit_event(
            SystevisorEventKind.HEALTH_RECOVERY_REQUESTED,
            now,
            instance=instance,
            data={'probe': health.name, 'recovery': recovery.value},
        )
        if recovery is SystevisorHealthRecovery.RESTART:
            instance.restart_requested = True
        elif recovery is SystevisorHealthRecovery.STOP:
            self._change_desired(
                instance,
                SystevisorDesiredState.INACTIVE,
                SystevisorDesiredOrigin.HEALTH,
                now,
            )
        else:
            raise TypeError(recovery)
        return True

    def _startup_failed(self, instance: SystevisorInstanceState, now: float, reason: str) -> None:
        instance.start_failures += 1
        instance.ready = False
        if instance.start_failures > instance.desired_spec.unit.restart.start_retries:
            self._transition(instance, SystevisorProcessState.FATAL, now, 'start_retries_exhausted')
            return

        self._transition(instance, SystevisorProcessState.BACKOFF, now, reason)
        restart = instance.desired_spec.unit.restart
        delay = min(
            restart.backoff_initial_secs * restart.backoff_multiplier ** (instance.start_failures - 1),
            restart.backoff_max_secs,
        )
        self._schedule_deadline(instance, SystevisorDeadlineKind.BACKOFF, now + delay)

    def _clear_run(self, instance: SystevisorInstanceState) -> None:
        instance.run_id = None
        instance.spawn_confirmed = False
        instance.started_at = None
        instance.ready = False
        instance.start_stable = False
        instance.deadline_id = None
        instance.deadline_kind = None
        instance.deadline_at = None
        for health in instance.health.values():
            health.scheduled_deadline_id = None
            health.next_check_at = None
            health.in_flight_check_id = None

    def _schedule_deadline(
            self,
            instance: SystevisorInstanceState,
            kind: SystevisorDeadlineKind,
            deadline_at: float,
    ) -> None:
        deadline_id = self._state.next_deadline_id
        self._state.next_deadline_id += 1
        instance.deadline_id = deadline_id
        instance.deadline_kind = kind
        instance.deadline_at = deadline_at
        self._effects.append(SystevisorScheduleDeadlineEffect(
            deadline_id=deadline_id,
            deadline_at=deadline_at,
            kind=kind,
            instance_id=instance.instance_id,
            run_id=instance.run_id,
        ))

    def _instances_for_unit(self, unit_name: SystevisorUnitName) -> ta.Sequence[SystevisorInstanceState]:
        return tuple(
            instance
            for instance in self._state.instances.values()
            if instance.unit_name == unit_name
        )

    def _stop_order(self) -> ta.Sequence[SystevisorInstanceState]:
        return tuple(sorted(
            self._state.instances.values(),
            key=lambda instance: (
                -instance.desired_spec.unit.priority,
                instance.unit_name,
                -instance.slot,
            ),
        ))

    def _start_order(self) -> ta.Sequence[SystevisorInstanceState]:
        return tuple(sorted(
            self._state.instances.values(),
            key=lambda instance: (
                instance.desired_spec.unit.priority,
                instance.unit_name,
                instance.slot,
            ),
        ))

    def _reconcile_dependency_desires(self, snapshot: SystevisorConfigSnapshot, now: float) -> None:
        configurable_origins = {
            SystevisorDesiredOrigin.CONFIG,
            SystevisorDesiredOrigin.COLLECTION,
            SystevisorDesiredOrigin.DEPENDENCY,
        }
        base: ta.Dict[
            SystevisorInstanceId,
            ta.Tuple[SystevisorDesiredState, SystevisorDesiredOrigin],
        ] = {}
        active_units: ta.Set[SystevisorUnitName] = set()
        for instance in self._state.instances.values():
            if instance.desired_state is SystevisorDesiredState.REMOVED:
                continue
            if instance.desired_origin in configurable_origins:
                configured = self._configured_desired_from_snapshot(instance.desired_spec, snapshot)
                base[instance.instance_id] = configured
                if configured[0] is SystevisorDesiredState.ACTIVE:
                    active_units.add(instance.unit_name)
            elif instance.desired_state is SystevisorDesiredState.ACTIVE:
                active_units.add(instance.unit_name)

        pending = sorted(active_units)
        while pending:
            unit_name = pending.pop(0)
            unit = snapshot.config.units.get(unit_name)
            if unit is None:
                continue
            for dependency_name in (*unit.dependencies.requires, *unit.dependencies.wants):
                dependency = SystevisorUnitName(dependency_name)
                if self._state.unit_desired_overrides.get(dependency) is False or dependency in active_units:
                    continue
                active_units.add(dependency)
                pending.append(dependency)

        for instance in self._state.instances.values():
            base_desired = base.get(instance.instance_id)
            if base_desired is None:
                continue
            desired_state, desired_origin = base_desired
            if desired_state is not SystevisorDesiredState.ACTIVE and instance.unit_name in active_units:
                desired_state = SystevisorDesiredState.ACTIVE
                desired_origin = SystevisorDesiredOrigin.DEPENDENCY
            previous_desired_state = instance.desired_state
            self._change_desired(instance, desired_state, desired_origin, now)
            if (
                    previous_desired_state is not SystevisorDesiredState.ACTIVE and
                    desired_state is SystevisorDesiredState.ACTIVE and
                    instance.process_state in {SystevisorProcessState.EXITED, SystevisorProcessState.FATAL}
            ):
                instance.start_failures = 0
                instance.completed_successfully = False
                self._transition(instance, SystevisorProcessState.STOPPED, now, 'configured_reactivation')

    def _dependency_condition_met(
            self,
            dependency_name: str,
            condition: SystevisorDependencyCondition,
    ) -> bool:
        instances = self._instances_for_unit(SystevisorUnitName(dependency_name))
        if not instances:
            return False
        if condition is SystevisorDependencyCondition.STARTED:
            return all(instance.process_state in {
                SystevisorProcessState.STARTING,
                SystevisorProcessState.RUNNING,
            } for instance in instances)
        if condition is SystevisorDependencyCondition.RUNNING:
            return all(instance.process_state is SystevisorProcessState.RUNNING for instance in instances)
        if condition is SystevisorDependencyCondition.READY:
            return all(
                instance.process_state is SystevisorProcessState.RUNNING and instance.ready
                for instance in instances
            )
        if condition is SystevisorDependencyCondition.COMPLETED:
            return all(
                instance.process_state is SystevisorProcessState.EXITED and instance.completed_successfully
                for instance in instances
            )
        raise TypeError(condition)

    def _ordering_dependency_settled(self, dependency_name: str) -> bool:
        instances = self._instances_for_unit(SystevisorUnitName(dependency_name))
        return bool(instances) and all(
            (
                instance.desired_state is not SystevisorDesiredState.ACTIVE and
                instance.process_state in _SYSTEVISOR_ENGINE_TERMINAL_PROCESS_STATES
            ) or instance.process_state in {
                SystevisorProcessState.RUNNING,
                SystevisorProcessState.EXITED,
                SystevisorProcessState.FATAL,
            }
            for instance in instances
        )

    def _blocking_dependency(self, instance: SystevisorInstanceState) -> ta.Optional[str]:
        dependencies = instance.desired_spec.unit.dependencies
        for dependency_name, condition in sorted(dependencies.requires.items()):
            if not self._dependency_condition_met(dependency_name, condition):
                return f'{dependency_name}:{condition.value}'

        ordering_names = set(dependencies.wants)
        ordering_names.update(dependencies.after)
        snapshot = self._state.snapshot
        if snapshot is not None:
            for other_name, other_unit in snapshot.config.units.items():
                if instance.unit_name in other_unit.dependencies.before:
                    ordering_names.add(other_name)
        for dependency_name in sorted(ordering_names):
            if not self._ordering_dependency_settled(dependency_name):
                return f'{dependency_name}:ordering'
        return None

    def _update_blocked_reason(
            self,
            instance: SystevisorInstanceState,
            blocked_reason: ta.Optional[str],
            now: float,
    ) -> None:
        if instance.blocked_reason == blocked_reason:
            return
        previous = instance.blocked_reason
        instance.blocked_reason = blocked_reason
        if blocked_reason is None:
            self._emit_event(
                SystevisorEventKind.DEPENDENCY_UNBLOCKED,
                now,
                instance=instance,
                data={'previous': previous},
            )
        else:
            self._emit_event(
                SystevisorEventKind.DEPENDENCY_BLOCKED,
                now,
                instance=instance,
                data={'dependency': blocked_reason},
            )

    def _spawn(self, instance: SystevisorInstanceState, now: float) -> None:
        run_id = SystevisorRunId(self._state.next_run_id)
        self._state.next_run_id += 1
        instance.run_id = run_id
        instance.applied_spec_digest = instance.desired_spec.spec_digest
        instance.spawn_confirmed = False
        instance.completed_successfully = False
        instance.last_return_code = None
        instance.restart_requested = False
        self._reset_health_for_run(instance)
        self._transition(instance, SystevisorProcessState.STARTING, now, 'spawn_requested')
        self._effects.append(SystevisorSpawnProcessEffect(
            run_id=run_id,
            instance_id=instance.instance_id,
            spec=instance.desired_spec,
        ))

    def _signal_stop(self, instance: SystevisorInstanceState, now: float) -> None:
        if instance.run_id is None:
            self._transition(instance, SystevisorProcessState.STOPPED, now, 'missing_run')
            return
        if instance.desired_state is SystevisorDesiredState.REMOVED:
            reason = SystevisorSignalReason.REMOVE
        elif instance.desired_origin is SystevisorDesiredOrigin.SHUTDOWN:
            reason = SystevisorSignalReason.SHUTDOWN
        elif instance.restart_requested:
            reason = SystevisorSignalReason.RESTART
        else:
            reason = SystevisorSignalReason.STOP
        self._transition(instance, SystevisorProcessState.STOPPING, now, reason.value)
        stop = instance.desired_spec.unit.stop
        self._effects.append(SystevisorSignalProcessEffect(
            run_id=instance.run_id,
            signal=stop.signal,
            scope=stop.scope,
            reason=reason,
        ))
        self._schedule_deadline(instance, SystevisorDeadlineKind.STOP_ESCALATION, now + stop.timeout_secs)

    def _collection_members(self, collection_name: SystevisorCollectionName) -> ta.Sequence[SystevisorInstanceState]:
        snapshot = self._state.snapshot
        if snapshot is None:
            return ()
        config = snapshot.config.collections.get(collection_name)
        if config is None:
            return ()
        unit_names = frozenset(config.units)
        return tuple(
            instance
            for instance in self._state.instances.values()
            if instance.unit_name in unit_names
        )

    @staticmethod
    def _collection_member_failure(instance: SystevisorInstanceState) -> ta.Optional[str]:
        if instance.process_state is SystevisorProcessState.FATAL:
            return 'fatal'
        if (
                instance.desired_state is SystevisorDesiredState.INACTIVE and
                instance.desired_origin is SystevisorDesiredOrigin.HEALTH
        ):
            return 'health_stop'
        if instance.process_state is SystevisorProcessState.EXITED:
            if (
                    instance.desired_spec.unit.kind is SystevisorUnitKind.ONESHOT and
                    instance.completed_successfully
            ):
                return None
            return 'terminal_exit'
        return None

    def _apply_collection_failures(self, now: float) -> None:
        snapshot = self._state.snapshot
        if snapshot is None:
            return
        changed = False
        for name, collection in self._state.collections.items():
            config = snapshot.config.collections.get(name)
            if config is None or not config.stop_together or not collection.desired_active:
                continue
            failure = next((
                (instance, reason)
                for instance in self._collection_members(name)
                if (reason := self._collection_member_failure(instance)) is not None
            ), None)
            if failure is None:
                continue
            instance, reason = failure
            collection.desired_active = False
            collection.desired_origin = SystevisorDesiredOrigin.COLLECTION_FAILURE
            collection.failure_instance_id = instance.instance_id
            collection.failure_reason = reason
            self._emit_collection_event(
                SystevisorEventKind.COLLECTION_STOP_TOGETHER,
                collection,
                now,
                data={'instance_id': instance.instance_id, 'reason': reason},
            )
            self._emit_collection_event(
                SystevisorEventKind.COLLECTION_DESIRED_CHANGED,
                collection,
                now,
                data={'from': True, 'to': False, 'origin': 'collection_failure'},
            )
            changed = True
        if changed:
            self._refresh_configured_desires(snapshot, now)

    @staticmethod
    def _collection_member_ready(instance: SystevisorInstanceState) -> bool:
        if instance.desired_spec.unit.kind is SystevisorUnitKind.ONESHOT:
            return (
                instance.process_state is SystevisorProcessState.EXITED and
                instance.completed_successfully
            )
        return instance.process_state is SystevisorProcessState.RUNNING and instance.ready

    @staticmethod
    def _collection_member_degraded(instance: SystevisorInstanceState) -> bool:
        return (
            instance.process_state is SystevisorProcessState.RUNNING and
            not instance.ready and
            any(
                health.role is SystevisorHealthRole.READINESS and
                health.status is SystevisorHealthStatus.FAILING
                for health in instance.health.values()
            )
        )

    def _collection_status(self, collection: SystevisorCollectionState) -> SystevisorCollectionStatus:
        members = self._collection_members(collection.name)
        if collection.failure_reason is not None:
            return SystevisorCollectionStatus.FAILED
        if not collection.desired_active:
            if any(
                    instance.desired_origin is SystevisorDesiredOrigin.COLLECTION and
                    instance.process_state in _SYSTEVISOR_ENGINE_LIVE_PROCESS_STATES
                    for instance in members
            ):
                return SystevisorCollectionStatus.STOPPING
            return SystevisorCollectionStatus.INACTIVE
        if any(self._collection_member_failure(instance) is not None for instance in members):
            return SystevisorCollectionStatus.DEGRADED
        if any(self._collection_member_degraded(instance) for instance in members):
            return SystevisorCollectionStatus.DEGRADED
        if members and all(self._collection_member_ready(instance) for instance in members):
            return SystevisorCollectionStatus.READY
        return SystevisorCollectionStatus.STARTING

    def _refresh_collection_statuses(self, now: float) -> None:
        for collection in self._state.collections.values():
            status = self._collection_status(collection)
            if status is collection.status:
                continue
            previous = collection.status
            collection.status = status
            self._emit_collection_event(
                SystevisorEventKind.COLLECTION_STATUS_CHANGED,
                collection,
                now,
                data={'from': previous.value, 'to': status.value},
            )

    def _stabilize(self, now: float) -> None:
        self._apply_collection_failures(now)
        if self._state.snapshot is not None:
            self._reconcile_dependency_desires(self._state.snapshot, now)

        for instance in self._stop_order():
            should_stop = (
                instance.desired_state is not SystevisorDesiredState.ACTIVE or
                instance.restart_requested
            )
            if should_stop and instance.process_state in {
                    SystevisorProcessState.STARTING,
                    SystevisorProcessState.RUNNING,
            }:
                self._signal_stop(instance, now)
            elif should_stop and instance.process_state is SystevisorProcessState.BACKOFF:
                instance.deadline_id = None
                instance.deadline_kind = None
                instance.deadline_at = None
                self._transition(instance, SystevisorProcessState.STOPPED, now, 'desired_inactive')

        for instance in self._start_order():
            if (
                    instance.desired_state is SystevisorDesiredState.ACTIVE and
                    instance.process_state is SystevisorProcessState.STOPPED
            ):
                blocked_reason = self._blocking_dependency(instance)
                self._update_blocked_reason(instance, blocked_reason, now)
                if blocked_reason is None:
                    self._spawn(instance, now)

        for instance_id in sorted(self._state.instances):
            instance = self._state.instances[instance_id]
            if (
                    instance.desired_state is SystevisorDesiredState.REMOVED and
                    instance.run_id is None and
                    instance.process_state in _SYSTEVISOR_ENGINE_TERMINAL_PROCESS_STATES
            ):
                del self._state.instances[instance_id]
                self._emit_event(
                    SystevisorEventKind.INSTANCE_REMOVED,
                    now,
                    instance=instance,
                    data={'unit_name': instance.unit_name, 'slot': instance.slot},
                )
        self._refresh_collection_statuses(now)
