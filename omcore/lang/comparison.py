import typing as ta


_comparison: ta.Any
try:
    from . import _comparison  # type: ignore
except ImportError:
    _comparison = None


K = ta.TypeVar('K')
V = ta.TypeVar('V')


##


def cmp(l: ta.Any, r: ta.Any) -> int:
    return (l > r) - (l < r)


def hash_eq_id_cmp(l: ta.Any, r: ta.Any) -> int:
    if l is r or l == r:
        return 0

    hl = hash(l)
    hr = hash(r)
    if hl < hr:
        return -1
    elif hl > hr:
        return 1

    il = id(l)
    ir = id(r)

    return (il > ir) - (il < ir)


class _KeyCmp:
    pass


@ta.final
class _DefaultKeyCmp(_KeyCmp):
    def __reduce__(self) -> tuple[ta.Callable[..., ta.Any], tuple[ta.Any, ...]]:
        return (_unpickle_key_cmp, ())

    def __call__(self, t0: tuple[ta.Any, ta.Any], t1: tuple[ta.Any, ta.Any]) -> int:
        return cmp(t0[0], t1[0])


@ta.final
class _HashEqIdKeyCmp(_KeyCmp):
    def __reduce__(self) -> tuple[ta.Callable[..., ta.Any], tuple[ta.Any, ...]]:
        return (_unpickle_key_cmp, ('hash_eq_id',))

    def __call__(self, t0: tuple[ta.Any, ta.Any], t1: tuple[ta.Any, ta.Any]) -> int:
        return hash_eq_id_cmp(t0[0], t1[0])


@ta.final
class _CustomKeyCmp(_KeyCmp):
    def __init__(self, fn: ta.Callable[[ta.Any, ta.Any], int]) -> None:
        self._fn = fn

    def __reduce__(self) -> tuple[ta.Callable[..., ta.Any], tuple[ta.Any, ...]]:
        return (_unpickle_key_cmp, (self._fn,))

    def __call__(self, t0: tuple[ta.Any, ta.Any], t1: tuple[ta.Any, ta.Any]) -> int:
        return self._fn(t0[0], t1[0])


def key_cmp(
        fn: ta.Callable[[K, K], int] | ta.Literal['hash_eq_id'] | None = None,
) -> ta.Callable[[tuple[K, V], tuple[K, V]], int]:
    if fn is None or fn is cmp:
        return _DefaultKeyCmp()
    elif fn == 'hash_eq_id' or fn is hash_eq_id_cmp:
        return _HashEqIdKeyCmp()
    else:
        return _CustomKeyCmp(fn)


def _unpickle_key_cmp(
        fn: ta.Callable[[ta.Any, ta.Any], int] | None = None,
) -> ta.Callable[[tuple[ta.Any, ta.Any], tuple[ta.Any, ta.Any]], int]:
    return key_cmp(fn)


if _comparison is not None:
    globals().update({a: getattr(_comparison, a) for a in [
        'cmp',
        'hash_eq_id_cmp',
        'key_cmp',
    ]})


##


class InfinityType:
    def __repr__(self) -> str:
        return 'Infinity'

    def __hash__(self) -> int:
        return hash(repr(self))

    def __lt__(self, other: ta.Any) -> bool:
        return False

    def __le__(self, other: ta.Any) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__)

    def __gt__(self, other: ta.Any) -> bool:
        return True

    def __ge__(self, other: ta.Any) -> bool:
        return True

    def __neg__(self: ta.Any) -> NegativeInfinityType:
        return NegativeInfinity


Infinity = InfinityType()


class NegativeInfinityType:
    def __repr__(self) -> str:
        return '-Infinity'

    def __hash__(self) -> int:
        return hash(repr(self))

    def __lt__(self, other: ta.Any) -> bool:
        return True

    def __le__(self, other: ta.Any) -> bool:
        return True

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__)

    def __gt__(self, other: ta.Any) -> bool:
        return False

    def __ge__(self, other: ta.Any) -> bool:
        return False

    def __neg__(self: ta.Any) -> InfinityType:
        return Infinity


NegativeInfinity = NegativeInfinityType()
