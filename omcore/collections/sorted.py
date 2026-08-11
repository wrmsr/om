import abc
import bisect
import operator
import typing as ta

from .. import lang
from .mappings import IterItemsViewMapping
from .mappings import IterValuesViewMapping


T = ta.TypeVar('T')
U = ta.TypeVar('U')
K = ta.TypeVar('K')
V = ta.TypeVar('V')


##


class SortedIter(
    lang.Abstract,
    abc.ABC,
    ta.Generic[T],
):
    __slots__ = ()

    @abc.abstractmethod
    def iter(self) -> ta.Iterator[T]:
        raise NotImplementedError

    @abc.abstractmethod
    def iter_desc(self) -> ta.Iterator[T]:
        raise NotImplementedError

    @abc.abstractmethod
    def iter_from(self, base: T) -> ta.Iterator[T]:
        raise NotImplementedError

    @abc.abstractmethod
    def iter_from_desc(self, base: T) -> ta.Iterator[T]:
        raise NotImplementedError


class SortedCollection(
    SortedIter[T],
    ta.Collection[T],
    lang.Abstract,
    abc.ABC,
    ta.Generic[T],
):
    __slots__ = ()

    Comparator = ta.Callable[[U, U], int]

    @staticmethod
    def default_comparator(a: T, b: T) -> int:
        """https://docs.python.org/3.0/whatsnew/3.0.html#ordering-comparisons"""

        return (a > b) - (a < b)  # type: ignore

    @abc.abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def __iter__(self) -> ta.Iterator[T]:
        raise NotImplementedError

    @abc.abstractmethod
    def __contains__(self, value: T) -> bool:  # type: ignore
        raise NotImplementedError

    @abc.abstractmethod
    def add(self, value: T) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def find(self, value: T) -> T | None:
        raise NotImplementedError

    @abc.abstractmethod
    def remove(self, value: T) -> None:
        raise NotImplementedError


#


class SortedItems(
    lang.Abstract,
    abc.ABC,
    ta.Generic[K, V],
):
    __slots__ = ()

    @abc.abstractmethod
    def iteritems(self) -> ta.Iterator[tuple[K, V]]:
        raise NotImplementedError

    @abc.abstractmethod
    def items_desc(self) -> ta.Iterator[tuple[K, V]]:
        raise NotImplementedError

    @abc.abstractmethod
    def items_from(self, key: K) -> ta.Iterator[tuple[K, V]]:
        raise NotImplementedError

    @abc.abstractmethod
    def items_from_desc(self, key: K) -> ta.Iterator[tuple[K, V]]:
        raise NotImplementedError


class SortedMapping(
    SortedItems[K, V],
    ta.Mapping[K, V],
    lang.Abstract,
    abc.ABC,
    ta.Generic[K, V],
):
    __slots__ = ()


class SortedMutableMapping(
    ta.MutableMapping[K, V],
    SortedMapping[K, V],
    lang.Abstract,
    abc.ABC,
    ta.Generic[K, V],
):
    __slots__ = ()


##


@ta.final
class BisectSortedMapping(
    IterValuesViewMapping[K, V],
    IterItemsViewMapping[K, V],
    SortedMapping[K, V],
    lang.Final,
):
    __slots__ = ('_items',)

    def __init__(self, items: ta.Iterable[tuple[K, V]] = ()) -> None:
        super().__init__()

        sorted_items = sorted(items, key=operator.itemgetter(0))
        deduplicated: list[tuple[K, V]] = []
        for item in sorted_items:
            if deduplicated and item[0] == deduplicated[-1][0]:
                deduplicated[-1] = item
            else:
                deduplicated.append(item)

        self._items = tuple(deduplicated)

    @staticmethod
    def _item_key(item: tuple[K, V]) -> K:
        return item[0]

    def _bisect_left(self, key: K) -> int:
        return bisect.bisect_left(self._items, key, key=self._item_key)  # type: ignore[call-overload]

    def _bisect_right(self, key: K) -> int:
        return bisect.bisect_right(self._items, key, key=self._item_key)  # type: ignore[call-overload]

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> ta.Iterator[K]:
        for key, _ in self._items:
            yield key

    def __getitem__(self, key: K) -> V:
        pos = self._bisect_left(key)
        if pos >= len(self._items) or self._items[pos][0] != key:
            raise KeyError(key)
        return self._items[pos][1]

    def itervalues(self) -> ta.Iterator[V]:
        return map(operator.itemgetter(1), self._items)

    def iteritems(self) -> ta.Iterator[tuple[K, V]]:
        return iter(self._items)

    def items_desc(self) -> ta.Iterator[tuple[K, V]]:
        return reversed(self._items)

    def items_from(self, key: K) -> ta.Iterator[tuple[K, V]]:
        pos = self._bisect_left(key)
        while pos < len(self._items):
            yield self._items[pos]
            pos += 1

    def items_from_desc(self, key: K) -> ta.Iterator[tuple[K, V]]:
        pos = self._bisect_right(key)
        while pos:
            pos -= 1
            yield self._items[pos]


#


class SortedListDict(
    IterValuesViewMapping[K, V],
    IterItemsViewMapping[K, V],
    SortedMutableMapping[K, V],
):
    @staticmethod
    def _item_comparator(a: tuple[K, V], b: tuple[K, V]) -> int:
        return SortedCollection.default_comparator(a[0], b[0])

    def __init__(self, impl: SortedCollection, *args, **kwargs) -> None:
        super().__init__()

        self._impl = impl
        for k, v in lang.yield_dict_init(*args, **kwargs):
            self[k] = v

    @property
    def debug(self) -> ta.Mapping[K, V]:
        return dict(self)

    def __getitem__(self, key: K) -> V:
        item = self._impl.find((key, None))
        if item is None:
            raise KeyError(key)
        return item[1]

    def __setitem__(self, key: K, value: V) -> None:
        try:
            self._impl.remove((key, None))
        except KeyError:
            pass
        self._impl.add((key, value))

    def __delitem__(self, key: K) -> None:
        self._impl.remove((key, None))

    def __len__(self) -> int:
        return len(self._impl)

    def __iter__(self) -> ta.Iterator[K]:
        for k, _ in self._impl:
            yield k

    def itervalues(self) -> ta.Iterator[V]:
        return map(operator.itemgetter(1), self.iteritems())

    def iteritems(self) -> ta.Iterator[tuple[K, V]]:
        yield from self._impl.iter()

    def items_desc(self) -> ta.Iterator[tuple[K, V]]:
        yield from self._impl.iter_desc()

    def items_from(self, key: K) -> ta.Iterator[tuple[K, V]]:
        yield from self._impl.iter_from((key, None))

    def items_from_desc(self, key: K) -> ta.Iterator[tuple[K, V]]:
        yield from self._impl.iter_from_desc((key, None))
