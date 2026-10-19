# ruff: noqa: UP006 UP007 UP045
# @om-lite
import os
import stat as stat_
import typing as ta

from omcore.lite.bytes import BytesLike

from .common import fs_file_digest
from .common import fs_glob_paths
from .common import fs_resolve_path
from .common import fs_write_file
from .ops import FsEntry
from .ops import FsFile
from .ops import FsGlobResult
from .ops import FsOps
from .ops import FsWriteResult


##


class LocalFsOps(FsOps):
    @staticmethod
    def _entry(path: str, *, dangling_ok: bool = False) -> FsEntry:
        lst = os.lstat(path)
        if stat_.S_ISLNK(lst.st_mode):
            try:
                st = os.stat(path)
            except OSError:
                if not dangling_ok:
                    raise
                st = lst
        else:
            st = lst

        birthtime_ns: ta.Optional[int] = getattr(st, 'st_birthtime_ns', None)
        if birthtime_ns is None and (birthtime := getattr(st, 'st_birthtime', None)) is not None:
            birthtime_ns = int(birthtime * 1_000_000_000)

        return FsEntry(
            path=path,
            resolved_path=fs_resolve_path(path),

            is_dir=stat_.S_ISDIR(st.st_mode),
            is_file=stat_.S_ISREG(st.st_mode),
            is_symlink=stat_.S_ISLNK(lst.st_mode),

            mode=st.st_mode,
            ino=st.st_ino,
            dev=st.st_dev,
            nlink=st.st_nlink,
            uid=st.st_uid,
            gid=st.st_gid,
            size=st.st_size,

            atime_ns=st.st_atime_ns,
            mtime_ns=st.st_mtime_ns,
            ctime_ns=st.st_ctime_ns,

            blksize=st.st_blksize,
            blocks=st.st_blocks,
            rdev=st.st_rdev,

            flags=getattr(st, 'st_flags', None),
            gen=getattr(st, 'st_gen', None),
            birthtime_ns=birthtime_ns,
        )

    async def resolve_path(self, path: str) -> str:
        return fs_resolve_path(path)

    async def stat(self, path: str) -> FsEntry:
        return self._entry(path)

    async def read_file(self, path: str) -> FsFile:
        with open(path, 'rb') as f:  # noqa
            data = f.read()
        return FsFile(
            data=data,
            digest=fs_file_digest(data),
        )

    async def write_file(
            self,
            path: str,
            content: BytesLike,
            *,
            overwrite: bool = False,
            expected_digest: ta.Optional[str] = None,
    ) -> FsWriteResult:
        return FsWriteResult(created=fs_write_file(
            path,
            content,
            overwrite=overwrite,
            expected_digest=expected_digest,
        ))

    async def list_dir(self, path: str) -> ta.Sequence[FsEntry]:
        entries: ta.List[FsEntry] = []
        with os.scandir(path) as it:
            for e in it:
                try:
                    entries.append(self._entry(e.path, dangling_ok=True))
                except FileNotFoundError:
                    # Gone since the directory was read.
                    continue
        return entries

    async def glob(
            self,
            pattern: str,
            *,
            max_results: ta.Optional[int] = None,
    ) -> FsGlobResult:
        paths, has_more = fs_glob_paths(
            pattern,
            max_results=max_results,
        )

        entries: ta.List[FsEntry] = []
        for p in paths:
            try:
                entries.append(self._entry(p, dangling_ok=True))
            except FileNotFoundError:
                # Gone since the glob saw it.
                continue

        return FsGlobResult(
            entries=entries,
            has_more=has_more,
        )
