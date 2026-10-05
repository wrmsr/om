"""
Adapters between the sync and async store interfaces. There are deliberately no convenience constructors combining these
with particular backends - compose them explicitly.
"""
import contextlib
import typing as ta

from omcore import lang

from .asyncs import AsyncBlobStore
from .asyncs import AsyncBlobWriter
from .caps import BlobCapability
from .checks import check_blob_stream_length
from .stores import BlobStore
from .stores import BlobWriter
from .types import Blob
from .types import BlobInfo
from .types import BlobPrefix
from .types import BlobRange
from .types import BlobReadPrecondition
from .types import BlobVersion
from .types import BlobWritePrecondition
from .types import IfMatch


T = ta.TypeVar('T')


##


class _SyncToAsyncBlobWriter(AsyncBlobWriter):
    def __init__(self, w: BlobWriter) -> None:
        super().__init__()

        self._w = w

    async def write(self, data: bytes) -> None:
        self._w.write(data)

    async def commit(self) -> BlobVersion:
        return self._w.commit()


class SyncToAsyncBlobStore(AsyncBlobStore):
    """
    Presents a sync store through the async interface by calling it inline. A blocking store (such as LocalBlobStore)
    blocks the event loop for the duration of each call.
    """

    def __init__(self, store: BlobStore) -> None:
        super().__init__()

        self._store = store

    def capabilities(self) -> BlobCapability:
        return self._store.capabilities()

    async def head(self, key: str, *, cond: BlobReadPrecondition | None = None) -> BlobInfo:
        return self._store.head(key, cond=cond)

    async def get(
            self,
            key: str,
            *,
            byte_range: BlobRange | None = None,
            cond: BlobReadPrecondition | None = None,
    ) -> Blob:
        return self._store.get(key, byte_range=byte_range, cond=cond)

    async def list(self, *, prefix: str = '', start_after: str | None = None) -> ta.AsyncIterator[BlobInfo]:
        for info in self._store.list(prefix=prefix, start_after=start_after):
            yield info

    async def list_shallow(self, *, prefix: str = '', delimiter: str = '/') -> ta.AsyncIterator[BlobInfo | BlobPrefix]:
        for e in self._store.list_shallow(prefix=prefix, delimiter=delimiter):
            yield e

    async def put(self, key: str, data: bytes, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        return self._store.put(key, data, cond=cond)

    async def put_stream(
            self,
            key: str,
            source: ta.AsyncIterable[bytes],
            *,
            length: int | None = None,
            cond: BlobWritePrecondition | None = None,
    ) -> BlobVersion:
        # Streams into the sync store's writer rather than buffering the whole source to hand to its put_stream.
        with self._store.open_writer(key, cond=cond) as w:
            n = 0
            async for chunk in source:
                w.write(chunk)
                n += len(chunk)
            check_blob_stream_length(n, length)
            return w.commit()

    @contextlib.asynccontextmanager
    async def open_writer(
            self,
            key: str,
            *,
            cond: BlobWritePrecondition | None = None,
    ) -> ta.AsyncIterator[AsyncBlobWriter]:
        with self._store.open_writer(key, cond=cond) as w:
            yield _SyncToAsyncBlobWriter(w)

    async def copy(self, src: str, dst: str, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        return self._store.copy(src, dst, cond=cond)

    async def delete(self, key: str, *, cond: IfMatch | None = None) -> None:
        self._store.delete(key, cond=cond)

    async def delete_many(self, keys: ta.Iterable[str]) -> None:
        self._store.delete_many(keys)


##


class _AsyncToSyncBlobWriter(BlobWriter):
    def __init__(self, w: AsyncBlobWriter) -> None:
        super().__init__()

        self._w = w

    def write(self, data: bytes) -> None:
        lang.sync_await(self._w.write(data))

    def commit(self) -> BlobVersion:
        return lang.sync_await(self._w.commit())


async def _to_async_iterable(it: ta.Iterable[T]) -> ta.AsyncIterator[T]:
    for v in it:
        yield v


def _sync_aiter_closing(ai: ta.AsyncIterator[T]) -> ta.Iterator[T]:
    try:
        while True:
            try:
                v = lang.sync_await(ai.__anext__())
            except StopAsyncIteration:
                break
            yield v
    finally:
        # Closes the async generator even if the sync iterator is abandoned midway.
        if (aclose := getattr(ai, 'aclose', None)) is not None:
            lang.sync_await(aclose())


class AsyncToSyncBlobStore(BlobStore):
    """
    Presents an async store through the sync interface via lang.sync_await. Only valid for async stores which never
    actually suspend - for example an S3BlobStore given a SyncAsyncHttpClient - otherwise every call fails with
    SyncAwaitCoroutineNotTerminatedError.
    """

    def __init__(self, store: AsyncBlobStore) -> None:
        super().__init__()

        self._store = store

    def capabilities(self) -> BlobCapability:
        return self._store.capabilities()

    def head(self, key: str, *, cond: BlobReadPrecondition | None = None) -> BlobInfo:
        return lang.sync_await(self._store.head(key, cond=cond))

    def get(
            self,
            key: str,
            *,
            byte_range: BlobRange | None = None,
            cond: BlobReadPrecondition | None = None,
    ) -> Blob:
        return lang.sync_await(self._store.get(key, byte_range=byte_range, cond=cond))

    def list(self, *, prefix: str = '', start_after: str | None = None) -> ta.Iterator[BlobInfo]:
        return _sync_aiter_closing(self._store.list(prefix=prefix, start_after=start_after))

    def list_shallow(self, *, prefix: str = '', delimiter: str = '/') -> ta.Iterator[BlobInfo | BlobPrefix]:
        return _sync_aiter_closing(self._store.list_shallow(prefix=prefix, delimiter=delimiter))

    def put(self, key: str, data: bytes, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        return lang.sync_await(self._store.put(key, data, cond=cond))

    def put_stream(
            self,
            key: str,
            source: ta.Iterable[bytes],
            *,
            length: int | None = None,
            cond: BlobWritePrecondition | None = None,
    ) -> BlobVersion:
        return lang.sync_await(self._store.put_stream(key, _to_async_iterable(source), length=length, cond=cond))

    @contextlib.contextmanager
    def open_writer(self, key: str, *, cond: BlobWritePrecondition | None = None) -> ta.Iterator[BlobWriter]:
        with lang.sync_async_with(self._store.open_writer(key, cond=cond)) as w:
            yield _AsyncToSyncBlobWriter(w)

    def copy(self, src: str, dst: str, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        return lang.sync_await(self._store.copy(src, dst, cond=cond))

    def delete(self, key: str, *, cond: IfMatch | None = None) -> None:
        lang.sync_await(self._store.delete(key, cond=cond))

    def delete_many(self, keys: ta.Iterable[str]) -> None:
        lang.sync_await(self._store.delete_many(keys))
