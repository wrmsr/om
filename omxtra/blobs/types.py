# ruff: noqa: UP006 UP007 UP045
# @om-lite
import dataclasses as dc
import datetime
import typing as ta

from omcore.lite.abstract import Abstract
from omcore.lite.check import check


##


@dc.dataclass(frozen=True)
class BlobVersion:
    """Opaque - compare for equality and hand back in preconditions, never parse."""

    etag: str


@dc.dataclass(frozen=True)
class BlobInfo:
    key: str
    size: int  # of the whole object, even when returned alongside a ranged read
    version: BlobVersion
    last_modified: datetime.datetime


@dc.dataclass(frozen=True)
class BlobPrefix:
    prefix: str


@dc.dataclass(frozen=True)
class Blob:
    info: BlobInfo
    data: bytes


##


class BlobRange(Abstract):
    """Python slice semantics on every backend: out-of-bounds ranges clamp rather than raise."""


@dc.dataclass(frozen=True)
class OffsetBlobRange(BlobRange):
    start: int
    stop: ta.Optional[int] = None

    def __post_init__(self) -> None:
        check.arg(self.start >= 0)
        check.arg(self.stop is None or self.stop > self.start)


@dc.dataclass(frozen=True)
class SuffixBlobRange(BlobRange):
    length: int

    def __post_init__(self) -> None:
        check.arg(self.length > 0)


##


class BlobPrecondition(Abstract):
    pass


class BlobWritePrecondition(BlobPrecondition, Abstract):
    pass


class BlobReadPrecondition(BlobPrecondition, Abstract):
    pass


@dc.dataclass(frozen=True)
class BlobIfAbsent(BlobWritePrecondition):
    pass


@dc.dataclass(frozen=True)
class BlobIfMatch(BlobWritePrecondition, BlobReadPrecondition):
    version: BlobVersion


@dc.dataclass(frozen=True)
class BlobIfNoneMatch(BlobReadPrecondition):
    version: BlobVersion
