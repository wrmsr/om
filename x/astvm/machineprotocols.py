# mypy: disable-error-code=attr-defined
import typing as ta

from .state import Task
from .values import _MISSING
from .values import _NOT_IMPLEMENTED


##


class MachineProtocols:
    _BINARY_METHODS: ta.ClassVar = {
        'Add': 'add',
        'Sub': 'sub',
        'Mult': 'mul',
        'Div': 'truediv',
        'FloorDiv': 'floordiv',
        'Mod': 'mod',
        'Pow': 'pow',
        'LShift': 'lshift',
        'RShift': 'rshift',
        'BitAnd': 'and',
        'BitOr': 'or',
        'BitXor': 'xor',
    }

    @classmethod
    def _binary_method(cls, name: str) -> str:
        return cls._BINARY_METHODS[name]

    def _task_special_next(self, task: Task) -> None:
        name, values, candidates, index = task.data

        if index == len(candidates):
            category, op = name.split(':')

            if category == 'compare':
                if op == 'NotEq' and self._space.special(values[0], '__eq__') is not _MISSING:
                    self._add('negate_bool', task.env)
                    self._add('truth_result', task.env)
                    self._operation('compare:Eq', task.env, *values)

                else:
                    self._push(self._space.compare(op, *values))

            else:
                self._push(self._space.binary(op, *values))

        else:
            method, args = candidates[index]
            self._add('special_result', task.env, data=task.data)
            self._invoke(task.env, method, args)

    def _task_special_result(self, task: Task) -> None:
        value = self._pop()

        if value is _NOT_IMPLEMENTED:
            name, values, candidates, index = task.data
            self._add('special_next', task.env, data=(name, values, candidates, index + 1))

        else:
            self._push(value)

    def _task_truth_result(self, task: Task) -> None:
        self._operation('truth', task.env, self._pop())

    def _task_negate_bool(self, task: Task) -> None:
        self._push(not self._pop())

    def _task_expect(self, task: Task) -> None:
        value = self._pop()
        expected = task.data

        if expected == 'bool' and type(value) is not bool:
            self._space.error('TypeError', '__bool__ should return bool')

        if expected in ('len', 'len_bool'):
            if type(value) not in (bool, int):
                self._space.error('TypeError', '__len__ should return an integer')
            if value < 0:
                self._space.error('ValueError', '__len__ should return a nonnegative integer')
            value = bool(value) if expected == 'len_bool' else int(value)

        if expected in ('str', 'ascii'):
            if type(value) is not str:
                self._space.error('TypeError', 'string protocol method should return a string')
            if expected == 'ascii':
                value = value.encode('ascii', 'backslashreplace').decode('ascii')
            self._budget.size(len(value), string=True)

        if expected == 'iterator':
            if self._space.kind(value) not in ('iterator', 'generator', 'adapter'):
                if self._space.special(value, '__next__') is _MISSING:
                    self._space.error('TypeError', '__iter__ returned a non-iterator')

        self._push(value)

    def _task_slice_assignment(self, task: Task) -> None:
        value, key = task.data

        self._space.set_item(value, key, self._pop())
        self._push(None)

    def _task_contains_result(self, task: Task) -> None:
        if task.data:
            self._add('negate_bool', task.env)
        self._operation('truth', task.env, self._pop())

    def _task_contains_iterator(self, task: Task) -> None:
        self._add('contains_next', task.env, data=(task.data, self._pop()))

    def _task_contains_next(self, task: Task) -> None:
        value, iterator = task.data

        self._pull(
            task.env, iterator,
            Task('contains_value', task.env, data=task.data),
            Task('contains_stop', task.env),
        )

    def _task_contains_value(self, task: Task) -> None:
        value = self._pop()

        if self._space.identical(task.data[0], value):
            self._push(True)
        else:
            self._add('contains_comparison', task.env, data=task.data)
            self._operation('compare:Eq', task.env, value, task.data[0])

    def _task_contains_comparison(self, task: Task) -> None:
        self._add('contains_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_contains_test(self, task: Task) -> None:
        if self._pop():
            self._push(True)
        else:
            self._add('contains_next', task.env, data=task.data)

    def _task_contains_stop(self, task: Task) -> None:
        self._pop()
        self._push(False)
