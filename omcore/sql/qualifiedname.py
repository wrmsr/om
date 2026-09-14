import typing as ta

from .. import dataclasses as dc
from .. import lang


type CanStrictQualifiedName = QualifiedName | lang.SequenceNotStr[str]

type CanQualifiedName = CanStrictQualifiedName | str


##


def coerce_parts(parts: ta.Sequence[str]) -> tuple[str, ...]:
    if isinstance(parts, str):
        raise TypeError(parts)
    if not isinstance(parts, tuple):
        parts = tuple(parts)
    if not parts:
        raise ValueError(parts)
    if not all(isinstance(p, str) and p for p in parts):
        raise ValueError(parts)
    return parts


#


@dc.dataclass(frozen=True)
class QualifiedName(ta.Sequence[str], lang.Final):
    parts: ta.Sequence[str] = dc.field() | dc.with_extra_field_params(coerce=coerce_parts)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}([{", ".join(map(repr, self.parts))}])'

    @property
    def dotted(self) -> str:
        return '.'.join(self.parts)

    def prefixed(self, sz: int) -> tuple[str | None, ...]:
        if len(self) > sz:
            raise ValueError(self)
        return ((None,) * (sz - len(self))) + tuple(self.parts)

    @property
    def pair(self) -> tuple[str | None, str]:
        return self.prefixed(2)  # type: ignore

    @property
    def triple(self) -> tuple[str | None, str | None, str]:
        return self.prefixed(3)  # type: ignore

    @property
    def quad(self) -> tuple[str | None, str | None, str | None, str]:
        return self.prefixed(4)  # type: ignore

    def __iter__(self) -> ta.Iterator[str]:
        return iter(self.parts)

    def __len__(self) -> int:
        return len(self.parts)

    def __getitem__(self, idx: int) -> str:  # type: ignore
        return self.parts[idx]

    @property
    def last(self) -> str:
        return self.parts[-1]

    def sibling(self, last: str) -> QualifiedName:
        """The name of an object living alongside this one, under the same qualification (schema, database, ...)."""

        return QualifiedName((*self.parts[:-1], last))

    #

    @classmethod
    def of_strict(cls, obj: CanStrictQualifiedName) -> QualifiedName:
        if isinstance(obj, QualifiedName):
            return obj
        elif isinstance(obj, str):  # type: ignore[unreachable]
            raise TypeError(obj)
        elif isinstance(obj, ta.Sequence):
            return cls(tuple(obj))
        else:
            raise TypeError(obj)

    @classmethod
    def of_optional_strict(cls, obj: CanStrictQualifiedName | None) -> QualifiedName | None:
        if obj is None:
            return None
        else:
            return cls.of_strict(obj)

    @classmethod
    def of(cls, obj: CanQualifiedName) -> QualifiedName:
        if isinstance(obj, str):
            return QualifiedName((obj,))
        else:
            return cls.of_strict(obj)

    @classmethod
    def of_optional(cls, obj: CanQualifiedName | None) -> QualifiedName | None:
        if obj is None:
            return None
        else:
            return cls.of(obj)

    @classmethod
    def of_dotted(cls, dotted: str) -> QualifiedName:
        return cls(dotted.split('.'))


def qn(*args: str) -> QualifiedName:
    return QualifiedName(args)
