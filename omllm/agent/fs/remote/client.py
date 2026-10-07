"""
The host side of the remote filesystem: `RemoteFsOps` implements the ordinary `FsOps` interface over an rpc peer to a
remote agent's `RemoteFsService`, so the filesystem tools need no remote-specific variants.
"""
import typing as ta

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
from .protocol import REMOTE_FS_READ_FILE_METHOD
from .protocol import REMOTE_FS_RESOLVE_PATH_METHOD
from .protocol import REMOTE_FS_STAT_METHOD
from .protocol import REMOTE_FS_WRITE_FILE_METHOD
from .protocol import RemoteFsEntry
from .protocol import RemoteFsGlobParams
from .protocol import RemoteFsGlobResult
from .protocol import RemoteFsPathParams
from .protocol import RemoteFsReadFileResult
from .protocol import RemoteFsStatResult
from .protocol import RemoteFsWriteFileParams
from .protocol import RemoteFsWriteFileResult


##


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
    def __init__(self, peer: RpcPeer) -> None:
        super().__init__()

        self._peer = peer

    async def _call(self, method: str, params: ta.Any) -> ta.Any:
        try:
            return await self._peer.call(method, params)
        except RpcRemoteError as e:
            raise _translate_remote_error(e) from e

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

    async def read_file(self, path: str) -> FsFile:
        r: RemoteFsReadFileResult = unmarshal_obj(
            await self._call(
                REMOTE_FS_READ_FILE_METHOD,
                marshal_obj(RemoteFsPathParams(
                    path,
                )),
            ),
            RemoteFsReadFileResult,
        )
        return FsFile(
            data=r.data,
            digest=r.digest,
        )

    async def write_file(
            self,
            path: str,
            content: lang.BytesLike,
            *,
            overwrite: bool = False,
            expected_digest: str | None = None,
    ) -> FsWriteResult:
        r: RemoteFsWriteFileResult = unmarshal_obj(
            await self._call(
                REMOTE_FS_WRITE_FILE_METHOD,
                marshal_obj(RemoteFsWriteFileParams(
                    path=path,
                    content=bytes(content),
                    overwrite=overwrite,
                    expected_digest=expected_digest,
                )),
            ),
            RemoteFsWriteFileResult,
        )
        return FsWriteResult(
            created=r.created,
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
