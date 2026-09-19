import typing as ta

from ... import dataclasses as dc


##


@dc.dataclass(frozen=True)
class BeginArray:
    pass


@dc.dataclass(frozen=True)
class EndArray:
    pass


@dc.dataclass(frozen=True)
class BeginObject:
    pass


@dc.dataclass(frozen=True)
class ObjectKey:
    key: str


@dc.dataclass(frozen=True)
class EndObject:
    pass


@dc.dataclass(frozen=True)
class Scalar:
    value: ta.Any


StructuralEvent: ta.TypeAlias = ta.Union[  # noqa
    BeginArray,
    EndArray,
    BeginObject,
    ObjectKey,
    EndObject,
    Scalar,
]
