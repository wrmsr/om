import abc
import glob as glob_
import hashlib
import os
import stat as stat_
import tempfile
import typing as ta

from omcore import dataclasses as dc
from omcore import lang


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


class FsFileChangedError(RuntimeError):
    pass


def fs_file_digest(data: lang.BytesLike) -> str:
    return hashlib.sha256(data).hexdigest()


_GLOB_MAGIC: ta.Final = frozenset('*?[')


def glob_root(pattern: str) -> str:
    """Returns the non-pattern prefix of an absolute glob without touching the filesystem."""

    if not os.path.isabs(pattern):
        raise ValueError(f'glob pattern must be absolute: {pattern!r}')

    pattern = os.path.normpath(pattern)

    drive, tail = os.path.splitdrive(pattern)
    root = drive + os.sep

    for part in tail.lstrip(os.sep).split(os.sep):
        if any(c in part for c in _GLOB_MAGIC):
            break
        root = os.path.join(root, part)

    return root


def path_is_under(path: str, root: str) -> bool:
    """Checks already-resolved target paths using POSIX-compatible lexical path semantics."""

    try:
        return os.path.commonpath((path, root)) == root
    except ValueError:
        return False


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
        return os.path.abspath(os.path.realpath(path))

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

    @staticmethod
    def _check_expected_digest(path: str, expected_digest: str) -> None:
        try:
            with open(path, 'rb') as f:  # noqa
                actual_digest = fs_file_digest(f.read())
        except FileNotFoundError:
            actual_digest = None

        if actual_digest != expected_digest:
            raise FsFileChangedError(f'File changed since it was read: {path!r}')

    async def write_file(
            self,
            path: str,
            content: lang.BytesLike,
            *,
            overwrite: bool = False,
            expected_digest: str | None = None,
    ) -> FsWriteResult:
        dst_dir = os.path.dirname(path)
        tmp_dir = tempfile.mkdtemp(prefix='.omllm-write-', dir=dst_dir)
        tmp_path = os.path.join(tmp_dir, 'file')
        fd = -1
        try:
            fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
            with os.fdopen(fd, 'wb') as f:
                fd = -1
                f.write(content)

            try:
                lst = os.lstat(path)
            except FileNotFoundError:
                if expected_digest is not None:
                    raise FsFileChangedError(f'File changed since it was read: {path!r}') from None

                # A hard link makes the fully-written file visible without replacing a path which appeared after the
                # lstat above. Both names are in the destination directory, so they are necessarily on one filesystem.
                os.link(tmp_path, path)
                os.unlink(tmp_path)
                tmp_path = ''
                return FsWriteResult(created=True)

            if not overwrite:
                raise FileExistsError(path)
            if not stat_.S_ISREG(lst.st_mode):
                raise IsADirectoryError(path)
            if expected_digest is not None:
                self._check_expected_digest(path, expected_digest)

            # Preserve the replaced file's permissions; the rename itself is atomic.
            os.chmod(tmp_path, stat_.S_IMODE(lst.st_mode))
            os.replace(tmp_path, path)
            tmp_path = ''
            return FsWriteResult(created=False)

        finally:
            if fd >= 0:
                os.close(fd)
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except FileNotFoundError:
                    pass
            os.rmdir(tmp_dir)

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
        if max_results is not None and max_results < 0:
            raise ValueError(max_results)

        resolved_root = await self.resolve_path(root)
        resolved_glob_root = await self.resolve_path(glob_root(pattern))
        if not path_is_under(resolved_glob_root, resolved_root):
            raise ValueError(f'glob root {resolved_glob_root!r} is outside permitted root {resolved_root!r}')

        entries: list[FsDirEntry] = []
        has_more = False
        for path in glob_.iglob(pattern, recursive=True):
            resolved_path = await self.resolve_path(path)
            if not path_is_under(resolved_path, resolved_root):
                continue

            if max_results is not None and len(entries) >= max_results:
                has_more = True
                break

            entries.append(self._entry(path))

        return FsGlobResult(
            entries=entries,
            has_more=has_more,
        )
