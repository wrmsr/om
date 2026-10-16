import enum
import typing as ta

from ... import check
from .specs import DbSpec


T = ta.TypeVar('T')


##


class DbSlot(enum.StrEnum):
    WRITER = 'writer'
    READER = 'reader'
    ANALYTICS = 'analytics'


DbSetKey: ta.TypeAlias = DbSlot | str
DbSetValue: ta.TypeAlias = DbSpec | DbSetKey


##


def _resolve_aliases(items: ta.Iterable[tuple[str | ta.Any, str | T]]) -> dict[str, T]:
    dct: dict[str, DbSpec | str] = {}

    for ek, ev in items:
        if type(ek) is not str:
            ek = str(ek)

        check.not_in(ek, dct)
        dct[ek] = ev

    # Not a set for stability
    todo = list(reversed(dct))

    while todo:
        k = todo.pop()

        if not isinstance(dct[k], str):
            continue

        path: list[str] = []
        path_set: set[str] = set()

        while True:
            check.isinstance(k, str)

            if not isinstance(v := dct[k], str):
                break

            if k in path_set:
                raise ValueError(f'Circular aliases: {" -> ".join([*path, k])}')
            path.append(k)
            path_set.add(k)

            k = v

        for k in path:
            dct[k] = v

    return {check.isinstance(k, str): check.isinstance(v, DbSpec) for k, v in dct.items()}


##


class DbSet(ta.Mapping[DbSetKey, DbSpec]):
    def __init__(
            self,
            entries: ta.Mapping[DbSetKey, DbSetValue] | None = None,
            *,
            writer: DbSetValue | None = None,
            reader: DbSetValue | None = None,
            analytics: DbSetValue | None = None,
    ) -> None:
        super().__init__()

        resolved = _resolve_aliases([
            *(entries.items() if entries else []),
            *([
                (k, v)
                for k, v in [
                    ('writer', writer),
                    ('reader', reader),
                    ('analytics', analytics),
                ]
                if v is not None
            ])
        ])

        self._specs = {
            check.isinstance(k, str): check.isinstance(v, DbSpec)
            for k, v in resolved.items()
        }

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}<{", ".join(map(repr, self._specs))}>'

    #

    #

    @property
    def writer(self) -> DbSpec:
        return self['writer']

    @property
    def reader(self) -> DbSpec:
        return self['reader']

    @property
    def analytics(self) -> DbSpec:
        return self['analytics']

    #

    def __len__(self) -> int:
        return len(self._specs)

    def __iter__(self) -> ta.Iterator[DbSetKey]:
        return iter(self._specs)

    def __getitem__(self, key: DbSetKey) -> DbSpec:
        return self._specs[key]


##


class DbSets(ta.Mapping[str, DbSet]):
    def __init__(self, sets: ta.Mapping[str, DbSet]) -> None:
        super().__init__()

        resolved = _resolve_aliases(sets.items())

        self._sets = {
            check.isinstance(k, str): check.isinstance(v, DbSet)
            for k, v in resolved.items()
        }

    #

    def __len__(self) -> int:
        return len(self._sets)

    def __iter__(self) -> ta.Iterator[DbSetKey]:
        return iter(self._sets)

    def __getitem__(self, name: str) -> DbSet:
        return self._sets[name]
