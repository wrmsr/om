import inspect
import itertools
import typing as ta

from .. import dataclasses as dc
from .. import lang
from .. import reflect as rfl
from .types import Tag


T = ta.TypeVar('T')


##


class TAG_NOT_SET(lang.Marker):  # noqa
    pass


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class Key(lang.Final, ta.Generic[T]):
    rty: rfl.Type = dc.xfield(validate=lambda o: isinstance(o, rfl.Type))

    _: dc.KW_ONLY

    tag: ta.Any = dc.xfield(
        default=None,
        validate=lambda o: not isinstance(o, Tag) and o is not TAG_NOT_SET,
        repr_fn=lang.opt_repr,
    )

    #

    # _rtk: rfl.TypeKey
    # _hash: int

    @property
    def rtk(self) -> rfl.TypeKey:
        return getattr(self, '_rtk')

    def __post_init__(self) -> None:
        object.__setattr__(self, '_rtk', self.rty.type_key())

    __hash__ = lang.cached_hash(lambda self: hash((
        self._rtk,
        self.tag,
    )))

    def __eq__(self, o: object) -> bool:
        if self is o:
            return True
        if self.__class__ is not o.__class__:
            return NotImplemented

        return (
            self._rtk == o._rtk and  # type: ignore[attr-defined]
            self.tag == o.tag  # noqa
        )


##


@ta.overload
def as_key(o: Key[T], *, tag: type[TAG_NOT_SET] = TAG_NOT_SET) -> Key[T]:
    ...


@ta.overload
def as_key(o: type[T], *, tag: ta.Any | type[TAG_NOT_SET] = TAG_NOT_SET) -> Key[T]:
    ...


@ta.overload
def as_key(o: ta.Any, *, tag: ta.Any | type[TAG_NOT_SET] = TAG_NOT_SET) -> Key:
    ...


def as_key(o, *, tag=TAG_NOT_SET):
    if isinstance(o, Key):
        if tag is not TAG_NOT_SET:
            raise TypeError(f'Cannot specify tag {tag!r} for existing Key instance {o!r}')
        return o

    if o is None or o is inspect.Parameter.empty:
        raise TypeError(o)

    return Key(rfl.reflect_type(o), tag=tag if tag is not TAG_NOT_SET else None)


##


@ta.final
class KeyList(ta.Sequence[Key]):
    def __init__(self, key: Key | ta.Sequence[Key], tail: KeyList | None = None) -> None:
        super().__init__()

        self._key = key
        self._tail = tail
        self._len: int = (len(tail) if tail is not None else 0) + (1 if isinstance(key, Key) else len(key))

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}([{", ".join(map(repr, self))}])'

    def __len__(self) -> int:
        return self._len

    def __iter__(self) -> ta.Iterator[Key]:
        cur: KeyList | None = self
        while cur is not None:
            if isinstance(key := cur._key, Key):  # noqa
                yield key
            else:
                yield from key
            cur = cur._tail  # noqa

    @ta.overload
    def __getitem__(self, index: int, /) -> Key: ...

    @ta.overload
    def __getitem__(self, index: slice[int | None], /) -> ta.Sequence[Key]: ...  # noqa

    def __getitem__(self, index):
        if isinstance(index, int):
            idx = index + self._len if index < 0 else index
            if not 0 <= idx < self._len:
                raise IndexError(f'index {index} out of range for sequence of length {self._len}')
            return next(itertools.islice(self, idx, None))

        elif isinstance(index, slice):
            return tuple(itertools.islice(self, *index.indices(self._len)))

        else:
            raise TypeError(index)
