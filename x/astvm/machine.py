import typing as ta

from .frontend import Frontend
from .frontend import Program
from .machineadapters import MachineAdapters
from .machinebuiltins import MachineBuiltins
from .machinecalls import MachineCalls
from .machinecomparisons import MachineComparisons
from .machinecomprehensions import MachineComprehensions
from .machineconstructors import MachineConstructors
from .machinecontrol import MachineControl
from .machineexpressions import MachineExpressions
from .machineflow import MachineFlow
from .machinefunctions import MachineFunctions
from .machineimports import MachineImports
from .machinemappings import MachineMappings
from .machinemethods import MachineMethods
from .machineoperations import MachineOperations
from .machineprotocols import MachineProtocols
from .machinereductions import MachineReductions
from .machinerepresentation import MachineRepresentation
from .machinestatements import MachineStatements
from .machinestrings import MachineStrings
from .objectspace import ObjectSpace
from .runtime import Runtime
from .state import Execution
from .state import SourceModule
from .state import Task
from .state import ThreadState
from .values import InterpreterError
from .values import _GuestRaise


##


class Machine(
    MachineFlow,
    MachineExpressions,
    MachineStatements,
    MachineControl,
    MachineFunctions,
    MachineOperations,
    MachineProtocols,
    MachineComparisons,
    MachineRepresentation,
    MachineCalls,
    MachineComprehensions,
    MachineImports,
    MachineConstructors,
    MachineBuiltins,
    MachineMethods,
    MachineMappings,
    MachineStrings,
    MachineAdapters,
    MachineReductions,
):
    def __init__(
            self,
            runtime: Runtime,
            space: ObjectSpace,
            frontend: Frontend,
            programs: list[Program],
            modules: ta.Mapping[str, SourceModule | ta.Mapping[str, object]],
    ) -> None:
        super().__init__()

        self._runtime = runtime
        self._space = space
        self._budget = space.budget
        self._frontend = frontend
        self._programs = programs
        self._modules = modules
        self._thread: ThreadState | None = None
        self._task: Task | None = None

        # Method names come exclusively from this implementation class, never from guest input.
        self._handlers = {
            name.removeprefix('_task_'): method.__get__(self, type(self))
            for cls in reversed(type(self).__mro__)
            for name, method in vars(cls).items()
            if name.startswith('_task_')
        }

    def _task_host_resume(self, task: Task) -> None:
        ref, mode, value = task.data

        self._resume_generator(task.env, ref, mode, value)

    def start(self, tasks: ta.Sequence[Task]) -> None:
        thread = self._runtime.edit_thread()
        if not thread.done:
            raise InterpreterError('execution already in progress')
        thread.executions = [Execution(tasks=list(tasks))]
        thread.call_depth = 0
        thread.done = False
        thread.result = None
        thread.error = None

    def step(self) -> bool:
        thread = self._runtime.edit_thread()
        if thread.done:
            return True
        self._thread = thread

        try:
            self._budget.tick()

            execution = self._execution()

            if execution.generator is not None:
                # Explicit write barrier for mutable suspended/active execution records.
                execution = self._runtime.edit_generator(execution.generator).execution
                thread.executions[-1] = execution

            if not execution.tasks:
                if execution.generator is not None:
                    raise InterpreterError('generator lost its end continuation')

                if len(execution.values) > 1:
                    raise InterpreterError('value stack was not balanced')

                thread.result = execution.values.pop() if execution.values else None
                thread.done = True

            else:
                self._task = execution.tasks.pop()

                try:
                    self._handlers[self._task.kind](self._task)
                except _GuestRaise as exc:
                    self._raise(exc.value)

            return thread.done

        finally:
            self._task = None
            self._thread = None
