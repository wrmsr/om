import bisect
import typing as ta

from ...asyncs import AsyncBlobStore
from .iterators import merge_newest_wins
from .manifests import LsmManifest
from .options import LsmOptions
from .records import LsmRecord
from .ssts import SstReader
from .ssts import SstRef


##


class LsmView:
    """Read access to the SSTs of one manifest. Shared by writers and readers, and cheap to replace per manifest."""

    def __init__(
            self,
            store: AsyncBlobStore,
            manifest: LsmManifest,
            *,
            options: LsmOptions,
            readers: dict[str, SstReader] | None = None,
    ) -> None:
        super().__init__()

        self._store = store
        self._manifest = manifest
        self._options = options

        # SST readers are immutable once opened, so they carry over between views of successive manifests.
        live = {r.key for r in manifest.all_ssts()}
        self._readers: dict[str, SstReader] = {k: v for k, v in (readers or {}).items() if k in live}

        self._l1_max_keys = [r.max_key for r in manifest.l1]

    @property
    def manifest(self) -> LsmManifest:
        return self._manifest

    def readers(self) -> dict[str, SstReader]:
        return dict(self._readers)

    async def _reader(self, ref: SstRef) -> SstReader:
        if (r := self._readers.get(ref.key)) is None:
            r = await SstReader.open(
                self._store,
                ref.key,
                prefetch=self._options.prefetch_bytes,
                cache_size=self._options.block_cache_size,
            )
            self._readers[ref.key] = r
        return r

    async def get(self, key: bytes) -> LsmRecord | None:
        for ref in self._manifest.l0:
            if ref.min_key <= key <= ref.max_key:
                if (rec := await (await self._reader(ref)).get(key)) is not None:
                    return rec
        l1 = self._manifest.l1
        if (i := bisect.bisect_left(self._l1_max_keys, key)) < len(l1) and l1[i].min_key <= key:
            return await (await self._reader(l1[i])).get(key)
        return None

    async def _scan_ref(self, ref: SstRef, start: bytes | None, end: bytes | None) -> ta.AsyncIterator[LsmRecord]:
        if (start is not None and ref.max_key < start) or (end is not None and ref.min_key >= end):
            return
        async for rec in (await self._reader(ref)).scan(start, end):
            yield rec

    async def _scan_l1(self, start: bytes | None, end: bytes | None) -> ta.AsyncIterator[LsmRecord]:
        i = bisect.bisect_left(self._l1_max_keys, start) if start is not None else 0
        for ref in self._manifest.l1[i:]:
            if end is not None and ref.min_key >= end:
                return
            async for rec in self._scan_ref(ref, start, end):
                yield rec

    def sources(self, start: bytes | None, end: bytes | None) -> list[ta.AsyncIterator[LsmRecord]]:
        """Sorted record streams, newest first, including tombstones."""

        return [
            *[self._scan_ref(ref, start, end) for ref in self._manifest.l0],
            self._scan_l1(start, end),
        ]

    def scan(self, start: bytes | None, end: bytes | None) -> ta.AsyncIterator[LsmRecord]:
        return merge_newest_wins(self.sources(start, end))
