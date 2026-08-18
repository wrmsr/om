# ruff: noqa: UP006 UP007 UP045
import dataclasses as dc
import enum
import typing as ta

from ..runtime.clocks import SystevisorClock
from ..runtime.events import SystevisorEventBus


class SystevisorOperationStatus(enum.Enum):
    PENDING = 'pending'
    SUCCEEDED = 'succeeded'
    REJECTED = 'rejected'
    FAILED = 'failed'


@dc.dataclass
class SystevisorOperation:
    operation_id: str
    kind: str
    target: ta.Optional[str]
    created_at: float
    status: SystevisorOperationStatus = SystevisorOperationStatus.PENDING
    completed_at: ta.Optional[float] = None
    message: ta.Optional[str] = None
    data: ta.Mapping[str, ta.Any] = dc.field(default_factory=dict)


@dc.dataclass(frozen=True)
class SystevisorOperationStoreState:
    state_schema_version: int
    capacity: int
    next_id: int
    operations: ta.Sequence[SystevisorOperation]


class SystevisorOperationStore:
    def __init__(
            self,
            event_bus: SystevisorEventBus,
            clock: SystevisorClock,
            capacity: int = 4096,
    ) -> None:
        if capacity < 1:
            raise ValueError(capacity)
        self._event_bus = event_bus
        self._clock = clock
        self._capacity = capacity
        self._operations: ta.Dict[str, SystevisorOperation] = {}
        self._next_id = 1

    def create(self, kind: str, target: ta.Optional[str] = None) -> SystevisorOperation:
        operation_id = f'op-{self._next_id:08d}'
        self._next_id += 1
        operation = SystevisorOperation(
            operation_id=operation_id,
            kind=kind,
            target=target,
            created_at=self._clock.monotonic(),
        )
        self._operations[operation_id] = operation
        self._trim()
        self._event_bus.publish('operation.created', operation, self._clock.monotonic())
        return operation

    def _trim(self) -> None:
        while len(self._operations) > self._capacity:
            for operation_id, operation in self._operations.items():
                if operation.status is not SystevisorOperationStatus.PENDING:
                    del self._operations[operation_id]
                    break
            else:
                break

    def finish(
            self,
            operation: SystevisorOperation,
            status: SystevisorOperationStatus,
            *,
            message: ta.Optional[str] = None,
            data: ta.Optional[ta.Mapping[str, ta.Any]] = None,
    ) -> None:
        if operation.status is not SystevisorOperationStatus.PENDING:
            return
        if status is SystevisorOperationStatus.PENDING:
            raise ValueError(status)
        operation.status = status
        operation.completed_at = self._clock.monotonic()
        operation.message = message
        operation.data = dict(data or {})
        self._event_bus.publish('operation.completed', operation, self._clock.monotonic())

    def get(self, operation_id: str) -> ta.Optional[SystevisorOperation]:
        return self._operations.get(operation_id)

    def list(self) -> ta.Sequence[SystevisorOperation]:
        return tuple(self._operations.values())

    def snapshot_state(self) -> SystevisorOperationStoreState:
        return SystevisorOperationStoreState(
            state_schema_version=1,
            capacity=self._capacity,
            next_id=self._next_id,
            operations=tuple(self._operations.values()),
        )

    def rehydrate(self, state: SystevisorOperationStoreState) -> None:
        if self._operations or self._next_id != 1:
            raise RuntimeError('operation store can only be rehydrated before use')
        if state.state_schema_version != 1:
            raise ValueError(f'unsupported operation store schema: {state.state_schema_version}')
        if state.capacity < 1 or state.next_id < 1 or len(state.operations) > state.capacity:
            raise ValueError('invalid operation store handoff state')
        operations: ta.Dict[str, SystevisorOperation] = {}
        for operation in state.operations:
            if operation.operation_id in operations:
                raise ValueError(f'duplicate operation id: {operation.operation_id}')
            operations[operation.operation_id] = operation
        self._capacity = state.capacity
        self._next_id = state.next_id
        self._operations = operations
