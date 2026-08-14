import enum
import random
import typing as ta

from .... import dataclasses as dc


##


@dc.dataclass(frozen=True)
class Suite:
    name: str
    parents: tuple[str, ...] = ()


def _build_suites() -> dict[str, Suite]:
    suites = (
        Suite('collection'),
        Suite('sequence', ('collection',)),
        Suite('mapping', ('collection',)),
        Suite('abstract_set', ('collection',)),
        Suite('mutable_sequence', ('sequence',)),
        Suite('mutable_mapping', ('mapping',)),
        Suite('set', ('abstract_set',)),
        Suite('sorted_collection', ('collection',)),
        Suite('sorted_mapping', ('mapping',)),
        Suite('sorted_mutable_mapping', ('sorted_mapping', 'mutable_mapping')),
        Suite('persistent_sequence', ('sequence',)),
        Suite('persistent_mapping', ('mapping',)),
    )
    return {suite.name: suite for suite in suites}


SUITES: ta.Mapping[str, Suite] = _build_suites()


def resolve_suites(names: ta.Iterable[str]) -> tuple[str, ...]:
    resolved: list[str] = []
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen:
            return
        try:
            suite = SUITES[name]
        except KeyError:
            raise ValueError(f'unknown suite: {name!r}') from None
        for parent in suite.parents:
            visit(parent)
        seen.add(name)
        resolved.append(name)

    for name in names:
        visit(name)
    return tuple(resolved)


##


class ContainerKind(enum.Enum):
    SEQUENCE = 'sequence'
    MAPPING = 'mapping'
    SET = 'set'


# The kind of data an implementation is exercised with, applied separately to keys (set elements / mapping keys) and
# mapping values so dtype-specializing implementations can cover their combinations. Non-specializing implementations
# should just use a single configuration - int, unless the implementation itself demands objects.
class DataKind(enum.Enum):
    INT = 'int'
    OBJECT = 'object'


@dc.dataclass(frozen=True, order=True, slots=True, weakref_slot=True)
class BenchmarkKey:
    value: int


def _sample[T](values: ta.Sequence[T], limit: int = 64) -> tuple[T, ...]:
    if len(values) <= limit:
        return tuple(values)
    return tuple(values[i * len(values) // limit] for i in range(limit))


@dc.dataclass(frozen=True)
class BenchmarkData:
    size: int
    values: tuple[int, ...]
    int_keys: tuple[int, ...]
    object_keys: tuple[BenchmarkKey, ...]
    missing_int_keys: tuple[int, ...]
    missing_object_keys: tuple[BenchmarkKey, ...]
    query_indices: tuple[int, ...]

    @classmethod
    def make(cls, size: int) -> ta.Self:
        if size <= 0:
            raise ValueError(size)

        indices = list(range(size))
        random.Random(size).shuffle(indices)
        int_keys = tuple(indices)

        return cls(
            size=size,
            values=tuple(range(size)),
            int_keys=int_keys,
            object_keys=tuple(BenchmarkKey(value) for value in int_keys),
            missing_int_keys=tuple(-value - 1 for value in range(size)),
            missing_object_keys=tuple(BenchmarkKey(-value - 1) for value in range(size)),
            query_indices=_sample(tuple(range(size))),
        )


type Factory = ta.Callable[[ta.Iterable[ta.Any]], ta.Any]


@dc.dataclass(frozen=True)
class Implementation:
    name: str
    suites: tuple[str, ...]
    container_kind: ContainerKind
    factory: Factory
    key_kind: DataKind = DataKind.INT
    value_kind: DataKind = DataKind.INT
    available: bool = True
    unavailable_reason: str | None = None

    @property
    def resolved_suites(self) -> tuple[str, ...]:
        return resolve_suites(self.suites)


class BenchmarkContext:
    def __init__(self, implementation: Implementation, data: BenchmarkData) -> None:
        super().__init__()

        self.implementation = implementation
        self.data = data

        if implementation.key_kind is DataKind.OBJECT:
            keys: tuple[ta.Any, ...] = data.object_keys
            missing_keys: tuple[ta.Any, ...] = data.missing_object_keys
        else:
            keys = data.int_keys
            missing_keys = data.missing_int_keys

        self._keys = keys
        self._missing_keys = missing_keys
        pairs: tuple[tuple[ta.Any, ta.Any], ...]
        replacement_pairs: tuple[tuple[ta.Any, ta.Any], ...]
        if implementation.value_kind is DataKind.OBJECT:
            pairs = tuple((key, BenchmarkKey(self.key_value(key))) for key in keys)
            replacement_pairs = tuple((key, BenchmarkKey(self.key_value(key) + data.size)) for key in keys)
        else:
            pairs = tuple((key, self.key_value(key)) for key in keys)
            replacement_pairs = tuple((key, value + data.size) for key, value in pairs)
        self._pairs = pairs
        self._replacement_pairs = replacement_pairs

        if implementation.container_kind is ContainerKind.SEQUENCE:
            collection_items: tuple[ta.Any, ...] = data.values
            missing_collection_items: tuple[ta.Any, ...] = data.missing_int_keys
            self._elements: ta.Iterable[ta.Any] = data.values
        elif implementation.container_kind is ContainerKind.MAPPING:
            collection_items = keys
            missing_collection_items = missing_keys
            self._elements = self._pairs
        elif implementation.container_kind is ContainerKind.SET:
            collection_items = keys
            missing_collection_items = missing_keys
            self._elements = keys
        else:
            raise TypeError(implementation.container_kind)

        self._collection_items = collection_items
        self._missing_collection_items = missing_collection_items
        self._query_collection_items = tuple(collection_items[index] for index in data.query_indices)
        self._query_missing_collection_items = tuple(missing_collection_items[index] for index in data.query_indices)

        self._sorted_keys = tuple(sorted(keys))
        self._middle_key = self._sorted_keys[data.size // 2]

        half = data.size // 2
        self._subset = frozenset(keys[:half])
        self._superset = frozenset(keys) | frozenset(missing_keys[:half])
        self._other_set = frozenset(keys[half:]) | frozenset(missing_keys[:half])
        self._disjoint_set = frozenset(missing_keys)

        self._base: ta.Any = None
        self._has_base = False
        self._comparison: ta.Any = None
        self._has_comparison = False

    @property
    def keys(self) -> tuple[ta.Any, ...]:
        return self._keys

    @property
    def missing_keys(self) -> tuple[ta.Any, ...]:
        return self._missing_keys

    @property
    def pairs(self) -> tuple[tuple[ta.Any, ta.Any], ...]:
        return self._pairs

    @property
    def replacement_pairs(self) -> tuple[tuple[ta.Any, ta.Any], ...]:
        return self._replacement_pairs

    @property
    def elements(self) -> ta.Iterable[ta.Any]:
        return self._elements

    @property
    def collection_items(self) -> tuple[ta.Any, ...]:
        return self._collection_items

    @property
    def missing_collection_items(self) -> tuple[ta.Any, ...]:
        return self._missing_collection_items

    @property
    def query_collection_items(self) -> tuple[ta.Any, ...]:
        return self._query_collection_items

    @property
    def query_missing_collection_items(self) -> tuple[ta.Any, ...]:
        return self._query_missing_collection_items

    @property
    def sorted_keys(self) -> tuple[ta.Any, ...]:
        return self._sorted_keys

    @property
    def middle_key(self) -> ta.Any:
        return self._middle_key

    @property
    def subset(self) -> ta.AbstractSet[ta.Any]:
        return self._subset

    @property
    def superset(self) -> ta.AbstractSet[ta.Any]:
        return self._superset

    @property
    def other_set(self) -> ta.AbstractSet[ta.Any]:
        return self._other_set

    @property
    def disjoint_set(self) -> ta.AbstractSet[ta.Any]:
        return self._disjoint_set

    @staticmethod
    def key_value(key: ta.Any) -> int:
        if isinstance(key, BenchmarkKey):
            return key.value
        return key

    def new(self) -> ta.Any:
        return self.implementation.factory(iter(self.elements))

    def empty(self) -> ta.Any:
        return self.implementation.factory(())

    def base(self) -> ta.Any:
        if not self._has_base:
            self._base = self.new()
            self._has_base = True
        return self._base

    def comparison(self) -> ta.Any:
        if not self._has_comparison:
            self._comparison = self.new()
            self._has_comparison = True
        return self._comparison
