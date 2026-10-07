import abc
import os
import stat as stat_
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .common import fs_file_digest
from .common import fs_glob_paths
from .common import fs_resolve_path
from .common import fs_write_file


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class FsFile:
    data: bytes

    # Opaque content identity suitable for a compare-before-write check.
    digest: str


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class FsStat:
    path: str

    size: int

    is_dir: bool
    is_file: bool
    is_symlink: bool


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class FsDirEntry:
    name: str
    path: str

    is_dir: bool
    is_file: bool
    is_symlink: bool


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class FsWriteResult:
    created: bool


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class FsGlobResult:
    entries: ta.Sequence[FsDirEntry]

    has_more: bool = False


##


class FsOps(lang.Abstract):
    @abc.abstractmethod
    def resolve_path(self, path: str) -> ta.Awaitable[str]:
        """Returns the target filesystem's absolute, symlink-resolved form of a path."""

        raise NotImplementedError

    @abc.abstractmethod
    def stat(self, path: str) -> ta.Awaitable[FsStat]:
        raise NotImplementedError

    @abc.abstractmethod
    def read_file(self, path: str) -> ta.Awaitable[FsFile]:
        raise NotImplementedError

    @abc.abstractmethod
    def write_file(
            self,
            path: str,
            content: lang.BytesLike,
            *,
            overwrite: bool = False,
            expected_digest: str | None = None,
    ) -> ta.Awaitable[FsWriteResult]:
        """
        Writes a complete file, optionally replacing an existing regular file. `expected_digest` makes replacement
        fail if the current content no longer matches a previously-read `FsFile`.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def list_dir(self, path: str) -> ta.Awaitable[ta.Sequence[FsDirEntry]]:
        raise NotImplementedError

    @abc.abstractmethod
    def glob(
            self,
            pattern: str,
            *,
            root: str,
            max_results: int | None = None,
    ) -> ta.Awaitable[FsGlobResult]:
        """Globs inside `root`, excluding matches whose resolved targets escape it."""

        raise NotImplementedError


##


class LocalFsOps(FsOps):
    @staticmethod
    def _entry(path: str, *, name: str | None = None) -> FsDirEntry:
        return FsDirEntry(
            name=os.path.basename(path) if name is None else name,
            path=path,

            is_dir=os.path.isdir(path),
            is_file=os.path.isfile(path),
            is_symlink=os.path.islink(path),
        )

    async def resolve_path(self, path: str) -> str:
        return fs_resolve_path(path)

    async def stat(self, path: str) -> FsStat:
        lst = os.lstat(path)
        st = os.stat(path)
        return FsStat(
            path=path,

            size=st.st_size,

            is_dir=stat_.S_ISDIR(st.st_mode),
            is_file=stat_.S_ISREG(st.st_mode),
            is_symlink=stat_.S_ISLNK(lst.st_mode),
        )

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
            content: lang.BytesLike,
            *,
            overwrite: bool = False,
            expected_digest: str | None = None,
    ) -> FsWriteResult:
        return FsWriteResult(created=fs_write_file(
            path,
            content,
            overwrite=overwrite,
            expected_digest=expected_digest,
        ))

    async def list_dir(self, path: str) -> ta.Sequence[FsDirEntry]:
        return [
            FsDirEntry(
                name=e.name,
                path=e.path,

                is_dir=e.is_dir(),
                is_file=e.is_file(),
                is_symlink=e.is_symlink(),
            )
            for e in os.scandir(path)
        ]

    async def glob(
            self,
            pattern: str,
            *,
            root: str,
            max_results: int | None = None,
    ) -> FsGlobResult:
        paths, has_more = fs_glob_paths(
            pattern,
            root=root,
            max_results=max_results,
        )
        return FsGlobResult(
            entries=[self._entry(p) for p in paths],
            has_more=has_more,
        )
