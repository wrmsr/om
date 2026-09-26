import contextlib
import threading
import typing as ta

from omcore import dataclasses as dc

from ..asyncs import AsyncBlobStore
from ..asyncs import AsyncBlobWriter
from ..caps import BlobCapability
from ..types import Blob
from ..types import BlobInfo
from ..types import BlobPrecondition
from ..types import BlobPrefix
from ..types import BlobRange
from ..types import BlobReadPrecondition
from ..types import BlobVersion
from ..types import BlobWritePrecondition
from ..types import IfMatch


##


@dc.dataclass(frozen=True, kw_only=True)
class RecordedBlobCall:
    op: str
    key: str
    byte_range: BlobRange | None = None
    cond: BlobPrecondition | None = None


class RecordingBlobStore(AsyncBlobStore):
    def __init__(self, store: AsyncBlobStore) -> None:
        super().__init__()

        self._store = store
        self._lock = threading.Lock()
        self._calls: list[RecordedBlobCall] = []

    def calls(self, op: str | None = None) -> list[RecordedBlobCall]:
        with self._lock:
            return [c for c in self._calls if op is None or c.op == op]

    def clear(self) -> None:
        with self._lock:
            self._calls.clear()

    def _record(self, op: str, key: str, **kwargs: ta.Any) -> None:
        with self._lock:
            self._calls.append(RecordedBlobCall(op=op, key=key, **kwargs))

    #

    def capabilities(self) -> BlobCapability:
        return self._store.capabilities()

    async def head(self, key: str, *, cond: BlobReadPrecondition | None = None) -> BlobInfo:
        self._record('head', key, cond=cond)
        return await self._store.head(key, cond=cond)

    async def get(
            self,
            key: str,
            *,
            byte_range: BlobRange | None = None,
            cond: BlobReadPrecondition | None = None,
    ) -> Blob:
        self._record('get', key, byte_range=byte_range, cond=cond)
        return await self._store.get(key, byte_range=byte_range, cond=cond)

    async def list(self, *, prefix: str = '', start_after: str | None = None) -> ta.AsyncIterator[BlobInfo]:
        self._record('list', prefix)
        async for info in self._store.list(prefix=prefix, start_after=start_after):
            yield info

    async def list_shallow(self, *, prefix: str = '', delimiter: str = '/') -> ta.AsyncIterator[BlobInfo | BlobPrefix]:
        self._record('list_shallow', prefix)
        async for e in self._store.list_shallow(prefix=prefix, delimiter=delimiter):
            yield e

    async def put(self, key: str, data: bytes, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        self._record('put', key, cond=cond)
        return await self._store.put(key, data, cond=cond)

    async def put_stream(
            self,
            key: str,
            source: ta.AsyncIterable[bytes],
            *,
            length: int | None = None,
            cond: BlobWritePrecondition | None = None,
    ) -> BlobVersion:
        self._record('put_stream', key, cond=cond)
        return await self._store.put_stream(key, source, length=length, cond=cond)

    @contextlib.asynccontextmanager
    async def open_writer(
            self,
            key: str,
            *,
            cond: BlobWritePrecondition | None = None,
    ) -> ta.AsyncIterator[AsyncBlobWriter]:
        self._record('open_writer', key, cond=cond)
        async with self._store.open_writer(key, cond=cond) as w:
            yield w

    async def copy(self, src: str, dst: str, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        self._record('copy', dst, cond=cond)
        return await self._store.copy(src, dst, cond=cond)

    async def delete(self, key: str, *, cond: IfMatch | None = None) -> None:
        self._record('delete', key, cond=cond)
        await self._store.delete(key, cond=cond)

    async def delete_many(self, keys: ta.Iterable[str]) -> None:
        ks = list(keys)
        for k in ks:
            self._record('delete_many', k)
        await self._store.delete_many(ks)
