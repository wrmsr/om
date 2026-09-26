"""
The S3 writer buffers per part: it starts a multipart upload only once a first full part exists, uploads each full
part as it fills, and commits with a single PutObject if the whole object fit in one part. Every part is exactly
part_size except the last, which also satisfies R2's uniform-part-size rule.

TODO: streamed writes. Once omcore.http request bodies can stream, each part should be sent as it is written instead of
 buffered: open the part's UploadPart request on the first write of the part, feed its (aws-chunked) body from a queue
 which write() pushes into, and complete it at the part boundary. That needs a background task running the in-flight
 request while write() calls return - which asynclite cannot spawn yet - and can never be used through
 AsyncToSyncBlobStore, whose callers cannot keep a request in flight between calls. All part transmission already goes
 through _send_part, which is where that change lands.
"""
import abc
import logging
import typing as ta

from omcore import check
from omcore import lang

from ... import blobs
from .streaming import S3StreamBody


log = logging.getLogger(__name__)


##


class S3MultipartOps(lang.Abstract):
    """The multipart primitives a writer needs - implemented by the store."""

    @abc.abstractmethod
    def put(
            self,
            key: str,
            data: bytes,
            *,
            cond: blobs.BlobWritePrecondition | None = None,
    ) -> ta.Awaitable[blobs.BlobVersion]:
        raise NotImplementedError

    @abc.abstractmethod
    def create_multipart_upload(self, key: str) -> ta.Awaitable[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def upload_part(
            self,
            key: str,
            upload_id: str,
            part_number: int,
            body: bytes | S3StreamBody,
    ) -> ta.Awaitable[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def complete_multipart_upload(
            self,
            key: str,
            upload_id: str,
            parts: ta.Sequence[tuple[int, str]],
            *,
            cond: blobs.BlobWritePrecondition | None,
    ) -> ta.Awaitable[blobs.BlobVersion]:
        raise NotImplementedError

    @abc.abstractmethod
    def abort_multipart_upload(self, key: str, upload_id: str) -> ta.Awaitable[None]:
        raise NotImplementedError


class S3BlobWriter(blobs.AsyncBlobWriter):
    def __init__(
            self,
            ops: S3MultipartOps,
            *,
            key: str,
            cond: blobs.BlobWritePrecondition | None,
            part_size: int,
    ) -> None:
        super().__init__()

        self._ops = ops
        self._key = key
        self._cond = cond
        self._part_size = part_size

        self._buf = bytearray()
        self._upload_id: str | None = None
        self._parts: list[tuple[int, str]] = []
        self._done = False
        self._committed = False

    async def _send_part(self, body: bytes | S3StreamBody) -> None:
        if self._upload_id is None:
            self._upload_id = await self._ops.create_multipart_upload(self._key)
        n = len(self._parts) + 1
        if n > 10_000:
            raise blobs.BlobStoreError(f'too many parts for {self._key!r}: raise the part size')
        etag = await self._ops.upload_part(self._key, self._upload_id, n, body)
        self._parts.append((n, etag))

    async def write(self, data: bytes) -> None:
        check.state(not self._done)
        self._buf.extend(data)
        while len(self._buf) >= self._part_size:
            part = bytes(self._buf[:self._part_size])
            del self._buf[:self._part_size]
            await self._send_part(part)

    async def commit(self) -> blobs.BlobVersion:
        check.state(not self._done)
        self._done = True
        if self._upload_id is None:
            v = await self._ops.put(self._key, bytes(self._buf), cond=self._cond)
        else:
            if self._buf:
                await self._send_part(bytes(self._buf))
                self._buf.clear()
            v = await self._ops.complete_multipart_upload(self._key, self._upload_id, self._parts, cond=self._cond)
        self._committed = True
        return v

    async def close(self) -> None:
        """Called on leaving the writer's context: aborts any started, uncommitted upload, best-effort."""

        self._done = True
        if self._committed or (upload_id := self._upload_id) is None:
            return
        try:
            await self._ops.abort_multipart_upload(self._key, upload_id)
        except Exception:  # noqa
            log.exception('failed to abort multipart upload %r of %r', upload_id, self._key)
