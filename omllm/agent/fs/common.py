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

            # A hard link makes the fully-written file visible without replacing a path which appeared after the lstat
            # above. Both names are in the destination directory, so they are necessarily on one filesystem.
            os.link(tmp_path, path)
            os.unlink(tmp_path)
            tmp_path = ''
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
        tmp_path = ''
        return False

    finally:
        if fd >= 0:
            os.close(fd)
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except FileNotFoundError:
                pass
        os.rmdir(tmp_dir)
