import dataclasses as dc
import typing as ta

from ..state import AdapterData
from ..state import BoundMethodData
from ..state import BuiltinData
from ..state import Environment
from ..state import ExceptionData
from ..state import InstanceData
from ..state import ReductionState
from ..state import SuperData
from ..state import Task
from ..values import _MISSING
from ..values import _NUMBERS
from ..values import InterpreterError
from ..values import ObjectRef
from ..values import Value
from .base import MachineBase


##


class MachineBuiltins(MachineBase):
    def _builtin(
            self,
            env: Environment,
            info: BuiltinData,
            args: tuple[Value, ...],
            kwargs: ta.Mapping[str, Value],
    ) -> None:
        space = self._space
        name = info.name

        if name in ('exception_init', 'exception_init_bound'):
            self._arity(name, args, kwargs, 1 if name == 'exception_init' else 0, None)
            value = args[0] if name == 'exception_init' else info.receiver

            if space.kind(value) != 'exception':
                space.error('TypeError', 'exception initializer requires a guest exception')
            value_ref = ta.cast(ObjectRef, value)
            if (
                    name == 'exception_init' and
                    not space.subclass(space.data(value_ref).cls, ta.cast(ObjectRef, info.receiver))
            ):
                space.error('TypeError', 'exception initializer received an unrelated exception')

            values = args[1:] if name == 'exception_init' else args
            self._runtime.replace(value_ref, dc.replace(space.data(value_ref), args=values))
            self._push(None)
            return

        elif name == 'object_new':
            self._arity(name, args, {}, 1, None)
            cls = args[0]
            cls_ref = ta.cast(ObjectRef, cls)
            if space.kind(cls) not in ('class', 'type') or not space.subclass(cls_ref, space.types['object']):
                space.error('TypeError', 'object.__new__ requires a guest class')
            if space.subclass(cls_ref, space.types['BaseException']):
                space.error('TypeError', 'object.__new__ cannot allocate exception classes')
            if space.kind(cls) == 'type' and cls != space.types['object']:
                space.error('TypeError', 'object.__new__ does not allocate intrinsic types')
            if len(args) > 1 or kwargs:
                # CPython lets object.__new__ ignore constructor arguments when __init__ is overridden.
                initializer = space.lookup_class(cls_ref, '__init__')
                accepts_arguments = (
                    space.lookup_class(cls_ref, '__new__') is _MISSING and
                    initializer is not _MISSING and
                    not (
                        space.kind(initializer) == 'builtin' and space.data(initializer).name == 'object_init'
                    )
                )
                if not accepts_arguments:
                    self._arity(name, args, kwargs, 1, 1)
            self._push(space.new('instance', InstanceData(cls_ref, space.new('namespace', {}))))
            return

        elif name == 'exception_new':
            self._arity(name, args, {}, 1, None)
            cls = args[0]
            cls_ref = ta.cast(ObjectRef, cls)
            if space.kind(cls) not in ('class', 'type') or not space.subclass(cls_ref, space.types['BaseException']):
                space.error('TypeError', 'BaseException.__new__ requires an exception class')
            self._push(space.new('exception', ExceptionData(cls_ref, args[1:])))
            return

        elif name == 'object_init':
            if info.receiver is not _MISSING:
                args = (info.receiver, *args)
            self._arity(name, args, {}, 1, None)
            if len(args) > 1 or kwargs:
                # The dual rule applies to object.__init__ when __new__ is overridden.
                value = args[0]
                accepts_arguments = False
                if space.kind(value) in ('instance', 'exception'):
                    cls = space.type_of(value)
                    initializer = space.lookup_class(cls, '__init__')
                    accepts_arguments = (
                        space.lookup_class(cls, '__new__') is not _MISSING and
                        (
                            initializer is _MISSING or
                            (space.kind(initializer) == 'builtin' and space.data(initializer).name == 'object_init')
                        )
                    )
                if not accepts_arguments:
                    self._arity(name, args, kwargs, 1, 1)
            self._push(None)
            return

        elif name == 'object_init_subclass':
            self._arity(name, args, kwargs, 0, 0)
            self._push(None)
            return

        elif name in ('staticmethod_get', 'classmethod_get', 'property_get'):
            self._arity(name, args, kwargs, 1, 2)
            instance = args[0]
            descriptor_owner = args[1] if len(args) == 2 else None
            if instance is None and descriptor_owner is None:
                space.error('TypeError', '__get__(None, None) is invalid')
            if name == 'staticmethod_get':
                self._push(space.data(info.receiver))
            elif name == 'classmethod_get':
                cls = descriptor_owner if descriptor_owner is not None else space.type_of(instance)
                self._push(space.new('bound_method', BoundMethodData(space.data(info.receiver), cls)))
            elif instance is None:
                self._push(info.receiver)
            else:
                getter = space.data(info.receiver).getter
                if getter is None:
                    space.error('AttributeError', 'property has no getter')
                self._invoke(env, getter, (instance,))
            return

        elif name in ('property_set', 'property_delete'):
            count = 2 if name == 'property_set' else 1
            self._arity(name, args, kwargs, count, count)
            data = space.data(info.receiver)
            method = data.setter if name == 'property_set' else data.deleter
            if method is None:
                space.error('AttributeError', 'property has no setter or deleter')
            self._add('constant', env, data=None)
            self._add('discard', env)
            self._invoke(env, method, args)
            return

        elif name == 'super_get':
            self._arity(name, args, kwargs, 1, 2)
            proxy = info.receiver
            data = space.data(proxy)
            if data.owner is not None or args[0] is None:
                self._push(proxy)
                return
            receiver = args[0]
            receiver_kind = space.kind(receiver)
            if receiver_kind in ('instance', 'exception'):
                owner = space.type_of(receiver)
            elif receiver_kind in ('class', 'type'):
                owner = ta.cast(ObjectRef, receiver)
            else:
                space.error('TypeError', 'super descriptor requires a guest instance or type')
            if not space.subclass(owner, data.start):
                space.error('TypeError', 'super descriptor receiver is not a subtype')
            self._push(space.new('super', SuperData(data.start, receiver, owner)))
            return

        elif name == 'object_hash':
            if info.receiver is not _MISSING:
                args = (info.receiver, *args)
            self._arity(name, args, kwargs, 1, 1)
            self._push(hash(space.identity_number(args[0])))
            return

        elif name == 'object_dir':
            if info.receiver is not _MISSING:
                args = (info.receiver, *args)
            self._arity(name, args, kwargs, 1, 1)
            self._push(space.new('list', sorted(self._dir_names(args[0]))))
            return

        elif name in ('object_getattribute', 'object_setattr', 'object_delattr'):
            if info.receiver is not _MISSING:
                args = (info.receiver, *args)
            count = 3 if name == 'object_setattr' else 2
            self._arity(name, args, kwargs, count, count)
            if space.kind(args[0]) not in ('instance', 'exception'):
                space.error('TypeError', 'object attribute method requires a guest instance')
            self._operation(name.removeprefix('object_') + '_base', env, *args)
            return

        if info.receiver is not _MISSING:
            self._method(env, info, args, kwargs)
            return

        if name in ('len', 'repr', 'ascii', 'iter', 'next', 'format'):
            self._arity(name, args, kwargs, 1, 2 if name in ('iter', 'next', 'format') else 1)

            if name == 'iter' and len(args) == 2:
                self._push(space.new('adapter', AdapterData('sentinel', (), args[0], extra=args[1])))

            elif name == 'next':
                if len(args) == 2:
                    self._add('default_next_guard', env, data=args[1])
                self._operation('next', env, args[0])

            elif name == 'format':
                self._operation('format', env, args[0], args[1] if len(args) == 2 else '')

            else:
                self._operation(name, env, args[0])

        elif name in ('getattr', 'hasattr'):
            self._arity(name, args, kwargs, 2, 3 if name == 'getattr' else 2)

            if name == 'hasattr' or len(args) == 3:
                self._add('hasattr_guard', env, data=(False if name == 'hasattr' else args[2], name == 'hasattr'))

            self._operation('getattr', env, args[0], args[1])

        elif name in ('setattr', 'delattr'):
            count = 3 if name == 'setattr' else 2
            self._arity(name, args, kwargs, count, count)
            self._operation(name, env, *args)

        elif name in ('isinstance', 'issubclass'):
            self._arity(name, args, kwargs, 2, 2)
            self._push(self._isinstance(*args, subclass=name == 'issubclass'))

        elif name == 'callable':
            self._arity(name, args, kwargs, 1, 1)
            value = args[0]
            self._push(
                space.kind(value) in (
                    'type', 'class', 'function', 'builtin', 'bound_method', 'capability', 'staticmethod',
                ) or
                space.special(value, '__call__') is not _MISSING,
            )

        elif name in ('globals', 'locals', 'vars'):
            self._arity(name, args, kwargs, 0, 1 if name == 'vars' else 0)

            if args:
                self._operation('getattr', env, args[0], '__dict__')

            elif name == 'globals':
                self._push(env.globals)

            elif env.scope.kind in ('function', 'comprehension'):
                self._push(space.new('namespace', dict(space.data(env.namespace))))

            else:
                self._push(env.namespace)

        elif name == 'dir':
            self._arity(name, args, kwargs, 0, 1)
            if args:
                value = args[0]
                if space.kind(value) in ('instance', 'exception'):
                    method = space.special(value, '__dir__')
                    if method is not _MISSING:
                        self._add('dir_collected', env)
                        self._invoke_special_method(env, value, method, ())
                        return
                names = self._dir_names(value)
            else:
                names = space.data(env.namespace).keys()
            self._push(space.new('list', sorted(names)))

        elif name == 'id':
            self._arity(name, args, kwargs, 1, 1)
            self._push(space.identity_number(args[0]))

        elif name == 'hash':
            self._arity(name, args, kwargs, 1, 1)
            value = args[0]
            if space.kind(value) in ('instance', 'exception'):
                method = space.special(value, '__hash__')
                if method is not _MISSING:
                    if method is None:
                        space.error('TypeError', 'unhashable type')
                    self._add('hash_result', env)
                    self._invoke_special_method(env, value, method, ())
                    return
            key = space.key(value)
            if space.kind(value) in (
                    'instance', 'exception', 'class', 'type', 'function', 'builtin', 'capability', 'generator', 'super',
            ):
                self._push(hash(space.identity_number(value)))
            else:
                self._push(hash(key))

        elif name in ('staticmethod', 'classmethod'):
            self._arity(name, args, kwargs, 1, 1)
            self._push(space.new(name, args[0]))

        elif name in ('chr', 'ord', 'bin', 'oct', 'hex'):
            self._arity(name, args, kwargs, 1, 1)

            if name == 'ord':
                if type(args[0]) not in (str, bytes):
                    space.error('TypeError', 'ord expects a string or bytes')
                self._push(space.native(ord, args[0]))

            else:
                self._add('integer_builtin', env, data=name)
                self._operation('index', env, args[0])

        elif name in ('abs', 'round'):
            self._arity(name, args, kwargs, 1, 2 if name == 'round' else 1)
            method = space.special(args[0], '__' + name + '__')

            if method is not _MISSING:
                self._invoke_special_method(env, args[0], method, args[1:])

            elif type(args[0]) in _NUMBERS:
                if len(args) == 2:
                    self._add('round_digits', env, data=args[0])
                    self._operation('index', env, args[1])
                else:
                    self._push(ta.cast(Value, space.native(abs if name == 'abs' else round, *args)))

            else:
                space.error('TypeError', 'invalid numeric operand')

        elif name == 'pow':
            self._arity(name, args, kwargs, 2, 3)

            if len(args) == 2 or args[2] is None:
                self._operation('binary:Pow', env, *args[:2])

            else:
                numbers = tuple(space.index(v) for v in args)
                work = max(1, abs(numbers[2]).bit_length()) ** 2 * max(1, abs(numbers[1]).bit_length())
                self._budget.tick(max(1, work // 1024))
                self._push(space.native(pow, *numbers))

        elif name == 'divmod':
            self._arity(name, args, kwargs, 2, 2)

            if any(type(v) not in _NUMBERS for v in args):
                space.error('TypeError', 'divmod requires intrinsic numeric values')

            self._push(space.import_value(space.native(divmod, *args)))

        elif name in ('enumerate', 'zip', 'map', 'filter', 'reversed'):
            if name == 'enumerate':
                self._arity(name, args, kwargs, 1, 2, frozenset({'start'}))

                if len(args) == 2 and 'start' in kwargs:
                    space.error('TypeError', 'multiple values for start')

                self._add('enumerate_start', env, data=args[0])
                self._operation('index', env, args[1] if len(args) == 2 else kwargs.get('start', 0))
                return

            elif name == 'zip':
                self._arity(name, args, kwargs, 0, None, frozenset({'strict'}))

                if type(kwargs.get('strict', False)) is not bool:
                    space.error('TypeError', 'this implementation requires a bool strict flag')

                state, inputs = AdapterData(name, (), strict=ta.cast(bool, kwargs.get('strict', False))), args

            elif name in ('map', 'filter'):
                self._arity(name, args, kwargs, 2, 2 if name == 'filter' else None)
                state, inputs = AdapterData(name, (), args[0]), args[1:]

            else:
                self._arity(name, args, kwargs, 1, 1)

                method = space.special(args[0], '__reversed__')
                if method is not _MISSING:
                    self._invoke_special_method(env, args[0], method, ())
                    return

                if (
                    space.kind(args[0]) in ('instance', 'exception') and
                    space.special(args[0], '__len__') is not _MISSING and
                    space.special(args[0], '__getitem__') is not _MISSING
                ):
                    self._add('reversed_length', env, data=args[0])
                    self._operation('len', env, args[0])
                    return

                if space.kind(args[0]) not in ('list', 'tuple', 'str', 'bytes', 'range'):
                    space.error('TypeError', 'reversed requires an intrinsic sequence or __reversed__')

                self._push(space.new('adapter', AdapterData(name, (), index=space.length(args[0]) - 1, extra=args[0])))
                return

            self._add('adapter_iterators', env, data=(state, inputs, 0))

        elif name in ('sum', 'all', 'any', 'min', 'max'):
            minimum = 1
            maximum = 2 if name == 'sum' else 1 if name in ('all', 'any') else None

            allowed = (
                frozenset({'start'}) if name == 'sum' else
                frozenset({'key', 'default'}) if name in ('min', 'max') else frozenset()
            )

            self._arity(name, args, kwargs, minimum, maximum, allowed)

            iterable: Value
            if name in ('min', 'max') and len(args) > 1:
                if 'default' in kwargs:
                    space.error('TypeError', 'default is only valid with a single iterable')
                iterable = space.new('tuple', args)

            else:
                iterable = args[0]

            if name == 'sum' and len(args) == 2 and 'start' in kwargs:
                space.error('TypeError', 'multiple values for start')

            initial = (args[1] if len(args) == 2 else kwargs.get('start', 0)) if name == 'sum' else _MISSING
            if name == 'sum' and type(initial) in (str, bytes):
                space.error('TypeError', 'sum cannot concatenate strings')

            reduction_state = ReductionState(
                name,
                None,
                initial,
                _MISSING,
                kwargs.get('key'),
                kwargs.get('default', _MISSING),
            )

            self._add('reduction_iterator', env, data=reduction_state)
            self._operation('iter', env, iterable)

        elif name == 'sorted':
            self._arity(name, args, kwargs, 1, 1, frozenset({'key', 'reverse'}))
            self._add('sort_reverse', env, data=(args[0], kwargs.get('key')))
            self._operation('truth', env, kwargs.get('reverse', False))

        else:
            raise InterpreterError('unimplemented registered builtin: ' + name)

    def _dir_names(self, value: Value) -> set[str]:
        space = self._space
        kind = space.kind(value)
        names = {'__class__'}
        object_methods = (
            '__dict__', '__init__', '__new__', '__dir__', '__getattribute__', '__setattr__', '__delattr__',
            '__hash__',
        )
        cls: ObjectRef | None = None

        if kind in ('instance', 'exception'):
            info = space.data(value)
            cls = info.cls
            if kind == 'instance' or info.namespace is not None:
                names.update(space.data(info.namespace))
            names.update(object_methods)
            if kind == 'exception':
                names.update(('args', '__cause__', '__context__', '__traceback__', '__suppress_context__'))

        elif kind in ('class', 'type'):
            cls = ta.cast(ObjectRef, value)
            names.update(object_methods)

        elif kind == 'module':
            names.update(space.data(space.data(value)))

        if cls is not None:
            for base in space.data(cls).mro:
                self._budget.tick()
                names.update(space.data(space.data(base).namespace))
        else:
            names.update(space.method_names(kind))

        return names

    def _task_dir_collected(self, task: Task) -> None:
        self._add('dir_result', task.env)
        self._collect(task.env, self._pop())

    def _task_dir_result(self, task: Task) -> None:
        values = self._space.data(self._pop())
        if any(type(value) is not str for value in values):
            self._space.error('TypeError', '__dir__() must return strings')
        self._push(self._space.new('list', sorted(values)))

    def _task_integer_builtin(self, task: Task) -> None:
        function = {'chr': chr, 'bin': bin, 'oct': oct, 'hex': hex}[task.data]
        self._push(self._space.native(function, self._pop()))

    def _task_hash_result(self, task: Task) -> None:
        value = self._pop()
        if type(value) not in (int, bool):
            self._space.error('TypeError', '__hash__ method should return an integer')
        self._push(hash(value))

    def _task_round_digits(self, task: Task) -> None:
        self._push(self._space.native(round, task.data, self._pop()))

    def _task_enumerate_start(self, task: Task) -> None:
        state = AdapterData('enumerate', (), index=ta.cast(int, self._pop()))
        self._add('adapter_iterators', task.env, data=(state, (task.data,), 0))

    def _task_reversed_length(self, task: Task) -> None:
        self._push(self._space.new('adapter', AdapterData(
            'reversed', (), index=ta.cast(int, self._pop()) - 1, extra=task.data,
        )))

    def _task_hasattr_guard(self, task: Task) -> None:
        if task.data[1]:
            self._pop()
            self._push(True)
