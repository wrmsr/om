# mypy: disable-error-code=attr-defined

from .state import Environment
from .state import Task
from .values import ObjectRef
from .values import Value


##


class MachineRepresentation:
    _REPRESENTED_CONTAINERS = ('list', 'tuple', 'dict', 'namespace', 'set', 'frozenset')

    def _flat_intrinsic_container(self, value: ObjectRef) -> bool:
        kind = self._space.kind(value)
        if kind in ('dict', 'namespace'):
            return all(
                type(key) is not ObjectRef and type(item) is not ObjectRef
                for key, item in self._space.mapping_pairs(value)
            )
        if kind in ('set', 'frozenset'):
            return all(type(item) is not ObjectRef for item in self._space.data(value).values())
        return all(type(item) is not ObjectRef for item in self._space.data(value))

    def _represent_container(self, env: Environment, value: ObjectRef, seen: tuple[int, ...] = ()) -> None:
        kind = self._space.kind(value)
        if value.serial in seen:
            self._push({
                'list': '[...]', 'tuple': '(...)', 'dict': '{...}', 'namespace': '{...}',
            }.get(kind, '...'))
            return
        if len(seen) > self._budget.limits.conversion_depth:
            self._budget.fail('representation nesting limit')

        if kind in ('list', 'dict', 'namespace'):
            entries = None
        elif kind in ('set', 'frozenset'):
            entries = tuple(self._space.data(value).values())
        else:
            entries = tuple(self._space.data(value))

        self._add('representation_next', env, data=(kind, value, (*seen, value.serial), entries, 0, (), 0))

    def _represent_part(self, env: Environment, value: Value, seen: tuple[int, ...]) -> None:
        if type(value) is ObjectRef and self._space.kind(value) in self._REPRESENTED_CONTAINERS:
            self._represent_container(env, value, seen)
        else:
            self._operation('repr', env, value)

    def _task_representation_next(self, task: Task) -> None:
        kind, value, seen, entries, index, parts, size = task.data
        if entries is None:
            entries = self._space.mapping_pairs(value) if kind in ('dict', 'namespace') else self._space.data(value)
        if index == len(entries):
            body = ', '.join(parts)
            if kind == 'list':
                result = '[' + body + ']'
            elif kind == 'tuple':
                result = '(' + body + (',' if len(parts) == 1 else '') + ')'
            elif kind == 'set':
                result = '{' + body + '}' if parts else 'set()'
            elif kind == 'frozenset':
                result = 'frozenset({' + body + '})' if parts else 'frozenset()'
            else:
                result = '{' + body + '}'
            self._budget.size(len(result), string=True)
            self._push(result)
            return

        if kind in ('dict', 'namespace'):
            self._add('representation_key', task.env, data=task.data)
            self._represent_part(task.env, entries[index][0], seen)
        else:
            self._add('representation_part', task.env, data=task.data)
            self._represent_part(task.env, entries[index], seen)

    def _task_representation_part(self, task: Task) -> None:
        kind, value, seen, entries, index, parts, size = task.data
        part = self._pop()
        size += len(part) + 2
        self._budget.size(size, string=True)
        self._add('representation_next', task.env, data=(kind, value, seen, entries, index + 1, (*parts, part), size))

    def _task_representation_key(self, task: Task) -> None:
        kind, value, seen, entries, index, parts, size = task.data
        if entries is None:
            entries = self._space.mapping_pairs(value)
        key_text = self._pop()
        self._add('representation_value', task.env, data=(*task.data, key_text))
        self._represent_part(task.env, entries[index][1], seen)

    def _task_representation_value(self, task: Task) -> None:
        kind, value, seen, entries, index, parts, size, key_text = task.data
        part = key_text + ': ' + self._pop()
        size += len(part) + 2
        self._budget.size(size, string=True)
        self._add('representation_next', task.env, data=(kind, value, seen, entries, index + 1, (*parts, part), size))

    def _task_representation_ascii(self, task: Task) -> None:
        text = self._pop().encode('ascii', 'backslashreplace').decode('ascii')
        self._budget.size(len(text), string=True)
        self._push(text)
