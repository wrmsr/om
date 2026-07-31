import enum
import typing as ta

from .... import dataclasses as dc
from .interfaces import BenchmarkContext


##


class WorkloadMode(enum.Enum):
    BUILD = 'build'
    READ = 'read'
    MUTATE = 'mutate'
    MUTATE_EMPTY = 'mutate_empty'


type Operation = ta.Callable[[BenchmarkContext, ta.Any], ta.Any]
type OperationCount = ta.Callable[[int], int]


@dc.dataclass(frozen=True)
class Workload:
    suite: str
    name: str
    mode: WorkloadMode
    operation: Operation | None
    operation_count: OperationCount
    comparison: bool = False

    @property
    def setup_per_cycle(self) -> bool:
        return self.mode in (WorkloadMode.BUILD, WorkloadMode.MUTATE, WorkloadMode.MUTATE_EMPTY)


@dc.dataclass(frozen=True)
class Trial:
    run: ta.Callable[[], ta.Any]
    operations: int


def prepare_trial(context: BenchmarkContext, workload: Workload, cycles: int) -> Trial:
    operations = cycles * workload.operation_count(context.data.size)

    if workload.comparison:
        context.comparison()

    if workload.mode is WorkloadMode.BUILD:
        if cycles == 1:
            return Trial(context.new, operations)

        def run_build() -> list[ta.Any]:
            return [context.new() for _ in range(cycles)]

        return Trial(run_build, operations)

    operation = workload.operation
    if operation is None:
        raise TypeError(workload)

    if workload.mode is WorkloadMode.READ:
        obj = context.base()

        def run_read() -> ta.Any:
            result = None
            for _ in range(cycles):
                result = operation(context, obj)
            return result

        return Trial(run_read, operations)

    if workload.mode is WorkloadMode.MUTATE:
        objects = [context.new() for _ in range(cycles)]
    elif workload.mode is WorkloadMode.MUTATE_EMPTY:
        objects = [context.empty() for _ in range(cycles)]
    else:
        raise TypeError(workload.mode)

    def run_mutate() -> ta.Any:
        result = None
        for obj in objects:
            result = operation(context, obj)
        return result

    return Trial(run_mutate, operations)


##


def _one(size: int) -> int:
    return 1


def _size(size: int) -> int:
    return size


def _half(size: int) -> int:
    return max(1, size // 2)


def _tail(size: int) -> int:
    return size - size // 2


def _queries(size: int) -> int:
    return min(size, 64)


def _consume(values: ta.Iterable[ta.Any]) -> int:
    count = 0
    for _ in values:
        count += 1
    return count


##


def _collection_len(context: BenchmarkContext, obj: ta.Collection) -> int:
    return len(obj)


def _collection_contains_hit(context: BenchmarkContext, obj: ta.Collection) -> int:
    return sum(item in obj for item in context.query_collection_items)


def _collection_contains_miss(context: BenchmarkContext, obj: ta.Collection) -> int:
    return sum(item in obj for item in context.query_missing_collection_items)


def _collection_iter(context: BenchmarkContext, obj: ta.Collection) -> int:
    return _consume(obj)


##


def _sequence_getitem(context: BenchmarkContext, obj: ta.Sequence) -> int:
    total = 0
    for index in context.data.query_indices:
        total += obj[index]
    return total


def _sequence_slice(context: BenchmarkContext, obj: ta.Sequence) -> ta.Sequence:
    start = context.data.size // 4
    return obj[start:start + context.data.size // 2]


def _sequence_reversed(context: BenchmarkContext, obj: ta.Sequence) -> int:
    return _consume(reversed(obj))


def _sequence_index_hit(context: BenchmarkContext, obj: ta.Sequence) -> int:
    return obj.index(context.data.values[-1])


def _sequence_index_miss(context: BenchmarkContext, obj: ta.Sequence) -> int:
    try:
        return obj.index(-1)
    except ValueError:
        return -1


def _sequence_count_hit(context: BenchmarkContext, obj: ta.Sequence) -> int:
    return obj.count(context.data.values[-1])


def _sequence_count_miss(context: BenchmarkContext, obj: ta.Sequence) -> int:
    return obj.count(-1)


##


def _mapping_getitem_hit(context: BenchmarkContext, obj: ta.Mapping) -> int:
    total = 0
    for key in context.query_collection_items:
        total += obj[key]
    return total


def _mapping_getitem_miss(context: BenchmarkContext, obj: ta.Mapping) -> int:
    misses = 0
    for key in context.query_missing_collection_items:
        try:
            obj[key]
        except KeyError:
            misses += 1
    return misses


def _mapping_get_hit(context: BenchmarkContext, obj: ta.Mapping) -> int:
    total = 0
    for key in context.query_collection_items:
        total += obj.get(key, 0)
    return total


def _mapping_get_miss(context: BenchmarkContext, obj: ta.Mapping) -> int:
    total = 0
    for key in context.query_missing_collection_items:
        total += obj.get(key, -1)
    return total


def _mapping_keys_view(context: BenchmarkContext, obj: ta.Mapping) -> ta.KeysView:
    return obj.keys()


def _mapping_items_view(context: BenchmarkContext, obj: ta.Mapping) -> ta.ItemsView:
    return obj.items()


def _mapping_values_view(context: BenchmarkContext, obj: ta.Mapping) -> ta.ValuesView:
    return obj.values()


def _mapping_iter_items(context: BenchmarkContext, obj: ta.Mapping) -> int:
    return _consume(obj.items())


def _mapping_iter_values(context: BenchmarkContext, obj: ta.Mapping) -> int:
    return _consume(obj.values())


def _mapping_eq(context: BenchmarkContext, obj: ta.Mapping) -> bool:
    return obj == context.comparison()


##


def _set_eq(context: BenchmarkContext, obj: ta.AbstractSet) -> bool:
    return obj == context.comparison()


def _set_subset(context: BenchmarkContext, obj: ta.AbstractSet) -> bool:
    return context.subset <= obj


def _set_strict_subset(context: BenchmarkContext, obj: ta.AbstractSet) -> bool:
    return context.subset < obj


def _set_superset(context: BenchmarkContext, obj: ta.AbstractSet) -> bool:
    return context.superset >= obj


def _set_strict_superset(context: BenchmarkContext, obj: ta.AbstractSet) -> bool:
    return context.superset > obj


def _set_intersection(context: BenchmarkContext, obj: ta.AbstractSet) -> ta.AbstractSet:
    return obj & context.other_set


def _set_union(context: BenchmarkContext, obj: ta.AbstractSet) -> ta.AbstractSet:
    return obj | context.other_set


def _set_difference(context: BenchmarkContext, obj: ta.AbstractSet) -> ta.AbstractSet:
    return obj - context.other_set


def _set_symmetric_difference(context: BenchmarkContext, obj: ta.AbstractSet) -> ta.AbstractSet:
    return obj ^ context.other_set


def _set_isdisjoint(context: BenchmarkContext, obj: ta.AbstractSet) -> bool:
    return obj.isdisjoint(context.disjoint_set)


##


def _mutable_sequence_setitem(context: BenchmarkContext, obj: ta.MutableSequence) -> ta.MutableSequence:
    for index in range(context.data.size):
        obj[index] = -index - 1
    return obj


def _mutable_sequence_delitem(context: BenchmarkContext, obj: ta.MutableSequence) -> ta.MutableSequence:
    for _ in range(context.data.size):
        del obj[-1]
    return obj


def _mutable_sequence_insert(context: BenchmarkContext, obj: ta.MutableSequence) -> ta.MutableSequence:
    for value in context.data.values:
        obj.insert(0, value)
    return obj


def _mutable_sequence_append(context: BenchmarkContext, obj: ta.MutableSequence) -> ta.MutableSequence:
    for value in context.data.values:
        obj.append(value)
    return obj


def _mutable_sequence_clear(context: BenchmarkContext, obj: ta.MutableSequence) -> ta.MutableSequence:
    obj.clear()
    return obj


def _mutable_sequence_reverse(context: BenchmarkContext, obj: ta.MutableSequence) -> ta.MutableSequence:
    obj.reverse()
    return obj


def _mutable_sequence_extend(context: BenchmarkContext, obj: ta.MutableSequence) -> ta.MutableSequence:
    obj.extend(context.data.values)
    return obj


def _mutable_sequence_pop(context: BenchmarkContext, obj: ta.MutableSequence) -> ta.MutableSequence:
    for _ in range(context.data.size):
        obj.pop()
    return obj


def _mutable_sequence_remove(context: BenchmarkContext, obj: ta.MutableSequence) -> ta.MutableSequence:
    for value in reversed(context.data.values):
        obj.remove(value)
    return obj


def _mutable_sequence_iadd(context: BenchmarkContext, obj: ta.MutableSequence) -> ta.MutableSequence:
    obj += context.data.values
    return obj


##


def _mutable_mapping_setitem_new(context: BenchmarkContext, obj: ta.MutableMapping) -> ta.MutableMapping:
    for key, value in context.pairs:
        obj[key] = value
    return obj


def _mutable_mapping_setitem_replace(context: BenchmarkContext, obj: ta.MutableMapping) -> ta.MutableMapping:
    for key, value in context.replacement_pairs:
        obj[key] = value
    return obj


def _mutable_mapping_delitem(context: BenchmarkContext, obj: ta.MutableMapping) -> ta.MutableMapping:
    for key in context.keys:
        del obj[key]
    return obj


def _mutable_mapping_pop(context: BenchmarkContext, obj: ta.MutableMapping) -> ta.MutableMapping:
    for key in context.keys:
        obj.pop(key)
    return obj


def _mutable_mapping_popitem(context: BenchmarkContext, obj: ta.MutableMapping) -> ta.MutableMapping:
    for _ in range(context.data.size):
        obj.popitem()
    return obj


def _mutable_mapping_clear(context: BenchmarkContext, obj: ta.MutableMapping) -> ta.MutableMapping:
    obj.clear()
    return obj


def _mutable_mapping_update(context: BenchmarkContext, obj: ta.MutableMapping) -> ta.MutableMapping:
    obj.update(context.replacement_pairs)
    return obj


def _mutable_mapping_setdefault_hit(context: BenchmarkContext, obj: ta.MutableMapping) -> ta.MutableMapping:
    for key in context.query_collection_items:
        obj.setdefault(key, -1)
    return obj


def _mutable_mapping_setdefault_miss(context: BenchmarkContext, obj: ta.MutableMapping) -> ta.MutableMapping:
    for key in context.query_missing_collection_items:
        obj.setdefault(key, context.key_value(key))
    return obj


##


def _mutable_set_add(context: BenchmarkContext, obj: ta.MutableSet) -> ta.MutableSet:
    for value in context.keys:
        obj.add(value)
    return obj


def _mutable_set_discard(context: BenchmarkContext, obj: ta.MutableSet) -> ta.MutableSet:
    for value in context.keys:
        obj.discard(value)
    return obj


def _mutable_set_remove(context: BenchmarkContext, obj: ta.MutableSet) -> ta.MutableSet:
    for value in context.keys:
        obj.remove(value)
    return obj


def _mutable_set_pop(context: BenchmarkContext, obj: ta.MutableSet) -> ta.MutableSet:
    for _ in range(context.data.size):
        obj.pop()
    return obj


def _mutable_set_clear(context: BenchmarkContext, obj: ta.MutableSet) -> ta.MutableSet:
    obj.clear()
    return obj


def _mutable_set_ior(context: BenchmarkContext, obj: ta.MutableSet) -> ta.MutableSet:
    obj |= context.other_set
    return obj


def _mutable_set_iand(context: BenchmarkContext, obj: ta.MutableSet) -> ta.MutableSet:
    obj &= context.other_set
    return obj


def _mutable_set_ixor(context: BenchmarkContext, obj: ta.MutableSet) -> ta.MutableSet:
    obj ^= context.other_set
    return obj


def _mutable_set_isub(context: BenchmarkContext, obj: ta.MutableSet) -> ta.MutableSet:
    obj -= context.other_set
    return obj


##


def _sorted_collection_iter(context: BenchmarkContext, obj: ta.Any) -> int:
    return _consume(obj.iter())


def _sorted_collection_iter_desc(context: BenchmarkContext, obj: ta.Any) -> int:
    return _consume(obj.iter_desc())


def _sorted_collection_iter_from(context: BenchmarkContext, obj: ta.Any) -> int:
    return _consume(obj.iter_from(context.middle_key))


def _sorted_collection_iter_from_desc(context: BenchmarkContext, obj: ta.Any) -> int:
    return _consume(obj.iter_from_desc(context.middle_key))


def _sorted_collection_add(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    for value in context.keys:
        obj.add(value)
    return obj


def _sorted_collection_find_hit(context: BenchmarkContext, obj: ta.Any) -> int:
    return sum(obj.find(value) is not None for value in context.query_collection_items)


def _sorted_collection_find_miss(context: BenchmarkContext, obj: ta.Any) -> int:
    return sum(obj.find(value) is None for value in context.query_missing_collection_items)


def _sorted_collection_remove(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    for value in context.keys:
        obj.remove(value)
    return obj


##


def _sorted_mapping_iteritems(context: BenchmarkContext, obj: ta.Any) -> int:
    return _consume(obj.iteritems())


def _sorted_mapping_items_desc(context: BenchmarkContext, obj: ta.Any) -> int:
    return _consume(obj.items_desc())


def _sorted_mapping_items_from(context: BenchmarkContext, obj: ta.Any) -> int:
    return _consume(obj.items_from(context.middle_key))


def _sorted_mapping_items_from_desc(context: BenchmarkContext, obj: ta.Any) -> int:
    return _consume(obj.items_from_desc(context.middle_key))


##


def _persistent_sequence_iter_from(context: BenchmarkContext, obj: ta.Any) -> int:
    return _consume(obj.iter_from(context.data.size // 2))


def _persistent_sequence_splice_insert(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    middle = context.data.size // 2
    return obj.splice(middle, middle, context.data.values)


def _persistent_sequence_splice_delete(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    start = context.data.size // 4
    return obj.splice(start, start + context.data.size // 2, ())


def _persistent_sequence_with(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    result = obj
    for index in context.data.query_indices:
        result = result.with_(index, -index - 1)
    return result


def _persistent_sequence_without(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    result = obj
    for index in range(context.data.size - 1, -1, -1):
        result = result.without(index)
    return result


def _persistent_sequence_without_slice(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    start = context.data.size // 4
    return obj.without(slice(start, start + context.data.size // 2))


def _persistent_sequence_append(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    result = obj
    for value in context.data.values:
        result = result.append(value)
    return result


def _persistent_sequence_extend(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    return obj.extend(context.data.values)


##


def _persistent_mapping_iteritems(context: BenchmarkContext, obj: ta.Any) -> int:
    return _consume(obj.iteritems())


def _persistent_mapping_with(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    result = obj
    for key in context.query_collection_items:
        result = result.with_(key, context.key_value(key) + context.data.size)
    return result


def _persistent_mapping_with_new(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    result = obj
    for key in context.query_missing_collection_items:
        result = result.with_(key, context.key_value(key))
    return result


def _persistent_mapping_without(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    result = obj
    for key in context.keys:
        result = result.without(key)
    return result


def _persistent_mapping_default_hit(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    result = obj
    for key in context.query_collection_items:
        result = result.default(key, -1)
    return result


def _persistent_mapping_default_miss(context: BenchmarkContext, obj: ta.Any) -> ta.Any:
    result = obj
    for key in context.query_missing_collection_items:
        result = result.default(key, context.key_value(key))
    return result


##


WORKLOADS: tuple[Workload, ...] = (
    Workload('collection', 'construct', WorkloadMode.BUILD, None, _size),
    Workload('collection', 'len', WorkloadMode.READ, _collection_len, _one),
    Workload('collection', 'contains_hit', WorkloadMode.READ, _collection_contains_hit, _queries),
    Workload('collection', 'contains_miss', WorkloadMode.READ, _collection_contains_miss, _queries),
    Workload('collection', 'iter', WorkloadMode.READ, _collection_iter, _size),

    Workload('sequence', 'getitem', WorkloadMode.READ, _sequence_getitem, _queries),
    Workload('sequence', 'getitem_slice_middle', WorkloadMode.READ, _sequence_slice, _half),
    Workload('sequence', 'reversed', WorkloadMode.READ, _sequence_reversed, _size),
    Workload('sequence', 'index_hit_last', WorkloadMode.READ, _sequence_index_hit, _one),
    Workload('sequence', 'index_miss', WorkloadMode.READ, _sequence_index_miss, _one),
    Workload('sequence', 'count_hit', WorkloadMode.READ, _sequence_count_hit, _one),
    Workload('sequence', 'count_miss', WorkloadMode.READ, _sequence_count_miss, _one),

    Workload('mapping', 'getitem_hit', WorkloadMode.READ, _mapping_getitem_hit, _queries),
    Workload('mapping', 'getitem_miss', WorkloadMode.READ, _mapping_getitem_miss, _queries),
    Workload('mapping', 'get_hit', WorkloadMode.READ, _mapping_get_hit, _queries),
    Workload('mapping', 'get_miss', WorkloadMode.READ, _mapping_get_miss, _queries),
    Workload('mapping', 'keys_view', WorkloadMode.READ, _mapping_keys_view, _one),
    Workload('mapping', 'items_view', WorkloadMode.READ, _mapping_items_view, _one),
    Workload('mapping', 'values_view', WorkloadMode.READ, _mapping_values_view, _one),
    Workload('mapping', 'iter_items', WorkloadMode.READ, _mapping_iter_items, _size),
    Workload('mapping', 'iter_values', WorkloadMode.READ, _mapping_iter_values, _size),
    Workload('mapping', 'eq', WorkloadMode.READ, _mapping_eq, _size, comparison=True),

    Workload('abstract_set', 'eq', WorkloadMode.READ, _set_eq, _size, comparison=True),
    Workload('abstract_set', 'subset', WorkloadMode.READ, _set_subset, _half),
    Workload('abstract_set', 'strict_subset', WorkloadMode.READ, _set_strict_subset, _half),
    Workload('abstract_set', 'superset', WorkloadMode.READ, _set_superset, _size),
    Workload('abstract_set', 'strict_superset', WorkloadMode.READ, _set_strict_superset, _size),
    Workload('abstract_set', 'intersection', WorkloadMode.READ, _set_intersection, _size),
    Workload('abstract_set', 'union', WorkloadMode.READ, _set_union, _size),
    Workload('abstract_set', 'difference', WorkloadMode.READ, _set_difference, _size),
    Workload('abstract_set', 'symmetric_difference', WorkloadMode.READ, _set_symmetric_difference, _size),
    Workload('abstract_set', 'isdisjoint', WorkloadMode.READ, _set_isdisjoint, _size),

    Workload('mutable_sequence', 'setitem', WorkloadMode.MUTATE, _mutable_sequence_setitem, _size),
    Workload('mutable_sequence', 'delitem_tail', WorkloadMode.MUTATE, _mutable_sequence_delitem, _size),
    Workload('mutable_sequence', 'insert_front', WorkloadMode.MUTATE_EMPTY, _mutable_sequence_insert, _size),
    Workload('mutable_sequence', 'append', WorkloadMode.MUTATE_EMPTY, _mutable_sequence_append, _size),
    Workload('mutable_sequence', 'clear', WorkloadMode.MUTATE, _mutable_sequence_clear, _one),
    Workload('mutable_sequence', 'reverse', WorkloadMode.MUTATE, _mutable_sequence_reverse, _size),
    Workload('mutable_sequence', 'extend', WorkloadMode.MUTATE_EMPTY, _mutable_sequence_extend, _size),
    Workload('mutable_sequence', 'pop_tail', WorkloadMode.MUTATE, _mutable_sequence_pop, _size),
    Workload('mutable_sequence', 'remove', WorkloadMode.MUTATE, _mutable_sequence_remove, _size),
    Workload('mutable_sequence', 'iadd', WorkloadMode.MUTATE_EMPTY, _mutable_sequence_iadd, _size),

    Workload('mutable_mapping', 'setitem_new', WorkloadMode.MUTATE_EMPTY, _mutable_mapping_setitem_new, _size),
    Workload('mutable_mapping', 'setitem_replace', WorkloadMode.MUTATE, _mutable_mapping_setitem_replace, _size),
    Workload('mutable_mapping', 'delitem', WorkloadMode.MUTATE, _mutable_mapping_delitem, _size),
    Workload('mutable_mapping', 'pop', WorkloadMode.MUTATE, _mutable_mapping_pop, _size),
    Workload('mutable_mapping', 'popitem', WorkloadMode.MUTATE, _mutable_mapping_popitem, _size),
    Workload('mutable_mapping', 'clear', WorkloadMode.MUTATE, _mutable_mapping_clear, _one),
    Workload('mutable_mapping', 'update', WorkloadMode.MUTATE, _mutable_mapping_update, _size),
    Workload('mutable_mapping', 'setdefault_hit', WorkloadMode.MUTATE, _mutable_mapping_setdefault_hit, _queries),
    Workload('mutable_mapping', 'setdefault_miss', WorkloadMode.MUTATE, _mutable_mapping_setdefault_miss, _queries),

    Workload('set', 'add', WorkloadMode.MUTATE_EMPTY, _mutable_set_add, _size),
    Workload('set', 'discard', WorkloadMode.MUTATE, _mutable_set_discard, _size),
    Workload('set', 'remove', WorkloadMode.MUTATE, _mutable_set_remove, _size),
    Workload('set', 'pop', WorkloadMode.MUTATE, _mutable_set_pop, _size),
    Workload('set', 'clear', WorkloadMode.MUTATE, _mutable_set_clear, _one),
    Workload('set', 'ior', WorkloadMode.MUTATE, _mutable_set_ior, _size),
    Workload('set', 'iand', WorkloadMode.MUTATE, _mutable_set_iand, _size),
    Workload('set', 'ixor', WorkloadMode.MUTATE, _mutable_set_ixor, _size),
    Workload('set', 'isub', WorkloadMode.MUTATE, _mutable_set_isub, _size),

    Workload('sorted_collection', 'iter', WorkloadMode.READ, _sorted_collection_iter, _size),
    Workload('sorted_collection', 'iter_desc', WorkloadMode.READ, _sorted_collection_iter_desc, _size),
    Workload('sorted_collection', 'iter_from', WorkloadMode.READ, _sorted_collection_iter_from, _tail),
    Workload('sorted_collection', 'iter_from_desc', WorkloadMode.READ, _sorted_collection_iter_from_desc, _tail),
    Workload('sorted_collection', 'add', WorkloadMode.MUTATE_EMPTY, _sorted_collection_add, _size),
    Workload('sorted_collection', 'find_hit', WorkloadMode.READ, _sorted_collection_find_hit, _queries),
    Workload('sorted_collection', 'find_miss', WorkloadMode.READ, _sorted_collection_find_miss, _queries),
    Workload('sorted_collection', 'remove', WorkloadMode.MUTATE, _sorted_collection_remove, _size),

    Workload('sorted_mapping', 'iteritems', WorkloadMode.READ, _sorted_mapping_iteritems, _size),
    Workload('sorted_mapping', 'items_desc', WorkloadMode.READ, _sorted_mapping_items_desc, _size),
    Workload('sorted_mapping', 'items_from', WorkloadMode.READ, _sorted_mapping_items_from, _tail),
    Workload('sorted_mapping', 'items_from_desc', WorkloadMode.READ, _sorted_mapping_items_from_desc, _tail),

    Workload('persistent_sequence', 'iter_from', WorkloadMode.READ, _persistent_sequence_iter_from, _tail),
    Workload('persistent_sequence', 'splice_insert', WorkloadMode.READ, _persistent_sequence_splice_insert, _size),
    Workload('persistent_sequence', 'splice_delete', WorkloadMode.READ, _persistent_sequence_splice_delete, _half),
    Workload('persistent_sequence', 'with', WorkloadMode.READ, _persistent_sequence_with, _queries),
    Workload('persistent_sequence', 'without', WorkloadMode.READ, _persistent_sequence_without, _size),
    Workload('persistent_sequence', 'without_slice', WorkloadMode.READ, _persistent_sequence_without_slice, _half),
    Workload('persistent_sequence', 'append', WorkloadMode.MUTATE_EMPTY, _persistent_sequence_append, _size),
    Workload('persistent_sequence', 'extend', WorkloadMode.MUTATE_EMPTY, _persistent_sequence_extend, _size),

    Workload('persistent_mapping', 'iteritems', WorkloadMode.READ, _persistent_mapping_iteritems, _size),
    Workload('persistent_mapping', 'with', WorkloadMode.READ, _persistent_mapping_with, _queries),
    Workload('persistent_mapping', 'with_new', WorkloadMode.READ, _persistent_mapping_with_new, _queries),
    Workload('persistent_mapping', 'without', WorkloadMode.READ, _persistent_mapping_without, _size),
    Workload('persistent_mapping', 'default_hit', WorkloadMode.READ, _persistent_mapping_default_hit, _queries),
    Workload('persistent_mapping', 'default_miss', WorkloadMode.READ, _persistent_mapping_default_miss, _queries),
)
