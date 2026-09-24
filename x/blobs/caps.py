import enum

from .errors import UnsupportedBlobOperationError
from .types import BlobWritePrecondition
from .types import IfAbsent
from .types import IfMatch


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


def put_capability(cond: BlobWritePrecondition | None) -> BlobCapability:
    match cond:
        case None:
            return BlobCapability(0)
        case IfAbsent():
            return BlobCapability.PUT_IF_ABSENT
        case IfMatch():
            return BlobCapability.PUT_IF_MATCH
    raise TypeError(cond)


def copy_capability(cond: BlobWritePrecondition | None) -> BlobCapability:
    match cond:
        case None:
            return BlobCapability(0)
        case IfAbsent():
            return BlobCapability.COPY_IF_ABSENT
        case IfMatch():
            return BlobCapability.COPY_IF_MATCH
    raise TypeError(cond)


def delete_capability(cond: IfMatch | None) -> BlobCapability:
    return BlobCapability(0) if cond is None else BlobCapability.DELETE_IF_MATCH
