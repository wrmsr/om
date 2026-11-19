# mypy: disable-error-code=attr-defined
import ast
import typing as ta

from ..state import Environment
from ..state import PropertyData
from ..state import RangeData
from ..state import SuperData
from ..state import Task
from ..values import _MISSING
from ..values import _NUMBERS
from ..values import ObjectRef
from ..values import Value


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
            self._update_mapping(env, result, args[0] if args else _MISSING, kwargs, result)

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
                    self._invoke_special_method(env, args[0], method, ())
                    return
                if (
                    name == 'int' and len(args) == 1 and not kwargs and
                    space.special(args[0], '__index__') is not _MISSING
                ):
                    self._operation('index', env, args[0])
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

            elif (
                space.kind(args[0]) in ('instance', 'exception') and
                space.special(args[0], '__index__') is not _MISSING
            ):
                self._add('bytes_count', env)
                self._operation('index', env, args[0])

            else:
                self._add('construct_bytes_iterator', env)
                self._operation('iter', env, args[0])

        elif name == 'range':
            self._arity(name, args, kwargs, 1, 3)
            self._add('range_index_next', env, data=(args, (), 0))
            self._operation('index', env, args[0])

        elif name == 'slice':
            self._arity(name, args, kwargs, 1, 3)
            parts = (None, args[0], None) if len(args) == 1 else (*args, None) if len(args) == 2 else args
            self._push(space.new('slice', parts))

        elif name == 'property':
            self._arity(name, args, kwargs, 0, 4, frozenset({'fget', 'fset', 'fdel', 'doc'}))
            fields = ('fget', 'fset', 'fdel', 'doc')
            values = {}
            for index, field in enumerate(fields):
                if field in kwargs and index < len(args):
                    space.error('TypeError', 'multiple values for property argument ' + field)
                values[field] = args[index] if index < len(args) else kwargs.get(field)
            explicit_doc = values['doc'] is not None
            getter = values['fget']
            if values['doc'] is None and space.kind(getter) == 'function':
                node = space.data(getter).node
                if isinstance(node, ast.FunctionDef):
                    values['doc'] = ast.get_docstring(node, clean=False)
            self._push(space.new('property', PropertyData(
                values['fget'], values['fset'], values['fdel'], values['doc'], explicit_doc,
            )))

        elif name == 'type':
            self._arity(name, args, kwargs, 1, 1)
            self._push(space.type_of(args[0]))

        elif name == 'super':
            self._arity(name, args, kwargs, 0, 2)
            if not args:
                frame = env
                while frame.scope.kind == 'comprehension' and not frame.scope.generator and frame.parent is not None:
                    frame = frame.parent
                if frame.first_arg_name is None:
                    space.error('RuntimeError', 'super(): no arguments')
                cell = self._class_cell(frame)
                if cell is None or space.data(cell) is _MISSING:
                    space.error('RuntimeError', 'super(): __class__ cell not found')
                local = space.data(frame.namespace)
                if frame.first_arg_name not in local:
                    space.error('RuntimeError', 'super(): arg[0] deleted')
                args = (space.data(cell), local[frame.first_arg_name])
            elif len(args) == 1:
                start = args[0]
                if space.kind(start) not in ('class', 'type'):
                    space.error('TypeError', 'super() argument 1 must be a guest type')
                self._push(space.new('super', SuperData(ta.cast(ObjectRef, start), None, None)))
                return
            start, receiver = args
            if space.kind(start) not in ('class', 'type'):
                space.error('TypeError', 'super() argument 1 must be a guest type')
            if receiver is None:
                self._push(space.new('super', SuperData(ta.cast(ObjectRef, start), None, None)))
                return
            receiver_kind = space.kind(receiver)
            if receiver_kind in ('instance', 'exception'):
                owner = space.type_of(receiver)
            elif receiver_kind in ('class', 'type'):
                owner = receiver
            else:
                space.error('TypeError', 'super() argument 2 must be a guest instance or type')
            start_ref = ta.cast(ObjectRef, start)
            owner_ref = ta.cast(ObjectRef, owner)
            if not space.subclass(owner_ref, start_ref):
                space.error('TypeError', 'super() argument 2 is not a subtype of argument 1')
            self._push(space.new('super', SuperData(start_ref, receiver, owner_ref)))

        else:
            space.error('TypeError', name + ' cannot be constructed directly')

    def _task_range_index_next(self, task: Task) -> None:
        args, converted, index = task.data
        numbers = (*converted, self._pop())

        if index + 1 < len(args):
            self._add('range_index_next', task.env, data=(args, numbers, index + 1))
            self._operation('index', task.env, args[index + 1])
            return

        if len(numbers) == 1:
            start, stop, step = 0, numbers[0], 1
        elif len(numbers) == 2:
            start, stop, step = *numbers, 1
        else:
            start, stop, step = numbers

        if step == 0:
            self._space.error('ValueError', 'range() arg 3 must not be zero')

        self._push(self._space.new('range', RangeData(start, stop, step)))

    def _task_bytes_count(self, task: Task) -> None:
        count = self._pop()
        self._budget.size(count, string=True)
        self._budget.allocate(max(0, count))
        self._push(self._space.native(bytes, count))

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

    def _task_construct_bytes_iterator(self, task: Task) -> None:
        self._add('construct_bytes_next', task.env, data=(self._pop(), ()))

    def _task_construct_bytes_next(self, task: Task) -> None:
        iterator, values = task.data
        self._pull(
            task.env, iterator,
            Task('construct_bytes_item', task.env, data=task.data),
            Task('construct_bytes_stop', task.env, data=values),
        )

    def _task_construct_bytes_item(self, task: Task) -> None:
        self._add('construct_bytes_indexed', task.env, data=task.data)
        self._operation('index', task.env, self._pop())

    def _task_construct_bytes_indexed(self, task: Task) -> None:
        value = self._pop()
        if not 0 <= value <= 255:
            self._space.error('ValueError', 'bytes must be in range(0, 256)')
        iterator, values = task.data
        self._budget.size(len(values) + 1, string=True)
        self._add('construct_bytes_next', task.env, data=(iterator, (*values, value)))

    def _task_construct_bytes_stop(self, task: Task) -> None:
        self._pop()
        self._budget.allocate(len(task.data))
        self._push(self._space.native(bytes, task.data))

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
