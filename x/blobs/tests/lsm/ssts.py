"""
SST layout:

    data block*   records in strictly increasing key order, then a crc32
    index         one entry per data block - varint(len(last_key)) last_key varint(offset) varint(length) - then a crc32
    footer        40 bytes: magic, format version, index offset, index length, entry count, crc32 of the preceding 36

Readers open an SST with a single suffix-ranged get, whose returned object size locates the footer and index without a
HEAD. Every later block read is pinned to the opened version with IfMatch.
"""
import bisect
import collections
import struct
import typing as ta
import zlib

from omcore import check
from omcore import dataclasses as dc

from ...asyncs import AsyncBlobStore
from ...asyncs import AsyncBlobWriter
from ...errors import BlobNotFoundError
from ...errors import BlobPreconditionFailedError
from ...types import BlobInfo
from ...types import IfAbsent
from ...types import IfMatch
from ...types import OffsetBlobRange
from ...types import SuffixBlobRange
from .blocks import BlockBuilder
from .blocks import parse_block
from .blocks import seal
from .blocks import unseal
from .errors import LsmCorruptionError
from .errors import LsmSnapshotExpiredError
from .records import LsmRecord
from .varints import decode_uvarint
from .varints import encode_uvarint


##


MAGIC = b'OMLSMSST'
FORMAT_VERSION = 1

_FOOTER_BODY = struct.Struct('<8sIQQQ')
_FOOTER = struct.Struct('<8sIQQQI')
FOOTER_SIZE = _FOOTER.size


@dc.dataclass(frozen=True, kw_only=True)
class SstRef:
    key: str
    min_key: bytes
    max_key: bytes
    size: int
    entries: int


@dc.dataclass(frozen=True)
class IndexEntry:
    last_key: bytes
    offset: int
    length: int


def encode_index(entries: ta.Sequence[IndexEntry]) -> bytes:
    return seal(b''.join(
        encode_uvarint(len(e.last_key)) + e.last_key + encode_uvarint(e.offset) + encode_uvarint(e.length)
        for e in entries
    ))


def decode_index(buf: bytes) -> list[IndexEntry]:
    payload = unseal(buf)
    out: list[IndexEntry] = []
    pos = 0
    try:
        while pos < len(payload):
            kl, pos = decode_uvarint(payload, pos)
            k = payload[pos:pos + kl]
            pos += kl
            off, pos = decode_uvarint(payload, pos)
            ln, pos = decode_uvarint(payload, pos)
            out.append(IndexEntry(k, off, ln))
    except ValueError as e:
        raise LsmCorruptionError('malformed index') from e
    return out


def encode_footer(*, index_offset: int, index_length: int, entries: int) -> bytes:
    body = _FOOTER_BODY.pack(MAGIC, FORMAT_VERSION, index_offset, index_length, entries)
    return body + struct.pack('<I', zlib.crc32(body))


def decode_footer(buf: bytes) -> tuple[int, int, int]:
    """Returns (index offset, index length, entry count)."""

    if len(buf) != FOOTER_SIZE:
        raise LsmCorruptionError('bad footer size')
    magic, version, index_offset, index_length, entries, crc = _FOOTER.unpack(buf)
    if magic != MAGIC:
        raise LsmCorruptionError('bad magic')
    if zlib.crc32(buf[:_FOOTER_BODY.size]) != crc:
        raise LsmCorruptionError('footer checksum mismatch')
    if version != FORMAT_VERSION:
        raise LsmCorruptionError(f'unsupported sst version: {version}')
    return index_offset, index_length, entries


##


class SstWriter:
    def __init__(self, writer: AsyncBlobWriter, *, key: str, block_size: int) -> None:
        super().__init__()

        self._writer = writer
        self._key = key
        self._block_size = block_size

        self._block = BlockBuilder()
        self._index: list[IndexEntry] = []
        self._offset = 0
        self._entries = 0
        self._min_key: bytes | None = None
        self._max_key: bytes | None = None

    @property
    def size(self) -> int:
        return self._offset + self._block.size

    @property
    def entries(self) -> int:
        return self._entries

    async def _flush_block(self) -> None:
        if not self._block.size:
            return
        data = self._block.finish()
        self._index.append(IndexEntry(check.not_none(self._block.last_key), self._offset, len(data)))
        await self._writer.write(data)
        self._offset += len(data)
        self._block = BlockBuilder()

    async def add(self, rec: LsmRecord) -> None:
        if self._max_key is not None and rec.key <= self._max_key:
            raise ValueError(f'keys must be strictly increasing: {rec.key!r} after {self._max_key!r}')
        if self._min_key is None:
            self._min_key = rec.key
        self._max_key = rec.key
        self._block.add(rec)
        self._entries += 1
        if self._block.size >= self._block_size:
            await self._flush_block()

    async def finish(self) -> SstRef:
        """Writes the index and footer and commits. Never called for an empty SST."""

        check.state(self._entries > 0)
        await self._flush_block()
        index = encode_index(self._index)
        index_offset = self._offset
        await self._writer.write(index)
        await self._writer.write(encode_footer(
            index_offset=index_offset,
            index_length=len(index),
            entries=self._entries,
        ))
        await self._writer.commit()
        return SstRef(
            key=self._key,
            min_key=check.not_none(self._min_key),
            max_key=check.not_none(self._max_key),
            size=index_offset + len(index) + FOOTER_SIZE,
            entries=self._entries,
        )


async def write_ssts(
        store: AsyncBlobStore,
        records: ta.AsyncIterator[LsmRecord],
        *,
        new_key: ta.Callable[[], str],
        block_size: int,
        target_size: int | None = None,
) -> list[SstRef]:
    """
    Writes records into as many SSTs as needed, starting a new one once the current one reaches target_size. Writes
    nothing for no records. SSTs are published with IfAbsent.
    """

    refs: list[SstRef] = []
    pending = await anext(records, None)
    while pending is not None:
        key = new_key()
        async with store.open_writer(key, cond=IfAbsent()) as w:
            sw = SstWriter(w, key=key, block_size=block_size)
            while pending is not None:
                await sw.add(pending)
                pending = await anext(records, None)
                if target_size is not None and sw.size >= target_size:
                    break
            refs.append(await sw.finish())
    return refs


##


class SstReader:
    def __init__(
            self,
            store: AsyncBlobStore,
            *,
            info: BlobInfo,
            index: ta.Sequence[IndexEntry],
            entries: int,
            tail: bytes,
            cache_size: int,
    ) -> None:
        super().__init__()

        self._store = store
        self._info = info
        self._index = index
        self._entries = entries
        self._tail = tail
        self._tail_start = info.size - len(tail)
        self._cache_size = cache_size

        self._last_keys = [e.last_key for e in index]
        self._cache: collections.OrderedDict[int, list[LsmRecord]] = collections.OrderedDict()

    @property
    def info(self) -> BlobInfo:
        return self._info

    @property
    def entries(self) -> int:
        return self._entries

    @property
    def num_blocks(self) -> int:
        return len(self._index)

    @staticmethod
    async def _get_range(store: AsyncBlobStore, key: str, *args: ta.Any, **kwargs: ta.Any) -> ta.Any:
        try:
            return await store.get(key, *args, **kwargs)
        except (BlobNotFoundError, BlobPreconditionFailedError) as e:
            # SSTs are immutable, so a vanished or changed one means garbage collection got to it first.
            raise LsmSnapshotExpiredError(key) from e

    @classmethod
    async def open(
            cls,
            store: AsyncBlobStore,
            key: str,
            *,
            prefetch: int = 64 * 1024,
            cache_size: int = 16,
    ) -> SstReader:
        blob = await cls._get_range(store, key, byte_range=SuffixBlobRange(max(prefetch, FOOTER_SIZE)))
        info, tail = blob.info, blob.data
        if len(tail) < FOOTER_SIZE:
            raise LsmCorruptionError(f'sst too small: {key!r}')
        index_offset, index_length, entries = decode_footer(tail[-FOOTER_SIZE:])
        if index_offset + index_length + FOOTER_SIZE != info.size:
            raise LsmCorruptionError(f'sst footer inconsistent with size: {key!r}')
        tail_start = info.size - len(tail)
        if index_offset >= tail_start:
            index_buf = tail[index_offset - tail_start:index_offset - tail_start + index_length]
        else:
            index_buf = (await cls._get_range(
                store,
                key,
                byte_range=OffsetBlobRange(index_offset, index_offset + index_length),
                cond=IfMatch(info.version),
            )).data
        return cls(
            store,
            info=info,
            index=decode_index(index_buf),
            entries=entries,
            tail=tail,
            cache_size=cache_size,
        )

    async def _block(self, i: int) -> list[LsmRecord]:
        if (recs := self._cache.get(i)) is not None:
            self._cache.move_to_end(i)
            return recs
        e = self._index[i]
        if e.offset >= self._tail_start:
            buf = self._tail[e.offset - self._tail_start:e.offset - self._tail_start + e.length]
        else:
            buf = (await self._get_range(
                self._store,
                self._info.key,
                byte_range=OffsetBlobRange(e.offset, e.offset + e.length),
                cond=IfMatch(self._info.version),
            )).data
        recs = parse_block(buf)
        self._cache[i] = recs
        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)
        return recs

    async def get(self, key: bytes) -> LsmRecord | None:
        """Returns the record for key, which may be a tombstone, or None if absent."""

        if (i := bisect.bisect_left(self._last_keys, key)) >= len(self._index):
            return None
        recs = await self._block(i)
        j = bisect.bisect_left([r.key for r in recs], key)
        if j < len(recs) and recs[j].key == key:
            return recs[j]
        return None

    async def scan(self, start: bytes | None = None, end: bytes | None = None) -> ta.AsyncIterator[LsmRecord]:
        """Records, including tombstones, with start <= key < end."""

        i = bisect.bisect_left(self._last_keys, start) if start is not None else 0
        for bi in range(i, len(self._index)):
            for rec in await self._block(bi):
                if start is not None and rec.key < start:
                    continue
                if end is not None and rec.key >= end:
                    return
                yield rec
