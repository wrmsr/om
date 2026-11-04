# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
The target side of a remote blob store: `RemoteBlobStoreService` serves any sync `BlobStore` - typically a
`LocalBlobStore` - on behalf of a host's `RemoteBlobStore`, as a method table for a connection's handler (see
`protocol.py` for the wire). Its handlers never suspend, so it runs under any runtime; a store which blocks, as the
local one does, belongs under the sync runtime, where handlers run inline and one at a time.

Writers are server-side state: register `close` as the connection's close callback, so a host which goes away midway
leaves nothing open behind it. Lite: this runs inside the target's amalgam under Python 3.8+.
"""
import itertools
import typing as ta

from omcore.lite.check import check
from omcore.lite.marshal import ObjMarshalerManager
from omcore.rpc.dispatch import RpcMethodFn
from omcore.rpc.errors import RpcErrorCodes
from omcore.rpc.errors import RpcHandlerError
from omcore.rpc.errors import RpcRemoteErrorData
from omcore.rpc.serde import LiteMarshalRpcSerde
from omcore.rpc.serde import rpc_typed_method

from ..errors import BlobConflictError
from ..errors import BlobDeleteManyError
from ..errors import BlobPreconditionFailedError
from ..errors import BlobStoreError
from ..stores import BlobStore
from ..stores import BlobWriter
from ..types import BlobIfMatch
from ..types import BlobInfo
from ..types import BlobPrefix
from ..types import BlobRange
from ..types import BlobVersion
from ..types import OffsetBlobRange
from ..types import SuffixBlobRange
from .protocol import REMOTE_BLOBS_CAPABILITIES_METHOD
from .protocol import REMOTE_BLOBS_COPY_METHOD
from .protocol import REMOTE_BLOBS_DELETE_MANY_METHOD
from .protocol import REMOTE_BLOBS_DELETE_METHOD
from .protocol import REMOTE_BLOBS_GET_METHOD
from .protocol import REMOTE_BLOBS_HEAD_METHOD
from .protocol import REMOTE_BLOBS_LIST_METHOD
from .protocol import REMOTE_BLOBS_LIST_SHALLOW_METHOD
from .protocol import REMOTE_BLOBS_MAX_CHUNK_BYTES
from .protocol import REMOTE_BLOBS_MAX_PAGE_SIZE
from .protocol import REMOTE_BLOBS_PUT_METHOD
from .protocol import REMOTE_BLOBS_WRITE_ABORT_METHOD
from .protocol import REMOTE_BLOBS_WRITE_BEGIN_METHOD
from .protocol import REMOTE_BLOBS_WRITE_CHUNK_METHOD
from .protocol import REMOTE_BLOBS_WRITE_COMMIT_METHOD
from .protocol import RemoteBlobsCapabilitiesResult
from .protocol import RemoteBlobsCopyParams
from .protocol import RemoteBlobsDeleteManyParams
from .protocol import RemoteBlobsDeleteManyResult
from .protocol import RemoteBlobsDeleteParams
from .protocol import RemoteBlobsGetParams
from .protocol import RemoteBlobsGetResult
from .protocol import RemoteBlobsHandle
from .protocol import RemoteBlobsHeadParams
from .protocol import RemoteBlobsKeyError
from .protocol import RemoteBlobsListParams
from .protocol import RemoteBlobsListResult
from .protocol import RemoteBlobsListShallowEntry
from .protocol import RemoteBlobsListShallowParams
from .protocol import RemoteBlobsListShallowResult
from .protocol import RemoteBlobsPutParams
from .protocol import RemoteBlobsWriteBeginParams
from .protocol import RemoteBlobsWriteChunkParams
from .protocol import remote_blob_error_type


##


def _remote_blobs_clamp_range(size: int, byte_range: ta.Optional[BlobRange]) -> ta.Tuple[int, int]:
    if byte_range is None:
        return 0, size
    elif isinstance(byte_range, OffsetBlobRange):
        s = min(byte_range.start, size)
        e = size if byte_range.stop is None else min(byte_range.stop, size)
        return s, max(s, e)
    elif isinstance(byte_range, SuffixBlobRange):
        return max(0, size - byte_range.length), size
    else:
        raise TypeError(byte_range)


def _remote_blobs_close_iterator(it: ta.Iterator[ta.Any]) -> None:
    if (close := getattr(it, 'close', None)) is not None:
        close()


class _RemoteBlobsOpenWriter:
    """A store writer held open between calls, its context entered at the begin and exited at the commit or abort."""

    def __init__(self, cm: ta.ContextManager[BlobWriter]) -> None:
        super().__init__()

        self._cm = cm
        self.writer = cm.__enter__()
        self._closed = False

    def close(self) -> None:
        if not self._closed:
            self._closed = True
            self._cm.__exit__(None, None, None)


##


class RemoteBlobStoreService:
    # How many times a read starts over when its object is replaced between learning its size and reading it.
    GET_ATTEMPTS: ta.ClassVar[int] = 8

    def __init__(
            self,
            store: BlobStore,
            *,
            msh: ta.Optional[ObjMarshalerManager] = None,
            max_open_writers: int = 64,
    ) -> None:
        super().__init__()

        check.arg(max_open_writers > 0)

        self._store = store
        self._serde = LiteMarshalRpcSerde(msh)
        self._max_open_writers = max_open_writers

        self._writers: ta.Dict[str, _RemoteBlobsOpenWriter] = {}
        self._handle_seq = 0

    @property
    def store(self) -> BlobStore:
        return self._store

    @property
    def num_open_writers(self) -> int:
        return len(self._writers)

    def close(self, *_: ta.Any) -> None:
        """Discards every writer still open. Takes and ignores arguments, to serve as a close callback."""

        writers, self._writers = self._writers, {}
        for w in writers.values():
            w.close()

    #

    def _capabilities(self) -> RemoteBlobsCapabilitiesResult:
        return RemoteBlobsCapabilitiesResult(self._store.capabilities().value)

    def _head(self, p: RemoteBlobsHeadParams) -> BlobInfo:
        return self._store.head(p.key, cond=p.cond)

    def _get(self, p: RemoteBlobsGetParams) -> RemoteBlobsGetResult:
        n = min(p.max_bytes, REMOTE_BLOBS_MAX_CHUNK_BYTES)
        check.arg(n > 0)

        r = p.byte_range
        if isinstance(r, OffsetBlobRange) and r.stop is not None and r.stop - r.start <= n:
            # Fits as asked: one read, applying the caller's precondition directly.
            b = self._store.get(p.key, byte_range=r, cond=p.cond)
            s = min(r.start, b.info.size)
            return RemoteBlobsGetResult(b.info, s, s + len(b.data), b.data)

        for _ in range(self.GET_ATTEMPTS):
            # The size bounds the range, and the version pins the read to the object the size is of.
            info = self._store.head(p.key, cond=p.cond)
            s, e = _remote_blobs_clamp_range(info.size, r)
            if s == e:
                return RemoteBlobsGetResult(info, s, e, b'')
            try:
                b = self._store.get(
                    p.key,
                    byte_range=OffsetBlobRange(s, s + min(e - s, n)),
                    cond=BlobIfMatch(info.version),
                )
            except BlobPreconditionFailedError:
                if isinstance(p.cond, BlobIfMatch):
                    # The caller's own version is gone.
                    raise
                # Replaced since the head: start over on the new object.
                continue
            return RemoteBlobsGetResult(b.info, s, e, b.data)

        raise BlobConflictError(f'{p.key!r} was repeatedly replaced while being read')

    def _list(self, p: RemoteBlobsListParams) -> RemoteBlobsListResult:
        limit = max(1, min(p.limit, REMOTE_BLOBS_MAX_PAGE_SIZE))
        it = self._store.list(prefix=p.prefix, start_after=p.start_after)
        try:
            infos = list(itertools.islice(it, limit + 1))
        finally:
            _remote_blobs_close_iterator(it)
        return RemoteBlobsListResult(infos[:limit], len(infos) > limit)

    def _list_shallow(self, p: RemoteBlobsListShallowParams) -> RemoteBlobsListShallowResult:
        # A shallow listing has no start_after of its own, but its entries are in strictly increasing order of their
        # key or prefix, so a page skips what earlier pages returned. Each page walks from the start again.
        limit = max(1, min(p.limit, REMOTE_BLOBS_MAX_PAGE_SIZE))
        entries: ta.List[RemoteBlobsListShallowEntry] = []
        truncated = False
        it = self._store.list_shallow(prefix=p.prefix, delimiter=p.delimiter)
        try:
            for e in it:
                k = e.prefix if isinstance(e, BlobPrefix) else e.key
                if p.start_after is not None and k <= p.start_after:
                    continue
                if len(entries) >= limit:
                    truncated = True
                    break
                if isinstance(e, BlobPrefix):
                    entries.append(RemoteBlobsListShallowEntry(prefix=e.prefix))
                else:
                    entries.append(RemoteBlobsListShallowEntry(info=e))
        finally:
            _remote_blobs_close_iterator(it)
        return RemoteBlobsListShallowResult(entries, truncated)

    def _put(self, p: RemoteBlobsPutParams) -> BlobVersion:
        check.arg(len(p.data) <= REMOTE_BLOBS_MAX_CHUNK_BYTES)
        return self._store.put(p.key, p.data, cond=p.cond)

    #

    def _open_writer(self, handle: str) -> _RemoteBlobsOpenWriter:
        try:
            return self._writers[handle]
        except KeyError:
            raise BlobStoreError(f'no such writer: {handle!r}') from None

    def _write_begin(self, p: RemoteBlobsWriteBeginParams) -> RemoteBlobsHandle:
        if len(self._writers) >= self._max_open_writers:
            raise BlobStoreError(f'too many open writers: {len(self._writers)}')
        w = _RemoteBlobsOpenWriter(self._store.open_writer(p.key, cond=p.cond))
        self._handle_seq += 1
        handle = f'w{self._handle_seq}'
        self._writers[handle] = w
        return RemoteBlobsHandle(handle)

    def _write_chunk(self, p: RemoteBlobsWriteChunkParams) -> None:
        check.arg(len(p.data) <= REMOTE_BLOBS_MAX_CHUNK_BYTES)
        w = self._open_writer(p.handle)
        try:
            w.writer.write(p.data)
        except BaseException:
            del self._writers[p.handle]
            w.close()
            raise

    def _write_commit(self, p: RemoteBlobsHandle) -> BlobVersion:
        w = self._open_writer(p.handle)
        del self._writers[p.handle]
        try:
            return w.writer.commit()
        finally:
            w.close()

    def _write_abort(self, p: RemoteBlobsHandle) -> None:
        if (w := self._writers.pop(p.handle, None)) is not None:
            w.close()

    #

    def _copy(self, p: RemoteBlobsCopyParams) -> BlobVersion:
        return self._store.copy(p.src, p.dst, cond=p.cond)

    def _delete(self, p: RemoteBlobsDeleteParams) -> None:
        self._store.delete(p.key, cond=p.cond)

    def _delete_many(self, p: RemoteBlobsDeleteManyParams) -> RemoteBlobsDeleteManyResult:
        check.arg(len(p.keys) <= REMOTE_BLOBS_MAX_PAGE_SIZE)
        try:
            self._store.delete_many(p.keys)
        except BlobDeleteManyError as e:
            return RemoteBlobsDeleteManyResult([
                RemoteBlobsKeyError(k, remote_blob_error_type(ke), str(ke))
                for k, ke in e.errors.items()
            ])
        return RemoteBlobsDeleteManyResult([])

    #

    def _method(self, fn: ta.Callable[..., ta.Any], params_type: ta.Any, result_type: ta.Any) -> RpcMethodFn:
        async def inner(*args: ta.Any) -> ta.Any:
            try:
                return fn(*args)
            except BlobStoreError as e:
                # Sent under a type naming the class, whatever module it lives in here, for the host to raise again.
                raise RpcHandlerError(RpcRemoteErrorData(
                    code=RpcErrorCodes.REMOTE,
                    remote_type=remote_blob_error_type(e),
                    message=str(e),
                )) from e

        return rpc_typed_method(inner, params_type, result_type, serde=self._serde)

    def method_table(self) -> ta.Mapping[str, RpcMethodFn]:
        m = self._method
        return {
            REMOTE_BLOBS_CAPABILITIES_METHOD: m(self._capabilities, None, RemoteBlobsCapabilitiesResult),
            REMOTE_BLOBS_HEAD_METHOD: m(self._head, RemoteBlobsHeadParams, BlobInfo),
            REMOTE_BLOBS_GET_METHOD: m(self._get, RemoteBlobsGetParams, RemoteBlobsGetResult),
            REMOTE_BLOBS_LIST_METHOD: m(self._list, RemoteBlobsListParams, RemoteBlobsListResult),
            REMOTE_BLOBS_LIST_SHALLOW_METHOD: m(self._list_shallow, RemoteBlobsListShallowParams, RemoteBlobsListShallowResult),  # noqa
            REMOTE_BLOBS_PUT_METHOD: m(self._put, RemoteBlobsPutParams, BlobVersion),
            REMOTE_BLOBS_WRITE_BEGIN_METHOD: m(self._write_begin, RemoteBlobsWriteBeginParams, RemoteBlobsHandle),
            REMOTE_BLOBS_WRITE_CHUNK_METHOD: m(self._write_chunk, RemoteBlobsWriteChunkParams, None),
            REMOTE_BLOBS_WRITE_COMMIT_METHOD: m(self._write_commit, RemoteBlobsHandle, BlobVersion),
            REMOTE_BLOBS_WRITE_ABORT_METHOD: m(self._write_abort, RemoteBlobsHandle, None),
            REMOTE_BLOBS_COPY_METHOD: m(self._copy, RemoteBlobsCopyParams, BlobVersion),
            REMOTE_BLOBS_DELETE_METHOD: m(self._delete, RemoteBlobsDeleteParams, None),
            REMOTE_BLOBS_DELETE_MANY_METHOD: m(self._delete_many, RemoteBlobsDeleteManyParams, RemoteBlobsDeleteManyResult),  # noqa
        }
