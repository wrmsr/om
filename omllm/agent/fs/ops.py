# ruff: noqa: UP006 UP007 UP045
# @om-lite
import abc
import dataclasses as dc
import typing as ta

from omcore.lite.abstract import Abstract
from omcore.lite.bytes import BytesLike
from omcore.lite.dataclasses import install_dataclass_kw_only_init


##


@ta.final
@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class FsFile:
    data: bytes

    # Opaque content identity suitable for a compare-before-write check.
    digest: str


@ta.final
@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class FsEntry:
    """
    A path's metadata, following symlinks as `os.stat` does - `is_symlink` alone is of the path itself, and an entry
    listed from a directory or a glob which is a dangling symlink is of the link. The numeric fields are
    `os.stat_result`'s, less their `st_` prefix; the optional ones are those not every platform has.
    """

    # The path as given, and its absolute, symlink-resolved form.
    path: str
    resolved_path: str

    is_dir: bool
    is_file: bool
    is_symlink: bool

    mode: int
    ino: int
    dev: int
    nlink: int
    uid: int
    gid: int
    size: int

    atime_ns: int
    mtime_ns: int
    ctime_ns: int

    blksize: int
    blocks: int
    rdev: int

    flags: ta.Optional[int] = None
    gen: ta.Optional[int] = None
    birthtime_ns: ta.Optional[int] = None

    @property
    def atime(self) -> float:
        return self.atime_ns / 1e9

    @property
    def mtime(self) -> float:
        return self.mtime_ns / 1e9

    @property
    def ctime(self) -> float:
        return self.ctime_ns / 1e9

    @property
    def birthtime(self) -> ta.Optional[float]:
        return self.birthtime_ns / 1e9 if self.birthtime_ns is not None else None


@ta.final
@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class FsWriteResult:
    created: bool


@ta.final
@install_dataclass_kw_only_init()
@dc.dataclass(frozen=True)
class FsGlobResult:
    entries: ta.Sequence[FsEntry]

    has_more: bool = False


##


class FsOps(Abstract):
    @abc.abstractmethod
    def resolve_path(self, path: str) -> ta.Awaitable[str]:
        """Returns the target filesystem's absolute, symlink-resolved form of a path."""

        raise NotImplementedError

    @abc.abstractmethod
    def stat(self, path: str) -> ta.Awaitable[FsEntry]:
        raise NotImplementedError

    @abc.abstractmethod
    def read_file(self, path: str) -> ta.Awaitable[FsFile]:
        raise NotImplementedError

    @abc.abstractmethod
    def write_file(
            self,
            path: str,
            content: BytesLike,
            *,
            overwrite: bool = False,
            expected_digest: ta.Optional[str] = None,
    ) -> ta.Awaitable[FsWriteResult]:
        """
        Writes a complete file, optionally replacing an existing regular file. `expected_digest` makes replacement
        fail if the current content no longer matches a previously-read `FsFile`.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def list_dir(self, path: str) -> ta.Awaitable[ta.Sequence[FsEntry]]:
        raise NotImplementedError

    @abc.abstractmethod
    def glob(
            self,
            pattern: str,
            *,
            max_results: ta.Optional[int] = None,
    ) -> ta.Awaitable[FsGlobResult]:
        """
        The entries matching an absolute pattern, as the glob produced them and with nothing filtered: what a caller
        may see of them is the caller's to decide, from their resolved paths.
        """

        raise NotImplementedError
