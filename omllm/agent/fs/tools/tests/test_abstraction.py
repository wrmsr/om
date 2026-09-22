import os.path
import typing as ta
import uuid

import pytest

from ....permissions.deciders import StaticPermissionDecider
from ....permissions.types import PermissionState
from ....types.tools import ToolContext
from ....types.tools import ToolEnvironment
from ...ops import FsDirEntry
from ...ops import FsFile
from ...ops import FsGlobResult
from ...ops import FsOps
from ...ops import FsStat
from ...ops import FsWriteResult
from ...ops import LocalFsOps
from ..edit import EditTool
from ..glob import GlobTool
from ..ls import LsTool
from ..read import ReadTool
from ..write import WriteTool


##


class _MappedFsOps(FsOps):
    """A target namespace backed by a different local directory, as a stand-in for a remote filesystem."""

    def __init__(self, target_root: str, local_root: str) -> None:
        super().__init__()

        self._target_root = target_root
        self._local_root = local_root
        self._local = LocalFsOps()

    def _to_local(self, path: str) -> str:
        if path == self._target_root:
            return self._local_root
        prefix = self._target_root + os.sep
        if not path.startswith(prefix):
            raise ValueError(path)
        return os.path.join(self._local_root, path[len(prefix):])

    def _to_target(self, path: str) -> str:
        if path == self._local_root:
            return self._target_root
        prefix = self._local_root + os.sep
        if not path.startswith(prefix):
            raise ValueError(path)
        return os.path.join(self._target_root, path[len(prefix):])

    @staticmethod
    def _replace_entry_path(entry: FsDirEntry, path: str) -> FsDirEntry:
        return FsDirEntry(
            name=entry.name,
            path=path,
            is_dir=entry.is_dir,
            is_file=entry.is_file,
            is_symlink=entry.is_symlink,
        )

    async def resolve_path(self, path: str) -> str:
        return self._to_target(await self._local.resolve_path(self._to_local(path)))

    async def stat(self, path: str) -> FsStat:
        st = await self._local.stat(self._to_local(path))
        return FsStat(
            path=path,
            size=st.size,
            is_dir=st.is_dir,
            is_file=st.is_file,
            is_symlink=st.is_symlink,
        )

    async def read_file(self, path: str) -> FsFile:
        return await self._local.read_file(self._to_local(path))

    async def write_file(
            self,
            path: str,
            content,
            *,
            overwrite: bool = False,
            expected_digest: str | None = None,
    ) -> FsWriteResult:
        return await self._local.write_file(
            self._to_local(path),
            content,
            overwrite=overwrite,
            expected_digest=expected_digest,
        )

    async def list_dir(self, path: str) -> ta.Sequence[FsDirEntry]:
        return [
            self._replace_entry_path(e, self._to_target(e.path))
            for e in await self._local.list_dir(self._to_local(path))
        ]

    async def glob(
            self,
            pattern: str,
            *,
            root: str,
            max_results: int | None = None,
    ) -> FsGlobResult:
        result = await self._local.glob(
            self._to_local(pattern),
            root=self._to_local(root),
            max_results=max_results,
        )
        return FsGlobResult(
            entries=[
                self._replace_entry_path(e, self._to_target(e.path))
                for e in result.entries
            ],
            has_more=result.has_more,
        )


async def _call(tool, cwd, args):
    result = await tool.execute_context(ToolContext(
        args=args,
        env=ToolEnvironment(cwd=cwd),
    ))
    assert result.error is None, result.content.text
    return result


@pytest.mark.asyncs('asyncio')
async def test_fs_tools_only_use_fs_ops(tmp_path):
    local_root = os.path.realpath(tmp_path)
    target_root = f'/__omllm_remote_workspace_{uuid.uuid4().hex}'
    assert not os.path.exists(target_root)

    os.mkdir(os.path.join(local_root, 'sub'))
    local = LocalFsOps()
    await local.write_file(os.path.join(local_root, 'seed.txt'), b'old\nline\n')
    await local.write_file(os.path.join(local_root, 'sub', 'nested.txt'), b'nested\n')

    fs = _MappedFsOps(target_root, local_root)
    permissions = StaticPermissionDecider(PermissionState.ALLOW)
    seed = os.path.join(target_root, 'seed.txt')
    created = os.path.join(target_root, 'created.txt')

    read = await _call(ReadTool(permissions=permissions, fs=fs), target_root, {'file_path': seed})
    assert 'old' in read.content.text

    await _call(
        EditTool(permissions=permissions, fs=fs),
        target_root,
        {'file_path': seed, 'old_string': 'old', 'new_string': 'new'},
    )
    assert (await local.read_file(os.path.join(local_root, 'seed.txt'))).data.startswith(b'new')

    await _call(
        WriteTool(permissions=permissions, fs=fs),
        target_root,
        {'file_path': created, 'contents': 'created'},
    )
    assert (await local.read_file(os.path.join(local_root, 'created.txt'))).data == b'created'

    ls = await _call(LsTool(permissions=permissions, fs=fs), target_root, {'dir_path': target_root})
    assert 'created.txt' in ls.content.text
    assert 'sub/' in ls.content.text

    glob = await _call(
        GlobTool(permissions=permissions, fs=fs),
        target_root,
        {'pattern': os.path.join(target_root, '**', '*.txt')},
    )
    assert seed in glob.content.text
    assert os.path.join(target_root, 'sub', 'nested.txt') in glob.content.text
