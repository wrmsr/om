"""
Backend-neutral column types. Each is a frozen dataclass carrying only the sql-level details meaningful across backends
(an integer's width, a string's bounded length). A detail left unspecified means 'the backend's default', and the ddl
differ treats it as matching anything, so an in-code default never churns against a reflected concrete type. The
module-level defaults (INTEGER, STRING, ...) serve the common case where no detail is needed.
"""
import typing as ta

from ... import check
from ... import dataclasses as dc
from ... import lang


##


@dc.dataclass(frozen=True)
class Dtype(lang.Abstract, lang.Sealed):
    pass


##


INTEGER_BITS: ta.Final[tuple[int, ...]] = (16, 32, 64)


@dc.dataclass(frozen=True, kw_only=True)
class Integer(Dtype, lang.Final):
    bits: int | None = None

    def __post_init__(self) -> None:
        if self.bits is not None:
            check.in_(self.bits, INTEGER_BITS)


@dc.dataclass(frozen=True, kw_only=True)
class String(Dtype, lang.Final):
    length: int | None = None

    def __post_init__(self) -> None:
        if self.length is not None:
            check.arg(self.length > 0)


@dc.dataclass(frozen=True)
class Datetime(Dtype, lang.Final):
    pass


@dc.dataclass(frozen=True)
class Uuid(Dtype, lang.Final):
    pass


@dc.dataclass(frozen=True)
class Boolean(Dtype, lang.Final):
    pass


@dc.dataclass(frozen=True)
class Float(Dtype, lang.Final):
    pass


@dc.dataclass(frozen=True)
class Bytes(Dtype, lang.Final):
    pass


@dc.dataclass(frozen=True)
class Json(Dtype, lang.Final):
    """
    A json document, held as one by a backend which has a type for them - to be looked into, and indexed - and as its
    text by one which does not. A value is whatever json can say, but for a null of its own at the top: that is no value
    at all, the column's null, as it is for every other dtype.
    """


##


INTEGER = Integer()
STRING = String()
DATETIME = Datetime()
UUID = Uuid()
BOOLEAN = Boolean()
FLOAT = Float()
BYTES = Bytes()
JSON = Json()
