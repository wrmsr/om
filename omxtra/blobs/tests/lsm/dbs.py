"""
The single writer. Opening takes over the database by committing a new manifest with a bumped epoch, which fences any
previous writer: its next commit collides with ours at the same manifest id. Only flushed data is durable - there is no
WAL - and close() flushes.
"""
import typing as ta
import uuid

from omcore import dataclasses as dc

from ...asyncs import AsyncBlobStore
from ...errors import BlobConflictError
from ...errors import BlobIndeterminateError
from ...manifests import ManifestConflictError
from ...manifests import ManifestStore
from .errors import LsmBrokenError
from .errors import LsmError
from .errors import LsmFencedError
from .iterators import drop_tombstones
from .iterators import merge_newest_wins
from .manifests import LsmManifest
from .manifests import decode_manifest
from .manifests import encode_manifest
from .memtables import Memtable
from .memtables import iter_records
from .options import LsmOptions
from .ssts import SstRef
from .ssts import write_ssts
from .views import LsmView


##


def manifest_prefix(prefix: str) -> str:
    return f'{prefix}/manifest'


def sst_prefix(prefix: str) -> str:
    return f'{prefix}/sst/'


def new_sst_key(prefix: str) -> str:
    return f'{sst_prefix(prefix)}{uuid.uuid7().hex}.sst'


class LsmDb:
    def __init__(
            self,
            store: AsyncBlobStore,
            prefix: str,
            *,
            options: LsmOptions,
            manifests: ManifestStore,
            manifest_id: int,
            manifest: LsmManifest,
    ) -> None:
        """Use LsmDb.open."""

        super().__init__()

        self._store = store
        self._prefix = prefix
        self._options = options
        self._manifests = manifests

        self._manifest_id = manifest_id
        self._view = LsmView(store, manifest, options=options)
        self._memtable = Memtable()

        self._fenced = False
        self._broken = False
        self._closed = False

    @classmethod
    async def open(
            cls,
            store: AsyncBlobStore,
            prefix: str,
            *,
            options: LsmOptions | None = None,
    ) -> LsmDb:
        if options is None:
            options = LsmOptions()
        ms = ManifestStore(store, prefix=manifest_prefix(prefix))
        writer_id = uuid.uuid7().hex
        for _ in range(options.open_retries):
            if (latest := await ms.find_latest()) is None:
                mid = 1
                m = LsmManifest(writer_id=writer_id, epoch=1, nonce=uuid.uuid7().hex, l0=[], l1=[])
            else:
                cur = decode_manifest(await ms.read(latest))
                mid = latest + 1
                m = dc.replace(cur, writer_id=writer_id, epoch=cur.epoch + 1, nonce=uuid.uuid7().hex)
            try:
                await ms.commit(mid, encode_manifest(m))
            except (ManifestConflictError, BlobConflictError):
                continue
            return cls(store, prefix, options=options, manifests=ms, manifest_id=mid, manifest=m)
        raise LsmError(f'could not take over {prefix!r}: too many concurrent openers')

    #

    @property
    def manifest_id(self) -> int:
        return self._manifest_id

    @property
    def manifest(self) -> LsmManifest:
        return self._view.manifest

    @property
    def unflushed_bytes(self) -> int:
        return self._memtable.size

    def _check_usable(self) -> None:
        if self._fenced:
            raise LsmFencedError(self._prefix)
        if self._broken:
            raise LsmBrokenError(self._prefix)
        if self._closed:
            raise LsmError(f'closed: {self._prefix!r}')

    async def _commit(self, l0: ta.Sequence[SstRef], l1: ta.Sequence[SstRef]) -> None:
        cur = self._view.manifest
        attempts = self._options.commit_conflict_retries + 1
        for attempt in range(attempts):
            new = dc.replace(cur, nonce=uuid.uuid7().hex, l0=list(l0), l1=list(l1))
            try:
                await self._manifests.commit(self._manifest_id + 1, encode_manifest(new))
            except ManifestConflictError:
                # Manifest ids are claimed strictly sequentially, so a rival at our next id has taken over.
                self._fenced = True
                raise LsmFencedError(self._prefix) from None
            except BlobConflictError:
                if attempt + 1 >= attempts:
                    raise
                continue
            except BlobIndeterminateError as e:
                self._broken = True
                raise LsmBrokenError(self._prefix) from e
            self._manifest_id += 1
            self._view = LsmView(self._store, new, options=self._options, readers=self._view.readers())
            return

    #

    async def put(self, key: bytes, value: bytes) -> None:
        self._check_usable()
        self._memtable.set(key, value)
        if self._memtable.size >= self._options.memtable_max_bytes:
            await self.flush()

    async def delete(self, key: bytes) -> None:
        self._check_usable()
        self._memtable.set(key, None)
        if self._memtable.size >= self._options.memtable_max_bytes:
            await self.flush()

    async def get(self, key: bytes) -> bytes | None:
        self._check_usable()
        if (rec := self._memtable.get(key)) is None:
            rec = await self._view.get(key)
        return rec.value if rec is not None else None

    async def scan(self, start: bytes | None = None, end: bytes | None = None) -> ta.AsyncIterator[tuple[bytes, bytes]]:
        self._check_usable()
        src = merge_newest_wins([
            iter_records(self._memtable.records(start, end)),
            *self._view.sources(start, end),
        ])
        async for rec in drop_tombstones(src):
            yield rec.key, rec.value  # type: ignore[misc]

    #

    async def flush(self) -> None:
        self._check_usable()
        if not len(self._memtable):
            return
        refs = await write_ssts(
            self._store,
            iter_records(self._memtable.records()),
            new_key=lambda: new_sst_key(self._prefix),
            block_size=self._options.block_size,
        )
        m = self._view.manifest
        await self._commit([*refs, *m.l0], m.l1)
        self._memtable.clear()
        if len(self._view.manifest.l0) >= self._options.l0_compaction_trigger:
            await self.compact()

    async def compact(self) -> None:
        """Merges all of L0 and L1 into a fresh L1, dropping shadowed records and - as L1 is the bottom - tombstones."""

        self._check_usable()
        m = self._view.manifest
        if not m.l0 and len(m.l1) <= 1:
            return
        refs = await write_ssts(
            self._store,
            drop_tombstones(self._view.scan(None, None)),
            new_key=lambda: new_sst_key(self._prefix),
            block_size=self._options.block_size,
            target_size=self._options.sst_target_size,
        )
        await self._commit([], refs)

    async def close(self) -> None:
        if self._closed:
            return
        if not (self._fenced or self._broken):
            await self.flush()
        self._closed = True

    async def __aenter__(self) -> ta.Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.close()
        else:
            self._closed = True
