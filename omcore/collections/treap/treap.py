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


class TreapBackend(ta.Protocol):  # noqa
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


TREAP_BACKEND: TreapBackend


##


from . import _treap_py  # noqa

try:
    from . import _treap  # type: ignore  # noqa
except ImportError:
    TREAP_BACKEND = ta.cast(ta.Any, _treap_py)
else:
    TREAP_BACKEND = _treap
