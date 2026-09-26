import bisect
import contextlib
import datetime
import io
import threading
import typing as ta
import uuid

from omcore import check

from .caps import ALL_BLOB_CAPABILITIES
from .caps import BlobCapability
from .caps import check_blob_capabilities
from .caps import copy_capability
from .caps import delete_capability
from .caps import put_capability
from .checks import check_blob_copy_keys
from .checks import check_blob_stream_length
from .errors import BlobAlreadyExistsError
from .errors import BlobNotFoundError
from .errors import BlobNotModifiedError
from .errors import BlobPreconditionFailedError
from .keys import check_blob_key
from .listings import shallow_list
from .stores import BlobStore
from .stores import BlobWriter
from .types import Blob
from .types import BlobInfo
from .types import BlobPrefix
from .types import BlobRange
from .types import BlobReadPrecondition
from .types import BlobVersion
from .types import BlobWritePrecondition
from .types import IfAbsent
from .types import IfMatch
from .types import IfNoneMatch
from .types import OffsetBlobRange
from .types import SuffixBlobRange


##


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.UTC)


class _DictBlobWriter(BlobWriter):
    def __init__(self, commit: ta.Callable[[bytes], BlobVersion]) -> None:
        super().__init__()

        self._commit = commit
        self._buf = io.BytesIO()
        self._done = False

    def close(self) -> None:
        self._done = True

    def write(self, data: bytes) -> None:
        check.state(not self._done)
        self._buf.write(data)

    def commit(self) -> BlobVersion:
        check.state(not self._done)
        self._done = True
        return self._commit(self._buf.getvalue())


class DictBlobStore(BlobStore):
    """The reference semantics, and the test double: restrict its capabilities to stand in for a weaker backend."""

    def __init__(
            self,
            *,
            capabilities: BlobCapability = ALL_BLOB_CAPABILITIES,
            clock: ta.Callable[[], datetime.datetime] | None = None,
    ) -> None:
        super().__init__()

        self._capabilities = capabilities
        self._clock = clock if clock is not None else _utcnow

        self._lock = threading.Lock()
        self._blobs: dict[str, Blob] = {}

    def capabilities(self) -> BlobCapability:
        return self._capabilities

    #

    def _get(self, key: str, cond: BlobReadPrecondition | None) -> Blob:
        check_blob_key(key)
        blob = self._blobs.get(key)
        if isinstance(cond, IfMatch) and (blob is None or blob.info.version != cond.version):
            raise BlobPreconditionFailedError(key)
        if blob is None:
            raise BlobNotFoundError(key)
        if isinstance(cond, IfNoneMatch) and blob.info.version == cond.version:
            raise BlobNotModifiedError(key)
        return blob

    def head(self, key: str, *, cond: BlobReadPrecondition | None = None) -> BlobInfo:
        return self._get(key, cond).info

    def get(
            self,
            key: str,
            *,
            byte_range: BlobRange | None = None,
            cond: BlobReadPrecondition | None = None,
    ) -> Blob:
        blob = self._get(key, cond)
        match byte_range:
            case None:
                return blob
            case OffsetBlobRange(start=start, stop=stop):
                data = blob.data[start:stop]
            case SuffixBlobRange(length=length):
                data = blob.data[-length:]
            case _:
                raise TypeError(byte_range)
        return Blob(info=blob.info, data=data)

    #

    def list(self, *, prefix: str = '', start_after: str | None = None) -> ta.Iterator[BlobInfo]:
        with self._lock:
            snap = dict(self._blobs)
        keys = sorted(snap)
        i = bisect.bisect_left(keys, prefix)
        if start_after is not None:
            i = max(i, bisect.bisect_right(keys, start_after))
        for k in keys[i:]:
            if not k.startswith(prefix):
                break
            yield snap[k].info

    def list_shallow(self, *, prefix: str = '', delimiter: str = '/') -> ta.Iterator[BlobInfo | BlobPrefix]:
        return shallow_list(self.list(prefix=prefix), prefix=prefix, delimiter=delimiter)

    #

    def _new_blob(self, key: str, data: bytes) -> Blob:
        return Blob(
            info=BlobInfo(
                key=key,
                size=len(data),
                version=BlobVersion(uuid.uuid7().hex),
                last_modified=self._clock(),
            ),
            data=bytes(data),
        )

    @staticmethod
    def _check_write(key: str, cur: Blob | None, cond: BlobWritePrecondition | None) -> None:
        if isinstance(cond, IfAbsent) and cur is not None:
            raise BlobAlreadyExistsError(key)
        if isinstance(cond, IfMatch) and (cur is None or cur.info.version != cond.version):
            raise BlobPreconditionFailedError(key)

    def put(self, key: str, data: bytes, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        check_blob_key(key)
        check_blob_capabilities(self._capabilities, put_capability(cond))
        with self._lock:
            self._check_write(key, self._blobs.get(key), cond)
            blob = self._blobs[key] = self._new_blob(key, data)
        return blob.info.version

    def put_stream(
            self,
            key: str,
            source: ta.Iterable[bytes],
            *,
            length: int | None = None,
            cond: BlobWritePrecondition | None = None,
    ) -> BlobVersion:
        check_blob_key(key)
        check_blob_capabilities(self._capabilities, put_capability(cond))
        data = b''.join(source)
        check_blob_stream_length(len(data), length)
        return self.put(key, data, cond=cond)

    @contextlib.contextmanager
    def open_writer(self, key: str, *, cond: BlobWritePrecondition | None = None) -> ta.Iterator[BlobWriter]:
        check_blob_key(key)
        check_blob_capabilities(self._capabilities, put_capability(cond))
        w = _DictBlobWriter(lambda data: self.put(key, data, cond=cond))
        try:
            yield w
        finally:
            w.close()

    def copy(self, src: str, dst: str, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        check_blob_copy_keys(src, dst)
        check_blob_capabilities(self._capabilities, copy_capability(cond))
        with self._lock:
            if (sb := self._blobs.get(src)) is None:
                raise BlobNotFoundError(src)
            self._check_write(dst, self._blobs.get(dst), cond)
            blob = self._blobs[dst] = self._new_blob(dst, sb.data)
        return blob.info.version

    def delete(self, key: str, *, cond: IfMatch | None = None) -> None:
        check_blob_key(key)
        check_blob_capabilities(self._capabilities, delete_capability(cond))
        with self._lock:
            self._check_write(key, self._blobs.get(key), cond)
            self._blobs.pop(key, None)

    def delete_many(self, keys: ta.Iterable[str]) -> None:
        ks = [check_blob_key(k) for k in keys]
        with self._lock:
            for k in ks:
                self._blobs.pop(k, None)
