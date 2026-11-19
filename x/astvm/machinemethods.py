# mypy: disable-error-code=attr-defined
import ast
import dataclasses as dc
import typing as ta

from .state import BuiltinData
from .state import Environment
from .state import Task
from .values import _SCALARS
from .values import InterpreterError
from .values import Value


##


class MachineMethods:
    def _method(
            self,
            env: Environment,
            info: BuiltinData,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
    ) -> None:
        kind, name = info.name.split('.', 1)
        value, space = info.receiver, self._space

        if kind == 'generator':
            if kwargs:
                space.error('TypeError', 'generator methods do not accept keywords')
            self._generator_method(env, value, name, args)
            return

        if kind in ('iterator', 'adapter'):
            self._arity(name, args, kwargs, 0, 0)
            if name == '__iter__':
                self._push(value)
            else:
                self._operation('next', env, value)
            return

        if kind == 'property':
            self._arity(name, args, kwargs, 1, 1)
            field = {'getter': 'getter', 'setter': 'setter', 'deleter': 'deleter'}[name]
            data = space.data(value)
            changes = {field: args[0]}
            if name == 'getter' and not data.doc_explicit:
                node = space.data(args[0]).node if space.kind(args[0]) == 'function' else None
                changes['doc'] = ast.get_docstring(node, clean=False) if isinstance(node, ast.FunctionDef) else None
            self._push(space.new('property', dc.replace(data, **changes)))
            return

        if kind in ('str', 'bytes'):
            self._string_method(env, value, name, args, kwargs)
            return

        if kind == 'range':
            self._arity(name, args, kwargs, 1, 1)

            if type(args[0]) not in _SCALARS:
                space.error('TypeError', 'range method requires intrinsic data')
            data = space.data(value)
            seq = range(data.start, data.stop, data.step)

            # Avoid native linear fallback for non-integral objects and enormous ranges.
            if type(args[0]) not in (int, bool):
                space.error('TypeError', 'range methods currently require an integer')

            self._push(space.native(range.count if name == 'count' else range.index, seq, args[0]))
            return

        if kind in ('list', 'tuple'):
            indices = (
                (0,) if kind == 'list' and name in ('insert', 'pop') and args else
                tuple(range(1, len(args))) if name == 'index' else
                ()
            )
            if any(space.kind(args[index]) in ('instance', 'exception') for index in indices):
                minimum, maximum = {'insert': (2, 2), 'pop': (0, 1), 'index': (1, 3)}[name]
                self._arity(name, args, kwargs, minimum, maximum)
                self._add('method_index_next', env, data=(info, args, kwargs, indices, 0))
                self._operation('index', env, args[indices[0]])
                return

        if name in ('copy', 'clear', 'reverse'):
            self._arity(name, args, kwargs, 0, 0)
            data = space.data(value)

            if name == 'copy':
                if kind == 'frozenset':
                    self._push(value)
                else:
                    self._push(space.new(kind, data.copy()))

            elif name == 'clear':
                self._runtime.replace(value, [] if kind == 'list' else {})
                self._push(None)

            else:
                self._runtime.replace(value, list(reversed(data)))
                self._push(None)

            return

        if kind == 'list' and name == 'append':
            self._arity(name, args, kwargs, 1, 1)
            space.append(value, args[0])
            self._push(None)

        elif kind in ('list', 'set') and name in ('extend', 'update'):
            self._arity(name, args, kwargs, 1, 1)
            self._add('extend_iterator', env, data=value)
            source = args[0]
            if kind == 'list' and space.identical(value, source):
                source = space.new('tuple', tuple(space.data(value)))
            self._operation('iter', env, source)

        elif kind == 'list' and name == 'insert':
            self._arity(name, args, kwargs, 2, 2)
            index = space.index(args[0])
            length = space.length(value)
            index = max(0, length + index) if index < 0 else min(index, length)
            self._budget.size(length + 1)
            self._budget.allocate(1)
            self._runtime.write(value, slice(index, index), [args[1]])
            self._push(None)

        elif kind == 'list' and name == 'pop':
            self._arity(name, args, kwargs, 0, 1)
            index = space.index(args[0]) if args else -1
            item = space.get_item(value, index)
            space.set_item(value, index, None, delete=True)
            self._push(item)

        elif kind in ('list', 'tuple') and name in ('count', 'index', 'remove'):
            self._arity(name, args, kwargs, 1, 3 if name == 'index' else 1)
            length = space.length(value)
            start = space.index(args[1]) if len(args) > 1 else 0
            stop = space.index(args[2]) if len(args) > 2 else length
            start = max(0, start + length) if start < 0 else start
            stop = max(0, stop + length) if stop < 0 else stop
            self._add('sequence_search', env, data=(value, name, args[0], start, stop, 0))

        elif kind in ('dict', 'namespace'):
            self._mapping_method(env, value, name, args, kwargs)

        elif kind == 'set' and name in ('add', 'discard', 'remove'):
            self._arity(name, args, kwargs, 1, 1)
            token = space.key(args[0])
            if name == 'add':
                space.set_item(value, args[0], None)
            elif token in space.data(value):
                space.set_item(value, args[0], None, delete=True)
            elif name == 'remove':
                space.error('KeyError', args[0])
            self._push(None)

        elif kind == 'set' and name == 'pop':
            self._arity(name, args, kwargs, 0, 0)
            data = space.data(value)
            if not data:
                space.error('KeyError', 'pop from an empty set')
            key = next(iter(data))
            item = data[key]
            self._runtime.delete(value, key)
            self._push(item)

        else:
            raise InterpreterError('unimplemented registered method: ' + info.name)

    def _task_extend_iterator(self, task: Task) -> None:
        self._add('extend_next', task.env, data=(task.data, self._pop()))

    def _task_method_index_next(self, task: Task) -> None:
        info, args, kwargs, indices, offset = task.data
        index = indices[offset]
        args = (*args[:index], self._pop(), *args[index + 1:])

        if offset + 1 < len(indices):
            self._add('method_index_next', task.env, data=(info, args, kwargs, indices, offset + 1))
            self._operation('index', task.env, args[indices[offset + 1]])
        else:
            self._method(task.env, info, args, kwargs)

    def _task_extend_next(self, task: Task) -> None:
        target, iterator = task.data
        self._pull(task.env, iterator, Task('extend_value', task.env, data=task.data), Task('extend_stop', task.env))

    def _task_extend_value(self, task: Task) -> None:
        target, iterator = task.data
        value = self._pop()
        if self._space.kind(target) == 'list':
            self._space.append(target, value)
        else:
            self._space.set_item(target, value, None)
        self._add('extend_next', task.env, data=task.data)

    def _task_extend_stop(self, task: Task) -> None:
        self._pop()
        self._push(None)

    def _task_sequence_search(self, task: Task) -> None:
        ref, name, sought, index, stop, count = task.data

        if index >= min(stop, self._space.length(ref)):
            if name == 'count':
                self._push(count)
            else:
                self._space.error('ValueError', 'value is not in sequence')

            return

        self._add('sequence_search_comparison', task.env, data=task.data)

        value = self._space.get_item(ref, index)
        if self._space.identical(value, sought):
            self._push(True)
        else:
            self._operation('compare:Eq', task.env, value, sought)

    def _task_sequence_search_comparison(self, task: Task) -> None:
        self._add('sequence_search_test', task.env, data=task.data)
        self._operation('truth', task.env, self._pop())

    def _task_sequence_search_test(self, task: Task) -> None:
        ref, name, sought, index, stop, count = task.data
        matches = self._pop()

        if matches and name != 'count':
            if name == 'remove':
                self._space.set_item(ref, index, None, delete=True)
                self._push(None)

            else:
                self._push(index)

        else:
            self._add('sequence_search', task.env, data=(ref, name, sought, index + 1, stop, count + int(matches)))
