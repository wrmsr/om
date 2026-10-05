import contextlib
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .asyncs import AsyncBlobStore
from .asyncs import AsyncBlobWriter
from .caps import BlobCapability
from .keys import check_blob_key
from .types import Blob
from .types import BlobInfo
from .types import BlobPrefix
from .types import BlobRange
from .types import BlobReadPrecondition
from .types import BlobVersion
from .types import BlobWritePrecondition
from .types import IfMatch


##


class PrefixedBlobStore(AsyncBlobStore):
    """Presents the keys of an underlying store beneath a fixed prefix as a store of their own."""

    def __init__(self, store: AsyncBlobStore, prefix: str) -> None:
        super().__init__()

        if not prefix.endswith('/'):
            raise ValueError(f'prefix must end with a slash: {prefix!r}')
        check_blob_key(prefix + '_')

        self._store = store
        self._prefix = prefix

    @property
    def prefix(self) -> str:
        return self._prefix

    def _k(self, key: str) -> str:
        return self._prefix + check_blob_key(key)

    def _strip(self, key: str) -> str:
        return check.non_empty_str(key.removeprefix(self._prefix) if key.startswith(self._prefix) else None)

    def _strip_info(self, info: BlobInfo) -> BlobInfo:
        return dc.replace(info, key=self._strip(info.key))

    def _strip_blob(self, blob: Blob) -> Blob:
        return dc.replace(blob, info=self._strip_info(blob.info))

    #

    def capabilities(self) -> BlobCapability:
        return self._store.capabilities()

    async def head(self, key: str, *, cond: BlobReadPrecondition | None = None) -> BlobInfo:
        return self._strip_info(await self._store.head(self._k(key), cond=cond))

    async def get(
            self,
            key: str,
            *,
            byte_range: BlobRange | None = None,
            cond: BlobReadPrecondition | None = None,
    ) -> Blob:
        return self._strip_blob(await self._store.get(self._k(key), byte_range=byte_range, cond=cond))

    async def list(self, *, prefix: str = '', start_after: str | None = None) -> ta.AsyncIterator[BlobInfo]:
        async for info in self._store.list(
                prefix=self._prefix + prefix,
                start_after=self._prefix + start_after if start_after is not None else None,
        ):
            yield self._strip_info(info)

    async def list_shallow(self, *, prefix: str = '', delimiter: str = '/') -> ta.AsyncIterator[BlobInfo | BlobPrefix]:
        async for e in self._store.list_shallow(prefix=self._prefix + prefix, delimiter=delimiter):
            if isinstance(e, BlobPrefix):
                yield BlobPrefix(self._strip(e.prefix))
            else:
                yield self._strip_info(e)

    async def put(self, key: str, data: bytes, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        return await self._store.put(self._k(key), data, cond=cond)

    async def put_stream(
            self,
            key: str,
            source: ta.AsyncIterable[bytes],
            *,
            length: int | None = None,
            cond: BlobWritePrecondition | None = None,
    ) -> BlobVersion:
        return await self._store.put_stream(self._k(key), source, length=length, cond=cond)

    @contextlib.asynccontextmanager
    async def open_writer(
            self,
            key: str,
            *,
            cond: BlobWritePrecondition | None = None,
    ) -> ta.AsyncIterator[AsyncBlobWriter]:
        async with self._store.open_writer(self._k(key), cond=cond) as w:
            yield w

    async def copy(self, src: str, dst: str, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        return await self._store.copy(self._k(src), self._k(dst), cond=cond)

    async def delete(self, key: str, *, cond: IfMatch | None = None) -> None:
        await self._store.delete(self._k(key), cond=cond)

    async def delete_many(self, keys: ta.Iterable[str]) -> None:
        await self._store.delete_many([self._k(k) for k in keys])
