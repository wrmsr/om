import typing as ta

from ..state import Environment
from ..state import Task
from ..values import _MISSING
from ..values import InterpreterError
from ..values import ObjectRef
from ..values import Value
from ..values import _GuestRaise
from .base import MachineBase


##


class MachineMappings(MachineBase):
    def _mapping_method(
            self,
            env: Environment,
            ref: ObjectRef,
            name: str,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
    ) -> None:
        space = self._space

        if name in ('get', 'pop', 'setdefault'):
            self._arity(name, args, kwargs, 1, 2)

            try:
                value = space.get_item(ref, args[0])

            except _GuestRaise as exc:
                if not space.exception_matches(exc.value, space.types['KeyError']):
                    raise

                if name == 'pop' and len(args) == 1:
                    raise

                value = args[1] if len(args) == 2 else None
                if name == 'setdefault':
                    space.set_item(ref, args[0], value)

            else:
                if name == 'pop':
                    space.set_item(ref, args[0], None, delete=True)

            self._push(value)

        elif name == 'popitem':
            self._arity(name, args, kwargs, 0, 0)

            pairs = space.mapping_pairs(ref)
            if not pairs:
                space.error('KeyError', 'popitem(): dictionary is empty')

            key, item = pairs[-1]
            space.set_item(ref, key, None, delete=True)
            self._push(space.new('tuple', (key, item)))

        elif name in ('keys', 'values', 'items'):
            self._arity(name, args, kwargs, 0, 0)
            self._push(space.new('dict_view', (ref, name)))

        elif name == 'update':
            self._arity(name, args, {}, 0, 1)
            self._update_mapping(env, ref, args[0] if args else _MISSING, kwargs, None)

        else:
            raise InterpreterError('unknown mapping method')

    def _update_mapping(
            self,
            env: Environment,
            target: ObjectRef,
            source: Value,
            keywords: ta.Mapping[str, Value],
            result: Value,
    ) -> None:
        self._add('mapping_update_keywords', env, data=(target, tuple(keywords.items()), result))

        if source is _MISSING:
            return

        if self._space.kind(source) in ('dict', 'namespace', 'mappingproxy'):
            for key, value in self._space.mapping_pairs(source):
                self._budget.tick()
                self._space.set_item(target, key, value)

        elif self._space.kind(source) in ('instance', 'exception'):
            self._add('mapping_keys_guard', env, data=(target, source))
            self._operation('getattr', env, source, 'keys')

        else:
            self._add('mapping_update_iterator', env, data=target)
            self._operation('iter', env, source)

    def _task_mapping_keys_guard(self, task: Task) -> None:
        self._add('mapping_keys_iterable', task.env, data=task.data)
        self._invoke(task.env, self._pop(), ())

    def _task_mapping_keys_iterable(self, task: Task) -> None:
        self._add('mapping_keys_iterator', task.env, data=task.data)
        self._collect(task.env, self._pop())

    def _task_mapping_keys_iterator(self, task: Task) -> None:
        target, source = task.data
        keys = tuple(self._space.data(self._pop()))
        self._add('mapping_keys_next', task.env, data=(target, source, keys, 0))

    def _task_mapping_keys_next(self, task: Task) -> None:
        target, source, keys, index = task.data
        if index == len(keys):
            return
        key = keys[index]
        self._add('mapping_keys_value', task.env, data=(task.data, key))
        self._operation('getitem', task.env, source, key)

    def _task_mapping_keys_value(self, task: Task) -> None:
        state, key = task.data
        self._space.set_item(state[0], key, self._pop())
        self._add('mapping_keys_next', task.env, data=(*state[:3], state[3] + 1))

    def _task_mapping_update_keywords(self, task: Task) -> None:
        target, pairs, result = task.data

        for key, value in pairs:
            self._budget.tick()
            self._space.set_item(target, key, value)

        self._push(result)

    def _task_mapping_update_iterator(self, task: Task) -> None:
        self._add('mapping_update_next', task.env, data=(task.data, self._pop()))

    def _task_mapping_update_next(self, task: Task) -> None:
        target, iterator = task.data

        self._pull(
            task.env, iterator,
            Task('mapping_update_item', task.env, data=task.data),
            Task('mapping_update_stop', task.env),
        )

    def _task_mapping_update_item(self, task: Task) -> None:
        self._add('mapping_update_pair', task.env, data=task.data)
        self._collect(task.env, self._pop(), 3)

    def _task_mapping_update_pair(self, task: Task) -> None:
        pair = self._space.data(self._pop())
        if len(pair) != 2:
            self._space.error('ValueError', 'dictionary update element must have length 2')

        self._space.set_item(task.data[0], pair[0], pair[1])
        self._add('mapping_update_next', task.env, data=task.data)

    def _task_mapping_update_stop(self, task: Task) -> None:
        self._pop()
