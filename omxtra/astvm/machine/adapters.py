import dataclasses as dc
import typing as ta

from ..state import Environment
from ..state import Task
from ..values import ObjectRef
from .base import MachineBase


##


class MachineAdapters(MachineBase):
    def _task_adapter_iterators(self, task: Task) -> None:
        state, inputs, index = task.data

        if index == len(inputs):
            self._push(self._space.new('adapter', state))
        else:
            self._add('adapter_iterator_value', task.env, data=task.data)
            self._operation('iter', task.env, inputs[index])

    def _task_adapter_iterator_value(self, task: Task) -> None:
        state, inputs, index = task.data
        state = dc.replace(state, iterators=(*state.iterators, self._pop()))

        self._add('adapter_iterators', task.env, data=(state, inputs, index + 1))

    def _adapter_stop(self, ref: ObjectRef) -> ta.NoReturn:
        self._runtime.replace(ref, dc.replace(self._space.data(ref), exhausted=True))
        self._space.error('StopIteration')

    def _adapter_next(self, env: Environment, ref: ObjectRef) -> None:
        info = self._space.data(ref)

        if info.exhausted:
            self._space.error('StopIteration')

        if info.kind == 'reversed':
            guest = self._space.kind(info.extra) in ('instance', 'exception')
            if info.index < 0 or (not guest and info.index >= self._space.length(info.extra)):
                self._adapter_stop(ref)
            if guest:
                self._add('reversed_guard', env, data=ref)
                self._add('reversed_value', env, data=ref)
                self._operation('getitem', env, info.extra, info.index)
                return
            value = self._space.get_item(info.extra, info.index)
            self._runtime.replace(ref, dc.replace(info, index=info.index - 1))
            self._push(value)

        elif info.kind == 'sentinel':
            self._add('sentinel_value', env, data=ref)
            self._add('sentinel_call_guard', env, data=ref)
            self._invoke(env, info.function, ())

        else:
            if not info.iterators:
                self._adapter_stop(ref)
            self._add('adapter_pull', env, data=(ref, (), 0))

    def _task_adapter_pull(self, task: Task) -> None:
        ref, row, index = task.data
        info = self._space.data(ref)

        if index == len(info.iterators):
            if info.kind == 'enumerate':
                self._runtime.replace(ref, dc.replace(info, index=self._budget.scalar(info.index + 1)))
                self._push(self._space.new('tuple', (info.index, row[0])))

            elif info.kind == 'zip':
                self._push(self._space.new('tuple', row))

            elif info.kind == 'map':
                self._invoke(task.env, info.function, row)

            elif info.kind == 'filter':
                self._add('filter_value', task.env, data=(ref, row[0]))
                if info.function is None:
                    self._push(row[0])
                else:
                    self._invoke(task.env, info.function, (row[0],))

            return

        self._pull(
            task.env, info.iterators[index],
            Task('adapter_item', task.env, data=task.data),
            Task('adapter_exhausted', task.env, data=task.data),
        )

    def _task_reversed_value(self, task: Task) -> None:
        value = self._pop()
        info = self._space.data(task.data)
        self._runtime.replace(task.data, dc.replace(info, index=info.index - 1))
        self._push(value)

    def _task_reversed_guard(self, task: Task) -> None:
        pass

    def _task_adapter_item(self, task: Task) -> None:
        ref, row, index = task.data

        self._add('adapter_pull', task.env, data=(ref, (*row, self._pop()), index + 1))

    def _task_adapter_exhausted(self, task: Task) -> None:
        exception = ta.cast(ObjectRef, self._pop())

        ref, row, index = task.data
        info = self._space.data(ref)

        if info.strict:
            if index:
                self._space.error('ValueError', 'zip arguments have different lengths')
            self._add('zip_probe', task.env, data=(ref, 1))
        else:
            self._raise(exception)

    def _task_zip_probe(self, task: Task) -> None:
        ref, index = task.data
        info = self._space.data(ref)

        if index == len(info.iterators):
            self._space.error('StopIteration')

        self._pull(
            task.env, info.iterators[index],
            Task('zip_too_long', task.env),
            Task('zip_probe_stop', task.env, data=(ref, index + 1)),
        )

    def _task_zip_probe_stop(self, task: Task) -> None:
        self._pop()
        self._add('zip_probe', task.env, data=task.data)

    def _task_zip_too_long(self, task: Task) -> None:
        self._pop()
        self._space.error('ValueError', 'zip arguments have different lengths')

    def _task_filter_value(self, task: Task) -> None:
        self._add('filter_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_filter_test(self, task: Task) -> None:
        ref, value = task.data

        if self._pop():
            self._push(value)
        else:
            self._operation('next', task.env, ref)

    def _task_sentinel_value(self, task: Task) -> None:
        value = self._pop()

        self._add('sentinel_comparison', task.env, data=(task.data, value))
        self._operation('compare:Eq', task.env, self._space.data(task.data).extra, value)

    def _task_sentinel_call_guard(self, task: Task) -> None:
        pass

    def _task_sentinel_comparison(self, task: Task) -> None:
        self._add('sentinel_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_sentinel_test(self, task: Task) -> None:
        ref, value = task.data

        if self._pop():
            self._adapter_stop(ref)
        self._push(value)
