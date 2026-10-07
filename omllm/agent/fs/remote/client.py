"""
The host side of the remote filesystem: `RemoteFsOps` implements the ordinary `FsOps` interface over an rpc peer to a
remote agent's `RemoteFsService`, so the filesystem tools need no remote-specific variants. Content crosses in chunks of
`chunk_bytes`: a file that fits one is a single call each way, a larger one a handle-based sequence (see `protocol.py`),
and a handle the host gives up on is released even when it is being cancelled.
"""
import asyncio
import typing as ta

from omcore import check
from omcore import lang
from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj

from ....core.rpc.errors import RpcRemoteError
from ....core.rpc.peers import RpcPeer
from ....core.rpc.translate import translate_rpc_remote_builtin_error
from ..common import FsFileChangedError
from ..ops import FsDirEntry
from ..ops import FsFile
from ..ops import FsGlobResult
from ..ops import FsOps
from ..ops import FsStat
from ..ops import FsWriteResult
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
from .protocol import RemoteFsStatResult
from .protocol import RemoteFsWriteChunkParams
from .protocol import RemoteFsWriteCommitParams
from .protocol import RemoteFsWriteFileParams
from .protocol import RemoteFsWriteFileResult


##


DEFAULT_REMOTE_FS_CHUNK_BYTES: ta.Final[int] = 4 * 1024 * 1024


def _translate_remote_error(exc: RpcRemoteError) -> Exception:
    # The service raises the shared `FsFileChangedError`, which comes back by name whatever module the amalgam gave it.
    if exc.remote_type.endswith('.FsFileChangedError'):
        return FsFileChangedError(exc.remote_message)
    return translate_rpc_remote_builtin_error(exc)


def _to_fs_dir_entry(entry: RemoteFsEntry) -> FsDirEntry:
    return FsDirEntry(
        name=entry.name,
        path=entry.path,
        is_dir=entry.is_dir,
        is_file=entry.is_file,
        is_symlink=entry.is_symlink,
    )


class RemoteFsOps(FsOps):
    def __init__(
            self,
            peer: RpcPeer,
            *,
            chunk_bytes: int = DEFAULT_REMOTE_FS_CHUNK_BYTES,
    ) -> None:
        super().__init__()

        check.arg(0 < chunk_bytes <= REMOTE_FS_MAX_CHUNK_BYTES)

        self._peer = peer
        self._chunk_bytes = chunk_bytes

    async def _call(self, method: str, params: ta.Any) -> ta.Any:
        try:
            return await self._peer.call(method, params)
        except RpcRemoteError as e:
            raise _translate_remote_error(e) from e

    async def _release(self, method: str, handle: str) -> None:
        """
        Gives a handle back after a sequence has failed. Best effort - the agent releases everything when the connection
        goes anyway - and seen through even when the caller is being cancelled: the request is shielded, so it completes
        on its own if the cancellation takes this away from awaiting it.
        """

        try:
            await asyncio.shield(self._call(method, marshal_obj(RemoteFsHandleParams(handle))))
        except Exception:  # noqa
            pass

    #

    async def resolve_path(self, path: str) -> str:
        return unmarshal_obj(
            await self._call(
                REMOTE_FS_RESOLVE_PATH_METHOD,
                marshal_obj(RemoteFsPathParams(
                    path,
                )),
            ),
            str,
        )

    async def stat(self, path: str) -> FsStat:
        r: RemoteFsStatResult = unmarshal_obj(
            await self._call(
                REMOTE_FS_STAT_METHOD,
                marshal_obj(RemoteFsPathParams(
                    path,
                )),
            ),
            RemoteFsStatResult,
        )
        return FsStat(
            path=r.path,
            size=r.size,
            is_dir=r.is_dir,
            is_file=r.is_file,
            is_symlink=r.is_symlink,
        )

    async def list_dir(self, path: str) -> ta.Sequence[FsDirEntry]:
        entries: list[RemoteFsEntry] = unmarshal_obj(
            await self._call(
                REMOTE_FS_LIST_DIR_METHOD,
                marshal_obj(RemoteFsPathParams(
                    path,
                )),
            ),
            list[RemoteFsEntry],
        )
        return [_to_fs_dir_entry(entry) for entry in entries]

    async def glob(
            self,
            pattern: str,
            *,
            root: str,
            max_results: int | None = None,
    ) -> FsGlobResult:
        r: RemoteFsGlobResult = unmarshal_obj(
            await self._call(
                REMOTE_FS_GLOB_METHOD,
                marshal_obj(RemoteFsGlobParams(
                    pattern=pattern,
                    root=root,
                    max_results=max_results,
                )),
            ),
            RemoteFsGlobResult,
        )
        return FsGlobResult(
            entries=[_to_fs_dir_entry(entry) for entry in r.entries],
            has_more=r.has_more,
        )

    #

    async def read_file(self, path: str) -> FsFile:
        first: RemoteFsReadFileResult = unmarshal_obj(
            await self._call(
                REMOTE_FS_READ_FILE_METHOD,
                marshal_obj(RemoteFsReadFileParams(
                    path=path,
                    max_bytes=self._chunk_bytes,
                )),
            ),
            RemoteFsReadFileResult,
        )
        if (handle := first.handle) is None:
            return FsFile(
                data=first.data,
                digest=check.not_none(first.digest),
            )

        parts = [first.data]
        try:
            while True:
                chunk: RemoteFsReadChunkResult = unmarshal_obj(
                    await self._call(
                        REMOTE_FS_READ_CHUNK_METHOD,
                        marshal_obj(RemoteFsReadChunkParams(
                            handle=handle,
                            max_bytes=self._chunk_bytes,
                        )),
                    ),
                    RemoteFsReadChunkResult,
                )
                parts.append(chunk.data)
                if (digest := chunk.digest) is not None:
                    # The last chunk released the handle.
                    return FsFile(
                        data=b''.join(parts),
                        digest=digest,
                    )

        except BaseException:
            await self._release(REMOTE_FS_READ_ABORT_METHOD, handle)
            raise

    async def write_file(
            self,
            path: str,
            content: lang.BytesLike,
            *,
            overwrite: bool = False,
            expected_digest: str | None = None,
    ) -> FsWriteResult:
        data = bytes(content)

        if len(data) <= self._chunk_bytes:
            r: RemoteFsWriteFileResult = unmarshal_obj(
                await self._call(
                    REMOTE_FS_WRITE_FILE_METHOD,
                    marshal_obj(RemoteFsWriteFileParams(
                        path=path,
                        content=data,
                        overwrite=overwrite,
                        expected_digest=expected_digest,
                    )),
                ),
                RemoteFsWriteFileResult,
            )
            return FsWriteResult(
                created=r.created,
            )

        begun: RemoteFsHandleResult = unmarshal_obj(
            await self._call(
                REMOTE_FS_WRITE_BEGIN_METHOD,
                marshal_obj(RemoteFsPathParams(
                    path,
                )),
            ),
            RemoteFsHandleResult,
        )
        handle = begun.handle

        try:
            for offset in range(0, len(data), self._chunk_bytes):
                await self._call(
                    REMOTE_FS_WRITE_CHUNK_METHOD,
                    marshal_obj(RemoteFsWriteChunkParams(
                        handle=handle,
                        data=data[offset:offset + self._chunk_bytes],
                    )),
                )

            # Finishes the stage whether or not it succeeds; a failure here leaves nothing to release.
            committed: RemoteFsWriteFileResult = unmarshal_obj(
                await self._call(
                    REMOTE_FS_WRITE_COMMIT_METHOD,
                    marshal_obj(RemoteFsWriteCommitParams(
                        handle=handle,
                        overwrite=overwrite,
                        expected_digest=expected_digest,
                    )),
                ),
                RemoteFsWriteFileResult,
            )

        except BaseException:
            await self._release(REMOTE_FS_WRITE_ABORT_METHOD, handle)
            raise

        return FsWriteResult(
            created=committed.created,
        )
