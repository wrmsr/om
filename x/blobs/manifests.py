"""
Numbered manifests: `<prefix>/<id, zero-padded>`, each published with IfAbsent. Needs only PUT_IF_ABSENT and ordered
listing, keeps history for free, and GC is plain deletes of old ids.
"""
from omcore import check

from .caps import BlobCapability
from .caps import check_blob_capabilities
from .errors import BlobAlreadyExistsError
from .errors import BlobIndeterminateError
from .stores import BlobStore
from .types import BlobVersion
from .types import IfAbsent


##


class ManifestConflictError(Exception):
    pass


class ManifestStore:
    _ID_WIDTH = 20

    def __init__(
            self,
            store: BlobStore,
            *,
            prefix: str,
            max_attempts: int = 8,
    ) -> None:
        super().__init__()

        check_blob_capabilities(store.capabilities(), BlobCapability.PUT_IF_ABSENT)

        self._store = store
        self._prefix = prefix
        self._max_attempts = max_attempts

    def _key(self, manifest_id: int) -> str:
        return f'{self._prefix}/{check.isinstance(manifest_id, int):0{self._ID_WIDTH}d}'

    def find_latest(self, *, after: int | None = None) -> int | None:
        latest = after
        start = self._key(after) if after is not None else None
        for info in self._store.list(prefix=f'{self._prefix}/', start_after=start):
            if (s := info.key.rpartition('/')[2]).isdigit() and len(s) == self._ID_WIDTH:
                latest = int(s)
        return latest

    def read(self, manifest_id: int) -> bytes:
        return self._store.get(self._key(manifest_id)).data

    def commit(self, manifest_id: int, data: bytes) -> BlobVersion:
        """
        Publishes manifest_id, which must be one past the caller's last-read manifest. `data` must be unique per writer
        (embed writer id + epoch) - after an indeterminate failure, reading back is the only way to tell our own write
        from someone else's.
        """

        key = self._key(manifest_id)
        maybe_landed = False
        for _ in range(self._max_attempts):
            try:
                return self._store.put(key, data, cond=IfAbsent())
            except BlobIndeterminateError:
                maybe_landed = True
                continue
            except BlobAlreadyExistsError:
                if not maybe_landed:
                    raise ManifestConflictError(manifest_id) from None
            blob = self._store.get(key)
            if blob.data != data:
                raise ManifestConflictError(manifest_id)
            return blob.info.version
        raise BlobIndeterminateError(key)
