# ruff: noqa: UP006 UP007 UP045
"""
The target side of the remote filesystem: `RemoteFsService` serves the `FsOps` operations on behalf of a host's
`RemoteFsOps`. Lite: this runs inside the remote agent amalgam under Python 3.8+, and imports nothing but the standard
library, `omcore.lite`, the rpc package, and the shared lite filesystem helpers.
"""
import os
import stat as stat_
import typing as ta

from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj

from ....core.rpc.handlers import RpcMethod
from ..common import fs_file_digest
from ..common import fs_glob_paths
from ..common import fs_resolve_path
from ..common import fs_write_file
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


class RemoteFsService:
    @staticmethod
    def _entry(path: str, name: ta.Optional[str] = None) -> RemoteFsEntry:
        return RemoteFsEntry(
            name=os.path.basename(path) if name is None else name,
            path=path,
            is_dir=os.path.isdir(path),
            is_file=os.path.isfile(path),
            is_symlink=os.path.islink(path),
        )

    async def resolve_path(self, params: ta.Any) -> str:
        p: RemoteFsPathParams = unmarshal_obj(params, RemoteFsPathParams)
        return fs_resolve_path(p.path)

    async def stat(self, params: ta.Any) -> ta.Any:
        p: RemoteFsPathParams = unmarshal_obj(params, RemoteFsPathParams)
        lst = os.lstat(p.path)
        st = os.stat(p.path)
        return marshal_obj(RemoteFsStatResult(
            path=p.path,
            size=st.st_size,
            is_dir=stat_.S_ISDIR(st.st_mode),
            is_file=stat_.S_ISREG(st.st_mode),
            is_symlink=stat_.S_ISLNK(lst.st_mode),
        ))

    async def read_file(self, params: ta.Any) -> ta.Any:
        p: RemoteFsPathParams = unmarshal_obj(params, RemoteFsPathParams)
        with open(p.path, 'rb') as f:  # noqa
            data = f.read()
        return marshal_obj(RemoteFsReadFileResult(
            data=data,
            digest=fs_file_digest(data),
        ))

    async def write_file(self, params: ta.Any) -> ta.Any:
        p: RemoteFsWriteFileParams = unmarshal_obj(params, RemoteFsWriteFileParams)
        created = fs_write_file(
            p.path,
            p.content,
            overwrite=p.overwrite,
            expected_digest=p.expected_digest,
        )
        return marshal_obj(RemoteFsWriteFileResult(
            created=created,
        ))

    async def list_dir(self, params: ta.Any) -> ta.Any:
        p: RemoteFsPathParams = unmarshal_obj(params, RemoteFsPathParams)
        return marshal_obj(
            [
                RemoteFsEntry(
                    name=entry.name,
                    path=entry.path,
                    is_dir=entry.is_dir(),
                    is_file=entry.is_file(),
                    is_symlink=entry.is_symlink(),
                )
                for entry in os.scandir(p.path)
            ],
            ta.List[RemoteFsEntry],
        )

    async def glob(self, params: ta.Any) -> ta.Any:
        p: RemoteFsGlobParams = unmarshal_obj(params, RemoteFsGlobParams)
        paths, has_more = fs_glob_paths(
            p.pattern,
            root=p.root,
            max_results=p.max_results,
        )
        return marshal_obj(RemoteFsGlobResult(
            entries=[self._entry(path) for path in paths],
            has_more=has_more,
        ))

    def methods(self) -> ta.Mapping[str, RpcMethod]:
        return {
            REMOTE_FS_RESOLVE_PATH_METHOD: self.resolve_path,
            REMOTE_FS_STAT_METHOD: self.stat,
            REMOTE_FS_READ_FILE_METHOD: self.read_file,
            REMOTE_FS_WRITE_FILE_METHOD: self.write_file,
            REMOTE_FS_LIST_DIR_METHOD: self.list_dir,
            REMOTE_FS_GLOB_METHOD: self.glob,
        }
