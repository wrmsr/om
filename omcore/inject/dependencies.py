import typing as ta

from .. import cached
from .. import check
from .. import dataclasses as dc
from .. import lang
from .keys import Key


##


def _set_repr(s: frozenset) -> str | None:
    return f'{{{", ".join(map(repr, s))}}}' if s else None


@ta.final
@dc.dataclass(frozen=True)
@dc.extra_class_params(terse_repr=True)
class Dependencies(ta.Collection[Key]):
    keys: frozenset[Key] = dc.xfield(repr_fn=_set_repr)

    _: dc.KW_ONLY

    optional: frozenset[Key] = dc.xfield(frozenset(), repr_fn=_set_repr)

    def __post_init__(self) -> None:
        check.isinstance(self.keys, frozenset)
        check.isinstance(self.optional, frozenset)
        if self.optional and (missing := (self.optional - self.keys)):
            raise ValueError(missing)

    #

    def __bool__(self) -> bool:
        return bool(self.keys)

    def __len__(self) -> int:
        return len(self.keys)

    def __contains__(self, key: Key) -> bool:  # type: ignore[override]
        return key in self.keys

    def __iter__(self) -> ta.Iterator[Key]:
        return iter(self.keys)

    #

    @cached.property
    def required(self) -> frozenset[Key]:
        return self.keys - self.optional

    #

    _EMPTY: ta.ClassVar[Dependencies]

    @classmethod
    def empty(cls) -> Dependencies:
        return cls._EMPTY

    #

    @lang.opt_self
    def merge(self: Dependencies | None, *others: Dependencies | None) -> Dependencies:
        keys: set[Key] = set()
        required: set[Key] = set()

        def do(cur: Dependencies | None) -> None:
            if cur:
                keys.update(cur.keys)
                required.update(cur.required)

        do(self)
        for other in others:
            do(other)

        if not keys:
            return Dependencies._EMPTY

        return Dependencies(
            frozenset(keys),
            optional=frozenset(keys - required),
        )

    def __or__(self, other: Dependencies) -> Dependencies:
        return self.merge(other)


Dependencies._EMPTY = Dependencies(frozenset())  # noqa
