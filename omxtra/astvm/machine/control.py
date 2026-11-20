import ast
import dataclasses as dc
import typing as ta

from ..state import Environment
from ..state import LoopState
from ..state import Outcome
from ..state import Task
from ..state import WithState
from ..values import _MISSING
from ..values import ObjectRef
from ..values import Value
from ..values import _GuestRaise
from .base import MachineBase


##


class MachineControl(MachineBase):
    def _task_if_value(self, task: Task) -> None:
        self._add('if_test', task.env, task.node)
        self._operation('truth', task.env, self._pop())

    def _task_if_test(self, task: Task) -> None:
        node = ta.cast('ast.If', task.node)

        self._suite(node.body if self._pop() else node.orelse, task.env)

    def _task_for_iterable(self, task: Task) -> None:
        self._add('for_iterator', task.env, task.node)
        self._operation('iter', task.env, self._pop())

    def _task_for_iterator(self, task: Task) -> None:
        node = ta.cast('ast.For', task.node)

        self._add('loop', task.env, data=LoopState(node, self._pop()))

    def _task_loop(self, task: Task) -> None:
        state = task.data

        if isinstance(state.node, ast.While):
            self._add('while_value', task.env, data=state)
            self._evaluate(state.node.test, task.env)

        else:
            self._pull(
                task.env,
                state.iterator,
                Task('for_value', task.env, data=state),
                Task('for_stop', task.env, data=state),
            )

    def _task_while_value(self, task: Task) -> None:
        self._add('while_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_while_test(self, task: Task) -> None:
        state = task.data

        if self._pop():
            self._add('loop', task.env, data=state)
            self._suite(state.node.body, task.env)
        else:
            self._suite(state.node.orelse, task.env)

    def _task_for_value(self, task: Task) -> None:
        state = task.data
        value = self._pop()

        self._add('loop', task.env, data=state)
        self._suite(state.node.body, task.env)
        self._add('assign', task.env, state.node.target, (value, False))

    def _task_for_stop(self, task: Task) -> None:
        self._pop()
        self._suite(task.data.node.orelse, task.env)

    def _task_return_value(self, task: Task) -> None:
        self._unwind(Outcome('return', self._pop()))

    def _task_finally(self, task: Task) -> None:
        self._finally(task, Outcome('normal'))

    def _task_restore_outcome(self, task: Task) -> None:
        outcome, depth = task.data

        self._restore_exception_depth(depth)

        if outcome.kind != 'normal':
            self._unwind(outcome)

    def _task_restore_exception(self, task: Task) -> None:
        self._restore_exception_depth(task.data)

    def _task_except(self, task: Task) -> None:
        node = ta.cast('ast.Try', task.node)

        self._suite(node.orelse, task.env)

    def _task_match_handler(self, task: Task) -> None:
        node = ta.cast('ast.Try', task.node)

        exception, index = task.data
        if index == len(node.handlers):
            self._unwind(Outcome('raise', exception))
            return

        handler = node.handlers[index]

        self._add('handler_type', task.env, node, task.data)

        if handler.type is None:
            self._push(self._space.types['BaseException'])
        else:
            self._evaluate(handler.type, task.env)

    def _task_handler_type(self, task: Task) -> None:
        node = ta.cast('ast.Try', task.node)

        exception, index = task.data
        cls = self._pop()

        if self._space.exception_matches(exception, cls):
            handler = node.handlers[index]
            if handler.name is not None:
                self._write_name(task.env, handler.name, exception)

            self._add('except_cleanup', task.env, data=handler.name)
            self._suite(handler.body, task.env)

        else:
            self._add('match_handler', task.env, node, (exception, index + 1))

    def _task_except_cleanup(self, task: Task) -> None:
        if task.data is not None:
            try:
                self._write_name(task.env, task.data, None, delete=True)

            except _GuestRaise as exc:
                if self._space.exception_name(exc.value) not in ('NameError', 'UnboundLocalError'):
                    raise

    def _normalize_exception(
            self,
            env: Environment,
            value: Value,
            args: tuple[Value, ...] = (),
    ) -> None:
        space = self._space
        kind = space.kind(value)

        if kind == 'exception':
            self._push(value)

        elif kind in ('class', 'type') and space.subclass(ta.cast(ObjectRef, value), space.types['BaseException']):
            self._invoke(env, value, args)

        else:
            space.error('TypeError', 'exceptions must derive from BaseException')

    def _task_raise_values(self, task: Task) -> None:
        values = self._space.data(self._pop())

        self._add('raise_exception', task.env, data=values[1] if len(values) > 1 else _MISSING)
        self._normalize_exception(task.env, values[0])

    def _task_raise_exception(self, task: Task) -> None:
        exception = self._pop()

        if task.data is _MISSING:
            self._raise(ta.cast(ObjectRef, exception))

        else:
            self._add('raise_cause', task.env, data=exception)
            if task.data is None:
                self._push(None)
            else:
                self._normalize_exception(task.env, task.data)

    def _task_raise_cause(self, task: Task) -> None:
        info = self._space.data(task.data)

        self._runtime.replace(task.data, dc.replace(info, cause=self._pop(), suppress_context=True))
        self._raise(task.data)

    def _task_assert_value(self, task: Task) -> None:
        self._add('assert_test', task.env, task.node)
        self._operation('truth', task.env, self._pop())

    def _task_assert_test(self, task: Task) -> None:
        node = ta.cast('ast.Assert', task.node)

        if not self._pop():
            if node.msg is None:
                self._space.error('AssertionError')
            self._add('assert_message', task.env)
            self._evaluate(node.msg, task.env)

    def _task_assert_message(self, task: Task) -> None:
        self._space.error('AssertionError', self._pop())

    def _task_with_item(self, task: Task) -> None:
        node = ta.cast('ast.With', task.node)

        if task.data == len(node.items):
            self._suite(node.body, task.env)
        else:
            self._add('with_manager', task.env, node, task.data)
            self._evaluate(node.items[task.data].context_expr, task.env)

    def _task_with_manager(self, task: Task) -> None:
        manager = self._pop()

        exit_method = self._space.special(manager, '__exit__')
        if exit_method is _MISSING:
            self._space.error('TypeError', 'object does not support the context manager protocol')

        self._add('with_exit_bound', task.env, data=(task.node, task.data, manager))
        self._bind_special_method(task.env, manager, exit_method)

    def _task_with_exit_bound(self, task: Task) -> None:
        node, index, manager = task.data
        exit_method = self._pop()
        enter_method = self._space.special(manager, '__enter__')
        if enter_method is _MISSING:
            self._space.error('TypeError', 'object does not support the context manager protocol')
        self._add('with_enter_bound', task.env, data=(node, index, exit_method))
        self._bind_special_method(task.env, manager, enter_method)

    def _task_with_enter_bound(self, task: Task) -> None:
        node, index, exit_method = task.data
        state = WithState(node, index, exit_method)
        self._add('with_entered', task.env, data=state)
        self._invoke(task.env, self._pop(), ())

    def _task_with_entered(self, task: Task) -> None:
        state = task.data
        value = self._pop()

        self._add('with_guard', task.env, data=state)
        self._add('with_item', task.env, state.node, state.index + 1)

        target = state.node.items[state.index].optional_vars
        if target is not None:
            self._add('assign', task.env, target, (value, False))

    def _task_with_guard(self, task: Task) -> None:
        self._with_exit(task, Outcome('normal'))

    def _task_with_exit_result(self, task: Task) -> None:
        value = self._pop()

        if task.data.kind == 'raise':
            self._add('with_suppressed', task.env, data=task.data)
            self._operation('truth', task.env, value)

        elif task.data.kind != 'normal':
            self._unwind(task.data)

    def _task_with_suppressed(self, task: Task) -> None:
        if not self._pop():
            self._unwind(task.data)
