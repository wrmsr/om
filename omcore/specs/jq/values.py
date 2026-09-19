import collections.abc
import functools
import json
import math
import operator
import sys
import typing as ta

from ... import dataclasses as dc
from .errors import JqCycleError
from .errors import JqPathError
from .errors import JqTypeError
from .errors import JqValueError
from .options import JqValueOptions
from .options import ObjectKeyPolicy


JqPathComponent: ta.TypeAlias = str | int
JqPath: ta.TypeAlias = tuple[JqPathComponent, ...]


##


@dc.dataclass(frozen=True)
class JqValueOps:
    options: JqValueOptions = JqValueOptions()

    _SEQUENCE_EXCLUSIONS: ta.ClassVar[tuple[type, ...]] = (str, bytes, bytearray, memoryview)

    def is_mapping(self, value: ta.Any) -> bool:
        return isinstance(value, collections.abc.Mapping)

    def is_sequence(self, value: ta.Any) -> bool:
        return (
            isinstance(value, collections.abc.Sequence) and
            not isinstance(value, self._SEQUENCE_EXCLUSIONS)
        )

    def adapt_object_key(self, key: object) -> str | None:
        if isinstance(key, str):
            return key

        if (stringifier := self.options.object_key_stringifier) is not None:
            adapted = stringifier(key)
            if not isinstance(adapted, str):
                raise JqTypeError('object key stringifier did not return a string')
            return adapted

        if self.options.object_key_policy is ObjectKeyPolicy.IGNORE:
            return None

        raise JqTypeError(f'jq object key is not a string: {key!r}')

    def iter_object_items(self, value: ta.Mapping[ta.Any, ta.Any]) -> ta.Iterator[tuple[str, ta.Any]]:
        for key, item in value.items():
            if (adapted := self.adapt_object_key(key)) is not None:
                yield adapted, item

    def object_dict(self, value: ta.Mapping[ta.Any, ta.Any]) -> dict[str, ta.Any]:
        return dict(self.iter_object_items(value))

    def type_name(self, value: ta.Any) -> str:
        if value is None:
            return 'null'
        if isinstance(value, bool):
            return 'boolean'
        if isinstance(value, (int, float)):
            if isinstance(value, float) and not math.isfinite(value):
                raise JqValueError('non-finite numbers are not jq values')
            return 'number'
        if isinstance(value, str):
            return 'string'
        if self.is_sequence(value):
            return 'array'
        if self.is_mapping(value):
            return 'object'
        raise JqTypeError(f'unsupported jq value: {value!r}')

    def truthy(self, value: ta.Any) -> bool:
        return value is not None and value is not False

    def equal(self, left: ta.Any, right: ta.Any) -> bool:
        return self._equal(left, right, set())

    def _equal(self, left: ta.Any, right: ta.Any, active: set[tuple[int, int]]) -> bool:
        left_type = self.type_name(left)
        right_type = self.type_name(right)

        if left_type == 'number' and right_type == 'number':
            return ta.cast('int | float', left) == ta.cast('int | float', right)
        if left_type != right_type:
            return False
        if left_type in ('null', 'boolean', 'string'):
            return left == right

        pair = (id(left), id(right))
        if pair in active:
            raise JqCycleError('cyclic jq value')
        active.add(pair)
        try:
            if left_type == 'array':
                left_seq = ta.cast('ta.Sequence[ta.Any]', left)
                right_seq = ta.cast('ta.Sequence[ta.Any]', right)
                return (
                    len(left_seq) == len(right_seq) and
                    all(self._equal(a, b, active) for a, b in zip(left_seq, right_seq))
                )

            left_obj = self.object_dict(ta.cast('ta.Mapping[ta.Any, ta.Any]', left))
            right_obj = self.object_dict(ta.cast('ta.Mapping[ta.Any, ta.Any]', right))
            return (
                left_obj.keys() == right_obj.keys() and
                all(self._equal(left_obj[key], right_obj[key], active) for key in left_obj)
            )
        finally:
            active.remove(pair)

    _TYPE_ORDER: ta.ClassVar[ta.Mapping[str, int]] = {
        'null': 0,
        'boolean': 1,
        'number': 2,
        'string': 3,
        'array': 4,
        'object': 5,
    }

    def compare(self, left: ta.Any, right: ta.Any) -> int:
        return self._compare(left, right, set())

    def _compare(self, left: ta.Any, right: ta.Any, active: set[tuple[int, int]]) -> int:
        left_type = self.type_name(left)
        right_type = self.type_name(right)
        if left_type != right_type:
            return self._cmp(self._TYPE_ORDER[left_type], self._TYPE_ORDER[right_type])

        if left_type == 'null':
            return 0
        if left_type in ('boolean', 'number', 'string'):
            return self._cmp(left, right)

        pair = (id(left), id(right))
        if pair in active:
            raise JqCycleError('cyclic jq value')
        active.add(pair)
        try:
            if left_type == 'array':
                left_seq = ta.cast('ta.Sequence[ta.Any]', left)
                right_seq = ta.cast('ta.Sequence[ta.Any]', right)
                for a, b in zip(left_seq, right_seq):
                    if (compared := self._compare(a, b, active)) != 0:
                        return compared
                return self._cmp(len(left_seq), len(right_seq))

            left_obj = self.object_dict(ta.cast('ta.Mapping[ta.Any, ta.Any]', left))
            right_obj = self.object_dict(ta.cast('ta.Mapping[ta.Any, ta.Any]', right))
            left_keys = sorted(left_obj)
            right_keys = sorted(right_obj)
            for a, b in zip(left_keys, right_keys):
                if (compared := self._cmp(a, b)) != 0:
                    return compared
            if (compared := self._cmp(len(left_keys), len(right_keys))) != 0:
                return compared
            for key in left_keys:
                if (compared := self._compare(left_obj[key], right_obj[key], active)) != 0:
                    return compared
            return 0
        finally:
            active.remove(pair)

    @staticmethod
    def _cmp(left: ta.Any, right: ta.Any) -> int:
        return (left > right) - (left < right)

    def sort(self, values: ta.Iterable[ta.Any]) -> list[ta.Any]:
        return sorted(values, key=functools.cmp_to_key(self.compare))

    def iterate(self, value: ta.Any) -> ta.Iterator[tuple[JqPathComponent, ta.Any]]:
        value_type = self.type_name(value)
        if value_type == 'array':
            yield from enumerate(ta.cast('ta.Sequence[ta.Any]', value))
            return
        if value_type == 'object':
            yield from self.iter_object_items(ta.cast('ta.Mapping[ta.Any, ta.Any]', value))
            return
        raise JqTypeError(f'cannot iterate over {value_type}')

    def index(self, value: ta.Any, key: ta.Any) -> ta.Any:
        value_type = self.type_name(value)
        if value_type == 'null':
            if isinstance(key, str) or self.array_index(key) is not None:
                return None
            raise JqTypeError(f'cannot index null with {self.type_name(key)}')
        if value_type == 'object':
            if not isinstance(key, str):
                raise JqTypeError(f'cannot index object with {self.type_name(key)}')
            if self.options.object_key_stringifier is None:
                try:
                    return value[key]
                except KeyError:
                    return None
            return self.object_dict(ta.cast('ta.Mapping[ta.Any, ta.Any]', value)).get(key)
        if value_type == 'array':
            index = self.array_index(key)
            if index is None:
                raise JqTypeError(f'cannot index array with {self.type_name(key)}')
            sequence = ta.cast('ta.Sequence[ta.Any]', value)
            if index < 0:
                index += len(sequence)
            if index < 0 or index >= len(sequence):
                return None
            return sequence[index]
        raise JqTypeError(f'cannot index {value_type}')

    def slice(self, value: ta.Any, start: ta.Any, end: ta.Any) -> ta.Any:
        value_type = self.type_name(value)
        if value_type == 'null':
            return None
        if value_type != 'array' and value_type != 'string':
            raise JqTypeError(f'cannot slice {value_type}')
        start_index = self._slice_index(start, end=False)
        end_index = self._slice_index(end, end=True)
        result = value[slice(start_index, end_index)]
        if value_type == 'array':
            return list(result)
        return result

    def length(self, value: ta.Any) -> int | float:
        value_type = self.type_name(value)
        if value_type == 'null':
            return 0
        if value_type == 'number':
            return abs(value)
        if value_type == 'string' or value_type == 'array':
            return len(value)
        if value_type == 'object':
            return len(self.object_dict(value))
        raise JqTypeError(f'{value_type} has no length')

    def keys(self, value: ta.Any, *, sorted_: bool) -> list[ta.Any]:
        value_type = self.type_name(value)
        if value_type == 'array':
            return list(range(len(value)))
        if value_type == 'object':
            keys = list(self.object_dict(value))
            if sorted_:
                keys.sort()
            return keys
        raise JqTypeError(f'{value_type} has no keys')

    def has(self, value: ta.Any, key: ta.Any) -> bool:
        value_type = self.type_name(value)
        if value_type == 'object':
            if not isinstance(key, str):
                raise JqTypeError('object key must be a string')
            if self.options.object_key_stringifier is None:
                return key in value
            return key in self.object_dict(value)
        if value_type == 'array':
            index = self.array_index(key)
            if index is None:
                raise JqTypeError('array index must be an integer')
            return 0 <= index < len(value)
        raise JqTypeError(f'cannot check membership in {value_type}')

    def add(self, left: ta.Any, right: ta.Any) -> ta.Any:
        if left is None:
            return right
        if right is None:
            return left
        left_type = self.type_name(left)
        right_type = self.type_name(right)
        if left_type == right_type == 'number':
            return self._number_binary(left, right, operator.add)
        if left_type == right_type == 'string':
            return left + right
        if left_type == right_type == 'array':
            return [*left, *right]
        if left_type == right_type == 'object':
            return {**self.object_dict(left), **self.object_dict(right)}
        raise JqTypeError(f'cannot add {left_type} and {right_type}')

    def subtract(self, left: ta.Any, right: ta.Any) -> ta.Any:
        left_type = self.type_name(left)
        right_type = self.type_name(right)
        if left_type == right_type == 'number':
            return self._number_binary(left, right, operator.sub)
        if left_type == right_type == 'array':
            return [item for item in left if not any(self.equal(item, removed) for removed in right)]
        raise JqTypeError(f'cannot subtract {right_type} from {left_type}')

    def multiply(self, left: ta.Any, right: ta.Any) -> ta.Any:
        left_type = self.type_name(left)
        right_type = self.type_name(right)
        if left_type == right_type == 'number':
            return self._number_binary(left, right, operator.mul)
        if left_type == 'string' and right_type == 'number':
            count = int(right)
            return None if count < 0 else left * count
        if left_type == 'number' and right_type == 'string':
            count = int(left)
            return None if count < 0 else right * count
        if left_type == right_type == 'object':
            return self._merge_objects(left, right)
        raise JqTypeError(f'cannot multiply {left_type} and {right_type}')

    def _merge_objects(self, left: ta.Any, right: ta.Any) -> dict[str, ta.Any]:
        result = self.object_dict(left)
        for key, right_value in self.iter_object_items(right):
            if key in result and self.is_mapping(result[key]) and self.is_mapping(right_value):
                result[key] = self._merge_objects(result[key], right_value)
            else:
                result[key] = right_value
        return result

    def divide(self, left: ta.Any, right: ta.Any) -> ta.Any:
        left_type = self.type_name(left)
        right_type = self.type_name(right)
        if left_type == right_type == 'number':
            if right == 0:
                raise JqValueError('division by zero')
            return self._number_binary(left, right, operator.truediv)
        if left_type == right_type == 'string':
            return list(left) if not right else left.split(right)
        raise JqTypeError(f'cannot divide {left_type} by {right_type}')

    def modulo(self, left: ta.Any, right: ta.Any) -> ta.Any:
        if self.type_name(left) != 'number' or self.type_name(right) != 'number':
            raise JqTypeError('modulo requires numbers')
        left_integer = int(left)
        right_integer = int(right)
        if right_integer == 0:
            raise JqValueError('modulo by zero')
        remainder = abs(left_integer) % abs(right_integer)
        return -remainder if left_integer < 0 else remainder

    def negate(self, value: ta.Any) -> ta.Any:
        if self.type_name(value) != 'number':
            raise JqTypeError('negation requires a number')
        return -value

    @staticmethod
    def _number_result(value: float) -> int | float:
        if isinstance(value, float):
            if math.isnan(value):
                raise JqValueError('numeric operation produced NaN')
            if math.isinf(value):
                return math.copysign(sys.float_info.max, value)
        return value

    @classmethod
    def _number_binary(
            cls,
            left: float,
            right: float,
            operation: ta.Callable[[ta.Any, ta.Any], int | float],
    ) -> int | float:
        try:
            return cls._number_result(operation(left, right))
        except OverflowError:
            if operation in (operator.mul, operator.truediv):
                sign = -1.0 if (left < 0) != (right < 0) else 1.0
            else:
                sign = -1.0 if left < 0 else 1.0
            return math.copysign(sys.float_info.max, sign)

    def tostring(self, value: ta.Any) -> str:
        if isinstance(value, str):
            return value
        return self.tojson(value)

    def tojson(self, value: ta.Any) -> str:
        return json.dumps(self.canonicalize(value), ensure_ascii=False, separators=(',', ':'), allow_nan=False)

    def fromjson(self, value: ta.Any) -> ta.Any:
        if not isinstance(value, str):
            raise JqTypeError('fromjson requires a string')
        try:
            result = json.loads(value)
        except (json.JSONDecodeError, ValueError) as exc:
            raise JqValueError(str(exc)) from exc
        self.validate(result)
        return result

    def canonicalize(self, value: ta.Any) -> ta.Any:
        return self._canonicalize(value, set())

    def _canonicalize(self, value: ta.Any, active: set[int]) -> ta.Any:
        value_type = self.type_name(value)
        if value_type in ('null', 'boolean', 'number', 'string'):
            return value
        value_id = id(value)
        if value_id in active:
            raise JqCycleError('cyclic jq value')
        active.add(value_id)
        try:
            if value_type == 'array':
                return [self._canonicalize(item, active) for item in value]
            return {key: self._canonicalize(item, active) for key, item in self.iter_object_items(value)}
        finally:
            active.remove(value_id)

    def validate(self, value: ta.Any) -> None:
        self._validate(value, set())

    def _validate(self, value: ta.Any, active: set[int]) -> None:
        value_type = self.type_name(value)
        if value_type in ('null', 'boolean', 'number', 'string'):
            return
        value_id = id(value)
        if value_id in active:
            raise JqCycleError('cyclic jq value')
        active.add(value_id)
        try:
            if value_type == 'array':
                for item in value:
                    self._validate(item, active)
            else:
                for _, item in self.iter_object_items(value):
                    self._validate(item, active)
        finally:
            active.remove(value_id)

    def contains(self, container: ta.Any, candidate: ta.Any) -> bool:
        container_type = self.type_name(container)
        candidate_type = self.type_name(candidate)
        if container_type != candidate_type:
            return False
        if container_type == 'string':
            return candidate in container
        if container_type == 'array':
            return all(any(self.contains(item, wanted) for item in container) for wanted in candidate)
        if container_type == 'object':
            container_obj = self.object_dict(container)
            return all(
                key in container_obj and self.contains(container_obj[key], value)
                for key, value in self.iter_object_items(candidate)
            )
        return self.equal(container, candidate)

    def getpath(self, value: ta.Any, path: ta.Iterable[ta.Any]) -> ta.Any:
        result = value
        for component in self.normalize_path(path):
            result = self.index(result, component)
        return result

    def setpath(self, value: ta.Any, path: ta.Iterable[ta.Any], replacement: ta.Any) -> ta.Any:
        normalized = self.normalize_path(path)
        return self._setpath(value, normalized, 0, replacement)

    def _setpath(self, value: ta.Any, path: JqPath, offset: int, replacement: ta.Any) -> ta.Any:
        if offset == len(path):
            return replacement

        component = path[offset]
        if isinstance(component, str):
            if value is None:
                result: dict[str, ta.Any] = {}
            elif self.is_mapping(value):
                result = self.object_dict(value)
            else:
                raise JqPathError(f'cannot index {self.type_name(value)} with a string path component')
            result[component] = self._setpath(result.get(component), path, offset + 1, replacement)
            return result

        if value is None:
            result_list: list[ta.Any] = []
        elif self.is_sequence(value):
            result_list = list(value)
        else:
            raise JqPathError(f'cannot index {self.type_name(value)} with an integer path component')
        index = component
        if index < 0:
            index += len(result_list)
        if index < 0:
            raise JqPathError(f'array index out of bounds: {component}')
        if index >= len(result_list):
            result_list.extend([None] * (index + 1 - len(result_list)))
        result_list[index] = self._setpath(result_list[index], path, offset + 1, replacement)
        return result_list

    def delpaths(self, value: ta.Any, paths: ta.Iterable[ta.Iterable[ta.Any]]) -> ta.Any:
        trie: dict[ta.Any, ta.Any] = {}
        terminal = object()
        for raw_path in paths:
            node = trie
            path = self.normalize_path(raw_path)
            if not path:
                node[terminal] = True
                continue
            for component in path:
                node = node.setdefault(component, {})
            node[terminal] = True
        result = self._deltrie(value, trie, terminal)
        return None if result is _DELETED else result

    def _deltrie(self, value: ta.Any, trie: dict[ta.Any, ta.Any], terminal: object) -> ta.Any:
        if terminal in trie:
            return _DELETED
        if value is None:
            return value
        value_type = self.type_name(value)
        if value_type == 'object':
            result = self.object_dict(value)
            for component, child_trie in trie.items():
                if not isinstance(component, str) or component not in result:
                    continue
                child = self._deltrie(result[component], child_trie, terminal)
                if child is _DELETED:
                    del result[component]
                else:
                    result[component] = child
            return result
        if value_type == 'array':
            result_list = list(value)
            indexed: list[tuple[int, ta.Any]] = []
            for component, child_trie in trie.items():
                if not self._is_int(component):
                    continue
                index = component if component >= 0 else len(result_list) + component
                if 0 <= index < len(result_list):
                    indexed.append((index, child_trie))
            for index, child_trie in sorted(indexed, reverse=True):
                child = self._deltrie(result_list[index], child_trie, terminal)
                if child is _DELETED:
                    del result_list[index]
                else:
                    result_list[index] = child
            return result_list
        return value

    def normalize_path(self, path: ta.Iterable[ta.Any]) -> JqPath:
        if isinstance(path, self._SEQUENCE_EXCLUSIONS) or not isinstance(path, collections.abc.Sequence):
            raise JqPathError('jq path must be an array')
        result: list[JqPathComponent] = []
        for component in path:
            if isinstance(component, str):
                result.append(component)
            elif (index := self.array_index(component)) is not None:
                result.append(index)
            else:
                raise JqPathError(f'invalid jq path component: {component!r}')
        return tuple(result)

    @staticmethod
    def _is_int(value: ta.Any) -> ta.TypeGuard[int]:
        return isinstance(value, int) and not isinstance(value, bool)

    @classmethod
    def array_index(cls, value: ta.Any) -> int | None:
        if cls._is_int(value):
            return value
        if isinstance(value, float) and math.isfinite(value):
            return int(value)
        return None

    @classmethod
    def _slice_index(cls, value: ta.Any, *, end: bool) -> int | None:
        if value is None:
            return None
        if cls._is_int(value):
            return value
        if isinstance(value, float) and math.isfinite(value):
            return math.ceil(value) if end else math.floor(value)
        raise JqTypeError('slice indexes must be numbers or null')


_DELETED = object()
