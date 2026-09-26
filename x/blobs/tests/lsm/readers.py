import typing as ta

from ...asyncs import AsyncBlobStore
from ...manifests import ManifestStore
from .dbs import manifest_prefix
from .errors import LsmError
from .iterators import drop_tombstones
from .manifests import decode_manifest
from .options import LsmOptions
from .views import LsmView


##


class LsmReader:
    """A read-only snapshot at one manifest. Must refresh within the GC retention window, or reads may expire."""

    def __init__(
            self,
            store: AsyncBlobStore,
            prefix: str,
            *,
            options: LsmOptions,
            manifests: ManifestStore,
            manifest_id: int,
            view: LsmView,
    ) -> None:
        """Use LsmReader.open."""

        super().__init__()

        self._store = store
        self._prefix = prefix
        self._options = options
        self._manifests = manifests
        self._manifest_id = manifest_id
        self._view = view

    @classmethod
    async def _load(
            cls,
            store: AsyncBlobStore,
            ms: ManifestStore,
            manifest_id: int | None,
            options: LsmOptions,
    ) -> tuple[int, LsmView]:
        if manifest_id is None:
            if (manifest_id := await ms.find_latest()) is None:
                raise LsmError('no manifests')
        return manifest_id, LsmView(store, decode_manifest(await ms.read(manifest_id)), options=options)

    @classmethod
    async def open(
            cls,
            store: AsyncBlobStore,
            prefix: str,
            *,
            manifest_id: int | None = None,
            options: LsmOptions | None = None,
    ) -> LsmReader:
        if options is None:
            options = LsmOptions()
        ms = ManifestStore(store, prefix=manifest_prefix(prefix))
        mid, view = await cls._load(store, ms, manifest_id, options)
        return cls(store, prefix, options=options, manifests=ms, manifest_id=mid, view=view)

    @property
    def manifest_id(self) -> int:
        return self._manifest_id

    async def refresh(self) -> None:
        latest = await self._manifests.find_latest(after=self._manifest_id)
        if latest is None or latest == self._manifest_id:
            return
        mid, view = await self._load(self._store, self._manifests, latest, self._options)
        self._manifest_id = mid
        self._view = LsmView(self._store, view.manifest, options=self._options, readers=self._view.readers())

    async def get(self, key: bytes) -> bytes | None:
        rec = await self._view.get(key)
        return rec.value if rec is not None else None

    async def scan(self, start: bytes | None = None, end: bytes | None = None) -> ta.AsyncIterator[tuple[bytes, bytes]]:
        async for rec in drop_tombstones(self._view.scan(start, end)):
            yield rec.key, rec.value  # type: ignore[misc]
