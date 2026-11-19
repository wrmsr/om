# mypy: disable-error-code=attr-defined

from ..state import Environment
from ..state import Task
from ..values import _MISSING
from ..values import _SCALARS
from ..values import Value


##


class MachineComparisons:
    def _compare_value(
            self,
            env: Environment,
            name: str,
            left: Value,
            right: Value,
            depth: int = 0,
    ) -> None:
        space = self._space
        if depth > self._budget.limits.conversion_depth:
            space.error('RecursionError', 'comparison nesting limit')

        lk, rk = space.kind(left), space.kind(right)
        if lk == rk and lk in ('list', 'tuple'):
            if self._flat_intrinsic_container(left) and self._flat_intrinsic_container(right):
                self._push(space.compare(name, left, right))
            else:
                self._add('sequence_compare_next', env, data=(name, left, right, 0, depth))
        elif name in ('Eq', 'NotEq') and lk in ('dict', 'namespace', 'mappingproxy') and rk in (
                'dict', 'namespace', 'mappingproxy',
        ):
            if self._flat_intrinsic_container(left) and self._flat_intrinsic_container(right):
                self._push(space.compare(name, left, right))
            else:
                self._add('mapping_compare_next', env, data=(name, left, right, 0, depth))
        else:
            self._push(space.compare(name, left, right))

    def _compare_element_equal(self, env: Environment, left: Value, right: Value, depth: int) -> None:
        if self._space.identical(left, right):
            self._push(True)
        elif type(left) in _SCALARS and type(right) in _SCALARS:
            self._push(self._space.compare('Eq', left, right))
        elif (
            self._space.kind(left) == self._space.kind(right) and
            self._space.kind(left) in ('list', 'tuple', 'dict', 'namespace', 'mappingproxy')
        ):
            self._compare_value(env, 'Eq', left, right, depth)
        else:
            self._add('truth_result', env)
            self._operation('compare:Eq', env, left, right)

    def _task_sequence_compare_next(self, task: Task) -> None:
        name, left, right, index, depth = task.data
        space = self._space
        a, b = space.data(left), space.data(right)

        if name in ('Eq', 'NotEq') and len(a) != len(b):
            self._push(name == 'NotEq')
            return

        while index < min(len(a), len(b)) and space.identical(a[index], b[index]):
            self._budget.tick()
            index += 1

        if index == min(len(a), len(b)):
            self._push(space.compare(name, len(a), len(b)))
            return

        self._add('sequence_compare_element', task.env, data=(name, left, right, index, depth))
        self._compare_element_equal(task.env, a[index], b[index], depth + 1)

    def _task_sequence_compare_element(self, task: Task) -> None:
        name, left, right, index, depth = task.data
        equal = self._pop()

        if equal:
            self._add('sequence_compare_next', task.env, data=(name, left, right, index + 1, depth))
        elif name in ('Eq', 'NotEq'):
            self._push(name == 'NotEq')
        else:
            a, b = self._space.data(left), self._space.data(right)
            x, y = a[index], b[index]
            if type(x) in _SCALARS and type(y) in _SCALARS:
                self._push(self._space.compare(name, x, y))
            elif self._space.kind(x) == self._space.kind(y) and self._space.kind(x) in ('list', 'tuple'):
                self._compare_value(task.env, name, x, y, depth + 1)
            else:
                self._add('truth_result', task.env)
                self._operation('compare:' + name, task.env, x, y)

    def _task_mapping_compare_next(self, task: Task) -> None:
        name, left, right, index, depth = task.data
        space = self._space
        a = space.mapping_pairs(left)

        if len(a) != space.length(right):
            self._push(name == 'NotEq')
            return
        if index == len(a):
            self._push(name == 'Eq')
            return

        key, value = a[index]
        data = space.data(right)
        if space.kind(right) == 'mappingproxy':
            data = space.data(data)
        record = data.get(space.key(key), _MISSING)
        if record is _MISSING:
            self._push(name == 'NotEq')
            return
        other = record[1] if space.kind(right) == 'dict' else record

        self._add('mapping_compare_element', task.env, data=(name, left, right, index, depth))
        self._compare_element_equal(task.env, value, other, depth + 1)

    def _task_mapping_compare_element(self, task: Task) -> None:
        name, left, right, index, depth = task.data
        if self._pop():
            self._add('mapping_compare_next', task.env, data=(name, left, right, index + 1, depth))
        else:
            self._push(name == 'NotEq')
