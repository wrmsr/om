"""
A blob store over a local filesystem, using plain blocking filesystem calls.

Layout (see paths.py for name encoding):

    <root>/
      .tmp/          in-flight writes, never listed
      .locks/        striped lock files, never listed, never deleted
      <seg>.dir/     a key prefix segment
        <seg>.file   an object

Writes go to a tmp file which is fsync'd and then committed into place. IfAbsent commits with an unlocked os.link, which
is an atomic create-if-absent. Every other mutation of a key - unconditional and IfMatch puts, and deletes - holds that
key's stripe lock, so an unconditional replace can never land between an IfMatch writer's check and its replace.
Readers never lock: an open descriptor pins the inode, so a concurrent replace never yields torn data.

Versions are `<inode>-<mtime_ns>-<size>`. Inode numbers are reused and kernel timestamps are coarse, so commits stamp an
explicit full-precision mtime - which requires a filesystem with nanosecond timestamps. The root must be on a local
filesystem (flock is not reliable over NFS).
"""
import contextlib
import datetime
import errno
import os
import time
import typing as ta

from omcore import dataclasses as dc

from ..caps import ALL_BLOB_CAPABILITIES
from ..caps import BlobCapability
from ..caps import check_blob_capabilities
from ..caps import copy_capability
from ..caps import delete_capability
from ..caps import put_capability
from ..checks import check_blob_copy_keys
from ..checks import check_blob_stream_length
from ..errors import BlobAlreadyExistsError
from ..errors import BlobDeleteManyError
from ..errors import BlobNotFoundError
from ..errors import BlobNotModifiedError
from ..errors import BlobPreconditionFailedError
from ..errors import BlobStoreError
from ..errors import InvalidBlobKeyError
from ..keys import check_blob_key
from ..listings import shallow_list
from ..stores import BlobStore
from ..stores import BlobWriter
from ..types import Blob
from ..types import BlobInfo
from ..types import BlobPrefix
from ..types import BlobRange
from ..types import BlobReadPrecondition
from ..types import BlobVersion
from ..types import BlobWritePrecondition
from ..types import IfAbsent
from ..types import IfMatch
from ..types import IfNoneMatch
from ..types import OffsetBlobRange
from ..types import SuffixBlobRange
from .fsyncs import fsync_dir
from .fsyncs import fsync_fd
from .listings import walk_files
from .listings import walk_shallow
from .locks import StripedFileLocks
from .paths import key_to_path
from .writers import LocalBlobWriter
from .writers import LocalTmpFile


##


_TMP_DIR_NAME = '.tmp'
_LOCKS_DIR_NAME = '.locks'

_MAX_COMMIT_ATTEMPTS = 8

_COPY_CHUNK_SIZE = 1024 * 1024

# Errors from os.link meaning hard links are unsupported here, as opposed to the target existing or a missing parent.
_LINK_UNSUPPORTED_ERRNOS = frozenset([errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EMLINK])


def _version_of(st: os.stat_result) -> BlobVersion:
    return BlobVersion(f'{st.st_ino:x}-{st.st_mtime_ns:x}-{st.st_size:x}')


def _last_modified_of(st: os.stat_result) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(st.st_mtime_ns / 1e9, tz=datetime.UTC)


def _clamp_range(size: int, byte_range: BlobRange | None) -> tuple[int, int]:
    match byte_range:
        case None:
            return 0, size
        case OffsetBlobRange(start=start, stop=stop):
            s = min(start, size)
            e = size if stop is None else min(stop, size)
            return s, max(s, e)
        case SuffixBlobRange(length=length):
            return max(0, size - length), size
        case _:
            raise TypeError(byte_range)


def _pread_exact(fd: int, n: int, offset: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        if not (b := os.pread(fd, n - len(buf), offset + len(buf))):
            break
        buf.extend(b)
    return bytes(buf)


class LocalBlobStore(BlobStore):
    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        no_fsync: bool = False  # tests only - never in production
        full_fsync: bool = False  # darwin: F_FULLFSYNC, which also flushes the drive's write cache
        lock_stripes: int = 256

    def __init__(self, root: str, *, config: Config | None = None) -> None:
        super().__init__()

        if config is None:
            config = LocalBlobStore.Config()

        self._root = root
        self._config = config

        self._tmp_dir = os.path.join(root, _TMP_DIR_NAME)
        self._locks = StripedFileLocks(os.path.join(root, _LOCKS_DIR_NAME), stripes=config.lock_stripes)

        self._dirs_ensured = False

    @property
    def root(self) -> str:
        return self._root

    def capabilities(self) -> BlobCapability:
        return ALL_BLOB_CAPABILITIES

    #

    def _ensure_dirs(self) -> None:
        if self._dirs_ensured:
            return
        if not os.path.isdir(self._root):
            raise FileNotFoundError(f'blob store root does not exist: {self._root!r}')
        for d in (self._tmp_dir, os.path.join(self._root, _LOCKS_DIR_NAME)):
            try:
                os.mkdir(d)
            except FileExistsError:
                pass
        self._dirs_ensured = True

    def _fsync_fd(self, fd: int) -> None:
        if not self._config.no_fsync:
            fsync_fd(fd, full=self._config.full_fsync)

    def _fsync_dir(self, path: str) -> None:
        if not self._config.no_fsync:
            fsync_dir(path, full=self._config.full_fsync)

    def _paths(self, key: str) -> tuple[ta.Sequence[str], str]:
        """Returns the chain of directory paths, root-most first, and the file path."""

        dir_names, name = key_to_path(key)
        dirs: list[str] = []
        cur = self._root
        for n in dir_names:
            cur = os.path.join(cur, n)
            dirs.append(cur)
        return dirs, os.path.join(cur, name)

    #

    def _open_file(self, key: str, path: str) -> int | None:
        try:
            return os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
        except (FileNotFoundError, NotADirectoryError):
            return None
        except OSError as e:
            if e.errno == errno.ENAMETOOLONG:
                raise InvalidBlobKeyError(key) from e
            raise

    def _info(self, key: str, st: os.stat_result) -> BlobInfo:
        return BlobInfo(
            key=key,
            size=st.st_size,
            version=_version_of(st),
            last_modified=_last_modified_of(st),
        )

    def _check_read(self, key: str, st: os.stat_result | None, cond: BlobReadPrecondition | None) -> None:
        if isinstance(cond, IfMatch) and (st is None or _version_of(st) != cond.version):
            raise BlobPreconditionFailedError(key)
        if st is None:
            raise BlobNotFoundError(key)
        if isinstance(cond, IfNoneMatch) and _version_of(st) == cond.version:
            raise BlobNotModifiedError(key)

    @contextlib.contextmanager
    def _reading(self, key: str, cond: BlobReadPrecondition | None) -> ta.Iterator[tuple[int, os.stat_result]]:
        check_blob_key(key)
        _, path = self._paths(key)
        fd = self._open_file(key, path)
        try:
            st = os.fstat(fd) if fd is not None else None
            self._check_read(key, st, cond)
            yield ta.cast(int, fd), ta.cast(os.stat_result, st)
        finally:
            if fd is not None:
                os.close(fd)

    def head(self, key: str, *, cond: BlobReadPrecondition | None = None) -> BlobInfo:
        with self._reading(key, cond) as (_, st):
            return self._info(key, st)

    def get(
            self,
            key: str,
            *,
            byte_range: BlobRange | None = None,
            cond: BlobReadPrecondition | None = None,
    ) -> Blob:
        with self._reading(key, cond) as (fd, st):
            s, e = _clamp_range(st.st_size, byte_range)
            return Blob(info=self._info(key, st), data=_pread_exact(fd, e - s, s))

    #

    def list(self, *, prefix: str = '', start_after: str | None = None) -> ta.Iterator[BlobInfo]:
        for e in walk_files(self._root, prefix=prefix, start_after=start_after):
            yield self._info(e.key, ta.cast(os.stat_result, e.stat))

    def list_shallow(self, *, prefix: str = '', delimiter: str = '/') -> ta.Iterator[BlobInfo | BlobPrefix]:
        if delimiter != '/':
            yield from shallow_list(self.list(prefix=prefix), prefix=prefix, delimiter=delimiter)
            return
        for e in walk_shallow(self._root, prefix=prefix):
            if e.is_dir:
                yield BlobPrefix(e.key)
            else:
                yield self._info(e.key, ta.cast(os.stat_result, e.stat))

    #

    def _ensure_parents(self, dirs: ta.Sequence[str]) -> None:
        parent = self._root
        for d in dirs:
            try:
                os.mkdir(d)
            except FileExistsError:
                pass
            else:
                self._fsync_dir(parent)
            parent = d

    def _stat_final(self, path: str) -> os.stat_result | None:
        try:
            return os.stat(path, follow_symlinks=False)
        except (FileNotFoundError, NotADirectoryError):
            return None

    def _commit_into(self, tmp: LocalTmpFile, key: str, path: str, cond: BlobWritePrecondition | None) -> None:
        """Raises FileNotFoundError if a parent directory vanished underneath us, in which case the caller retries."""

        if isinstance(cond, IfAbsent):
            try:
                os.link(tmp.path, path)
            except FileExistsError:
                raise BlobAlreadyExistsError(key) from None
            except OSError as e:
                if e.errno not in _LINK_UNSUPPORTED_ERRNOS:
                    raise
                with self._locks.lock(key):
                    if os.path.lexists(path):
                        raise BlobAlreadyExistsError(key) from None
                    os.replace(tmp.path, path)
            else:
                os.unlink(tmp.path)

        elif isinstance(cond, IfMatch):
            with self._locks.lock(key):
                st = self._stat_final(path)
                if st is None or _version_of(st) != cond.version:
                    raise BlobPreconditionFailedError(key)
                os.replace(tmp.path, path)

        elif cond is None:
            with self._locks.lock(key):
                os.replace(tmp.path, path)

        else:
            raise TypeError(cond)

    def _commit(self, tmp: LocalTmpFile, key: str, cond: BlobWritePrecondition | None) -> BlobVersion:
        try:
            dirs, path = self._paths(key)

            t = time.time_ns()
            os.utime(tmp.fd if os.utime in os.supports_fd else tmp.path, ns=(t, t))
            self._fsync_fd(tmp.fd)

            for _ in range(_MAX_COMMIT_ATTEMPTS):
                if not isinstance(cond, IfMatch):
                    # An IfMatch target must already exist, and so must its parents.
                    self._ensure_parents(dirs)
                try:
                    self._commit_into(tmp, key, path, cond)
                except FileNotFoundError:
                    if isinstance(cond, IfMatch):
                        raise BlobPreconditionFailedError(key) from None
                    # A concurrent delete pruned a parent directory between our mkdir and our commit.
                    continue
                break
            else:
                raise BlobStoreError(f'parent directories repeatedly vanished while committing {key!r}')

            self._fsync_dir(os.path.dirname(path))
            return _version_of(os.fstat(tmp.fd))

        finally:
            tmp.discard()

    def _new_tmp(self) -> LocalTmpFile:
        self._ensure_dirs()
        return LocalTmpFile(self._tmp_dir)

    def _check_put(self, key: str, cond: BlobWritePrecondition | None) -> None:
        check_blob_key(key)
        check_blob_capabilities(self.capabilities(), put_capability(cond))
        self._paths(key)

    def put(self, key: str, data: bytes, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        self._check_put(key, cond)
        tmp = self._new_tmp()
        try:
            tmp.write(data)
        except BaseException:
            tmp.discard()
            raise
        return self._commit(tmp, key, cond)

    def put_stream(
            self,
            key: str,
            source: ta.Iterable[bytes],
            *,
            length: int | None = None,
            cond: BlobWritePrecondition | None = None,
    ) -> BlobVersion:
        self._check_put(key, cond)
        tmp = self._new_tmp()
        try:
            for chunk in source:
                tmp.write(chunk)
            check_blob_stream_length(tmp.size, length)
        except BaseException:
            tmp.discard()
            raise
        return self._commit(tmp, key, cond)

    @contextlib.contextmanager
    def open_writer(self, key: str, *, cond: BlobWritePrecondition | None = None) -> ta.Iterator[BlobWriter]:
        self._check_put(key, cond)
        w = LocalBlobWriter(self._new_tmp(), lambda tmp: self._commit(tmp, key, cond))
        try:
            yield w
        finally:
            w.close()

    def _copy_into(self, src_fd: int, tmp: LocalTmpFile) -> None:
        try:
            while os.copy_file_range(src_fd, tmp.fd, _COPY_CHUNK_SIZE):
                pass
            return
        except OSError as e:
            if e.errno not in (errno.EXDEV, errno.ENOSYS, errno.EINVAL, errno.EOPNOTSUPP):
                raise
        os.lseek(src_fd, 0, os.SEEK_SET)
        os.ftruncate(tmp.fd, 0)
        os.lseek(tmp.fd, 0, os.SEEK_SET)
        while b := os.read(src_fd, _COPY_CHUNK_SIZE):
            tmp.write(b)

    def copy(self, src: str, dst: str, *, cond: BlobWritePrecondition | None = None) -> BlobVersion:
        check_blob_copy_keys(src, dst)
        check_blob_capabilities(self.capabilities(), copy_capability(cond))
        _, src_path = self._paths(src)
        self._paths(dst)
        if (src_fd := self._open_file(src, src_path)) is None:
            raise BlobNotFoundError(src)
        try:
            tmp = self._new_tmp()
            try:
                if hasattr(os, 'copy_file_range'):
                    self._copy_into(src_fd, tmp)
                else:
                    while b := os.read(src_fd, _COPY_CHUNK_SIZE):
                        tmp.write(b)
            except BaseException:
                tmp.discard()
                raise
        finally:
            os.close(src_fd)
        return self._commit(tmp, dst, cond)

    #

    def _prune(self, dirs: ta.Sequence[str]) -> None:
        for d in reversed(dirs):
            try:
                os.rmdir(d)
            except OSError:
                # Not empty, already gone, or raced by a writer - all fine, and all mean stop.
                return

    def _delete(self, key: str, cond: IfMatch | None) -> None:
        dirs, path = self._paths(key)
        self._ensure_dirs()
        with self._locks.lock(key):
            if cond is not None:
                st = self._stat_final(path)
                if st is None or _version_of(st) != cond.version:
                    raise BlobPreconditionFailedError(key)
            try:
                os.unlink(path)
            except (FileNotFoundError, NotADirectoryError):
                return
        if dirs:
            self._fsync_dir(dirs[-1])
        else:
            self._fsync_dir(self._root)
        self._prune(dirs)

    def delete(self, key: str, *, cond: IfMatch | None = None) -> None:
        check_blob_key(key)
        check_blob_capabilities(self.capabilities(), delete_capability(cond))
        self._delete(key, cond)

    def delete_many(self, keys: ta.Iterable[str]) -> None:
        ks = [check_blob_key(k) for k in keys]
        for k in ks:
            self._paths(k)
        errors: dict[str, BlobStoreError] = {}
        for k in ks:
            try:
                self._delete(k, None)
            except BlobStoreError as e:
                errors[k] = e
            except OSError as e:
                err = BlobStoreError(k)
                err.__cause__ = e
                errors[k] = err
        if errors:
            raise BlobDeleteManyError(errors)

    #

    def remove_stale_tmp_files(
            self,
            *,
            older_than: datetime.timedelta,
            now: datetime.datetime | None = None,
    ) -> int:
        """
        Removes tmp files left behind by crashed writers. A tmp file's mtime is when it was last written to, so
        older_than must comfortably exceed how long any live writer may sit idle.
        """

        if now is None:
            now = datetime.datetime.now(tz=datetime.UTC)
        cutoff = (now - older_than).timestamp()
        n = 0
        try:
            it = os.scandir(self._tmp_dir)
        except FileNotFoundError:
            return 0
        with it:
            for e in it:
                if not e.name.endswith('.tmp'):
                    continue
                try:
                    if e.stat(follow_symlinks=False).st_mtime < cutoff:
                        os.unlink(e.path)
                        n += 1
                except FileNotFoundError:
                    continue
        return n
