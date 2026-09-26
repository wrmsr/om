"""
Garbage collection. Keeps the newest manifests, deletes older ones, and deletes SSTs referenced by no retained manifest
once they are older than a grace period. The grace period matters because writers upload SSTs before the manifest
commit referencing them lands - it must comfortably exceed the longest flush or compaction. Readers must refresh within
the retention window, or their snapshots may expire. Assumes a single collector at a time.
"""
import datetime

from omcore import dataclasses as dc

from ...asyncs import AsyncBlobStore
from ...manifests import ManifestStore
from .dbs import manifest_prefix
from .dbs import sst_prefix
from .manifests import decode_manifest


##


@dc.dataclass(frozen=True, kw_only=True)
class GcStats:
    manifests_deleted: int
    ssts_deleted: int


async def collect_garbage(
        store: AsyncBlobStore,
        prefix: str,
        *,
        keep_manifests: int,
        sst_grace: datetime.timedelta,
        now: datetime.datetime,
) -> GcStats:
    ms = ManifestStore(store, prefix=manifest_prefix(prefix))
    ids = [i async for i in ms.iter_ids()]
    if not ids:
        return GcStats(manifests_deleted=0, ssts_deleted=0)

    retained = ids[-max(1, keep_manifests):]
    referenced: set[str] = set()
    for i in retained:
        referenced.update(r.key for r in decode_manifest(await ms.read(i)).all_ssts())

    old = ids[:len(ids) - len(retained)]
    await ms.delete_ids(old)

    cutoff = now - sst_grace
    doomed = [
        info.key
        async for info in store.list(prefix=sst_prefix(prefix))
        if info.key not in referenced and info.last_modified < cutoff
    ]
    await store.delete_many(doomed)

    return GcStats(manifests_deleted=len(old), ssts_deleted=len(doomed))
