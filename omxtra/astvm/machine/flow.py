import ast
import dataclasses as dc
import typing as ta

from ..state import CollectionState
from ..state import Environment
from ..state import Execution
from ..state import Outcome
from ..state import Task
from ..state import ThreadState
from ..values import _MISSING
from ..values import InterpreterError
from ..values import ObjectRef
from ..values import Value
from .base import MachineBase


##


class MachineFlow(MachineBase):
    def _thread_state(self) -> ThreadState:
        thread = self._thread
        if thread is None:
            raise InterpreterError('machine has no active thread')
        return thread

    def _execution(self) -> Execution:
        return self._thread_state().executions[-1]

    def _push(self, value: Value) -> None:
        self._execution().values.append(value)

    def _pop(self) -> Value:
        return self._execution().values.pop()

    def _add(
            self,
            kind: str,
            env: Environment,
            node: ast.AST | None = None,
            data: ta.Any = None,
    ) -> None:
        self._execution().tasks.append(Task(
            kind,
            env,
            node,
            data,
            len(self._execution().values),
        ))

    def _suite(self, body: ta.Sequence[ast.stmt], env: Environment) -> None:
        for node in reversed(body):
            self._add('exec', env, node)

    def _evaluate(self, node: ast.expr, env: Environment) -> None:
        self._add('eval', env, node)

    def _invoke(
            self,
            env: Environment,
            function: Value,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value] | None = None,
    ) -> None:
        self._add('invoke', env, data=(function, args, dict(kwargs or {})))

    def _operation(
            self,
            name: str,
            env: Environment,
            *values: Value,
    ) -> None:
        self._add('operation', env, data=(name, values))

    def _many(self, nodes: ta.Sequence[ast.expr], env: Environment) -> None:
        self._add('many_next', env, data=(tuple(nodes), 0, ()))

    def _pull(
            self,
            env: Environment,
            iterator: Value,
            on_value: Task,
            on_stop: Task,
    ) -> None:
        self._add('next_guard', env, data=(on_value, on_stop))
        self._operation('next', env, iterator)

    def _collect(
            self,
            env: Environment,
            value: Value,
            limit: int | None = None,
    ) -> None:
        self._add('collect_start', env, data=limit)
        self._operation('iter', env, value)

    def _find_nonlocal(self, env: Environment, name: str) -> Environment | None:
        current = env.parent

        while current is not None:
            if current.scope.kind not in ('module', 'class'):
                if name in current.scope.global_names:
                    return None

                if name in current.scope.local_names:
                    return current

            current = current.parent

        return None

    def _class_cell(self, env: Environment) -> ObjectRef | None:
        current: Environment | None = env
        while current is not None:
            if current.scope.kind in ('function', 'comprehension') and '__class__' in (
                    current.scope.local_names | current.scope.global_names
            ):
                return None
            if current.class_cell is not None:
                return current.class_cell
            current = current.parent
        return None

    def _read_name(self, env: Environment, name: str) -> Value:
        space = self._space
        scope = env.scope

        if name not in scope.global_names:
            local = space.data(env.namespace)
            if name in local:
                return local[name]

            if scope.kind in ('function', 'comprehension') and name in scope.local_names:
                space.error('UnboundLocalError', f"local variable '{name}' is not bound")

            if scope.kind != 'class' or name not in scope.local_names:
                parent = self._find_nonlocal(env, name)
                if parent is not None:
                    namespace = space.data(parent.namespace)
                    if name not in namespace:
                        space.error('NameError', f"free variable '{name}' is not bound")
                    return namespace[name]

            if name == '__class__' and scope.kind in ('function', 'comprehension'):
                cell = self._class_cell(env)
                if cell is not None:
                    value = space.data(cell)
                    if value is _MISSING:
                        space.error('NameError', "free variable '__class__' is not bound")
                    return value

        global_values = space.data(env.globals)
        if name in global_values:
            return global_values[name]

        builtin_values = space.data(space.builtins)
        if name in builtin_values:
            return builtin_values[name]

        return space.error('NameError', f"name '{name}' is not defined")

    def _write_name(
            self,
            env: Environment,
            name: str,
            value: Value,
            *,
            delete: bool = False,
    ) -> None:
        space = self._space

        if name in env.scope.global_names:
            namespace = env.globals

        elif name in env.scope.nonlocal_names:
            parent = self._find_nonlocal(env, name)
            if parent is not None:
                namespace = parent.namespace
            elif name == '__class__' and (cell := self._class_cell(env)) is not None:
                if delete and space.data(cell) is _MISSING:
                    space.error('NameError', "free variable '__class__' is not bound")
                self._runtime.replace(cell, _MISSING if delete else value)
                return
            else:
                raise InterpreterError('unresolved nonlocal binding')

        else:
            namespace = env.namespace

        if delete:
            if name not in space.data(namespace):
                local_function = env.scope.kind == 'function' and namespace == env.namespace
                error = 'UnboundLocalError' if local_function else 'NameError'
                space.error(error, name)

            self._runtime.delete(namespace, name)

        else:
            self._runtime.write(namespace, name, value)

    def _active_exception(self) -> ObjectRef | None:
        for execution in reversed(self._thread_state().executions):
            if execution.exceptions:
                return execution.exceptions[-1]
        return None

    def _raise(self, value: ObjectRef) -> None:
        space = self._space
        info = space.data(value)

        active = self._active_exception()
        if active is not None and active != value and info.context is None:
            info = dc.replace(info, context=active)

        task = self._task
        if task is not None and task.node is not None:
            entry = (task.env.program.filename, getattr(task.node, 'lineno', 0), task.env.scope.kind)
            info = dc.replace(info, traceback=(*info.traceback, entry))

        self._runtime.replace(value, info)
        self._unwind(Outcome('raise', value))

    def _restore_exception_depth(self, depth: int) -> None:
        del self._execution().exceptions[depth:]

    def _finally(self, task: Task, outcome: Outcome) -> None:
        depth = len(self._execution().exceptions)

        if outcome.kind == 'raise':
            self._execution().exceptions.append(ta.cast(ObjectRef, outcome.value))

        self._add('restore_outcome', task.env, data=(outcome, depth))
        self._suite(task.data, task.env)

    def _with_exit(self, task: Task, outcome: Outcome) -> None:
        depth = len(self._execution().exceptions)
        space = self._space

        self._add('restore_exception', task.env, data=depth)
        self._add('with_exit_result', task.env, data=outcome)

        if outcome.kind == 'raise':
            self._execution().exceptions.append(ta.cast(ObjectRef, outcome.value))
            info = space.data(outcome.value)
            args = (info.cls, outcome.value, space.traceback_value(ta.cast(ObjectRef, outcome.value)))
        else:
            args = (None, None, None)

        self._invoke(task.env, task.data.exit, args)

    _UNWIND_KINDS: ta.ClassVar = (
        'finally',
        'except',
        'except_cleanup',
        'restore_outcome',
        'restore_exception',
        'loop',
        'function_end',
        'generator_end',
        'next_guard',
        'with_guard',
        'class_end',
        'module_end',
        'hasattr_guard',
        'delegate_guard',
        'default_next_guard',
        'sequence_next_guard',
        'reversed_guard',
        'sentinel_call_guard',
        'mapping_keys_guard',
        'call_kwargs_guard',
        'dict_unpack_guard',
        'descriptor_get_guard',
    )

    def _unwind(self, outcome: Outcome) -> None:
        execution = self._execution()
        space = self._space

        while execution.tasks:
            self._budget.tick()

            task = execution.tasks.pop()
            kind = task.kind

            if kind in self._UNWIND_KINDS:
                del execution.values[task.base:]

            if kind == 'finally':
                self._finally(task, outcome)
                return

            if kind == 'except' and outcome.kind == 'raise':
                depth = len(execution.exceptions)
                execution.exceptions.append(ta.cast(ObjectRef, outcome.value))
                self._add('restore_exception', task.env, data=depth)
                self._add('match_handler', task.env, task.node, (outcome.value, 0))
                return

            if kind == 'except_cleanup':
                self._task_except_cleanup(task)

            elif kind == 'restore_exception':
                self._restore_exception_depth(task.data)

            elif kind == 'restore_outcome':
                self._restore_exception_depth(task.data[1])

            elif kind == 'loop':
                if outcome.kind == 'break':
                    return

                if outcome.kind == 'continue':
                    self._add('loop', task.env, data=task.data)
                    return

            elif kind == 'function_end':
                self._thread_state().call_depth -= 1
                if outcome.kind == 'return':
                    self._push(outcome.value)
                    return

            elif kind == 'generator_end':
                if outcome.kind in ('return', 'raise'):
                    self._finish_generator(outcome)
                    return

            elif kind == 'next_guard' and outcome.kind == 'raise':
                if space.exception_matches(ta.cast(ObjectRef, outcome.value), space.types['StopIteration']):
                    self._push(outcome.value)
                    execution.tasks.append(task.data[1])
                    return

            elif kind == 'default_next_guard' and outcome.kind == 'raise':
                if space.exception_matches(ta.cast(ObjectRef, outcome.value), space.types['StopIteration']):
                    self._push(task.data)
                    return

            elif kind == 'sequence_next_guard' and outcome.kind == 'raise':
                index_error = space.exception_matches(ta.cast(ObjectRef, outcome.value), space.types['IndexError'])
                if index_error or space.exception_matches(
                        ta.cast(ObjectRef, outcome.value), space.types['StopIteration'],
                ):
                    info = space.data(task.data)
                    self._runtime.replace(task.data, dc.replace(info, exhausted=True))
                    if index_error:
                        outcome = Outcome('raise', space.exception('StopIteration', ()))

            elif kind == 'reversed_guard' and outcome.kind == 'raise':
                info = space.data(task.data)
                self._runtime.replace(task.data, dc.replace(info, exhausted=True))
                exception = ta.cast(ObjectRef, outcome.value)
                if (
                        space.exception_matches(exception, space.types['IndexError']) or
                        space.exception_matches(exception, space.types['StopIteration'])
                ):
                    outcome = Outcome('raise', space.exception('StopIteration', ()))

            elif kind == 'sentinel_call_guard' and outcome.kind == 'raise':
                if space.exception_matches(ta.cast(ObjectRef, outcome.value), space.types['StopIteration']):
                    info = space.data(task.data)
                    self._runtime.replace(task.data, dc.replace(info, exhausted=True))
                    outcome = Outcome('raise', space.exception('StopIteration', ()))

            elif kind == 'mapping_keys_guard' and outcome.kind == 'raise':
                if space.exception_matches(ta.cast(ObjectRef, outcome.value), space.types['AttributeError']):
                    target, source = task.data
                    self._add('mapping_update_iterator', task.env, data=target)
                    self._operation('iter', task.env, source)
                    return

            elif kind in ('call_kwargs_guard', 'class_kwargs_guard') and outcome.kind == 'raise':
                if space.exception_matches(ta.cast(ObjectRef, outcome.value), space.types['AttributeError']):
                    outcome = Outcome('raise', space.exception('TypeError', ('argument after ** must be a mapping',)))

            elif kind == 'dict_unpack_guard' and outcome.kind == 'raise':
                if space.exception_matches(ta.cast(ObjectRef, outcome.value), space.types['AttributeError']):
                    outcome = Outcome(
                        'raise', space.exception('TypeError', ('dictionary unpacking requires a mapping',)),
                    )

            elif kind == 'descriptor_get_guard' and outcome.kind == 'raise':
                receiver, attribute, fallback = task.data
                if fallback and space.exception_matches(
                        ta.cast(ObjectRef, outcome.value), space.types['AttributeError'],
                ):
                    method = space.special(receiver, '__getattr__')
                    if method is not _MISSING:
                        self._invoke_special_method(task.env, receiver, method, (attribute,))
                        return

            elif kind == 'hasattr_guard' and outcome.kind == 'raise':
                if space.exception_matches(ta.cast(ObjectRef, outcome.value), space.types['AttributeError']):
                    self._push(task.data[0])
                    return

            elif kind == 'with_guard':
                self._with_exit(task, outcome)
                return

            elif kind == 'module_end':
                self._runtime.set_module(task.data[0], None)

        if execution.generator is not None:
            self._finish_generator(outcome)
            return

        self._thread_state().done = True

        if outcome.kind == 'raise':
            self._thread_state().error = ta.cast(ObjectRef, outcome.value)
        else:
            raise InterpreterError(f'unhandled control flow: {outcome.kind}')

    def _task_discard(self, task: Task) -> None:
        self._pop()

    def _task_constant(self, task: Task) -> None:
        self._push(task.data)

    def _task_many_next(self, task: Task) -> None:
        nodes, index, values = task.data
        if index == len(nodes):
            self._push(self._space.new('tuple', values))
        else:
            self._add('many_value', task.env, data=(nodes, index, values))
            self._evaluate(nodes[index], task.env)

    def _task_many_value(self, task: Task) -> None:
        nodes, index, values = task.data
        self._add('many_next', task.env, data=(nodes, index + 1, (*values, self._pop())))

    def _task_next_guard(self, task: Task) -> None:
        self._execution().tasks.append(task.data[0])

    def _task_default_next_guard(self, task: Task) -> None:
        pass

    def _task_collect_start(self, task: Task) -> None:
        state = CollectionState(self._pop(), self._space.new('list', []), task.data)
        self._add('collect_next', task.env, data=state)

    def _task_collect_next(self, task: Task) -> None:
        state = task.data
        if state.limit is not None and self._space.length(state.result) >= state.limit:
            self._push(state.result)
            return

        self._pull(
            task.env,
            state.iterator,
            Task('collect_value', task.env, data=state),
            Task('collect_stop', task.env, data=state),
        )

    def _task_collect_value(self, task: Task) -> None:
        self._space.append(task.data.result, self._pop())
        self._add('collect_next', task.env, data=task.data)

    def _task_collect_stop(self, task: Task) -> None:
        self._pop()
        self._push(task.data.result)
