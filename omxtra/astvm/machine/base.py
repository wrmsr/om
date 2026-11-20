import ast
import typing as ta

from ..budget import Budget
from ..frontend import Frontend
from ..frontend import Program
from ..runtime import Runtime
from ..space import ObjectSpace
from ..state import BuiltinData
from ..state import Environment
from ..state import Execution
from ..state import Outcome
from ..state import SourceModule
from ..state import Task
from ..state import ThreadState
from ..values import ObjectRef
from ..values import Value


##


class MachineBase:
    _runtime: Runtime
    _space: ObjectSpace
    _budget: Budget
    _frontend: Frontend
    _programs: list[Program]
    _modules: ta.Mapping[str, SourceModule | ta.Mapping[str, object]]
    _thread: ThreadState | None
    _task: Task | None
    _handlers: dict[str, ta.Callable[[Task], None]]

    _REPRESENTED_CONTAINERS: ta.ClassVar[tuple[str, ...]]

    if ta.TYPE_CHECKING:
        def _thread_state(self) -> ThreadState:
            ...

        def _active_exception(self) -> ObjectRef | None:
            ...

        def _adapter_next(self, env: Environment, ref: ObjectRef) -> None:
            ...

        def _add(
                self,
                kind: str,
                env: Environment,
                node: ast.AST | None = None,
                data: ta.Any = None,
        ) -> None:
            ...

        def _arity(
                self,
                name: str,
                args: tuple[Value, ...],
                kwargs: ta.Mapping[str, Value],
                minimum: int,
                maximum: int | None,
                allowed: ta.AbstractSet[str] = frozenset(),
        ) -> None:
            ...

        @classmethod
        def _binary_method(cls, name: str) -> str:
            ...

        def _bind_special_method(self, env: Environment, receiver: Value, method: Value) -> None:
            ...

        def _builtin(
                self,
                env: Environment,
                info: BuiltinData,
                args: tuple[Value, ...],
                kwargs: ta.Mapping[str, Value],
        ) -> None:
            ...

        def _class_cell(self, env: Environment) -> ObjectRef | None:
            ...

        def _collect(
                self,
                env: Environment,
                value: Value,
                limit: int | None = None,
        ) -> None:
            ...

        def _compare_value(
                self,
                env: Environment,
                name: str,
                left: Value,
                right: Value,
                depth: int = 0,
        ) -> None:
            ...

        def _constructor(
                self,
                env: Environment,
                name: str,
                args: tuple[Value, ...],
                kwargs: ta.Mapping[str, Value],
        ) -> None:
            ...

        def _define_function(self, node: ast.FunctionDef | ast.Lambda, env: Environment) -> None:
            ...

        def _enter_function(
                self,
                function: ObjectRef,
                args: tuple[Value, ...],
                kwargs: ta.Mapping[str, Value],
        ) -> None:
            ...

        def _evaluate(self, node: ast.expr, env: Environment) -> None:
            ...

        def _execution(self) -> Execution:
            ...

        def _finally(self, task: Task, outcome: Outcome) -> None:
            ...

        def _finish_generator(self, outcome: Outcome) -> None:
            ...

        def _flat_intrinsic_container(self, value: ObjectRef) -> bool:
            ...

        def _generator_method(
                self,
                env: Environment,
                ref: ObjectRef,
                name: str,
                args: tuple[Value, ...],
        ) -> None:
            ...

        def _invoke(
                self,
                env: Environment,
                function: Value,
                args: tuple[Value, ...],
                kwargs: ta.Mapping[str, Value] | None = None,
        ) -> None:
            ...

        def _invoke_special_method(
                self,
                env: Environment,
                receiver: Value,
                method: Value,
                args: tuple[Value, ...],
                kwargs: ta.Mapping[str, Value] | None = None,
        ) -> None:
            ...

        def _isinstance(
                self,
                value: Value,
                classes: Value,
                *,
                subclass: bool = False,
        ) -> bool:
            ...

        def _many(self, nodes: ta.Sequence[ast.expr], env: Environment) -> None:
            ...

        def _mapping_method(
                self,
                env: Environment,
                ref: ObjectRef,
                name: str,
                args: tuple[Value, ...],
                kwargs: ta.Mapping[str, Value],
        ) -> None:
            ...

        def _method(
                self,
                env: Environment,
                info: BuiltinData,
                args: tuple[Value, ...],
                kwargs: ta.Mapping[str, Value],
        ) -> None:
            ...

        def _normalize_exception(
                self,
                env: Environment,
                value: Value,
                args: tuple[Value, ...] = (),
        ) -> None:
            ...

        def _operation(
                self,
                name: str,
                env: Environment,
                *values: Value,
        ) -> None:
            ...

        def _pop(self) -> Value:
            ...

        def _pull(
                self,
                env: Environment,
                iterator: Value,
                on_value: Task,
                on_stop: Task,
        ) -> None:
            ...

        def _push(self, value: Value) -> None:
            ...

        def _raise(self, value: ObjectRef) -> None:
            ...

        def _read_name(self, env: Environment, name: str) -> Value:
            ...

        def _represent_container(self, env: Environment, value: ObjectRef, seen: tuple[int, ...] = ()) -> None:
            ...

        def _resolve(self, value: Value, env: Environment) -> None:
            ...

        def _restore_exception_depth(self, depth: int) -> None:
            ...

        def _resume_generator(
                self,
                env: Environment,
                ref: ObjectRef,
                mode: str,
                value: Value,
        ) -> None:
            ...

        def _string_method(
                self,
                env: Environment,
                value: Value,
                name: str,
                args: tuple[Value, ...],
                kwargs: ta.Mapping[str, Value],
        ) -> None:
            ...

        def _suite(self, body: ta.Sequence[ast.stmt], env: Environment) -> None:
            ...

        def _suspend(
                self,
                value: Value,
                *,
                waiting: str,
        ) -> None:
            ...

        def _task_except_cleanup(self, task: Task) -> None:
            ...

        def _unwind(self, outcome: Outcome) -> None:
            ...

        def _update_mapping(
                self,
                env: Environment,
                target: ObjectRef,
                source: Value,
                keywords: ta.Mapping[str, Value],
                result: Value,
        ) -> None:
            ...

        def _with_exit(self, task: Task, outcome: Outcome) -> None:
            ...

        def _write_name(
                self,
                env: Environment,
                name: str,
                value: Value,
                *,
                delete: bool = False,
        ) -> None:
            ...
