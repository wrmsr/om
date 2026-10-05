"""
Streaming reads built from ranged gets. The first get learns the object's size and version, and every later get is
pinned to that version with IfMatch, so a concurrent replace surfaces as BlobPreconditionFailedError rather than a torn
read.
"""
import io
import typing as ta

from omcore import check

from .asyncs import AsyncBlobStore
from .types import BlobInfo
from .types import BlobVersion
from .types import IfMatch
from .types import OffsetBlobRange


##


DEFAULT_BLOCK_SIZE = 1 << 20


class BlobReader:
    def __init__(
            self,
            store: AsyncBlobStore,
            *,
            info: BlobInfo,
            first_block: bytes,
            block_size: int,
    ) -> None:
        super().__init__()

        self._store = store
        self._info = info
        check.arg(block_size > 0, 'block_size must be positive')
        self._block_size = block_size

        self._pos = 0
        self._block_start = 0
        self._block = first_block

    @property
    def info(self) -> BlobInfo:
        return self._info

    def tell(self) -> int:
        return self._pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            pos = offset
        elif whence == io.SEEK_CUR:
            pos = self._pos + offset
        elif whence == io.SEEK_END:
            pos = self._info.size + offset
        else:
            raise ValueError(whence)
        if pos < 0:
            raise ValueError(f'negative seek position: {pos}')
        self._pos = pos
        return pos

    async def _fetch(self, start: int) -> None:
        stop = min(self._info.size, start + self._block_size)
        blob = await self._store.get(
            self._info.key,
            byte_range=OffsetBlobRange(start, stop),
            cond=IfMatch(self._info.version),
        )
        check.equal(len(blob.data), stop - start)
        self._block_start = start
        self._block = blob.data

    async def read(self, n: int = -1) -> bytes:
        size = self._info.size
        end = size if n < 0 else min(size, self._pos + n)
        out = io.BytesIO()
        while self._pos < end:
            if not (self._block_start <= self._pos < self._block_start + len(self._block)):
                await self._fetch(self._pos)
            o = self._pos - self._block_start
            chunk = self._block[o:o + (end - self._pos)]
            out.write(chunk)
            self._pos += len(chunk)
        return out.getvalue()


async def open_blob_reader(
        store: AsyncBlobStore,
        key: str,
        *,
        version: BlobVersion | None = None,
        block_size: int = DEFAULT_BLOCK_SIZE,
) -> BlobReader:
    blob = await store.get(
        key,
        byte_range=OffsetBlobRange(0, block_size),
        cond=IfMatch(version) if version is not None else None,
    )
    return BlobReader(
        store,
        info=blob.info,
        first_block=blob.data,
        block_size=block_size,
    )


async def iter_blob_chunks(
        store: AsyncBlobStore,
        key: str,
        *,
        chunk_size: int = DEFAULT_BLOCK_SIZE,
        version: BlobVersion | None = None,
) -> ta.AsyncIterator[bytes]:
    reader = await open_blob_reader(store, key, version=version, block_size=chunk_size)
    while chunk := await reader.read(chunk_size):
        yield chunk
