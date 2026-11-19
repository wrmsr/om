# mypy: disable-error-code=attr-defined
import dataclasses as dc
import operator
import typing as ta

from ..state import IteratorData
from ..state import RangeData
from ..values import _ELLIPSIS
from ..values import _MISSING
from ..values import _NOT_IMPLEMENTED
from ..values import _SCALARS
from ..values import InterpreterError
from ..values import ObjectRef
from ..values import Value


##


@dc.dataclass(frozen=True, slots=True)
class _IdentityKey:
    serial: int


class SpaceCollections:
    def traceback_value(self, value: ObjectRef) -> Value:
        entries = self.data(value).traceback
        return self.import_value(entries) if entries else None

    def native(
            self,
            function: ta.Callable[..., object],
            *args: object,
            **kwargs: object,
    ) -> object:
        # Only internal call sites select this function. Inputs were reduced to exact primitive data.
        try:
            result = function(*args, **kwargs)

        except (ArithmeticError, ValueError, TypeError, LookupError) as exc:
            name = type(exc).__name__
            if name not in self.types:
                name = 'ValueError'

            self.error(name, str(exc))

        if type(result) in _SCALARS:
            self.budget.scalar(result)

        return result

    def key(self, value: Value, depth: int = 0) -> object:
        self.budget.tick()
        if depth > self.budget.limits.conversion_depth:
            self.budget.fail('key nesting limit')

        kind = self.kind(value)

        if type(value) in _SCALARS:
            return value

        if kind == 'tuple':
            return tuple(self.key(v, depth + 1) for v in self.data(value))

        if kind == 'frozenset':
            return frozenset(self.key(v, depth + 1) for v in self.data(value).values())

        if type(value) is ObjectRef and kind in ('instance', 'exception'):
            cls = self.data(value).cls
            method = self.lookup_class(cls, '__hash__')
            if method is _MISSING or (
                    self.kind(method) == 'builtin' and self.data(method).name == 'object_hash'
            ):
                return _IdentityKey(value.serial)

        if kind in ('class', 'type', 'function', 'builtin', 'capability', 'generator', 'super'):
            return _IdentityKey(value.serial)

        if value is _ELLIPSIS or value is _NOT_IMPLEMENTED:
            return value

        return self.error('TypeError', f'unhashable or unsupported key type: {kind}')

    def make_dict(self, pairs: ta.Iterable[tuple[Value, Value]]) -> ObjectRef:
        result = self.new('dict', {})
        for key, value in pairs:
            self.set_item(result, key, value)
        return result

    def length(self, value: Value) -> int:
        kind = self.kind(value)

        if type(value) in (str, bytes):
            return len(value)

        if kind in ('list', 'tuple', 'dict', 'namespace', 'set', 'frozenset'):
            return len(self.data(value))

        if kind == 'dict_view':
            return self.length(self.data(value)[0])

        if kind == 'range':
            info = self.data(value)
            if info.step > 0:
                return max(0, (info.stop - info.start + info.step - 1) // info.step)
            return max(0, (info.start - info.stop - info.step - 1) // -info.step)

        return self.error('TypeError', f'{kind} has no intrinsic length')

    def truth(self, value: Value) -> bool:
        if type(value) in _SCALARS:
            return bool(value)

        kind = self.kind(value)

        if kind in ('list', 'tuple', 'dict', 'namespace', 'set', 'frozenset', 'range', 'dict_view'):
            return self.length(value) != 0

        if value is _NOT_IMPLEMENTED:
            self.error('TypeError', 'NotImplemented should not be used in a boolean context')

        return True

    def index(self, value: Value) -> int:
        if type(value) not in (int, bool):
            self.error('TypeError', 'an integer is required')
        return int(value)

    def slice_value(self, value: ObjectRef) -> slice:
        parts = self.data(value)
        return slice(*(None if v is None else self.index(v) for v in parts))

    def get_item(self, value: Value, key: Value) -> Value:
        kind = self.kind(value)

        if kind == 'dict':
            record = self.data(value).get(self.key(key), _MISSING)
            if record is _MISSING:
                self.error('KeyError', key)
            return record[1]

        if kind == 'namespace':
            if type(key) is not str:
                self.error('KeyError', key)

            data = self.data(value)
            if key not in data:
                self.error('KeyError', key)
            return data[key]

        if kind in ('list', 'tuple', 'str', 'bytes', 'range'):
            if kind == 'range':
                info = self.data(value)
                seq = range(info.start, info.stop, info.step)
            else:
                seq = self.data(value) if kind in ('list', 'tuple') else value

            if self.kind(key) == 'slice':
                result = self.native(operator.getitem, seq, self.slice_value(key))

                if kind == 'range':
                    return self.new('range', RangeData(result.start, result.stop, result.step))

                if kind in ('list', 'tuple'):
                    return self.new(kind, result)

                return result

            return self.native(operator.getitem, seq, self.index(key))

        return self.error('TypeError', f'{kind} is not intrinsically subscriptable')

    def set_item(
            self,
            value: Value,
            key: Value,
            item: Value,
            *,
            delete: bool = False,
    ) -> None:
        kind = self.kind(value)

        if kind in ('dict', 'namespace', 'set'):
            if kind == 'namespace':
                if type(key) is not str:
                    self.error('TypeError', 'namespace keys must be strings')
                token, record = key, item

            else:
                token = self.key(key)
                record = key if kind == 'set' else (key, item)

            data = self.data(value)

            if delete:
                if token not in data:
                    self.error('KeyError', key)
                self.runtime.delete(value, token)

            else:
                if token not in data:
                    self.budget.size(len(data) + 1)
                    self.budget.allocate(1)
                elif kind == 'dict':
                    record = (data[token][0], item)

                self.runtime.write(value, token, record)

            return

        if kind == 'list':
            data = self.data(value)

            if self.kind(key) == 'slice':
                sl = self.slice_value(key)
                if sl.step == 0:
                    self.error('ValueError', 'slice step cannot be zero')

                if delete:
                    self.runtime.delete(value, sl)

                else:
                    if self.kind(item) not in ('list', 'tuple'):
                        raise InterpreterError('slice RHS must have been collected')

                    parts = list(self.data(item))
                    start, stop, step = sl.indices(len(data))
                    removed = len(range(start, stop, step))
                    if step != 1 and removed != len(parts):
                        self.error('ValueError', 'attempt to assign sequence of wrong size to extended slice')

                    self.budget.size(len(data) - removed + len(parts))
                    self.budget.allocate(len(parts))
                    self.runtime.write(value, sl, parts)

            else:
                index = self.index(key)
                if index < 0:
                    index += len(data)
                if not 0 <= index < len(data):
                    self.error('IndexError', 'list assignment index out of range')

                if delete:
                    self.runtime.delete(value, index)
                else:
                    self.runtime.write(value, index, item)

            return

        self.error('TypeError', f'{kind} does not support item mutation')

    def append(self, ref: ObjectRef, value: Value) -> None:
        self.budget.size(len(self.data(ref)) + 1)
        self.budget.allocate(1)
        self.runtime.append(ref, value)

    def iter_value(self, value: Value) -> Value:
        kind = self.kind(value)

        if kind in ('iterator', 'generator', 'adapter'):
            return value

        if kind == 'dict_view':
            target, _ = self.data(value)
            keys = tuple(k for k, _ in self.mapping_pairs(target))
            return self.new('iterator', IteratorData(value, keys=keys, size=len(keys)))

        if kind in ('list', 'tuple', 'str', 'bytes', 'range'):
            return self.new('iterator', IteratorData(value))

        if kind in ('dict', 'namespace', 'set', 'frozenset'):
            data = self.data(value)
            if kind == 'dict':
                keys = tuple(entry[0] for entry in data.values())
            elif kind == 'namespace':
                keys = tuple(data)
            else:
                keys = tuple(data.values())

            return self.new('iterator', IteratorData(value, keys=keys, size=len(data)))

        return self.error('TypeError', f'{kind} is not iterable')

    def next_value(self, iterator: ObjectRef) -> Value:
        info = self.data(iterator)

        if info.exhausted:
            self.error('StopIteration')

        if info.size is not None and self.length(info.target) != info.size:
            self.error('RuntimeError', 'container changed size during iteration')

        if info.keys is not None:
            if info.index >= len(info.keys):
                self.runtime.replace(iterator, dc.replace(info, exhausted=True))
                self.error('StopIteration')

            value = info.keys[info.index]

            if self.kind(info.target) == 'dict_view':
                target, mode = self.data(info.target)
                if mode != 'keys':
                    item = self.get_item(target, value)
                    value = item if mode == 'values' else self.new('tuple', (value, item))

        else:
            if info.index >= self.length(info.target):
                self.runtime.replace(iterator, dc.replace(info, exhausted=True))
                self.error('StopIteration')

            value = self.get_item(info.target, info.index)

        self.runtime.replace(iterator, dc.replace(info, index=info.index + 1))
        return value
