# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
The wire of a remote blob store: the calls a host's `RemoteBlobStore` makes of a target's `RemoteBlobStoreService`, and
their shapes. Lite: shared with the target's amalgam, so Python 3.8 compatible and marshaled with the lite marshaler.
The blobs types travel as themselves - the marshaler handles the precondition and range hierarchies polymorphically.

Content crosses in bounded chunks, so an object's size is bounded by the store rather than by the rpc's frame limit:

- **Reads** are stateless. `blobs.get` answers with the requested range's absolute bounds and up to `max_bytes` of it,
  along with the object's info; the client fetches the rest with further gets of the remaining range pinned by
  `BlobIfMatch` to the version the first saw, and starts over should the object be replaced midway.
- **Writes** which fit one chunk are a single `blobs.put`. Larger ones open a server-side writer with
  `blobs.write_begin`, feed it with `blobs.write_chunk`, and publish it with `blobs.write_commit` - or drop it with
  `blobs.write_abort` - with exactly the semantics of the store's own `open_writer`. Writers a connection leaves open
  are discarded when it closes.
- **Listings** are paged by `start_after`, `limit` entries at a time. They are not snapshots, as they are not locally
  either.

Store errors cross as rpc errors whose type is `blobs.<ErrorClassName>`, and are raised
again as that class on the host: `remote_blob_error_type` and `remote_blob_error_of` are the two directions.
"""
import dataclasses as dc
import typing as ta

from ..errors import BlobAlreadyExistsError
from ..errors import BlobConflictError
from ..errors import BlobIndeterminateError
from ..errors import BlobNotFoundError
from ..errors import BlobNotModifiedError
from ..errors import BlobPreconditionFailedError
from ..errors import BlobStoreError
from ..errors import BlobStreamLengthError
from ..errors import BlobThrottledError
from ..errors import BlobTransportError
from ..errors import InvalidBlobKeyError
from ..errors import UnsupportedBlobOperationError
from ..types import BlobIfMatch
from ..types import BlobInfo
from ..types import BlobRange
from ..types import BlobReadPrecondition
from ..types import BlobWritePrecondition


##


REMOTE_BLOBS_CAPABILITIES_METHOD = 'blobs.capabilities'
REMOTE_BLOBS_HEAD_METHOD = 'blobs.head'
REMOTE_BLOBS_GET_METHOD = 'blobs.get'
REMOTE_BLOBS_LIST_METHOD = 'blobs.list'
REMOTE_BLOBS_LIST_SHALLOW_METHOD = 'blobs.list_shallow'
REMOTE_BLOBS_PUT_METHOD = 'blobs.put'
REMOTE_BLOBS_WRITE_BEGIN_METHOD = 'blobs.write_begin'
REMOTE_BLOBS_WRITE_CHUNK_METHOD = 'blobs.write_chunk'
REMOTE_BLOBS_WRITE_COMMIT_METHOD = 'blobs.write_commit'
REMOTE_BLOBS_WRITE_ABORT_METHOD = 'blobs.write_abort'
REMOTE_BLOBS_COPY_METHOD = 'blobs.copy'
REMOTE_BLOBS_DELETE_METHOD = 'blobs.delete'
REMOTE_BLOBS_DELETE_MANY_METHOD = 'blobs.delete_many'

# No piece of content on the wire exceeds this, so no frame approaches the rpc's default limit once base64 encoded. The
# service refuses larger pieces, and caps the reads it is asked for to it.
REMOTE_BLOBS_MAX_CHUNK_BYTES = 4 * 1024 * 1024

# Nor does a page of a listing, or a batch of a delete_many, exceed this many entries.
REMOTE_BLOBS_MAX_PAGE_SIZE = 1_000


##
# Errors


REMOTE_BLOBS_ERROR_TYPE_PREFIX = 'blobs.'

REMOTE_BLOBS_ERROR_TYPES: ta.Mapping[str, ta.Type[BlobStoreError]] = {
    t.__name__: t
    for t in [
        BlobStoreError,
        InvalidBlobKeyError,
        BlobStreamLengthError,
        UnsupportedBlobOperationError,
        BlobNotFoundError,
        BlobPreconditionFailedError,
        BlobAlreadyExistsError,
        BlobNotModifiedError,
        BlobConflictError,
        BlobTransportError,
        BlobIndeterminateError,
        BlobThrottledError,
    ]
}


def remote_blob_error_type(e: BlobStoreError) -> str:
    """The wire type of a store error: that of its nearest class the wire knows."""

    for t in type(e).__mro__:
        if t.__name__ in REMOTE_BLOBS_ERROR_TYPES and REMOTE_BLOBS_ERROR_TYPES[t.__name__] is t:
            return REMOTE_BLOBS_ERROR_TYPE_PREFIX + t.__name__
    return REMOTE_BLOBS_ERROR_TYPE_PREFIX + BlobStoreError.__name__


def remote_blob_error_of(remote_type: str, message: str) -> ta.Optional[BlobStoreError]:
    """The store error a wire type names, or None if it names none."""

    if not remote_type.startswith(REMOTE_BLOBS_ERROR_TYPE_PREFIX):
        return None
    t = REMOTE_BLOBS_ERROR_TYPES.get(remote_type[len(REMOTE_BLOBS_ERROR_TYPE_PREFIX):], BlobStoreError)
    return t(message)


##
# Shapes


@dc.dataclass(frozen=True)
class RemoteBlobsCapabilitiesResult:
    flags: int


@dc.dataclass(frozen=True)
class RemoteBlobsHeadParams:
    key: str
    cond: ta.Optional[BlobReadPrecondition] = None


@dc.dataclass(frozen=True)
class RemoteBlobsGetParams:
    key: str
    max_bytes: int
    byte_range: ta.Optional[BlobRange] = None
    cond: ta.Optional[BlobReadPrecondition] = None


@dc.dataclass(frozen=True)
class RemoteBlobsGetResult:
    info: BlobInfo

    # The absolute bounds of the whole range asked for, clamped to the object.
    start: int
    stop: int

    # The range's content from its start: all of it, or the first max_bytes.
    data: bytes


@dc.dataclass(frozen=True)
class RemoteBlobsListParams:
    limit: int
    prefix: str = ''
    start_after: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class RemoteBlobsListResult:
    infos: ta.List[BlobInfo]
    truncated: bool


@dc.dataclass(frozen=True)
class RemoteBlobsListShallowParams:
    limit: int
    prefix: str = ''
    delimiter: str = '/'
    start_after: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class RemoteBlobsListShallowEntry:
    """Exactly one of the two."""

    info: ta.Optional[BlobInfo] = None
    prefix: ta.Optional[str] = None


@dc.dataclass(frozen=True)
class RemoteBlobsListShallowResult:
    entries: ta.List[RemoteBlobsListShallowEntry]
    truncated: bool


@dc.dataclass(frozen=True)
class RemoteBlobsPutParams:
    key: str
    data: bytes
    cond: ta.Optional[BlobWritePrecondition] = None


@dc.dataclass(frozen=True)
class RemoteBlobsWriteBeginParams:
    key: str
    cond: ta.Optional[BlobWritePrecondition] = None


@dc.dataclass(frozen=True)
class RemoteBlobsHandle:
    handle: str


@dc.dataclass(frozen=True)
class RemoteBlobsWriteChunkParams:
    handle: str
    data: bytes


@dc.dataclass(frozen=True)
class RemoteBlobsCopyParams:
    src: str
    dst: str
    cond: ta.Optional[BlobWritePrecondition] = None


@dc.dataclass(frozen=True)
class RemoteBlobsDeleteParams:
    key: str
    cond: ta.Optional[BlobIfMatch] = None


@dc.dataclass(frozen=True)
class RemoteBlobsDeleteManyParams:
    keys: ta.List[str]


@dc.dataclass(frozen=True)
class RemoteBlobsKeyError:
    key: str
    type: str
    message: str


@dc.dataclass(frozen=True)
class RemoteBlobsDeleteManyResult:
    errors: ta.List[RemoteBlobsKeyError]
