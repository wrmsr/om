# mypy: disable-error-code=attr-defined
import dataclasses as dc
import typing as ta

from .state import AdapterData
from .state import BuiltinData
from .state import Environment
from .state import ReductionState
from .state import Task
from .values import _MISSING
from .values import _NUMBERS
from .values import InterpreterError
from .values import Value


##


class MachineBuiltins:
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
            if name == 'exception_init' and not space.subclass(space.data(value).cls, info.receiver):
                space.error('TypeError', 'exception initializer received an unrelated exception')

            values = args[1:] if name == 'exception_init' else args
            self._runtime.replace(value, dc.replace(space.data(value), args=values))
            self._push(None)
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
            space.set_attribute(args[0], args[1], args[2] if len(args) == 3 else None, delete=name == 'delattr')
            self._push(None)

        elif name in ('isinstance', 'issubclass'):
            self._arity(name, args, kwargs, 2, 2)
            self._push(self._isinstance(*args, subclass=name == 'issubclass'))

        elif name == 'callable':
            self._arity(name, args, kwargs, 1, 1)
            value = args[0]
            self._push(
                space.kind(value) in ('type', 'class', 'function', 'builtin', 'bound_method', 'capability') or
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

        elif name == 'id':
            self._arity(name, args, kwargs, 1, 1)
            self._push(space.identity_number(args[0]))

        elif name == 'hash':
            self._arity(name, args, kwargs, 1, 1)
            self._push(hash(space.key(args[0])))

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
                self._push(space.native({'chr': chr, 'bin': bin, 'oct': oct, 'hex': hex}[name], space.index(args[0])))

        elif name in ('abs', 'round'):
            self._arity(name, args, kwargs, 1, 2 if name == 'round' else 1)
            method = space.special(args[0], '__' + name + '__')

            if method is not _MISSING:
                self._invoke(env, method, args[1:])

            elif type(args[0]) in _NUMBERS:
                if len(args) == 2:
                    space.index(args[1])
                self._push(space.native(abs if name == 'abs' else round, *args))

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

                index = space.index(args[1] if len(args) == 2 else kwargs.get('start', 0))
                state, inputs = AdapterData(name, (), index=index), args[:1]

            elif name == 'zip':
                self._arity(name, args, kwargs, 0, None, frozenset({'strict'}))

                if type(kwargs.get('strict', False)) is not bool:
                    space.error('TypeError', 'this implementation requires a bool strict flag')

                state, inputs = AdapterData(name, (), strict=kwargs.get('strict', False)), args

            elif name in ('map', 'filter'):
                self._arity(name, args, kwargs, 2, 2 if name == 'filter' else None)
                state, inputs = AdapterData(name, (), args[0]), args[1:]

            else:
                self._arity(name, args, kwargs, 1, 1)

                method = space.special(args[0], '__reversed__')
                if method is not _MISSING:
                    self._invoke(env, method, ())
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

            state = ReductionState(
                name,
                None,
                initial,
                _MISSING,
                kwargs.get('key'),
                kwargs.get('default', _MISSING),
            )

            self._add('reduction_iterator', env, data=state)
            self._operation('iter', env, iterable)

        elif name == 'sorted':
            self._arity(name, args, kwargs, 1, 1, frozenset({'key', 'reverse'}))
            self._add('sort_reverse', env, data=(args[0], kwargs.get('key')))
            self._operation('truth', env, kwargs.get('reverse', False))

        else:
            raise InterpreterError('unimplemented registered builtin: ' + name)

    def _task_hasattr_guard(self, task: Task) -> None:
        if task.data[1]:
            self._pop()
            self._push(True)
