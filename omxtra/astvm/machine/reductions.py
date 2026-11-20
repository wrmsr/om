import dataclasses as dc
import math
import typing as ta

from ..state import SortState
from ..state import Task
from ..values import _MISSING
from ..values import ObjectRef
from .base import MachineBase


##


class MachineReductions(MachineBase):
    def _task_reduction_iterator(self, task: Task) -> None:
        self._add('reduction_next', task.env, data=dc.replace(task.data, iterator=self._pop()))

    def _task_reduction_next(self, task: Task) -> None:
        self._pull(
            task.env, task.data.iterator,
            Task('reduction_item', task.env, data=task.data),
            Task('reduction_stop', task.env, data=task.data),
        )

    def _task_reduction_item(self, task: Task) -> None:
        value = self._pop()
        state = task.data

        if state.name in ('all', 'any'):
            self._add('reduction_truth', task.env, data=state)
            self._operation('truth', task.env, value)

        elif state.name == 'sum':
            if (
                type(state.value) in (bool, int, float) and
                type(value) in (bool, int, float) and
                (type(state.value) is float or type(value) is float or state.compensation is not None)
            ):
                total = self._space.native(float, state.value)
                part = self._space.native(float, value)
                next_total = total + part
                compensation = state.compensation or 0.0

                if math.isfinite(next_total):
                    if abs(total) >= abs(part):
                        compensation += (total - next_total) + part
                    else:
                        compensation += (part - next_total) + total
                else:
                    compensation = 0.0

                self._budget.tick()
                self._add('reduction_next', task.env, data=dc.replace(
                    state, value=next_total, compensation=compensation,
                ))

            else:
                if state.compensation is not None:
                    state = dc.replace(state, value=state.value + state.compensation, compensation=None)
                self._add('reduction_sum', task.env, data=state)
                self._operation('binary:Add', task.env, state.value, value)

        else:
            self._add('reduction_key', task.env, data=(state, value))
            if state.key is None:
                self._push(value)
            else:
                self._invoke(task.env, state.key, (value,))

    def _task_reduction_truth(self, task: Task) -> None:
        value = self._pop()

        if value == (task.data.name == 'any'):
            self._push(value)
        else:
            self._add('reduction_next', task.env, data=task.data)

    def _task_reduction_sum(self, task: Task) -> None:
        self._add('reduction_next', task.env, data=dc.replace(task.data, value=self._pop()))

    def _task_reduction_key(self, task: Task) -> None:
        state, value = task.data
        key = self._pop()

        if state.value is _MISSING:
            self._add('reduction_next', task.env, data=dc.replace(state, value=value, value_key=key))

        else:
            self._add('reduction_comparison', task.env, data=(state, value, key))
            self._operation('compare:' + ('Lt' if state.name == 'min' else 'Gt'), task.env, key, state.value_key)

    def _task_reduction_comparison(self, task: Task) -> None:
        self._add('reduction_selected', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_reduction_selected(self, task: Task) -> None:
        state, value, key = task.data

        if self._pop():
            state = dc.replace(state, value=value, value_key=key)
        self._add('reduction_next', task.env, data=state)

    def _task_reduction_stop(self, task: Task) -> None:
        self._pop()

        state = task.data

        if state.name in ('all', 'any'):
            self._push(state.name == 'all')

        elif state.value is not _MISSING:
            if state.name == 'sum' and state.compensation is not None:
                self._push(state.value + state.compensation)
            else:
                self._push(state.value)

        elif state.default is not _MISSING:
            self._push(state.default)

        else:
            self._space.error('ValueError', state.name + '() iterable is empty')

    def _task_sort_reverse(self, task: Task) -> None:
        source, key = task.data

        self._add('sort_collected', task.env, data=(key, self._pop()))
        self._collect(task.env, source)

    def _task_sort_collected(self, task: Task) -> None:
        source = self._pop()
        key, reverse = task.data

        state = SortState(
            ta.cast(ObjectRef, source),
            self._space.new('list', []),
            self._space.new('list', []),
            key,
            reverse,
        )

        self._add('sort_key_next', task.env, data=state)

    def _task_sort_key_next(self, task: Task) -> None:
        state = task.data

        if state.index == self._space.length(state.source):
            self._add('sort_next', task.env, data=dc.replace(state, index=0))

        else:
            value = self._space.get_item(state.source, state.index)
            self._add('sort_key_value', task.env, data=(state, value))
            if state.key is None:
                self._push(value)
            else:
                self._invoke(task.env, state.key, (value,))

    def _task_sort_key_value(self, task: Task) -> None:
        state, value = task.data
        pair = self._space.new('tuple', (self._pop(), value))

        self._space.append(state.decorated, pair)
        self._add('sort_key_next', task.env, data=dc.replace(state, index=state.index + 1))

    def _task_sort_next(self, task: Task) -> None:
        state = task.data

        if state.index == self._space.length(state.decorated):
            self._push(self._space.new('list', [self._space.data(p)[1] for p in self._space.data(state.output)]))
        else:
            self._add('sort_search', task.env, data=(state, 0, self._space.length(state.output)))

    def _task_sort_search(self, task: Task) -> None:
        state, low, high = task.data
        pair = self._space.get_item(state.decorated, state.index)

        if low == high:
            self._budget.allocate(1)
            self._runtime.write(state.output, slice(low, low), [pair])
            self._add('sort_next', task.env, data=dc.replace(state, index=state.index + 1))

        else:
            middle = (low + high) // 2
            other = self._space.get_item(state.output, middle)
            self._add('sort_comparison', task.env, data=(state, low, high, middle))
            self._operation(
                'compare:Gt' if state.reverse else 'compare:Lt', task.env,
                self._space.data(pair)[0], self._space.data(other)[0],
            )

    def _task_sort_comparison(self, task: Task) -> None:
        self._add('sort_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_sort_test(self, task: Task) -> None:
        state, low, high, middle = task.data

        if self._pop():
            high = middle
        else:
            low = middle + 1

        self._add('sort_search', task.env, data=(state, low, high))
