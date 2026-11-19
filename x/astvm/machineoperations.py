# mypy: disable-error-code=attr-defined
import operator
import re
import sys
import typing as ta

from .state import BuiltinData
from .state import Task
from .values import _MISSING
from .values import _NUMBERS
from .values import _SCALARS
from .values import InterpreterError


##


class MachineOperations:
    _TASK_OPERATION_NAMES: ta.ClassVar = (
        'truth',
        'len',
        'iter',
        'next',
        'str',
        'repr',
        'ascii',
        'format',
        'getitem',
        'setitem',
        'delitem',
    )

    _TASK_OPERATION_SPECIAL_NAMES: ta.ClassVar = {
        'truth': '__bool__',
        'len': '__len__',
        'iter': '__iter__',
        'next': '__next__',
        'str': '__str__',
        'repr': '__repr__',
        'ascii': '__repr__',
        'format': '__format__',
        'getitem': '__getitem__',
        'setitem': '__setitem__',
        'delitem': '__delitem__',
    }

    _TASK_OPERATION_EXPECTED: ta.ClassVar = {
        'truth': 'bool',
        'len': 'len',
        'iter': 'iterator',
        'str': 'str',
        'repr': 'str',
        'ascii': 'ascii',
        'format': 'str',
    }

    def _task_operation(self, task: Task) -> None:
        name, values = task.data
        env, space = task.env, self._space
        value = values[0] if values else None
        kind = space.kind(value)

        if name in self._TASK_OPERATION_NAMES:
            special_name = self._TASK_OPERATION_SPECIAL_NAMES[name]
            method = space.special(value, special_name)
            expected = self._TASK_OPERATION_EXPECTED.get(name)

            if method is _MISSING and name == 'truth':
                method = space.special(value, '__len__')
                expected = 'len_bool'

            if method is _MISSING and name == 'str':
                method = space.special(value, '__repr__')

            if method is not _MISSING:
                if expected is not None:
                    self._add('expect', env, data=expected)

                args = values[1:]
                if name in ('setitem', 'delitem'):
                    self._add('constant', env, data=None)
                    self._add('discard', env)
                    args = values[1:2] if name == 'delitem' else values[1:]

                self._invoke(env, method, args)
                return

        if name == 'truth':
            self._push(space.truth(value))

        elif name == 'len':
            length = space.length(value)
            if length > sys.maxsize:
                space.error('OverflowError', 'length does not fit in a platform index')
            self._push(length)

        elif name == 'iter':
            if kind == 'adapter':
                self._push(value)
            else:
                self._push(space.iter_value(value))

        elif name == 'next':
            if kind == 'generator':
                self._resume_generator(env, value, 'next', None)
            elif kind == 'iterator':
                self._push(space.next_value(value))
            elif kind == 'adapter':
                self._adapter_next(env, value)
            else:
                space.error('TypeError', 'object is not an iterator')

        elif name == 'getattr':
            self._resolve(space.get_attribute(value, values[1]), env)

        elif name == 'getitem':
            self._resolve(space.get_item(value, values[1]), env)

        elif name in ('setitem', 'delitem'):
            if name == 'setitem' and kind == 'list' and space.kind(values[1]) == 'slice':
                self._add('slice_assignment', env, data=values[:2])
                self._collect(env, values[2])
            else:
                space.set_item(value, values[1], values[2], delete=name == 'delitem')
                self._push(None)

        elif name.startswith(('binary:', 'inplace:', 'compare:')):
            category, op = name.split(':')
            left, right = values

            if category == 'compare' and op in ('Is', 'IsNot'):
                self._push(space.compare(op, left, right))
                return

            if category == 'compare' and op in ('In', 'NotIn'):
                self._add('contains_result', env, data=op == 'NotIn')
                method = space.special(right, '__contains__')

                if method is not _MISSING:
                    self._invoke(env, method, (left,))

                elif space.kind(right) in ('dict', 'namespace', 'set', 'frozenset'):
                    if space.kind(right) == 'namespace':
                        self._push(type(left) is str and left in space.data(right))
                    else:
                        self._push(space.key(left) in space.data(right))

                elif type(right) in (str, bytes):
                    if type(left) not in (str, bytes, int, bool):
                        space.error('TypeError', 'invalid string membership operand')
                    self._push(space.native(operator.contains, right, left))

                elif space.kind(right) == 'range' and type(left) in (bool, int):
                    info = space.data(right)
                    self._push(left in range(info.start, info.stop, info.step))

                else:
                    self._add('contains_iterator', env, data=left)
                    self._operation('iter', env, right)

                return

            if category == 'inplace' and kind == 'list' and op == 'Add':
                self._add('constant', env, data=left)
                self._add('discard', env)
                self._invoke(env, space.new('builtin', BuiltinData('list.extend', left)), (right,))
                return

            if category == 'inplace' and kind == 'list' and op == 'Mult':
                result = space.binary(op, left, right)
                self._runtime.replace(left, list(space.data(result)))
                self._push(left)
                return

            if category == 'inplace' and kind in ('dict', 'namespace') and op == 'BitOr':
                self._update_mapping(env, left, right, {}, left)
                return

            if category == 'inplace' and kind == 'set' and op in ('BitOr', 'BitAnd', 'BitXor', 'Sub'):
                result = space.binary(op, left, right)
                self._runtime.replace(left, dict(space.data(result)))
                self._push(left)
                return

            candidates = []
            if category == 'inplace':
                method = space.special(left, '__i' + self._binary_method(op) + '__')
                if method is not _MISSING:
                    candidates.append((method, (right,)))

            if category == 'compare':
                methods = {
                    'Eq': ('__eq__', '__eq__'),
                    'NotEq': ('__ne__', '__ne__'),
                    'Lt': ('__lt__', '__gt__'),
                    'LtE': ('__le__', '__ge__'),
                    'Gt': ('__gt__', '__lt__'),
                    'GtE': ('__ge__', '__le__'),
                }
                lname, rname = methods[op]
            else:
                method_name = self._binary_method(op)
                lname, rname = '__' + method_name + '__', '__r' + method_name + '__'

            lm, rm = space.special(left, lname), space.special(right, rname)
            lt, rt = space.type_of(left), space.type_of(right)

            reverse_first = lt != rt and space.subclass(rt, lt)
            left_pair, right_pair = (lm, (right,)), (rm, (left,))
            for method, args in ((right_pair, left_pair) if reverse_first else (left_pair, right_pair)):
                if method is not _MISSING:
                    if method == rm and category != 'compare' and lt == rt and not reverse_first:
                        continue
                    candidates.append((method, args))

            self._add('special_next', env, data=(name, values, tuple(candidates), 0))

        elif name.startswith('unary:'):
            op = name.split(':')[1]

            if op == 'Not':
                self._add('negate_bool', env)
                self._operation('truth', env, value)
                return

            method = space.special(
                value,
                {
                    'UAdd': '__pos__',
                    'USub': '__neg__',
                    'Invert': '__invert__',
                }[op],
            )

            if method is not _MISSING:
                self._invoke(env, method, ())

            elif type(value) in _NUMBERS:
                operation = {'UAdd': operator.pos, 'USub': operator.neg, 'Invert': operator.invert}[op]
                self._push(space.native(operation, value))

            else:
                space.error('TypeError', 'invalid unary operand')

        elif name in ('str', 'repr', 'ascii'):
            text = space.representation(value, string=name == 'str')
            if name == 'ascii':
                text = text.encode('ascii', 'backslashreplace').decode('ascii')
            self._budget.size(len(text), string=True)
            self._push(text)

        elif name == 'format':
            spec = values[1]

            if type(spec) is not str:
                space.error('TypeError', 'format specification must be a string')

            if type(value) not in _SCALARS:
                if spec:
                    space.error('TypeError', 'unsupported format specification')
                self._operation('str', env, value)
                return

            for digits in re.findall(r'\d+', spec):
                if len(digits) > 7 or int(digits) > self._budget.limits.string:
                    self._budget.fail('format width/precision limit')

            text = space.native(format, value, spec)
            self._budget.allocate(len(text))
            self._push(text)

        else:
            raise InterpreterError('unknown object-space operation: ' + name)
