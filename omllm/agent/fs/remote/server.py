# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
The target side of the remote filesystem: `RemoteFsService` serves the `FsOps` operations on behalf of a host's
`RemoteFsOps`, including the chunked reads and staged writes through which content larger than one chunk crosses the
connection (see `protocol.py`). The operations which are the same call on either side - paths, metadata, and a write
that fits one chunk - are a `LocalFsOps`'s; the handle-based reads and staged writes are the service's own, so that
content streams through it rather than being held whole. Lite: this runs inside the remote agent amalgam under Python
3.8+, and imports nothing but the standard library, `omcore.lite`, the rpc package, and the shared lite filesystem
helpers and ops.
"""
import hashlib
import os
import typing as ta

from omcore.lite.check import check
from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj

from ....core.rpc.handlers import RpcMethod
from ..common import FsStagedWrite
from ..local import LocalFsOps
from ..ops import FsEntry
from .protocol import REMOTE_FS_GLOB_METHOD
from .protocol import REMOTE_FS_LIST_DIR_METHOD
from .protocol import REMOTE_FS_MAX_CHUNK_BYTES
from .protocol import REMOTE_FS_READ_ABORT_METHOD
from .protocol import REMOTE_FS_READ_CHUNK_METHOD
from .protocol import REMOTE_FS_READ_FILE_METHOD
from .protocol import REMOTE_FS_RESOLVE_PATH_METHOD
from .protocol import REMOTE_FS_STAT_METHOD
from .protocol import REMOTE_FS_WRITE_ABORT_METHOD
from .protocol import REMOTE_FS_WRITE_BEGIN_METHOD
from .protocol import REMOTE_FS_WRITE_CHUNK_METHOD
from .protocol import REMOTE_FS_WRITE_COMMIT_METHOD
from .protocol import REMOTE_FS_WRITE_FILE_METHOD
from .protocol import RemoteFsEntry
from .protocol import RemoteFsGlobParams
from .protocol import RemoteFsGlobResult
from .protocol import RemoteFsHandleParams
from .protocol import RemoteFsHandleResult
from .protocol import RemoteFsPathParams
from .protocol import RemoteFsReadChunkParams
from .protocol import RemoteFsReadChunkResult
from .protocol import RemoteFsReadFileParams
from .protocol import RemoteFsReadFileResult
from .protocol import RemoteFsWriteChunkParams
from .protocol import RemoteFsWriteCommitParams
from .protocol import RemoteFsWriteFileParams
from .protocol import RemoteFsWriteFileResult


##


class _RemoteFsOpenRead:
    """
    A file held open across the chunks of one read. The size seen at the open bounds what is served, so the whole read
    is of the file as it was then: a writer replacing it atomically leaves this inode untouched.
    """

    def __init__(self, file: ta.BinaryIO) -> None:
        super().__init__()

        self.file = file
        self.size = os.fstat(file.fileno()).st_size
        self.hasher = hashlib.sha256()

    def read(self, max_bytes: int) -> ta.Tuple[bytes, bool]:
        """The next piece, and whether it was the last."""

        data = self.file.read(max_bytes)
        self.hasher.update(data)
        done = not data or self.file.tell() >= self.size
        return data, done

    def close(self) -> None:
        self.file.close()


class RemoteFsService:
    def __init__(
            self,
            *,
            local_ops: ta.Optional[LocalFsOps] = None,
            max_chunk_bytes: int = REMOTE_FS_MAX_CHUNK_BYTES,
            max_open_handles: int = 64,
    ) -> None:
        super().__init__()

        check.arg(0 < max_chunk_bytes <= REMOTE_FS_MAX_CHUNK_BYTES)
        check.arg(max_open_handles > 0)

        if local_ops is None:
            local_ops = LocalFsOps()

        self._local_ops = local_ops
        self._max_chunk_bytes = max_chunk_bytes
        self._max_open_handles = max_open_handles

        self._reads: ta.Dict[str, _RemoteFsOpenRead] = {}
        self._writes: ta.Dict[str, FsStagedWrite] = {}
        self._next_handle = 1
        self._closed = False

    @property
    def num_open_handles(self) -> int:
        return len(self._reads) + len(self._writes)

    def _new_handle(self, prefix: str) -> str:
        if self._closed:
            raise RuntimeError('remote filesystem service is closed')
        if self.num_open_handles >= self._max_open_handles:
            raise RuntimeError(f'too many open remote filesystem handles: {self._max_open_handles}')
        handle = f'{prefix}{self._next_handle}'
        self._next_handle += 1
        return handle

    def _chunk_bytes(self, requested: int) -> int:
        return min(requested, self._max_chunk_bytes)

    @staticmethod
    def _entry(e: FsEntry) -> RemoteFsEntry:
        return RemoteFsEntry(
            path=e.path,
            resolved_path=e.resolved_path,

            is_dir=e.is_dir,
            is_file=e.is_file,
            is_symlink=e.is_symlink,

            mode=e.mode,
            ino=e.ino,
            dev=e.dev,
            nlink=e.nlink,
            uid=e.uid,
            gid=e.gid,
            size=e.size,

            atime_ns=e.atime_ns,
            mtime_ns=e.mtime_ns,
            ctime_ns=e.ctime_ns,

            blksize=e.blksize,
            blocks=e.blocks,
            rdev=e.rdev,

            flags=e.flags,
            gen=e.gen,
            birthtime_ns=e.birthtime_ns,
        )

    #

    async def resolve_path(self, params: ta.Any) -> str:
        p: RemoteFsPathParams = unmarshal_obj(params, RemoteFsPathParams)
        return await self._local_ops.resolve_path(p.path)

    async def stat(self, params: ta.Any) -> ta.Any:
        p: RemoteFsPathParams = unmarshal_obj(params, RemoteFsPathParams)
        return marshal_obj(self._entry(await self._local_ops.stat(p.path)))

    async def list_dir(self, params: ta.Any) -> ta.Any:
        p: RemoteFsPathParams = unmarshal_obj(params, RemoteFsPathParams)
        return marshal_obj(
            [self._entry(e) for e in await self._local_ops.list_dir(p.path)],
            ta.List[RemoteFsEntry],
        )

    async def glob(self, params: ta.Any) -> ta.Any:
        p: RemoteFsGlobParams = unmarshal_obj(params, RemoteFsGlobParams)
        r = await self._local_ops.glob(
            p.pattern,
            max_results=p.max_results,
        )
        return marshal_obj(RemoteFsGlobResult(
            entries=[self._entry(e) for e in r.entries],
            has_more=r.has_more,
        ))

    #

    def _lookup_read(self, handle: str) -> _RemoteFsOpenRead:
        try:
            return self._reads[handle]
        except KeyError:
            raise ValueError(f'No such remote filesystem read: {handle!r}') from None

    async def read_file(self, params: ta.Any) -> ta.Any:
        p: RemoteFsReadFileParams = unmarshal_obj(params, RemoteFsReadFileParams)
        if self._closed:
            raise RuntimeError('remote filesystem service is closed')

        rd = _RemoteFsOpenRead(open(p.path, 'rb'))  # noqa
        try:
            data, done = rd.read(self._chunk_bytes(p.max_bytes))
            if done:
                return marshal_obj(RemoteFsReadFileResult(
                    data=data,
                    digest=rd.hasher.hexdigest(),
                    handle=None,
                ))

            handle = self._new_handle('r')

        except BaseException:
            rd.close()
            raise

        self._reads[handle] = rd
        return marshal_obj(RemoteFsReadFileResult(
            data=data,
            digest=None,
            handle=handle,
        ))

    async def read_chunk(self, params: ta.Any) -> ta.Any:
        p: RemoteFsReadChunkParams = unmarshal_obj(params, RemoteFsReadChunkParams)
        rd = self._lookup_read(p.handle)

        try:
            data, done = rd.read(self._chunk_bytes(p.max_bytes))
        except BaseException:
            self._reads.pop(p.handle, None)
            rd.close()
            raise

        if not done:
            return marshal_obj(RemoteFsReadChunkResult(
                data=data,
                digest=None,
            ))

        self._reads.pop(p.handle, None)
        rd.close()
        return marshal_obj(RemoteFsReadChunkResult(
            data=data,
            digest=rd.hasher.hexdigest(),
        ))

    async def read_abort(self, params: ta.Any) -> None:
        # Idempotent: the handle may already have gone with its last chunk.
        p: RemoteFsHandleParams = unmarshal_obj(params, RemoteFsHandleParams)
        if (rd := self._reads.pop(p.handle, None)) is not None:
            rd.close()

    #

    def _lookup_write(self, handle: str) -> FsStagedWrite:
        try:
            return self._writes[handle]
        except KeyError:
            raise ValueError(f'No such remote filesystem write: {handle!r}') from None

    async def write_file(self, params: ta.Any) -> ta.Any:
        p: RemoteFsWriteFileParams = unmarshal_obj(params, RemoteFsWriteFileParams)
        check.arg(len(p.content) <= self._max_chunk_bytes)
        r = await self._local_ops.write_file(
            p.path,
            p.content,
            overwrite=p.overwrite,
            expected_digest=p.expected_digest,
        )
        return marshal_obj(RemoteFsWriteFileResult(
            created=r.created,
        ))

    async def write_begin(self, params: ta.Any) -> ta.Any:
        p: RemoteFsPathParams = unmarshal_obj(params, RemoteFsPathParams)
        handle = self._new_handle('w')
        self._writes[handle] = FsStagedWrite(p.path)
        return marshal_obj(RemoteFsHandleResult(
            handle=handle,
        ))

    async def write_chunk(self, params: ta.Any) -> None:
        p: RemoteFsWriteChunkParams = unmarshal_obj(params, RemoteFsWriteChunkParams)
        stage = self._lookup_write(p.handle)
        try:
            check.arg(len(p.data) <= self._max_chunk_bytes)
            stage.write(p.data)
        except BaseException:
            # A stage that failed to take a piece cannot be completed: it is discarded, and the commit will say so.
            self._writes.pop(p.handle, None)
            stage.abort()
            raise

    async def write_commit(self, params: ta.Any) -> ta.Any:
        p: RemoteFsWriteCommitParams = unmarshal_obj(params, RemoteFsWriteCommitParams)
        stage = self._lookup_write(p.handle)
        self._writes.pop(p.handle, None)
        # Finishes the stage either way, cleaning up after a failure.
        created = stage.commit(
            overwrite=p.overwrite,
            expected_digest=p.expected_digest,
        )
        return marshal_obj(RemoteFsWriteFileResult(
            created=created,
        ))

    async def write_abort(self, params: ta.Any) -> None:
        # Idempotent: the handle may already have gone with a failed chunk or commit.
        p: RemoteFsHandleParams = unmarshal_obj(params, RemoteFsHandleParams)
        if (stage := self._writes.pop(p.handle, None)) is not None:
            stage.abort()

    #

    def methods(self) -> ta.Mapping[str, RpcMethod]:
        return {
            REMOTE_FS_RESOLVE_PATH_METHOD: self.resolve_path,
            REMOTE_FS_STAT_METHOD: self.stat,
            REMOTE_FS_LIST_DIR_METHOD: self.list_dir,
            REMOTE_FS_GLOB_METHOD: self.glob,

            REMOTE_FS_READ_FILE_METHOD: self.read_file,
            REMOTE_FS_READ_CHUNK_METHOD: self.read_chunk,
            REMOTE_FS_READ_ABORT_METHOD: self.read_abort,

            REMOTE_FS_WRITE_FILE_METHOD: self.write_file,
            REMOTE_FS_WRITE_BEGIN_METHOD: self.write_begin,
            REMOTE_FS_WRITE_CHUNK_METHOD: self.write_chunk,
            REMOTE_FS_WRITE_COMMIT_METHOD: self.write_commit,
            REMOTE_FS_WRITE_ABORT_METHOD: self.write_abort,
        }

    async def aclose(self) -> None:
        """Releases every open read and discards every unfinished write - a host that has gone cannot finish them."""

        self._closed = True

        reads, self._reads = self._reads, {}
        for rd in reads.values():
            rd.close()

        writes, self._writes = self._writes, {}
        for stage in writes.values():
            stage.abort()
