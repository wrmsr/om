import abc
import operator
import typing as ta

from .. import lang
from .mappings import IterItemsViewMapping
from .mappings import IterValuesViewMapping


T = ta.TypeVar('T')
K = ta.TypeVar('K')
V = ta.TypeVar('V')


##


class PersistentSequence(ta.Sequence[T], lang.Abstract, ta.Generic[T]):
    __slots__ = ()

    @abc.abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def __iter__(self) -> ta.Iterator[T]:
        raise NotImplementedError

    @abc.abstractmethod
    def iter_from(self, idx: int) -> ta.Iterator[T]:
        raise NotImplementedError

    @ta.overload
    @abc.abstractmethod
    def __getitem__(self, item: int) -> T:
        raise NotImplementedError

    @ta.overload
    @abc.abstractmethod
    def __getitem__(self, item: slice) -> ta.Self:
        raise NotImplementedError

    @abc.abstractmethod
    def __getitem__(self, item):
        raise NotImplementedError

    @abc.abstractmethod
    def splice(
            self,
            start: int | None,
            stop: int | None,
            items: ta.Iterable[T],
    ) -> ta.Self:
        raise NotImplementedError

    @abc.abstractmethod
    def with_(self, idx: int, item: T) -> ta.Self:
        raise NotImplementedError

    @abc.abstractmethod
    def without(self, item: int | slice) -> ta.Self:
        raise NotImplementedError

    @abc.abstractmethod
    def append(self, item: T) -> ta.Self:
        raise NotImplementedError

    @abc.abstractmethod
    def extend(self, items: ta.Iterable[T]) -> ta.Self:
        raise NotImplementedError


##


class PersistentMap(lang.Abstract, ta.Generic[K, V]):
    __slots__ = ()

    @abc.abstractmethod
    def __len__(self) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def __contains__(self, item: K) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def __getitem__(self, item: K) -> V:
        raise NotImplementedError

    @abc.abstractmethod
    def __iter__(self) -> ta.Iterator[K]:
        raise NotImplementedError

    @abc.abstractmethod
    def iteritems(self) -> ta.Iterator[tuple[K, V]]:
        raise NotImplementedError

    @abc.abstractmethod
    def with_(self, k: K, v: V) -> ta.Self:
        raise NotImplementedError

    @abc.abstractmethod
    def without(self, k: K) -> ta.Self:
        raise NotImplementedError

    @abc.abstractmethod
    def default(self, k: K, v: V) -> ta.Self:
        raise NotImplementedError


class PersistentMapping(
    PersistentMap[K, V],
    ta.Mapping[K, V],
    lang.Abstract,
    ta.Generic[K, V],
):
    __slots__ = ()

    @abc.abstractmethod
    def __contains__(self, item: K) -> bool:  # type: ignore[override]
        raise NotImplementedError


##


@ta.final
class TuplePersistentSequence(PersistentSequence[T]):
    """Naive PersistentSequence backed by a tuple, fully copied on every update."""

    __slots__ = ('_t',)

    def __init__(self, items: ta.Iterable[T] = ()) -> None:
        self._t = tuple(items)

    @property
    def debug(self) -> tuple[T, ...]:
        return self._t

    def __len__(self) -> int:
        return len(self._t)

    def __contains__(self, value: ta.Any) -> bool:
        return value in self._t

    @ta.overload
    def __getitem__(self, item: int) -> T:
        ...

    @ta.overload
    def __getitem__(self, item: slice) -> ta.Self:
        ...

    def __getitem__(self, item):
        if isinstance(item, slice):
            start, stop = self._normalize_slice(item)

            if stop - start == len(self._t):
                return self

            return TuplePersistentSequence(self._t[start:stop])

        return self._t[item]

    def __iter__(self) -> ta.Iterator[T]:
        return iter(self._t)

    def __reversed__(self) -> ta.Iterator[T]:
        return reversed(self._t)

    def iter_from(self, idx: int) -> ta.Iterator[T]:
        start, _ = self._normalize_bounds(idx, None)
        return iter(self._t[start:])

    def index(self, value: ta.Any, start: int = 0, stop: int | None = None) -> int:
        if stop is None:
            return self._t.index(value, start)
        return self._t.index(value, start, stop)

    def count(self, value: ta.Any) -> int:
        return self._t.count(value)

    def splice(
            self,
            start: int | None,
            stop: int | None,
            items: ta.Iterable[T],
    ) -> ta.Self:
        start, stop = self._normalize_bounds(start, stop)

        items_t = tuple(items)
        if start == stop and not items_t:
            return self

        return TuplePersistentSequence(self._t[:start] + items_t + self._t[stop:])

    def with_(self, idx: int, item: T) -> ta.Self:
        idx = self._normalize_index(idx)

        if self._t[idx] is item:
            return self

        return TuplePersistentSequence((*self._t[:idx], item, *self._t[idx + 1:]))

    def without(self, item: int | slice) -> ta.Self:
        if isinstance(item, slice):
            start, stop = self._normalize_slice(item)

            if start == stop:
                return self

            return TuplePersistentSequence(self._t[:start] + self._t[stop:])

        idx = self._normalize_index(item)
        return TuplePersistentSequence(self._t[:idx] + self._t[idx + 1:])

    def append(self, item: T) -> ta.Self:
        return TuplePersistentSequence((*self._t, item))

    def extend(self, items: ta.Iterable[T]) -> ta.Self:
        if not (items_t := tuple(items)):
            return self

        return TuplePersistentSequence(self._t + items_t)

    def _normalize_index(self, idx: int) -> int:
        idx = operator.index(idx)

        ln = len(self._t)

        if idx < 0:
            idx += ln

        if idx < 0 or idx >= ln:
            raise IndexError(idx)

        return idx

    def _normalize_slice(self, slc: slice) -> tuple[int, int]:
        if slc.step not in (None, 1):
            raise ValueError('slice steps other than 1 are not supported')

        start, stop, _ = slc.indices(len(self._t))

        if stop < start:
            stop = start

        return start, stop

    def _normalize_bounds(
            self,
            start: int | None,
            stop: int | None,
    ) -> tuple[int, int]:
        start, stop, _ = slice(start, stop).indices(len(self._t))

        if stop < start:
            stop = start

        return start, stop


##


@ta.final
class DictPersistentMapping(
    IterValuesViewMapping[K, V],
    IterItemsViewMapping[K, V],
    PersistentMapping[K, V],
):
    """Naive PersistentMapping backed by a dict, fully copied on every update."""

    __slots__ = ('_d',)

    def __init__(
            self,
            items: ta.Iterable[tuple[K, V]] | None = None,
            *,
            _d: dict[K, V] | None = None,
    ) -> None:
        if _d is None:
            _d = dict(items) if items is not None else {}
        elif items is not None:
            raise TypeError('may not pass both items and _d')

        self._d = _d

    @property
    def debug(self) -> ta.Mapping[K, V]:
        return dict(self._d)

    def __len__(self) -> int:
        return len(self._d)

    def __contains__(self, item: K) -> bool:  # type: ignore[override]
        return item in self._d

    def __getitem__(self, item: K) -> V:
        return self._d[item]

    def __iter__(self) -> ta.Iterator[K]:
        return iter(self._d)

    def iteritems(self) -> ta.Iterator[tuple[K, V]]:
        return iter(self._d.items())

    def itervalues(self) -> ta.Iterator[V]:
        return iter(self._d.values())

    def with_(self, k: K, v: V) -> ta.Self:
        d = dict(self._d)
        d[k] = v
        return DictPersistentMapping(_d=d)

    def without(self, k: K) -> ta.Self:
        if k not in self._d:
            return self

        d = dict(self._d)
        del d[k]
        return DictPersistentMapping(_d=d)

    def default(self, k: K, v: V) -> ta.Self:
        if k in self._d:
            return self

        return self.with_(k, v)
