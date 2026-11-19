# mypy: disable-error-code=attr-defined
import dataclasses as dc
import typing as ta

from ..capabilities import CapabilityFailure
from ..state import Environment
from ..state import ExceptionData
from ..state import InstanceData
from ..state import Outcome
from ..state import Task
from ..values import _MISSING
from ..values import InterpreterError
from ..values import ObjectRef
from ..values import Value
from ..values import _GuestRaise


##


class MachineCalls:
    def _task_invoke(self, task: Task) -> None:
        function, args, kwargs = task.data
        space = self._space
        kind = space.kind(function)

        if kind == 'bound_method':
            info = space.data(function)
            self._invoke(task.env, info.function, (info.receiver, *args), kwargs)

        elif kind == 'function':
            self._enter_function(function, args, kwargs)

        elif kind == 'staticmethod':
            self._invoke(task.env, space.data(function), args, kwargs)

        elif kind == 'builtin':
            self._builtin(task.env, space.data(function), args, kwargs)

        elif kind == 'capability':
            if space.capabilities.guest_arguments(space.data(function)):
                exported_args = list(args)
                exported_kwargs = dict(kwargs)
            else:
                memo: dict[int, object] = {}
                exported_args = [space.export_value(v, memo=memo) for v in args]
                exported_kwargs = {k: space.export_value(v, memo=memo) for k, v in kwargs.items()}

            try:
                result = space.capabilities.invoke(space.data(function), exported_args, exported_kwargs)
            except CapabilityFailure as exc:
                imported = tuple(space.import_value(v) for v in exc.args)
                space.error(exc.name, *imported)

            self._push(space.import_value(result, capabilities=True))

        elif kind in ('class', 'type'):
            if space.subclass(function, space.types['BaseException']):
                constructor = space.lookup_class(function, '__new__') if kind == 'class' else _MISSING
                if constructor is not _MISSING:
                    if space.kind(constructor) == 'staticmethod':
                        constructor = space.data(constructor)
                    self._add('class_new_result', task.env, data=(function, args, dict(kwargs)))
                    self._invoke(task.env, constructor, (function, *args), kwargs)
                else:
                    value = space.new('exception', ExceptionData(function, args))
                    self._initialize_constructed(task.env, function, value, args, kwargs, new_invoked=False)

            elif kind == 'type' and function != space.types['object']:
                self._constructor(task.env, space.data(function).name, args, kwargs)

            else:
                constructor = space.lookup_class(function, '__new__')
                if constructor is not _MISSING:
                    if space.kind(constructor) == 'staticmethod':
                        constructor = space.data(constructor)
                    self._add('class_new_result', task.env, data=(function, args, dict(kwargs)))
                    self._invoke(task.env, constructor, (function, *args), kwargs)
                else:
                    value = space.new('instance', InstanceData(function, space.new('namespace', {})))
                    self._initialize_constructed(task.env, function, value, args, kwargs, new_invoked=False)

        else:
            method = space.special(function, '__call__')
            if method is _MISSING:
                space.error('TypeError', 'object is not callable')
            self._invoke(task.env, method, args, kwargs)

    def _task_class_new_result(self, task: Task) -> None:
        cls, args, kwargs = task.data
        self._initialize_constructed(task.env, cls, self._pop(), args, kwargs, new_invoked=True)

    def _initialize_constructed(
            self,
            env: Environment,
            cls: ObjectRef,
            value: Value,
            args: tuple[Value, ...],
            kwargs: dict[str, Value] | ta.Mapping[str, Value],
            *,
            new_invoked: bool,
    ) -> None:
        space = self._space
        value_kind = space.kind(value)
        if value_kind not in ('instance', 'exception') or not space.subclass(space.type_of(value), cls):
            self._push(value)
            return

        init = space.special(value, '__init__')
        if init is not _MISSING:
            self._add('instance_initialized', env, data=value)
            self._invoke(env, init, args, kwargs)
        elif value_kind == 'exception':
            if kwargs:
                space.error('TypeError', 'exception constructor does not accept keywords')
            self._push(value)
        elif (args or kwargs) and not new_invoked:
            space.error('TypeError', 'class takes no arguments')
        else:
            self._push(value)

    def _resume_generator(
            self,
            env: Environment,
            ref: ObjectRef,
            mode: str,
            value: Value,
    ) -> None:
        info = self._runtime.edit_generator(ref)

        if info.running:
            self._space.error('ValueError', 'generator already executing')

        if info.closed:
            if mode == 'close':
                self._push(None)
            elif mode == 'throw':
                self._raise(value)
            else:
                self._space.error('StopIteration')
            return

        if not info.started:
            if mode == 'send' and value is not None:
                self._space.error('TypeError', "can't send non-None value to a just-started generator")
            if mode in ('throw', 'close'):
                info.closed = True
                info.execution.tasks.clear()
                if mode == 'throw':
                    self._raise(value)
                else:
                    self._push(None)
                return

        if self._thread.call_depth >= self._budget.limits.call_depth:
            self._budget.fail('guest call depth limit')
        self._thread.call_depth += 1

        info.running = True
        info.execution.resume_mode = mode

        self._thread.executions.append(info.execution)

        if mode == 'close':
            value = self._space.exception('GeneratorExit', ())

        if not info.started:
            info.started = True
        elif info.waiting == 'delegate':
            info.packet = Outcome('raise' if mode in ('throw', 'close') else 'send', value)
        elif mode in ('throw', 'close'):
            self._raise(value)
        else:
            self._push(value)

        info.waiting = ''

    def _suspend(
            self,
            value: Value,
            *,
            waiting: str,
    ) -> None:
        execution = self._execution()

        if execution.generator is None:
            raise InterpreterError('yield without a generator execution')

        info = self._runtime.edit_generator(execution.generator)
        info.running = False
        info.waiting = waiting

        mode = execution.resume_mode

        self._thread.executions.pop()
        self._thread.call_depth -= 1

        if mode == 'close':
            self._space.error('RuntimeError', 'generator ignored GeneratorExit')

        self._push(value)

    def _finish_generator(self, outcome: Outcome) -> None:
        execution = self._execution()

        info = self._runtime.edit_generator(execution.generator)
        info.running = False
        info.closed = True
        info.waiting = ''

        mode = execution.resume_mode

        execution.tasks.clear()
        execution.values.clear()
        execution.exceptions.clear()

        self._thread.executions.pop()
        self._thread.call_depth -= 1

        if outcome.kind == 'raise':
            exception = outcome.value

            if self._space.exception_matches(exception, self._space.types['StopIteration']):
                replacement = self._space.exception('RuntimeError', ('generator raised StopIteration',))
                self._runtime.replace(replacement, dc.replace(
                    self._space.data(replacement), cause=exception, context=exception, suppress_context=True,
                ))
                self._raise(replacement)

            elif mode == 'close' and self._space.exception_matches(exception, self._space.types['GeneratorExit']):
                self._push(None)

            else:
                self._raise(exception)

        elif mode == 'close':
            self._push(outcome.value)

        else:
            args = () if outcome.value is None else (outcome.value,)
            self._raise(self._space.exception('StopIteration', args))

    def _task_generator_end(self, task: Task) -> None:
        self._finish_generator(Outcome('return'))

    def _task_yield_value(self, task: Task) -> None:
        self._suspend(self._pop(), waiting='yield')

    def _task_yieldfrom_iterable(self, task: Task) -> None:
        self._add('yieldfrom_iterator', task.env)
        self._operation('iter', task.env, self._pop())

    def _task_yieldfrom_iterator(self, task: Task) -> None:
        self._delegate(task.env, self._pop(), Outcome('send'))

    def _optional_attribute(self, value: Value, name: str) -> Value:
        try:
            return self._space.get_attribute(value, name)
        except _GuestRaise as exc:
            if self._space.exception_matches(exc.value, self._space.types['AttributeError']):
                return _MISSING
            raise

    def _delegate(
            self,
            env: Environment,
            iterator: Value,
            packet: Outcome,
    ) -> None:
        space = self._space

        if packet.kind == 'raise' and space.exception_matches(packet.value, space.types['GeneratorExit']):
            close = self._optional_attribute(iterator, 'close')
            if close is _MISSING:
                self._raise(packet.value)
            else:
                self._add('delegate_closed', env, data=packet.value)
                self._invoke(env, close, ())
            return

        on_value = Task('delegate_value', env, data=iterator)
        on_stop = Task('delegate_stop', env)

        if packet.kind == 'send' and packet.value is None:
            self._pull(env, iterator, on_value, on_stop)
            return

        if packet.kind == 'raise':
            method = self._optional_attribute(iterator, 'throw')
            if method is _MISSING:
                self._raise(packet.value)
                return

        else:
            method = space.get_attribute(iterator, 'send')

        self._add('next_guard', env, data=(on_value, on_stop))
        self._invoke(env, method, (packet.value,))

    def _task_delegate_value(self, task: Task) -> None:
        value = self._pop()

        self._add('delegate_resume', task.env, data=task.data)
        self._suspend(value, waiting='delegate')

    def _task_delegate_resume(self, task: Task) -> None:
        packet = self._runtime.edit_generator(self._execution().generator).packet

        self._delegate(task.env, task.data, packet)

    def _task_delegate_stop(self, task: Task) -> None:
        exception = self._pop()
        args = self._space.data(exception).args

        self._push(args[0] if args else None)

    def _task_delegate_closed(self, task: Task) -> None:
        self._pop()
        self._raise(task.data)

    def _generator_method(
            self,
            env: Environment,
            ref: ObjectRef,
            name: str,
            args: tuple[Value, ...],
    ) -> None:
        if name in ('__iter__', '__next__', 'close'):
            self._arity(name, args, {}, 0, 0)
            if name == '__iter__':
                self._push(ref)
            else:
                self._resume_generator(env, ref, 'close' if name == 'close' else 'next', None)

        elif name == 'send':
            self._arity(name, args, {}, 1, 1)
            self._resume_generator(env, ref, 'send', args[0])

        elif name == 'throw':
            self._arity(name, args, {}, 1, 3)

            if len(args) > 2 and args[2] is not None:
                self._space.error('TypeError', 'non-None throw traceback is not supported')

            kind = self._space.kind(args[0])

            if kind == 'exception':
                if len(args) > 1 and args[1] is not None:
                    self._space.error('TypeError', 'instance exception may not have a separate value')
                exception, values = args[0], ()

            elif (
                    kind in ('class', 'type') and
                    self._space.subclass(args[0], self._space.types['BaseException'])
            ):
                exception, values = args[0], ()
                if len(args) > 1 and args[1] is not None:
                    if (
                            self._space.kind(args[1]) == 'exception' and
                            self._space.subclass(self._space.data(args[1]).cls, args[0])
                    ):
                        exception = args[1]
                    else:
                        values = self._space.data(args[1]) if self._space.kind(args[1]) == 'tuple' else (args[1],)

            else:
                self._space.error('TypeError', 'exceptions must derive from BaseException')

            self._add('generator_throw_normalized', env, data=ref)
            self._normalize_exception(env, exception, tuple(values))

        else:
            raise InterpreterError('unknown generator method')

    def _task_generator_throw_normalized(self, task: Task) -> None:
        self._resume_generator(task.env, task.data, 'throw', self._pop())
