import typing as ta


T = ta.TypeVar('T')

Comparer: ta.TypeAlias = ta.Callable[[T, T], int]


##


class TreapNode(ta.Protocol[T]):
    @property
    def value(self) -> T: ...

    @property
    def priority(self) -> int: ...

    @property
    def left(self) -> TreapNode[T] | None: ...

    @property
    def right(self) -> TreapNode[T] | None: ...

    @property
    def count(self) -> int: ...

    def __iter__(self) -> ta.Iterator[T]: ...


##


class _TreapBackend(ta.Protocol):  # noqa
    def new(
        self,
        value: T,
        *,
        priority: int | None = None,
    ) -> TreapNode[T]: ...

    def find(
        self,
        n: TreapNode[T] | None,
        v: T,
        c: Comparer[T] | None,
    ) -> TreapNode[T] | None: ...

    def place(
        self,
        n: TreapNode[T] | None,
        v: T,
        c: Comparer[T] | None,
        desc: bool,
    ) -> list[TreapNode[T]]: ...

    def union(
        self,
        n: TreapNode[T] | None,
        other: TreapNode[T] | None,
        c: Comparer[T] | None,
        overwrite: bool,
    ) -> TreapNode[T] | None: ...

    def split(
        self,
        n: TreapNode[T] | None,
        v: T,
        c: Comparer[T] | None,
    ) -> tuple[
        TreapNode[T] | None,
        TreapNode[T] | None,
        TreapNode[T] | None,
    ]: ...

    def intersect(
        self,
        n: TreapNode[T] | None,
        other: TreapNode[T] | None,
        c: Comparer[T] | None,
    ) -> TreapNode[T] | None: ...

    def delete(
        self,
        n: TreapNode[T] | None,
        v: T,
        c: Comparer[T] | None,
    ) -> TreapNode[T] | None: ...

    def _join(
        self,
        n: TreapNode[T] | None,
        other: TreapNode[T] | None,
    ) -> TreapNode[T] | None: ...


##


from ._treap_py import (  # noqa
    new,
    find,
    place,
    union,
    split,
    intersect,
    delete,
    diff,
)


try:
    from . import _treap  # type: ignore
except ImportError:
    pass
else:
    globals().update({a: getattr(_treap, a) for a in [
        'new',
        'find',
        'place',
        'union',
        'split',
        'intersect',
        'delete',
        'diff',
    ]})
