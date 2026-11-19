# mypy: disable-error-code=attr-defined
import typing as ta

from .state import Environment
from .state import RangeData
from .state import Task
from .values import _MISSING
from .values import _NUMBERS
from .values import Value


##


class MachineConstructors:
    def _arity(
            self,
            name: str,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
            minimum: int,
            maximum: int | None,
            allowed: ta.AbstractSet[str] = frozenset(),
    ) -> None:
        if len(args) < minimum or (maximum is not None and len(args) > maximum):
            self._space.error('TypeError', f'{name}: wrong number of arguments')

        if any(k not in allowed for k in kwargs):
            self._space.error('TypeError', f'{name}: unsupported keyword argument')

    def _constructor(
            self,
            env: Environment,
            name: str,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
    ) -> None:
        space = self._space

        if name in ('list', 'tuple', 'set', 'frozenset'):
            self._arity(name, args, kwargs, 0, 1)

            if not args:
                self._push(space.new(name, [] if name == 'list' else (() if name == 'tuple' else {})))
            elif name == 'tuple' and space.kind(args[0]) == 'tuple':
                self._push(args[0])
            else:
                self._add('construct_collection', env, data=name)
                self._collect(env, args[0])

        elif name == 'dict':
            self._arity(name, args, {}, 0, 1)
            result = space.new('dict', {})
            self._update_mapping(env, result, args[0] if args else None, kwargs, result)

        elif name == 'bool':
            self._arity(name, args, kwargs, 0, 1)

            if args:
                self._operation('truth', env, args[0])
            else:
                self._push(False)

        elif name == 'str':
            self._arity(name, args, kwargs, 0, 1)

            if args:
                self._operation('str', env, args[0])
            else:
                self._push('')

        elif name in ('int', 'float', 'complex'):
            allowed = frozenset({'base'}) if name == 'int' else frozenset()
            self._arity(name, args, kwargs, 0, 2 if name in ('int', 'complex') else 1, allowed)

            if args and space.kind(args[0]) == 'instance':
                method = space.special(args[0], '__' + name + '__')
                if method is not _MISSING and len(args) == 1 and not kwargs:
                    self._add('numeric_constructed', env, data=name)
                    self._invoke(env, method, ())
                    return

            if any(type(v) not in (*_NUMBERS, str, bytes) for v in args):
                space.error('TypeError', 'unsupported numeric conversion')
            if any(type(v) not in (int, bool) for v in kwargs.values()):
                space.error('TypeError', 'base must be an integer')

            if name == 'int':
                text = args[0] if args else None
                if type(text) in (str, bytes) and len(text) > space.budget.limits.integer_bits:
                    space.budget.fail('integer parsing size limit')

            function = {'int': int, 'float': float, 'complex': complex}[name]
            self._push(space.native(function, *args, **kwargs))

        elif name == 'bytes':
            self._arity(name, args, kwargs, 0, 1)

            if not args:
                self._push(b'')

            elif type(args[0]) is bytes:
                self._push(args[0])

            elif type(args[0]) in (int, bool):
                count = space.index(args[0])
                self._budget.size(count, string=True)
                self._budget.allocate(max(0, count))
                self._push(space.native(bytes, count))

            else:
                self._add('construct_bytes', env)
                self._collect(env, args[0])

        elif name == 'range':
            self._arity(name, args, kwargs, 1, 3)
            numbers = tuple(space.index(v) for v in args)

            if len(numbers) == 1:
                start, stop, step = 0, numbers[0], 1
            elif len(numbers) == 2:
                start, stop, step = *numbers, 1
            else:
                start, stop, step = numbers

            if step == 0:
                space.error('ValueError', 'range() arg 3 must not be zero')

            self._push(space.new('range', RangeData(start, stop, step)))

        elif name == 'slice':
            self._arity(name, args, kwargs, 1, 3)
            parts = (None, args[0], None) if len(args) == 1 else (*args, None) if len(args) == 2 else args
            self._push(space.new('slice', parts))

        elif name == 'type':
            self._arity(name, args, kwargs, 1, 1)
            self._push(space.type_of(args[0]))

        else:
            space.error('TypeError', name + ' cannot be constructed directly')

    def _task_numeric_constructed(self, task: Task) -> None:
        value = self._pop()
        expected = {'int': int, 'float': float, 'complex': complex}[task.data]

        if type(value) is not expected:
            self._space.error('TypeError', 'numeric conversion returned the wrong type')

        self._push(value)

    def _task_construct_collection(self, task: Task) -> None:
        value = self._pop()

        if task.data == 'list':
            self._push(value)

        elif task.data == 'tuple':
            self._push(self._space.new('tuple', tuple(self._space.data(value))))

        else:
            result = {}
            for item in self._space.data(value):
                result[self._space.key(item)] = item
            self._push(self._space.new(task.data, result))

    def _task_construct_bytes(self, task: Task) -> None:
        values = self._space.data(self._pop())

        self._budget.size(len(values), string=True)
        self._push(self._space.native(bytes, [self._space.index(v) for v in values]))

    def _isinstance(
            self,
            value: Value,
            classes: Value,
            *,
            subclass: bool = False,
    ) -> bool:
        space = self._space
        cls = value if subclass else space.type_of(value)
        if subclass and space.kind(cls) not in ('type', 'class'):
            space.error('TypeError', 'issubclass first argument must be a class')

        todo = [classes]

        while todo:
            self._budget.tick()
            base = todo.pop()
            kind = space.kind(base)

            if kind == 'tuple':
                todo.extend(reversed(space.data(base)))

            elif kind not in ('type', 'class'):
                space.error('TypeError', 'class information must be a class or tuple of classes')

            elif space.subclass(cls, base):
                return True

        return False
