"""
The host side of a remote blob store: `RemoteBlobStore`, an `AsyncBlobStore` over an `omcore.rpc` connection to a
`RemoteBlobStoreService` (see `protocol.py` for the wire, and `subprocesses.py` for launching a target).

It keeps the store contract across the connection. Static checks - keys, capabilities, copy keys - run here, before
any call; reads are pinned to one version across their chunks; writers publish nothing until committed, and are
discarded on the target if abandoned. Store errors are raised as their own classes. A failure of the connection itself
is a `BlobTransportError` for reads and for calls which never left, and a `BlobIndeterminateError` for a mutation which
may have reached the target.

Over a connection on the sync runtime nothing ever suspends, so `AsyncToSyncBlobStore` presents it as a sync store.
"""
import contextlib
import typing as ta

from omcore import check
from omcore.lite.marshal import ObjMarshalerManager
from omcore.rpc.connection import RpcConnection
from omcore.rpc.errors import RpcConnectionClosedError
from omcore.rpc.errors import RpcRemoteError
from omcore.rpc.errors import RpcRemoteShuttingDownError
from omcore.rpc.errors import RpcTimeoutError
from omcore.rpc.serde import LiteMarshalRpcSerde
from omcore.rpc.serde import RpcTypedCaller
from omcore.rpc.translate import translate_rpc_remote_builtin_error

from ..asyncs import AsyncBlobStore
from ..asyncs import AsyncBlobWriter
from ..caps import BlobCapability
from ..caps import blob_copy_capability
from ..caps import blob_delete_capability
from ..caps import blob_put_capability
from ..caps import check_blob_capabilities
from ..checks import check_blob_copy_keys
from ..checks import check_blob_stream_length
from ..errors import BlobConflictError
from ..errors import BlobDeleteManyError
from ..errors import BlobIndeterminateError
from ..errors import BlobPreconditionFailedError
from ..errors import BlobStoreError
from ..errors import BlobTransportError
from ..keys import check_blob_key
from ..types import Blob
from ..types import BlobIfMatch
from ..types import BlobInfo
from ..types import BlobPrefix
from ..types import BlobRange
from ..types import BlobReadPrecondition
from ..types import BlobVersion
from ..types import BlobWritePrecondition
from ..types import OffsetBlobRange
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
from .protocol import RemoteBlobsListParams
from .protocol import RemoteBlobsListResult
from .protocol import RemoteBlobsListShallowParams
from .protocol import RemoteBlobsListShallowResult
from .protocol import RemoteBlobsPutParams
from .protocol import RemoteBlobsWriteBeginParams
from .protocol import RemoteBlobsWriteChunkParams
from .protocol import remote_blob_error_of


T = ta.TypeVar('T')


##


class _RemoteBlobCaller:
    """Typed calls, with rpc failures raised as the store errors they amount to."""

    def __init__(self, connection: RpcConnection, msh: ObjMarshalerManager | None) -> None:
        super().__init__()

        self._connection = connection
        self._caller = RpcTypedCaller(connection, LiteMarshalRpcSerde(msh))

    async def call(self, method: str, params: ta.Any, result_type: ta.Any, *, mutating: bool) -> ta.Any:
        if self._connection.is_closed:
            raise BlobTransportError(f'{method}: connection closed')

        try:
            return await self._caller.call(
                method,
                params,
                result_type,
                params_type=type(params) if params is not None else None,
            )

        except RpcRemoteShuttingDownError as e:
            # Answered by the target's teardown: what happened to the call is not known.
            raise (BlobIndeterminateError if mutating else BlobTransportError)(f'{method}: {e}') from e

        except RpcRemoteError as e:
            if (be := remote_blob_error_of(e.remote_type, e.remote_message)) is not None:
                raise be from e
            if (te := translate_rpc_remote_builtin_error(e)) is not e:
                raise te from e
            raise BlobStoreError(f'{method}: {e}') from e

        except (RpcConnectionClosedError, RpcTimeoutError, OSError) as e:
            raise (BlobIndeterminateError if mutating else BlobTransportError)(f'{method}: {e!r}') from e


class _RemoteBlobWriter(AsyncBlobWriter):
    """Buffers up to a chunk, feeding the target's writer a chunk at a time. Any failure discards it."""

    def __init__(self, caller: _RemoteBlobCaller, handle: str, chunk_bytes: int) -> None:
        super().__init__()

        self._caller = caller
        self._handle = handle
        self._chunk_bytes = chunk_bytes

        self._buf = bytearray()
        self._done = False

    async def _send(self, data: bytes) -> None:
        await self._caller.call(
            REMOTE_BLOBS_WRITE_CHUNK_METHOD,
            RemoteBlobsWriteChunkParams(self._handle, data),
            None,
            mutating=False,
        )

    async def _flush(self, *, final: bool) -> None:
        n = self._chunk_bytes
        while len(self._buf) >= n or (final and self._buf):
            piece = bytes(self._buf[:n])
            del self._buf[:n]
            await self._send(piece)

    async def write(self, data: bytes) -> None:
        check.state(not self._done)
        self._buf += data
        try:
            await self._flush(final=False)
        except BaseException:
            await self.close()
            raise

    async def commit(self) -> BlobVersion:
        check.state(not self._done)
        try:
            await self._flush(final=True)
        except BaseException:
            await self.close()
            raise

        # From here the target owns the outcome: it discards its writer however the commit ends.
        self._done = True
        return await self._caller.call(
            REMOTE_BLOBS_WRITE_COMMIT_METHOD,
            RemoteBlobsHandle(self._handle),
            BlobVersion,
            mutating=True,
        )

    async def close(self) -> None:
        if self._done:
            return
        self._done = True
        self._buf.clear()
        try:
            await self._caller.call(
                REMOTE_BLOBS_WRITE_ABORT_METHOD,
                RemoteBlobsHandle(self._handle),
                None,
                mutating=False,
            )
        except BlobStoreError:
            # Best effort: a target which cannot be told discards its writers when the connection closes.
            pass


##


class RemoteBlobStore(AsyncBlobStore):
    DEFAULT_CHUNK_BYTES: ta.ClassVar[int] = 1024 * 1024
    DEFAULT_PAGE_SIZE: ta.ClassVar[int] = REMOTE_BLOBS_MAX_PAGE_SIZE

    # How many times a read starts over when its object is replaced between its chunks.
    GET_ATTEMPTS: ta.ClassVar[int] = 8

    def __init__(
            self,
            connection: RpcConnection,
            capabilities: BlobCapability,
            *,
            chunk_bytes: int | None = None,
            page_size: int | None = None,
            msh: ObjMarshalerManager | None = None,
    ) -> None:
        """Prefer `connect`, which asks the target for its capabilities."""

        super().__init__()

        if chunk_bytes is None:
            chunk_bytes = self.DEFAULT_CHUNK_BYTES
        if page_size is None:
            page_size = self.DEFAULT_PAGE_SIZE
        check.arg(0 < chunk_bytes <= REMOTE_BLOBS_MAX_CHUNK_BYTES)
        check.arg(0 < page_size <= REMOTE_BLOBS_MAX_PAGE_SIZE)

        self._connection = connection
        self._capabilities = capabilities
        self._chunk_bytes = chunk_bytes
        self._page_size = page_size

        self._caller = _RemoteBlobCaller(connection, msh)

    @classmethod
    async def connect(
            cls,
            connection: RpcConnection,
            *,
            msh: ObjMarshalerManager | None = None,
            **kwargs: ta.Any,
    ) -> RemoteBlobStore:
        r: RemoteBlobsCapabilitiesResult = await _RemoteBlobCaller(connection, msh).call(
            REMOTE_BLOBS_CAPABILITIES_METHOD,
            None,
            RemoteBlobsCapabilitiesResult,
            mutating=False,
        )
        return cls(connection, BlobCapability(r.flags), msh=msh, **kwargs)

    @property
    def connection(self) -> RpcConnection:
        return self._connection

    def capabilities(self) -> BlobCapability:
        return self._capabilities

    async def _call(self, method: str, params: ta.Any, result_type: ta.Any, *, mutating: bool = False) -> ta.Any:
        return await self._caller.call(method, params, result_type, mutating=mutating)

    ##
    # reads

    async def head(self, key: str, *, cond: BlobReadPrecondition | None = None) -> BlobInfo:
        check_blob_key(key)
        return await self._call(REMOTE_BLOBS_HEAD_METHOD, RemoteBlobsHeadParams(key, cond), BlobInfo)

    async def _get_chunk(
            self,
            key: str,
            byte_range: BlobRange | None,
            cond: BlobReadPrecondition | None,
    ) -> RemoteBlobsGetResult:
        return await self._call(
            REMOTE_BLOBS_GET_METHOD,
            RemoteBlobsGetParams(key, self._chunk_bytes, byte_range, cond),
            RemoteBlobsGetResult,
        )

    async def get(
            self,
            key: str,
            *,
            byte_range: BlobRange | None = None,
            cond: BlobReadPrecondition | None = None,
    ) -> Blob:
        check_blob_key(key)

        for _ in range(self.GET_ATTEMPTS):
            first = await self._get_chunk(key, byte_range, cond)
            parts = [first.data]
            pos = first.start + len(first.data)
            pin = BlobIfMatch(first.info.version)
            try:
                while pos < first.stop:
                    c = await self._get_chunk(key, OffsetBlobRange(pos, min(first.stop, pos + self._chunk_bytes)), pin)
                    if not c.data:
                        raise BlobStoreError(f'short read of {key!r} at {pos}')
                    parts.append(c.data)
                    pos += len(c.data)
            except BlobPreconditionFailedError:
                if isinstance(cond, BlobIfMatch):
                    # The caller's own version is gone.
                    raise
                # Replaced since the first chunk: start over on the new object.
                continue
            return Blob(first.info, b''.join(parts))

        raise BlobConflictError(f'{key!r} was repeatedly replaced while being read')

    async def list(self, *, prefix: str = '', start_after: str | None = None) -> ta.AsyncIterator[BlobInfo]:
        after = start_after
        while True:
            r: RemoteBlobsListResult = await self._call(
                REMOTE_BLOBS_LIST_METHOD,
                RemoteBlobsListParams(self._page_size, prefix, after),
                RemoteBlobsListResult,
            )
            for info in r.infos:
                yield info
            if not r.truncated or not r.infos:
                return
            after = r.infos[-1].key

    async def list_shallow(
            self,
            *,
            prefix: str = '',
            delimiter: str = '/',
    ) -> ta.AsyncIterator[BlobInfo | BlobPrefix]:
        after: str | None = None
        while True:
            r: RemoteBlobsListShallowResult = await self._call(
                REMOTE_BLOBS_LIST_SHALLOW_METHOD,
                RemoteBlobsListShallowParams(self._page_size, prefix, delimiter, after),
                RemoteBlobsListShallowResult,
            )
            for e in r.entries:
                if e.prefix is not None:
                    after = e.prefix
                    yield BlobPrefix(e.prefix)
                else:
                    info = check.not_none(e.info)
                    after = info.key
                    yield info
            if not r.truncated or not r.entries:
                return

    ##
    # writes

    def _check_put(self, key: str, cond: BlobWritePrecondition | None) -> None:
        check_blob_key(key)
        check_blob_capabilities(self._capabilities, blob_put_capability(cond))

    async def _begin_writer(self, key: str, cond: BlobWritePrecondition | None) -> _RemoteBlobWriter:
        h: RemoteBlobsHandle = await self._call(
            REMOTE_BLOBS_WRITE_BEGIN_METHOD,
            RemoteBlobsWriteBeginParams(key, cond),
            RemoteBlobsHandle,
        )
        return _RemoteBlobWriter(self._caller, h.handle, self._chunk_bytes)

    @contextlib.asynccontextmanager
    async def _writing(self, key: str, cond: BlobWritePrecondition | None) -> ta.AsyncIterator[_RemoteBlobWriter]:
        w = await self._begin_writer(key, cond)
        try:
            yield w
        finally:
            await w.close()

    async def put(self, key: str, data: bytes, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        self._check_put(key, cond)

        if len(data) <= self._chunk_bytes:
            return await self._call(
                REMOTE_BLOBS_PUT_METHOD,
                RemoteBlobsPutParams(key, bytes(data), cond),
                BlobVersion,
                mutating=True,
            )

        async with self._writing(key, cond) as w:
            await w.write(data)
            return await w.commit()

    async def put_stream(
            self,
            key: str,
            source: ta.AsyncIterable[bytes],
            *,
            length: int | None = None,
            cond: BlobWritePrecondition | None = None,
    ) -> BlobVersion:
        self._check_put(key, cond)

        async with self._writing(key, cond) as w:
            n = 0
            async for chunk in source:
                await w.write(chunk)
                n += len(chunk)
            check_blob_stream_length(n, length)
            return await w.commit()

    @contextlib.asynccontextmanager
    async def open_writer(
            self,
            key: str,
            *,
            cond: BlobWritePrecondition | None = None,
    ) -> ta.AsyncIterator[AsyncBlobWriter]:
        self._check_put(key, cond)

        async with self._writing(key, cond) as w:
            yield w

    async def copy(self, src: str, dst: str, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        check_blob_copy_keys(src, dst)
        check_blob_capabilities(self._capabilities, blob_copy_capability(cond))
        return await self._call(
            REMOTE_BLOBS_COPY_METHOD,
            RemoteBlobsCopyParams(src, dst, cond),
            BlobVersion,
            mutating=True,
        )

    async def delete(self, key: str, *, cond: BlobIfMatch | None = None) -> None:
        check_blob_key(key)
        check_blob_capabilities(self._capabilities, blob_delete_capability(cond))
        await self._call(REMOTE_BLOBS_DELETE_METHOD, RemoteBlobsDeleteParams(key, cond), None, mutating=True)

    async def delete_many(self, keys: ta.Iterable[str]) -> None:
        ks = [check_blob_key(k) for k in keys]

        errors: dict[str, BlobStoreError] = {}
        for i in range(0, len(ks), self._page_size):
            r: RemoteBlobsDeleteManyResult = await self._call(
                REMOTE_BLOBS_DELETE_MANY_METHOD,
                RemoteBlobsDeleteManyParams(ks[i:i + self._page_size]),
                RemoteBlobsDeleteManyResult,
                mutating=True,
            )
            for ke in r.errors:
                errors[ke.key] = remote_blob_error_of(ke.type, ke.message) or BlobStoreError(ke.message)

        if errors:
            raise BlobDeleteManyError(errors)
