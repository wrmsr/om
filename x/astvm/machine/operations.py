# mypy: disable-error-code=attr-defined
import operator
import re
import sys
import typing as ta

from ..state import BuiltinData
from ..state import IteratorData
from ..state import Task
from ..values import _MISSING
from ..values import _NUMBERS
from ..values import _SCALARS
from ..values import InterpreterError
from ..values import _GuestRaise


##


class MachineOperations:
    _TASK_OPERATION_NAMES: ta.ClassVar = (
        'truth',
        'len',
        'index',
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
        'index': '__index__',
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
        'index': 'index',
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

                self._invoke_special_method(env, value, method, args)
                return

        if name == 'truth':
            self._push(space.truth(value))

        elif name == 'len':
            length = space.length(value)
            if length > sys.maxsize:
                space.error('OverflowError', 'length does not fit in a platform index')
            self._push(length)

        elif name == 'index':
            self._push(space.index(value))

        elif name == 'iter':
            if kind == 'adapter':
                self._push(value)
            elif kind in ('instance', 'exception') and space.special(value, '__getitem__') is not _MISSING:
                self._push(space.new('iterator', IteratorData(value)))
            else:
                self._push(space.iter_value(value))

        elif name == 'next':
            if kind == 'generator':
                self._resume_generator(env, value, 'next', None)
            elif kind == 'iterator':
                info = space.data(value)
                if space.kind(info.target) in ('instance', 'exception'):
                    if info.exhausted:
                        space.error('StopIteration')
                    method = space.special(info.target, '__getitem__')
                    if method is _MISSING:
                        space.error('TypeError', 'sequence no longer supports indexing')
                    self._add('sequence_next_guard', env, data=value)
                    self._add('sequence_next_value', env, data=value)
                    self._invoke_special_method(env, info.target, method, (info.index,))
                else:
                    self._push(space.next_value(value))
            elif kind == 'adapter':
                self._adapter_next(env, value)
            else:
                space.error('TypeError', 'object is not an iterator')

        elif name in ('getattr', 'getattribute_base'):
            attribute_name = values[1]
            if type(attribute_name) is not str:
                space.error('TypeError', 'attribute name must be a string')
            if kind == 'super':
                if attribute_name in ('__class__', '__thisclass__', '__self__', '__self_class__', '__get__'):
                    self._push(space.get_attribute(value, attribute_name))
                    return
                info = space.data(value)
                if info.owner is None:
                    space.error('AttributeError', attribute_name)
                found = space.lookup_super(info.start, info.owner, attribute_name, info.receiver)
                if found is _MISSING:
                    space.error('AttributeError', attribute_name)
                receiver = info.receiver if space.kind(info.receiver) in ('instance', 'exception') else _MISSING
                if space.kind(found) == 'property':
                    if receiver is _MISSING:
                        self._push(found)
                    else:
                        getter = space.data(found).getter
                        if getter is None:
                            space.error('AttributeError', attribute_name)
                        self._invoke(env, getter, (receiver,))
                    return
                getter = space.special(found, '__get__')
                if getter is not _MISSING:
                    self._invoke_special_method(
                        env, found, getter, (receiver if receiver is not _MISSING else None, info.owner),
                    )
                else:
                    self._resolve(space.bind(found, receiver, info.owner), env)
                return
            fallback = name == 'getattr'
            if fallback and kind in ('instance', 'exception'):
                method = space.special(value, '__getattribute__')
                if method is not _MISSING:
                    self._add('descriptor_get_guard', env, data=(value, attribute_name, True))
                    self._invoke_special_method(env, value, method, (attribute_name,))
                    return
            exception_fields = (
                'args', '__cause__', '__context__', '__suppress_context__', '__traceback__', '__dict__',
            )
            if (
                kind in ('instance', 'exception', 'class') and attribute_name != '__class__' and
                (kind != 'exception' or attribute_name not in exception_fields)
            ):
                cls = space.type_of(value) if kind in ('instance', 'exception') else value
                found = space.lookup_class(cls, attribute_name)
                if found is not _MISSING:
                    if space.kind(found) == 'property':
                        if kind == 'class':
                            self._push(found)
                            return
                        getter = space.data(found).getter
                        if getter is None:
                            getattr_method = space.special(value, '__getattr__') if fallback else _MISSING
                            if getattr_method is not _MISSING:
                                self._invoke_special_method(env, value, getattr_method, (attribute_name,))
                                return
                            space.error('AttributeError', attribute_name)
                        self._add('descriptor_get_guard', env, data=(value, attribute_name, fallback))
                        self._invoke(env, getter, (value,))
                        return

                    getter = space.special(found, '__get__')
                    if getter is not _MISSING:
                        namespace_ref = space.data(value).namespace if kind in ('instance', 'exception') else None
                        namespace = space.data(namespace_ref) if namespace_ref is not None else {}
                        data_descriptor = (
                            space.special(found, '__set__') is not _MISSING or
                            space.special(found, '__delete__') is not _MISSING
                        )
                        if kind == 'class' or data_descriptor or attribute_name not in namespace:
                            self._add('descriptor_get_guard', env, data=(value, attribute_name, fallback))
                            self._invoke_special_method(
                                env, found, getter, (value if kind in ('instance', 'exception') else None, cls),
                            )
                            return

            try:
                attribute = space.get_attribute(value, values[1])

            except _GuestRaise as exc:
                if not fallback or kind not in ('instance', 'exception') or not space.exception_matches(
                    exc.value, space.types['AttributeError'],
                ):
                    raise

                method = space.special(value, '__getattr__')
                if method is _MISSING:
                    raise

                self._invoke_special_method(env, value, method, (values[1],))

            else:
                self._resolve(attribute, env)

        elif name in ('setattr', 'delattr', 'setattr_base', 'delattr_base'):
            attribute_name = values[1]
            if type(attribute_name) is not str:
                space.error('TypeError', 'attribute name must be a string')
            delete = name in ('delattr', 'delattr_base')
            if name in ('setattr', 'delattr') and kind in ('instance', 'exception'):
                method = space.special(value, '__delattr__' if delete else '__setattr__')
                if method is not _MISSING:
                    self._add('constant', env, data=None)
                    self._add('discard', env)
                    self._invoke_special_method(
                        env, value, method, (attribute_name,) if delete else (attribute_name, values[2]),
                    )
                    return
            structural: tuple[str, ...] = ('__class__', '__dict__', '__bases__', '__mro__')
            if kind == 'exception':
                structural += ('args', '__cause__', '__context__', '__suppress_context__', '__traceback__')
            if kind in ('instance', 'exception') and attribute_name not in structural:
                found = space.lookup_class(space.type_of(value), attribute_name)
                if found is not _MISSING:
                    if space.kind(found) == 'property':
                        data = space.data(found)
                        method = data.deleter if delete else data.setter
                        if method is None:
                            space.error('AttributeError', attribute_name)
                        self._add('constant', env, data=None)
                        self._add('discard', env)
                        self._invoke(env, method, (value,) if delete else (value, values[2]))
                        return

                    method = space.special(found, '__delete__' if delete else '__set__')
                    if method is not _MISSING:
                        self._add('constant', env, data=None)
                        self._add('discard', env)
                        self._invoke_special_method(
                            env, found, method, (value,) if delete else (value, values[2]),
                        )
                        return
                    if space.special(found, '__set__' if delete else '__delete__') is not _MISSING:
                        space.error('AttributeError', 'descriptor does not support this operation')
            space.set_attribute(
                value, attribute_name, values[2] if not delete else None, delete=delete,
            )
            self._push(None)

        elif name == 'getitem':
            if kind in ('list', 'tuple', 'str', 'bytes', 'range') and space.kind(values[1]) == 'slice' and any(
                space.kind(part) in ('instance', 'exception') for part in space.data(values[1]) if part is not None
            ):
                self._add('slice_index_next', env, data=(name, values, tuple(space.data(values[1])), 0))
            elif (
                kind in ('list', 'tuple', 'str', 'bytes', 'range') and
                space.kind(values[1]) in ('instance', 'exception')
            ):
                self._add('indexed_getitem', env, data=value)
                self._operation('index', env, values[1])
            else:
                self._resolve(space.get_item(value, values[1]), env)

        elif name in ('setitem', 'delitem'):
            if kind == 'list' and space.kind(values[1]) == 'slice' and any(
                space.kind(part) in ('instance', 'exception') for part in space.data(values[1]) if part is not None
            ):
                self._add('slice_index_next', env, data=(name, values, tuple(space.data(values[1])), 0))
            elif name == 'setitem' and kind == 'list' and space.kind(values[1]) == 'slice':
                self._add('slice_assignment', env, data=values[:2])
                self._collect(env, values[2])
            elif kind == 'list' and space.kind(values[1]) in ('instance', 'exception'):
                self._add('indexed_setitem', env, data=(value, values[2], name == 'delitem'))
                self._operation('index', env, values[1])
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
                    self._invoke_special_method(env, right, method, (left,))

                elif space.kind(right) in ('dict', 'namespace', 'mappingproxy', 'set', 'frozenset'):
                    if space.kind(right) in ('namespace', 'mappingproxy'):
                        namespace = space.data(right)
                        if space.kind(right) == 'mappingproxy':
                            namespace = space.data(namespace)
                        self._push(type(left) is str and left in namespace)
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
                if space.kind(right) in ('instance', 'exception'):
                    self._add('inplace_repeat_index', env, data=left)
                    self._operation('index', env, right)
                else:
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
                    candidates.append((left, method, (right,)))

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
            if reverse_first and category != 'compare':
                reverse_first = (
                    rm is not _MISSING and
                    space.lookup_class(rt, rname) != space.lookup_class(lt, rname)
                )
            left_pair, right_pair = (left, lm, (right,)), (right, rm, (left,))
            pairs = (right_pair, left_pair) if reverse_first else (left_pair, right_pair)
            for pair_index, (receiver, method, args) in enumerate(pairs):
                if method is not _MISSING:
                    if pair_index == 1 and category != 'compare' and lt == rt:
                        continue
                    candidates.append((receiver, method, args))

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
                self._invoke_special_method(env, value, method, ())

            elif type(value) in _NUMBERS:
                operation = {'UAdd': operator.pos, 'USub': operator.neg, 'Invert': operator.invert}[op]
                self._push(space.native(operation, value))

            else:
                space.error('TypeError', 'invalid unary operand')

        elif name in ('str', 'repr', 'ascii'):
            if kind in self._REPRESENTED_CONTAINERS:
                if self._flat_intrinsic_container(value):
                    text = space.representation(value)
                    if name == 'ascii':
                        text = text.encode('ascii', 'backslashreplace').decode('ascii')
                    self._budget.size(len(text), string=True)
                    self._push(text)
                else:
                    if name == 'ascii':
                        self._add('representation_ascii', env)
                    self._represent_container(env, value)
                return
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
