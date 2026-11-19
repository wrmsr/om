import ast
import typing as ta

from .budget import Budget
from .budget import Limits
from .capabilities import Capabilities
from .capabilities import HostCall
from .capabilities import HostObject
from .frontend import Frontend
from .frontend import Program
from .frontend import Scope
from .machine import Machine
from .objectspace import ObjectSpace
from .runtime import DictRuntime
from .runtime import Runtime
from .state import Checkpoint
from .state import Environment
from .state import SourceModule
from .state import Task
from .values import GuestError
from .values import InterpreterError
from .values import ObjectRef
from .values import Value


##


class Interpreter:
    def __init__(
            self,
            *,
            runtime: Runtime | None = None,
            limits: Limits | None = None,
            modules: ta.Mapping[str, SourceModule | ta.Mapping[str, object]] | None = None,
    ) -> None:
        super().__init__()

        self._runtime = runtime if runtime is not None else DictRuntime()
        self._budget = Budget(limits)
        self._capabilities = Capabilities()
        self._space = ObjectSpace(self._runtime, self._budget, self._capabilities)
        self._frontend = Frontend(self._budget)
        self._programs: list[Program] = []
        self._machine = Machine(
            self._runtime,
            self._space,
            self._frontend,
            self._programs,
            dict(modules or {}),
        )
        self._globals = self._space.new('namespace', {'__name__': '__main__'})
        self._busy = False
        self._poisoned = False

    @property
    def done(self) -> bool:
        return self._runtime.read_thread().done

    @property
    def steps_used(self) -> int:
        return self._budget.steps

    def _check_host_entry(self) -> None:
        if self._busy:
            raise InterpreterError('interpreter is non-reentrant')
        if self._poisoned:
            raise InterpreterError('interpreter aborted; create a fresh instance')

    def _environment(self, program: Program) -> Environment:
        scope = program.scopes.get(program.tree, Scope('module', frozenset(), frozenset(), frozenset()))
        return Environment(program, scope, self._globals, self._globals)

    def _host_environment(self) -> Environment:
        if not self._programs:
            self.prepare('')
        return self._environment(self._programs[0])

    def _check_error(self) -> None:
        error = self._runtime.read_thread().error
        if error is not None:
            raise GuestError(
                self._space.exception_name(error),
                self._space.representation(error, string=True),
                error,
            )

    def _snapshot_memo(self) -> dict[int, object]:
        # AST identity indexes scope metadata. Programs are immutable trusted code, not mutable guest state.
        memo: dict[int, object] = {}
        for program in self._programs:
            memo[id(program)] = program
            for node in ast.walk(program.tree):
                memo[id(node)] = node
        return memo

    def prepare(
            self,
            source: str,
            *,
            filename: str = '<guest>',
            expression: bool = False,
    ) -> Program:
        self._check_host_entry()
        program = self._frontend.prepare(
            source,
            filename=filename,
            expression=expression,
        )
        self._programs.append(program)
        return program

    def start(
            self,
            source: str | Program,
            *,
            filename: str = '<guest>',
    ) -> None:
        self._check_host_entry()

        program = self.prepare(source, filename=filename) if type(source) is str else source
        if type(program) is not Program:
            raise TypeError('expected source text or a prepared Program')
        if not self._programs or self._programs[-1] is not program:
            if not any(existing is program for existing in self._programs):
                self._programs.append(program)

        env = self._environment(program)

        if isinstance(program.tree, ast.Expression):
            tasks = [Task('eval', env, program.tree.body)]
        else:
            tasks = [Task('exec', env, node) for node in reversed(program.tree.body)]

        self._machine.start(tasks)

    def step(self, count: int = 1) -> bool:
        self._check_host_entry()

        if type(count) is not int or count < 0:
            raise ValueError('step count must be a nonnegative integer')

        self._busy = True
        try:
            for _ in range(count):
                if self._machine.step():
                    break

        except Exception:
            self._poisoned = True
            raise

        finally:
            self._busy = False

        if self.done:
            self._check_error()

        return self.done

    def run(self) -> Value:
        self._check_host_entry()

        while not self.done:
            self.step()

        self._check_error()

        return self._runtime.read_thread().result

    def execute(
            self,
            source: str | Program,
            *,
            filename: str = '<guest>',
    ) -> None:
        self.start(source, filename=filename)
        self.run()

    def evaluate_value(
            self,
            source: str,
            *,
            filename: str = '<guest>',
    ) -> Value:
        program = self.prepare(
            source,
            filename=filename,
            expression=True,
        )
        self.start(program)
        return self.run()

    def evaluate(
            self,
            source: str,
            *,
            filename: str = '<guest>',
    ) -> object:
        return self.export(self.evaluate_value(source, filename=filename))

    def get_value(self, name: str) -> Value:
        self._check_host_entry()
        return self._space.data(self._globals)[name]

    def get(self, name: str) -> object:
        return self.export(self.get_value(name))

    def set(self, name: str, value: object) -> None:
        self._check_host_entry()

        if type(name) is not str:
            raise TypeError('name must be a string')

        self._runtime.write(self._globals, name, self._space.import_value(value))

    def export(self, value: Value) -> object:
        self._check_host_entry()

        return self._space.export_value(value)

    def grant(self, name: str, callback: ta.Callable[..., object] | HostCall) -> None:
        self._check_host_entry()

        if type(name) is not str:
            raise TypeError('name must be a string')

        value = self._space.new('capability', self._capabilities.register(callback))

        self._runtime.write(self._globals, name, value)

    def grant_object(self, name: str, obj: HostObject) -> None:
        self._check_host_entry()

        if type(name) is not str or type(obj) is not HostObject:
            raise TypeError('expected a name and an explicit HostObject method table')

        self._runtime.write(self._globals, name, self._space.import_value(obj, capabilities=True))

    def call_value(
            self,
            function: Value,
            args: ta.Sequence[Value] = (),
            kwargs: ta.Mapping[str, Value] | None = None,
    ) -> Value:
        self._check_host_entry()

        self._space.kind(function)
        for value in [*args, *(kwargs or {}).values()]:
            self._space.kind(value)

        task = Task(
            'invoke',
            self._host_environment(),
            data=(
                function,
                tuple(args),
                dict(kwargs or {}),
            ),
        )

        self._machine.start([task])

        return self.run()

    def call(
            self,
            function: Value,
            *args: object,
            **kwargs: object,
    ) -> object:
        self._check_host_entry()

        memo = {}

        imported_args = tuple(self._space.import_value(v, memo=memo) for v in args)
        imported_kwargs = {k: self._space.import_value(v, memo=memo) for k, v in kwargs.items()}

        return self.export(self.call_value(function, imported_args, imported_kwargs))

    def resume_value(
            self,
            generator: ObjectRef,
            *,
            mode: str = 'next',
            value: Value = None,
    ) -> Value:
        self._check_host_entry()

        if self._space.kind(generator) != 'generator' or mode not in ('next', 'send', 'throw', 'close'):
            raise ValueError('invalid generator resume request')
        self._space.kind(value)
        if mode == 'throw' and self._space.kind(value) != 'exception':
            raise ValueError('throw requires a guest exception instance')

        task = Task(
            'host_resume',
            self._host_environment(),
            data=(generator, mode, value),
        )

        self._machine.start([task])

        return self.run()

    def checkpoint(self) -> Checkpoint:
        self._check_host_entry()
        return self._runtime.checkpoint(self._snapshot_memo())

    def restore(self, checkpoint: Checkpoint) -> None:
        self._check_host_entry()
        self._runtime.restore(checkpoint, self._snapshot_memo())
