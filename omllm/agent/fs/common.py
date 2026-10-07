# ruff: noqa: UP006 UP007 UP045
"""
Filesystem primitives shared by the local `FsOps` and the remote agent's filesystem service. Lite: this is included in
the remote agent amalgam, so it is Python 3.8 compatible and imports nothing but the standard library.
"""
import glob as glob_
import hashlib
import os
import stat as stat_
import tempfile
import typing as ta


##


class FsFileChangedError(RuntimeError):
    """A compare-before-write found the file's content no longer matching the digest it was read with."""


def fs_file_digest(data: ta.Union[bytes, bytearray, memoryview]) -> str:
    return hashlib.sha256(data).hexdigest()


def fs_resolve_path(path: str) -> str:
    """The absolute, symlink-resolved form of a path."""

    return os.path.abspath(os.path.realpath(path))


_FS_GLOB_MAGIC = frozenset('*?[')


def fs_glob_root(pattern: str) -> str:
    """Returns the non-pattern prefix of an absolute glob without touching the filesystem."""

    if not os.path.isabs(pattern):
        raise ValueError(f'glob pattern must be absolute: {pattern!r}')

    pattern = os.path.normpath(pattern)

    drive, tail = os.path.splitdrive(pattern)
    root = drive + os.sep

    for part in tail.lstrip(os.sep).split(os.sep):
        if any(c in part for c in _FS_GLOB_MAGIC):
            break
        root = os.path.join(root, part)

    return root


def fs_path_is_under(path: str, root: str) -> bool:
    """Checks already-resolved target paths using POSIX-compatible lexical path semantics."""

    try:
        return os.path.commonpath((path, root)) == root
    except ValueError:
        return False


def fs_glob_paths(
        pattern: str,
        *,
        root: str,
        max_results: ta.Optional[int] = None,
) -> ta.Tuple[ta.List[str], bool]:
    """
    Globs inside `root`, excluding matches whose resolved targets escape it. Returns the matched paths as the glob
    produced them, and whether more were available than `max_results` allowed.
    """

    if max_results is not None and max_results < 0:
        raise ValueError(max_results)

    resolved_root = fs_resolve_path(root)
    resolved_glob_root = fs_resolve_path(fs_glob_root(pattern))
    if not fs_path_is_under(resolved_glob_root, resolved_root):
        raise ValueError(f'glob root {resolved_glob_root!r} is outside permitted root {resolved_root!r}')

    paths: ta.List[str] = []
    has_more = False
    for path in glob_.iglob(pattern, recursive=True):
        if not fs_path_is_under(fs_resolve_path(path), resolved_root):
            continue

        if max_results is not None and len(paths) >= max_results:
            has_more = True
            break

        paths.append(path)

    return paths, has_more


def fs_check_expected_digest(path: str, expected_digest: str) -> None:
    try:
        with open(path, 'rb') as f:  # noqa
            actual_digest = fs_file_digest(f.read())
    except FileNotFoundError:
        actual_digest = None

    if actual_digest != expected_digest:
        raise FsFileChangedError(f'File changed since it was read: {path!r}')


##


class FsStagedWrite:
    """
    A file being written next to its destination, invisible there until `commit` makes it so atomically, or `abort`
    discards it. Either finishes the stage and cleans up after it, as does a commit that fails. Content may arrive in
    any number of `write`s, so a caller which has it in pieces need not hold all of them at once.
    """

    def __init__(self, path: str) -> None:
        super().__init__()

        self._path = path

        self._tmp_dir: ta.Optional[str] = tempfile.mkdtemp(prefix='.omllm-write-', dir=os.path.dirname(path))
        self._tmp_path: ta.Optional[str] = os.path.join(self._tmp_dir, 'file')
        self._file: ta.Optional[ta.BinaryIO] = None
        self._size = 0
        self._finished = False

        try:
            fd = os.open(self._tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
            try:
                self._file = os.fdopen(fd, 'wb')
            except BaseException:
                os.close(fd)
                raise
        except BaseException:
            self.abort()
            raise

    @property
    def path(self) -> str:
        return self._path

    @property
    def size(self) -> int:
        """How many bytes have been written so far."""

        return self._size

    @property
    def finished(self) -> bool:
        return self._finished

    def write(self, data: ta.Union[bytes, bytearray, memoryview]) -> None:
        if self._finished or self._file is None:
            raise RuntimeError('staged write is finished')
        self._file.write(data)
        self._size += len(data)

    def _close_file(self) -> None:
        if (f := self._file) is not None:
            self._file = None
            f.close()

    def abort(self) -> None:
        """Discards whatever is staged. Idempotent, and harmless after a commit."""

        self._finished = True
        self._close_file()

        if (tmp_path := self._tmp_path) is not None:
            self._tmp_path = None
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass

        if (tmp_dir := self._tmp_dir) is not None:
            self._tmp_dir = None
            try:
                os.rmdir(tmp_dir)
            except FileNotFoundError:
                pass

    def commit(
            self,
            *,
            overwrite: bool = False,
            expected_digest: ta.Optional[str] = None,
    ) -> bool:
        """
        Makes the staged content visible at the destination, optionally replacing an existing regular file.
        `expected_digest` makes replacement fail if the current content no longer matches a previous read. Returns
        whether the file was created rather than replaced.
        """

        if self._finished or (tmp_path := self._tmp_path) is None:
            raise RuntimeError('staged write is finished')
        path = self._path

        try:
            # Everything buffered is on disk under the temporary name before that name is linked or renamed.
            self._close_file()

            try:
                lst = os.lstat(path)
            except FileNotFoundError:
                if expected_digest is not None:
                    raise FsFileChangedError(f'File changed since it was read: {path!r}') from None

                # A hard link makes the fully-written file visible without replacing a path which appeared after the
                # lstat above. Both names are in the destination directory, so they are necessarily on one filesystem.
                os.link(tmp_path, path)
                return True

            if not overwrite:
                raise FileExistsError(path)
            if not stat_.S_ISREG(lst.st_mode):
                raise IsADirectoryError(path)
            if expected_digest is not None:
                fs_check_expected_digest(path, expected_digest)

            # Preserve the replaced file's permissions; the rename itself is atomic.
            os.chmod(tmp_path, stat_.S_IMODE(lst.st_mode))
            os.replace(tmp_path, path)
            self._tmp_path = None  # Consumed by the rename: only the directory is left to remove.
            return False

        finally:
            self.abort()


def fs_write_file(
        path: str,
        content: ta.Union[bytes, bytearray, memoryview],
        *,
        overwrite: bool = False,
        expected_digest: ta.Optional[str] = None,
) -> bool:
    """
    Writes a complete file, optionally replacing an existing regular file. `expected_digest` makes replacement fail if
    the current content no longer matches a previous read. Returns whether the file was created rather than replaced.
    """

    stage = FsStagedWrite(path)
    try:
        stage.write(content)
    except BaseException:
        stage.abort()
        raise
    return stage.commit(
        overwrite=overwrite,
        expected_digest=expected_digest,
    )
