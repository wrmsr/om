# ruff: noqa: UP006 UP007 UP045
# @om-lite
import enum
import typing as ta

from .errors import UnsupportedBlobOperationError
from .types import BlobIfAbsent
from .types import BlobIfMatch
from .types import BlobWritePrecondition


##


class BlobCapability(enum.Flag):
    """
    Optional features only. Everything else - head, ranged and conditional get, put, delete, list, copy, open_writer -
    is mandatory for every backend.
    """

    PUT_IF_ABSENT = enum.auto()
    PUT_IF_MATCH = enum.auto()
    DELETE_IF_MATCH = enum.auto()
    COPY_IF_ABSENT = enum.auto()
    COPY_IF_MATCH = enum.auto()


ALL_BLOB_CAPABILITIES = ~BlobCapability(0)


def check_blob_capabilities(have: BlobCapability, need: BlobCapability) -> None:
    if missing := need & ~have:
        raise UnsupportedBlobOperationError(missing)


##


def blob_put_capability(cond: ta.Optional[BlobWritePrecondition]) -> BlobCapability:
    if cond is None:
        return BlobCapability(0)
    elif isinstance(cond, BlobIfAbsent):
        return BlobCapability.PUT_IF_ABSENT
    elif isinstance(cond, BlobIfMatch):
        return BlobCapability.PUT_IF_MATCH
    raise TypeError(cond)


def blob_copy_capability(cond: ta.Optional[BlobWritePrecondition]) -> BlobCapability:
    if cond is None:
        return BlobCapability(0)
    elif isinstance(cond, BlobIfAbsent):
        return BlobCapability.COPY_IF_ABSENT
    elif isinstance(cond, BlobIfMatch):
        return BlobCapability.COPY_IF_MATCH
    raise TypeError(cond)


def blob_delete_capability(cond: ta.Optional[BlobIfMatch]) -> BlobCapability:
    return BlobCapability(0) if cond is None else BlobCapability.DELETE_IF_MATCH
