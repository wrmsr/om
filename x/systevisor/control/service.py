# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import enum
import typing as ta

from ..configs.models import SystevisorUnitKind
from ..core.events import SystevisorEvent
from ..core.events import SystevisorEventKind
from ..core.identities import SystevisorCollectionName
from ..core.identities import SystevisorInstanceId
from ..core.identities import SystevisorUnitName
from ..core.inputs import SystevisorRestartInstanceCommand
from ..core.inputs import SystevisorSetCollectionDesiredCommand
from ..core.inputs import SystevisorSetInstanceDesiredCommand
from ..core.inputs import SystevisorSetUnitDesiredCommand
from ..core.inputs import SystevisorShutdownCommand
from ..core.state import SystevisorInstanceState
from ..core.states import SystevisorCollectionStatus
from ..core.states import SystevisorDesiredState
from ..core.states import SystevisorProcessState
from ..runtime.coordinator import SystevisorRuntimeCoordinator
from ..runtime.events import SystevisorBusEvent
from ..runtime.events import SystevisorEventSubscription
from .configs import SystevisorConfigController
from .operations import SystevisorOperation
from .operations import SystevisorOperationStatus
from .operations import SystevisorOperationStore


class SystevisorControlGoalKind(enum.Enum):
    START = 'start'
    STOP = 'stop'
    RESTART = 'restart'
    SHUTDOWN = 'shutdown'


@dc.dataclass(frozen=True)
class SystevisorControlGoal:
    kind: SystevisorControlGoalKind
    instance_ids: ta.Sequence[SystevisorInstanceId]
    initial_run_ids: ta.Mapping[SystevisorInstanceId, ta.Optional[int]] = dc.field(default_factory=dict)
    collection_name: ta.Optional[SystevisorCollectionName] = None


class SystevisorControlService:
    def __init__(
            self,
            coordinator: SystevisorRuntimeCoordinator,
            config_controller: SystevisorConfigController,
            operations: SystevisorOperationStore,
    ) -> None:
        self._coordinator = coordinator
        self._config_controller = config_controller
        self._operations = operations
        self._goals: ta.Dict[str, SystevisorControlGoal] = {}
        self._last_exited_run_ids: ta.Dict[SystevisorInstanceId, int] = {}
        self._event_subscription: SystevisorEventSubscription = (
            coordinator.event_bus.subscribe_callback(self._on_event)
        )

    @property
    def operations(self) -> SystevisorOperationStore:
        return self._operations

    @property
    def coordinator(self) -> SystevisorRuntimeCoordinator:
        return self._coordinator

    def _instances_for_unit(self, unit_name: str) -> ta.Sequence[SystevisorInstanceId]:
        return tuple(
            instance.instance_id
            for instance in self._coordinator.engine.state.instances.values()
            if instance.unit_name == unit_name
        )

    def _instances_for_collection(self, collection_name: str) -> ta.Sequence[SystevisorInstanceId]:
        snapshot = self._coordinator.engine.state.snapshot
        if snapshot is None or collection_name not in snapshot.config.collections:
            return ()
        unit_names = set(snapshot.config.collections[collection_name].units)
        return tuple(
            instance.instance_id
            for instance in self._coordinator.engine.state.instances.values()
            if instance.unit_name in unit_names
        )

    def _create_goal(
            self,
            operation: SystevisorOperation,
            kind: SystevisorControlGoalKind,
            instance_ids: ta.Sequence[SystevisorInstanceId],
            *,
            collection_name: ta.Optional[SystevisorCollectionName] = None,
    ) -> None:
        state = self._coordinator.engine.state
        self._goals[operation.operation_id] = SystevisorControlGoal(
            kind=kind,
            instance_ids=tuple(instance_ids),
            initial_run_ids={
                instance_id: state.instances[instance_id].run_id
                for instance_id in instance_ids
                if instance_id in state.instances
            },
            collection_name=collection_name,
        )

    def set_unit(self, unit_name: str, active: bool) -> SystevisorOperation:
        operation = self._operations.create(f'unit.{"start" if active else "stop"}', unit_name)
        self._create_goal(
            operation,
            SystevisorControlGoalKind.START if active else SystevisorControlGoalKind.STOP,
            self._instances_for_unit(unit_name),
        )
        self._coordinator.submit(SystevisorSetUnitDesiredCommand(
            SystevisorUnitName(unit_name),
            active,
            operation.operation_id,
        ))
        self._refresh(operation.operation_id)
        return operation

    def set_collection(self, collection_name: str, active: bool) -> SystevisorOperation:
        operation = self._operations.create(
            f'collection.{"start" if active else "stop"}',
            collection_name,
        )
        self._create_goal(
            operation,
            SystevisorControlGoalKind.START if active else SystevisorControlGoalKind.STOP,
            self._instances_for_collection(collection_name),
            collection_name=SystevisorCollectionName(collection_name),
        )
        self._coordinator.submit(SystevisorSetCollectionDesiredCommand(
            SystevisorCollectionName(collection_name),
            active,
            operation.operation_id,
        ))
        self._refresh(operation.operation_id)
        return operation

    def set_instance(self, instance_id: str, active: bool) -> SystevisorOperation:
        typed_instance_id = SystevisorInstanceId(instance_id)
        operation = self._operations.create(f'instance.{"start" if active else "stop"}', instance_id)
        self._create_goal(
            operation,
            SystevisorControlGoalKind.START if active else SystevisorControlGoalKind.STOP,
            (typed_instance_id,),
        )
        self._coordinator.submit(SystevisorSetInstanceDesiredCommand(
            typed_instance_id,
            active,
            operation.operation_id,
        ))
        self._refresh(operation.operation_id)
        return operation

    def restart_instance(self, instance_id: str) -> SystevisorOperation:
        typed_instance_id = SystevisorInstanceId(instance_id)
        operation = self._operations.create('instance.restart', instance_id)
        self._create_goal(operation, SystevisorControlGoalKind.RESTART, (typed_instance_id,))
        self._coordinator.submit(SystevisorRestartInstanceCommand(
            typed_instance_id,
            operation.operation_id,
        ))
        self._refresh(operation.operation_id)
        return operation

    def restart_unit(self, unit_name: str) -> SystevisorOperation:
        instance_ids = self._instances_for_unit(unit_name)
        operation = self._operations.create('unit.restart', unit_name)
        self._create_goal(operation, SystevisorControlGoalKind.RESTART, instance_ids)
        for instance_id in instance_ids:
            self._coordinator.submit(SystevisorRestartInstanceCommand(
                instance_id,
                operation.operation_id,
            ))
        self._refresh(operation.operation_id)
        return operation

    def shutdown(self) -> SystevisorOperation:
        operation = self._operations.create('manager.shutdown')
        self._create_goal(
            operation,
            SystevisorControlGoalKind.SHUTDOWN,
            tuple(self._coordinator.engine.state.instances),
        )
        self._coordinator.submit(SystevisorShutdownCommand(operation.operation_id))
        self._refresh(operation.operation_id)
        return operation

    def check_config(self) -> SystevisorOperation:
        operation = self._operations.create('config.check')
        result = self._config_controller.check(operation.operation_id)
        self._operations.finish(
            operation,
            SystevisorOperationStatus.SUCCEEDED if result.attempt.valid else SystevisorOperationStatus.REJECTED,
            message=None if result.attempt.valid else 'configuration is invalid',
            data={'attempt_sequence': result.attempt.sequence},
        )
        return operation

    def reload_config(self) -> SystevisorOperation:
        operation = self._operations.create('config.reload')
        result = self._config_controller.reload(operation.operation_id)
        self._operations.finish(
            operation,
            SystevisorOperationStatus.SUCCEEDED if result.attempt.applied else SystevisorOperationStatus.REJECTED,
            message=None if result.attempt.applied else 'configuration is invalid',
            data={
                'attempt_sequence': result.attempt.sequence,
                'digest': result.attempt.digest,
            },
        )
        return operation

    def _on_event(self, event: SystevisorBusEvent) -> None:
        if event.topic != 'engine' or not isinstance(event.payload, SystevisorEvent):
            return
        engine_event = event.payload
        if (
                engine_event.kind is SystevisorEventKind.PROCESS_EXITED and
                engine_event.instance_id is not None and
                engine_event.run_id is not None
        ):
            self._last_exited_run_ids[engine_event.instance_id] = engine_event.run_id
        if (
                engine_event.kind is SystevisorEventKind.COMMAND_REJECTED and
                engine_event.request_id is not None
        ):
            operation = self._operations.get(engine_event.request_id)
            if operation is not None:
                self._operations.finish(
                    operation,
                    SystevisorOperationStatus.REJECTED,
                    message=str(engine_event.data.get('message', 'command rejected')),
                )
                self._goals.pop(operation.operation_id, None)
        for operation_id in tuple(self._goals):
            self._refresh(operation_id)

    def _goal_instances(self, goal: SystevisorControlGoal) -> ta.Sequence[SystevisorInstanceState]:
        state = self._coordinator.engine.state
        return tuple(
            state.instances[instance_id]
            for instance_id in goal.instance_ids
            if instance_id in state.instances
        )

    @staticmethod
    def _start_succeeded(instance: SystevisorInstanceState) -> bool:
        if instance.desired_spec.unit.kind is SystevisorUnitKind.ONESHOT:
            return (
                instance.process_state is SystevisorProcessState.EXITED and
                instance.completed_successfully
            )
        return instance.process_state is SystevisorProcessState.RUNNING and instance.ready

    def _refresh(self, operation_id: str) -> None:
        operation = self._operations.get(operation_id)
        goal = self._goals.get(operation_id)
        if operation is None or goal is None or operation.status is not SystevisorOperationStatus.PENDING:
            self._goals.pop(operation_id, None)
            return
        instances = self._goal_instances(goal)
        if len(instances) != len(goal.instance_ids):
            if goal.kind not in (SystevisorControlGoalKind.STOP, SystevisorControlGoalKind.SHUTDOWN):
                self._operations.finish(
                    operation,
                    SystevisorOperationStatus.FAILED,
                    message='one or more target instances no longer exist',
                )
                self._goals.pop(operation_id, None)
                return

        if goal.collection_name is not None:
            collection = self._coordinator.engine.state.collections.get(goal.collection_name)
            if collection is None:
                self._operations.finish(
                    operation,
                    SystevisorOperationStatus.FAILED,
                    message='target collection no longer exists',
                )
                self._goals.pop(operation_id, None)
                return
            if goal.kind is SystevisorControlGoalKind.START:
                if collection.status is SystevisorCollectionStatus.READY:
                    self._operations.finish(operation, SystevisorOperationStatus.SUCCEEDED)
                    self._goals.pop(operation_id, None)
                elif collection.status is SystevisorCollectionStatus.FAILED:
                    self._operations.finish(
                        operation,
                        SystevisorOperationStatus.FAILED,
                        message=collection.failure_reason or 'collection failed during startup',
                    )
                    self._goals.pop(operation_id, None)
                return
            if goal.kind is SystevisorControlGoalKind.STOP:
                if collection.status is SystevisorCollectionStatus.INACTIVE:
                    self._operations.finish(operation, SystevisorOperationStatus.SUCCEEDED)
                    self._goals.pop(operation_id, None)
                return

        succeeded = False
        failed_message: ta.Optional[str] = None
        if goal.kind is SystevisorControlGoalKind.START:
            succeeded = all(self._start_succeeded(instance) for instance in instances)
            if any(instance.process_state in (
                    SystevisorProcessState.FATAL,
                    SystevisorProcessState.EXITED,
            ) and not self._start_succeeded(instance) for instance in instances):
                failed_message = 'one or more instances terminated before startup completed'
        elif goal.kind in (SystevisorControlGoalKind.STOP, SystevisorControlGoalKind.SHUTDOWN):
            succeeded = all(
                instance.desired_state is not SystevisorDesiredState.ACTIVE and instance.run_id is None
                for instance in instances
            )
        elif goal.kind is SystevisorControlGoalKind.RESTART:
            succeeded = bool(instances) and all(
                self._start_succeeded(instance) and
                (
                    self._last_exited_run_ids.get(instance.instance_id)
                    if instance.desired_spec.unit.kind is SystevisorUnitKind.ONESHOT
                    else instance.run_id
                ) is not None and
                (
                    self._last_exited_run_ids.get(instance.instance_id)
                    if instance.desired_spec.unit.kind is SystevisorUnitKind.ONESHOT
                    else instance.run_id
                ) != goal.initial_run_ids.get(instance.instance_id)
                for instance in instances
            )
            if any(instance.process_state is SystevisorProcessState.FATAL for instance in instances):
                failed_message = 'restarted instance entered fatal state'

        if succeeded:
            self._operations.finish(operation, SystevisorOperationStatus.SUCCEEDED)
            self._goals.pop(operation_id, None)
        elif failed_message is not None:
            self._operations.finish(operation, SystevisorOperationStatus.FAILED, message=failed_message)
            self._goals.pop(operation_id, None)

    def close(self) -> None:
        self._event_subscription.close()
        self._goals.clear()
        self._last_exited_run_ids.clear()
