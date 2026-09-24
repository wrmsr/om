import datetime

from omcore import check
from omcore import dataclasses as dc
from omcore import lang


##


@dc.dataclass(frozen=True)
class BlobVersion(lang.Final):
    """Opaque - compare for equality and hand back in preconditions, never parse."""

    etag: str


@dc.dataclass(frozen=True, kw_only=True)
class BlobInfo(lang.Final):
    key: str
    size: int  # of the whole object, even when returned alongside a ranged read
    version: BlobVersion
    last_modified: datetime.datetime


@dc.dataclass(frozen=True)
class BlobPrefix(lang.Final):
    prefix: str


@dc.dataclass(frozen=True, kw_only=True)
class Blob(lang.Final):
    info: BlobInfo
    data: bytes


##


class BlobRange(lang.Abstract, lang.Sealed):
    """Python slice semantics on every backend: out-of-bounds ranges clamp rather than raise."""


@dc.dataclass(frozen=True)
class OffsetBlobRange(BlobRange, lang.Final):
    start: int
    stop: int | None = None

    def __post_init__(self) -> None:
        check.arg(self.start >= 0)
        check.arg(self.stop is None or self.stop > self.start)


@dc.dataclass(frozen=True)
class SuffixBlobRange(BlobRange, lang.Final):
    length: int

    def __post_init__(self) -> None:
        check.arg(self.length > 0)


##


class BlobPrecondition(lang.Abstract, lang.Sealed):
    pass


class BlobWritePrecondition(BlobPrecondition, lang.Abstract):
    pass


class BlobReadPrecondition(BlobPrecondition, lang.Abstract):
    pass


@dc.dataclass(frozen=True)
class IfAbsent(BlobWritePrecondition, lang.Final):
    pass


@dc.dataclass(frozen=True)
class IfMatch(BlobWritePrecondition, BlobReadPrecondition, lang.Final):
    version: BlobVersion


@dc.dataclass(frozen=True)
class IfNoneMatch(BlobReadPrecondition, lang.Final):
    version: BlobVersion
