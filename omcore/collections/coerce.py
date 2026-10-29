import typing as ta

from .. import check
from .frozen import FrozenDict
from .frozen import FrozenList


K = ta.TypeVar('K')
FK = ta.TypeVar('FK')
TK = ta.TypeVar('TK')

V = ta.TypeVar('V')
FV = ta.TypeVar('FV')
TV = ta.TypeVar('TV')

FE0 = ta.TypeVar('FE0')
TE0 = ta.TypeVar('TE0')

FE1 = ta.TypeVar('FE1')
TE1 = ta.TypeVar('TE1')

FE2 = ta.TypeVar('FE2')
TE2 = ta.TypeVar('TE2')


##


def _unpack_fn(fn):
    if isinstance(fn, tuple):
        return check.of_isinstance(fn)
    elif isinstance(fn, type) or callable(fn):
        return fn
    else:
        raise TypeError(fn)


# region seq


def seq(
        it: ta.Iterable[V],
) -> ta.Sequence[V]:
    if isinstance(it, str):
        raise TypeError(it)
    elif type(it) is FrozenList:
        return it
    else:
        return FrozenList(it)


def opt_seq(
        it: ta.Iterable[V] | None,
) -> ta.Sequence[V] | None:
    if it is None:
        return None
    else:
        return seq(it)


def seq_or_none(
        it: ta.Iterable[V] | None,
) -> ta.Sequence[V] | None:
    ret = opt_seq(it)
    if ret:
        return ret
    else:
        return None


def seq_of(
        fn: ta.Callable[[FV], TV] | tuple,
) -> ta.Callable[[ta.Iterable[FV]], ta.Sequence[TV]]:
    def inner(it):
        return seq(fn(e) for e in it)  # type: ignore

    fn = _unpack_fn(fn)
    return inner


def opt_seq_of(
        fn: ta.Callable[[FV], TV] | tuple,
) -> ta.Callable[[ta.Iterable[FV] | None], ta.Sequence[TV] | None]:
    def inner(it):
        if it is None:
            return None
        else:
            return seq(fn(e) for e in it)  # type: ignore

    fn = _unpack_fn(fn)
    return inner


def seq_of_or_none(
        fn: ta.Callable[[FV], TV] | tuple,
) -> ta.Callable[[ta.Iterable[FV] | None], ta.Sequence[TV] | None]:
    def inner(it):
        if it is None:
            return None
        else:
            ret = seq(fn(e) for e in it)  # type: ignore
            if ret:
                return ret
            else:
                return None

    fn = _unpack_fn(fn)
    return inner


# endregion


# region tuple


@ta.overload
def tuple_of(
        fn0: ta.Callable[[FE0], TE0],
        /,
) -> ta.Callable[
    [tuple[FE0]],
    tuple[TE0],
]:
    ...


@ta.overload
def tuple_of(
        fn0: ta.Callable[[FE0], TE0],
        fn1: ta.Callable[[FE1], TE1],
        /,
) -> ta.Callable[
    [tuple[FE0, FE1]],
    tuple[TE0, TE1],
]:
    ...


@ta.overload
def tuple_of(
        fn0: ta.Callable[[FE0], TE0],
        fn1: ta.Callable[[FE1], TE1],
        fn2: ta.Callable[[FE2], TE2],
        /,
) -> ta.Callable[
    [tuple[FE0, FE1, FE2]],
    tuple[TE0, TE1, TE2],
]:
    ...


@ta.overload
def tuple_of(
        *fns: ta.Callable[[ta.Any], ta.Any],
) -> ta.Callable[
    [tuple],
    tuple,
]:
    ...


def tuple_of(*fns):
    def inner(tup):
        return tuple(fn(e) for fn, e in zip(fns, check.isinstance(tup, tuple), strict=True))

    fns = [check.callable(fn) for fn in fns]  # type: ignore[assignment]
    return inner


@ta.overload
def opt_tuple_of(
        fn0: ta.Callable[[FE0], TE0],
        /,
) -> ta.Callable[
    [tuple[FE0] | None],
    tuple[TE0] | None,
]:
    ...


@ta.overload
def opt_tuple_of(
        fn0: ta.Callable[[FE0], TE0],
        fn1: ta.Callable[[FE1], TE1],
        /,
) -> ta.Callable[
    [tuple[FE0, FE1] | None],
    tuple[TE0, TE1] | None,
]:
    ...


@ta.overload
def opt_tuple_of(
        fn0: ta.Callable[[FE0], TE0],
        fn1: ta.Callable[[FE1], TE1],
        fn2: ta.Callable[[FE2], TE2],
        /,
) -> ta.Callable[
    [tuple[FE0, FE1, FE2] | None],
    tuple[TE0, TE1, TE2] | None,
]:
    ...


@ta.overload
def opt_tuple_of(
        *fns: ta.Callable[[ta.Any], ta.Any],
) -> ta.Callable[
    [tuple | None],
    tuple | None,
]:
    ...


def opt_tuple_of(*fns):
    def inner(tup):
        if tup is None:
            return None
        else:
            return tuple(fn(e) for fn, e in zip(fns, check.isinstance(tup, tuple), strict=True))

    fns = [check.callable(fn) for fn in fns]  # type: ignore[assignment]
    return inner


# endregion


# region abs_set


def abs_set(
        it: ta.Iterable[V],
) -> ta.AbstractSet[V]:
    if isinstance(it, str):
        raise TypeError(it)
    elif isinstance(it, frozenset):
        return it
    else:
        return frozenset(it)


def opt_abs_set(
        it: ta.Iterable[V] | None,
) -> ta.AbstractSet[V] | None:
    if it is None:
        return None
    else:
        return abs_set(it)


def abs_set_or_none(
        it: ta.Iterable[V] | None,
) -> ta.AbstractSet[V] | None:
    ret = opt_abs_set(it)
    if ret:
        return ret
    else:
        return None


def abs_set_of(
        fn: ta.Callable[[FV], TV] | tuple,
) -> ta.Callable[[ta.Iterable[FV]], ta.AbstractSet[TV]]:
    def inner(it):
        return abs_set(fn(e) for e in it)  # type: ignore

    fn = _unpack_fn(fn)
    return inner


def opt_abs_set_of(
        fn: ta.Callable[[FV], TV] | tuple,
) -> ta.Callable[[ta.Iterable[FV] | None], ta.AbstractSet[TV] | None]:
    def inner(it):
        if it is None:
            return None
        else:
            return abs_set(fn(e) for e in it)  # type: ignore

    fn = _unpack_fn(fn)
    return inner


def abs_set_of_or_none(
        fn: ta.Callable[[FV], TV] | tuple,
) -> ta.Callable[[ta.Iterable[FV] | None], ta.AbstractSet[TV] | None]:
    def inner(it):
        if it is None:
            return None
        else:
            ret = abs_set(fn(e) for e in it)  # type: ignore
            if ret:
                return ret
            else:
                return None

    fn = _unpack_fn(fn)
    return inner


# endregion


# region frozenset


def frozenset_(
        it: ta.Iterable[V],
) -> frozenset[V]:
    if isinstance(it, str):
        raise TypeError(it)
    elif isinstance(it, frozenset):
        return it
    else:
        return frozenset(it)


def opt_frozenset(
        it: ta.Iterable[V] | None,
) -> frozenset[V] | None:
    if it is None:
        return None
    else:
        return frozenset_(it)


def frozenset_or_none(
        it: ta.Iterable[V] | None,
) -> frozenset[V] | None:
    ret = opt_frozenset(it)
    if ret:
        return ret
    else:
        return None


def frozenset_of(
        fn: ta.Callable[[FV], TV] | tuple,
) -> ta.Callable[[ta.Iterable[FV]], frozenset[TV]]:
    def inner(it):
        return frozenset_(fn(e) for e in it)  # type: ignore

    fn = _unpack_fn(fn)
    return inner


def opt_frozenset_of(
        fn: ta.Callable[[FV], TV] | tuple,
) -> ta.Callable[[ta.Iterable[FV] | None], frozenset[TV] | None]:
    def inner(it):
        if it is None:
            return None
        else:
            return frozenset_(fn(e) for e in it)  # type: ignore

    fn = _unpack_fn(fn)
    return inner


def frozenset_of_or_none(
        fn: ta.Callable[[FV], TV] | tuple,
) -> ta.Callable[[ta.Iterable[FV] | None], frozenset[TV] | None]:
    def inner(it):
        if it is None:
            return None
        else:
            ret = frozenset_(fn(e) for e in it)  # type: ignore
            if ret:
                return ret
            else:
                return None

    fn = _unpack_fn(fn)
    return inner


# endregion


# region map


def map(  # noqa
        src: ta.Mapping[K, V] | ta.Iterable[tuple[K, V]],
) -> ta.Mapping[K, V]:
    return FrozenDict(src)


def opt_map(
        src: ta.Mapping[K, V] | ta.Iterable[tuple[K, V]] | None,
) -> ta.Mapping[K, V] | None:
    if src is None:
        return None
    else:
        return map(src)


def map_or_none(
        src: ta.Mapping[K, V] | ta.Iterable[tuple[K, V]] | None,
) -> ta.Mapping[K, V] | None:
    ret = opt_map(src)
    if ret:
        return ret
    else:
        return None


def map_of(
        key_fn: ta.Callable[[FK], TK] | tuple,
        value_fn: ta.Callable[[FV], TV] | tuple,
) -> ta.Callable[
    [ta.Mapping[FK, FV] | ta.Iterable[tuple[FK, FV]]],
    ta.Mapping[TK, TV],
]:
    def inner(src):
        return map((key_fn(k), value_fn(v)) for k, v in dict(src).items())  # type: ignore

    key_fn = _unpack_fn(key_fn)
    value_fn = _unpack_fn(value_fn)
    return inner


def opt_map_of(
        key_fn: ta.Callable[[FK], TK] | tuple,
        value_fn: ta.Callable[[FV], TV] | tuple,
) -> ta.Callable[
    [ta.Mapping[FK, FV] | ta.Iterable[tuple[FK, FV]] | None],
    ta.Mapping[TK, TV] | None,
]:
    def inner(src):
        if src is None:
            return None
        else:
            return map((key_fn(k), value_fn(v)) for k, v in dict(src).items())  # type: ignore

    key_fn = _unpack_fn(key_fn)
    value_fn = _unpack_fn(value_fn)
    return inner


def map_of_or_none(
        key_fn: ta.Callable[[FK], TK] | tuple,
        value_fn: ta.Callable[[FV], TV] | tuple,
) -> ta.Callable[
    [ta.Mapping[FK, FV] | ta.Iterable[tuple[FK, FV]] | None],
    ta.Mapping[TK, TV] | None,
]:
    def inner(src):
        if src is None:
            return None
        else:
            ret = map((key_fn(k), value_fn(v)) for k, v in dict(src).items())  # type: ignore
            if ret:
                return ret
            else:
                return None

    key_fn = _unpack_fn(key_fn)
    value_fn = _unpack_fn(value_fn)
    return inner


# endregion
