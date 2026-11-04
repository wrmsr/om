# ruff: noqa: UP006 UP007 UP017 UP037 UP045
# @om-lite
"""
A blob store over a local filesystem, using plain blocking filesystem calls.

Layout (see paths.py for name encoding):

    <root>/
      .tmp/          in-flight writes, never listed
      .locks/        striped lock files, never listed, never deleted
      <seg>.dir/     a key prefix segment
        <seg>.file   an object

Writes go to a tmp file which is fsync'd and then committed into place. BlobIfAbsent commits with an unlocked os.link,
which is an atomic create-if-absent. Every other mutation of a key - unconditional and BlobIfMatch puts, and deletes -
holds that key's stripe lock, so an unconditional replace can never land between a BlobIfMatch writer's check and its
replace.
Readers never lock: an open descriptor pins the inode, so a concurrent replace never yields torn data.

Versions are `<inode>-<mtime_ns>-<size>`. Inode numbers are reused and kernel timestamps are coarse, so commits stamp an
explicit full-precision mtime - which requires a filesystem with nanosecond timestamps. The root must be on a local
filesystem (flock is not reliable over NFS).
"""
import contextlib
import dataclasses as dc
import datetime
import errno
import os
import sys
import time
import typing as ta

from ..caps import ALL_BLOB_CAPABILITIES
from ..caps import BlobCapability
from ..caps import blob_copy_capability
from ..caps import blob_delete_capability
from ..caps import blob_put_capability
from ..caps import check_blob_capabilities
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
from ..listings import shallow_list_blobs
from ..stores import BlobStore
from ..stores import BlobWriter
from ..types import Blob
from ..types import BlobIfAbsent
from ..types import BlobIfMatch
from ..types import BlobIfNoneMatch
from ..types import BlobInfo
from ..types import BlobPrefix
from ..types import BlobRange
from ..types import BlobReadPrecondition
from ..types import BlobVersion
from ..types import BlobWritePrecondition
from ..types import OffsetBlobRange
from ..types import SuffixBlobRange
from .fsyncs import local_blob_fsync_dir
from .fsyncs import local_blob_fsync_fd
from .listings import local_blob_walk_files
from .listings import local_blob_walk_shallow
from .locks import LocalBlobStripedFileLocks
from .paths import local_blob_key_to_path
from .writers import LocalBlobTmpFile
from .writers import LocalBlobWriter


##


_LOCAL_BLOB_TMP_DIR_NAME = '.tmp'
_LOCAL_BLOB_LOCKS_DIR_NAME = '.locks'

_LOCAL_BLOB_MAX_COMMIT_ATTEMPTS = 8

_LOCAL_BLOB_COPY_CHUNK_SIZE = 1024 * 1024

# Errors from os.link meaning hard links are unsupported here, as opposed to the target existing or a missing parent.
_LOCAL_BLOB_LINK_UNSUPPORTED_ERRNOS = frozenset([errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EMLINK])


def _local_blob_version_of(st: os.stat_result) -> BlobVersion:
    return BlobVersion(f'{st.st_ino:x}-{st.st_mtime_ns:x}-{st.st_size:x}')


def _local_blob_last_modified_of(st: os.stat_result) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(st.st_mtime_ns / 1e9, tz=datetime.timezone.utc)


def _local_blob_clamp_range(size: int, byte_range: ta.Optional[BlobRange]) -> ta.Tuple[int, int]:
    if byte_range is None:
        return 0, size
    elif isinstance(byte_range, OffsetBlobRange):
        s = min(byte_range.start, size)
        e = size if byte_range.stop is None else min(byte_range.stop, size)
        return s, max(s, e)
    elif isinstance(byte_range, SuffixBlobRange):
        return max(0, size - byte_range.length), size
    else:
        raise TypeError(byte_range)


def _local_blob_pread_exact(fd: int, n: int, offset: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        if not (b := os.pread(fd, n - len(buf), offset + len(buf))):
            break
        buf.extend(b)
    return bytes(buf)


class LocalBlobStore(BlobStore):
    @dc.dataclass(frozen=True)
    class Config:
        no_fsync: bool = False  # tests only - never in production
        full_fsync: bool = False  # darwin: F_FULLFSYNC, which also flushes the drive's write cache
        lock_stripes: int = 256

    def __init__(self, root: str, *, config: ta.Optional['LocalBlobStore.Config'] = None) -> None:
        super().__init__()

        if config is None:
            config = LocalBlobStore.Config()

        self._root = root
        self._config = config

        self._tmp_dir = os.path.join(root, _LOCAL_BLOB_TMP_DIR_NAME)
        self._locks = LocalBlobStripedFileLocks(
            os.path.join(root, _LOCAL_BLOB_LOCKS_DIR_NAME),
            stripes=config.lock_stripes,
        )

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
        for d in (self._tmp_dir, os.path.join(self._root, _LOCAL_BLOB_LOCKS_DIR_NAME)):
            try:
                os.mkdir(d)
            except FileExistsError:
                pass
        self._dirs_ensured = True

    def _fsync_fd(self, fd: int) -> None:
        if not self._config.no_fsync:
            local_blob_fsync_fd(fd, full=self._config.full_fsync)

    def _fsync_dir(self, path: str) -> None:
        if not self._config.no_fsync:
            local_blob_fsync_dir(path, full=self._config.full_fsync)

    def _paths(self, key: str) -> ta.Tuple[ta.Sequence[str], str]:
        """Returns the chain of directory paths, root-most first, and the file path."""

        dir_names, name = local_blob_key_to_path(key)
        dirs: ta.List[str] = []
        cur = self._root
        for n in dir_names:
            cur = os.path.join(cur, n)
            dirs.append(cur)
        return dirs, os.path.join(cur, name)

    #

    def _open_file(self, key: str, path: str) -> ta.Optional[int]:
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
            version=_local_blob_version_of(st),
            last_modified=_local_blob_last_modified_of(st),
        )

    def _check_read(self, key: str, st: ta.Optional[os.stat_result], cond: ta.Optional[BlobReadPrecondition]) -> None:
        if isinstance(cond, BlobIfMatch) and (st is None or _local_blob_version_of(st) != cond.version):
            raise BlobPreconditionFailedError(key)
        if st is None:
            raise BlobNotFoundError(key)
        if isinstance(cond, BlobIfNoneMatch) and _local_blob_version_of(st) == cond.version:
            raise BlobNotModifiedError(key)

    @contextlib.contextmanager
    def _reading(self, key: str, cond: ta.Optional[BlobReadPrecondition]) -> ta.Iterator[ta.Tuple[int, os.stat_result]]:
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

    def head(self, key: str, *, cond: ta.Optional[BlobReadPrecondition] = None) -> BlobInfo:
        with self._reading(key, cond) as (_, st):
            return self._info(key, st)

    def get(
            self,
            key: str,
            *,
            byte_range: ta.Optional[BlobRange] = None,
            cond: ta.Optional[BlobReadPrecondition] = None,
    ) -> Blob:
        with self._reading(key, cond) as (fd, st):
            s, e = _local_blob_clamp_range(st.st_size, byte_range)
            return Blob(info=self._info(key, st), data=_local_blob_pread_exact(fd, e - s, s))

    #

    def list(self, *, prefix: str = '', start_after: ta.Optional[str] = None) -> ta.Iterator[BlobInfo]:
        for e in local_blob_walk_files(self._root, prefix=prefix, start_after=start_after):
            yield self._info(e.key, ta.cast(os.stat_result, e.stat))

    def list_shallow(self, *, prefix: str = '', delimiter: str = '/') -> ta.Iterator[ta.Union[BlobInfo, BlobPrefix]]:
        if delimiter != '/':
            yield from shallow_list_blobs(self.list(prefix=prefix), prefix=prefix, delimiter=delimiter)
            return
        for e in local_blob_walk_shallow(self._root, prefix=prefix):
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

    def _stat_final(self, path: str) -> ta.Optional[os.stat_result]:
        try:
            return os.stat(path, follow_symlinks=False)
        except (FileNotFoundError, NotADirectoryError):
            return None

    def _commit_into(
            self,
            tmp: LocalBlobTmpFile,
            key: str,
            path: str,
            cond: ta.Optional[BlobWritePrecondition],
    ) -> None:
        """Raises FileNotFoundError if a parent directory vanished underneath us, in which case the caller retries."""

        if isinstance(cond, BlobIfAbsent):
            try:
                os.link(tmp.path, path)
            except FileExistsError:
                raise BlobAlreadyExistsError(key) from None
            except OSError as e:
                if e.errno not in _LOCAL_BLOB_LINK_UNSUPPORTED_ERRNOS:
                    raise
                with self._locks.lock(key):
                    if os.path.lexists(path):
                        raise BlobAlreadyExistsError(key) from None
                    os.replace(tmp.path, path)
            else:
                os.unlink(tmp.path)

        elif isinstance(cond, BlobIfMatch):
            with self._locks.lock(key):
                st = self._stat_final(path)
                if st is None or _local_blob_version_of(st) != cond.version:
                    raise BlobPreconditionFailedError(key)
                os.replace(tmp.path, path)

        elif cond is None:
            with self._locks.lock(key):
                os.replace(tmp.path, path)

        else:
            raise TypeError(cond)

    def _commit(self, tmp: LocalBlobTmpFile, key: str, cond: ta.Optional[BlobWritePrecondition]) -> BlobVersion:
        try:
            dirs, path = self._paths(key)

            t = time.time_ns()
            os.utime(tmp.fd if os.utime in os.supports_fd else tmp.path, ns=(t, t))
            self._fsync_fd(tmp.fd)

            for _ in range(_LOCAL_BLOB_MAX_COMMIT_ATTEMPTS):
                if not isinstance(cond, BlobIfMatch):
                    # A BlobIfMatch target must already exist, and so must its parents.
                    self._ensure_parents(dirs)
                try:
                    self._commit_into(tmp, key, path, cond)
                except FileNotFoundError:
                    if isinstance(cond, BlobIfMatch):
                        raise BlobPreconditionFailedError(key) from None
                    # A concurrent delete pruned a parent directory between our mkdir and our commit.
                    continue
                break
            else:
                raise BlobStoreError(f'parent directories repeatedly vanished while committing {key!r}')

            self._fsync_dir(os.path.dirname(path))
            return _local_blob_version_of(os.fstat(tmp.fd))

        finally:
            tmp.discard()

    def _new_tmp(self) -> LocalBlobTmpFile:
        self._ensure_dirs()
        return LocalBlobTmpFile(self._tmp_dir)

    def _check_put(self, key: str, cond: ta.Optional[BlobWritePrecondition]) -> None:
        check_blob_key(key)
        check_blob_capabilities(self.capabilities(), blob_put_capability(cond))
        self._paths(key)

    def put(self, key: str, data: bytes, *, cond: ta.Optional[BlobWritePrecondition] = None) -> BlobVersion:
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
            length: ta.Optional[int] = None,
            cond: ta.Optional[BlobWritePrecondition] = None,
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
    def open_writer(self, key: str, *, cond: ta.Optional[BlobWritePrecondition] = None) -> ta.Iterator[BlobWriter]:
        self._check_put(key, cond)
        w = LocalBlobWriter(self._new_tmp(), lambda tmp: self._commit(tmp, key, cond))
        try:
            yield w
        finally:
            w.close()

    def _copy_into(self, src_fd: int, tmp: LocalBlobTmpFile) -> None:
        if sys.platform == 'linux':
            try:
                while os.copy_file_range(src_fd, tmp.fd, _LOCAL_BLOB_COPY_CHUNK_SIZE):
                    pass
                return
            except OSError as e:
                if e.errno not in (errno.EXDEV, errno.ENOSYS, errno.EINVAL, errno.EOPNOTSUPP):
                    raise
            # copy_file_range may have made partial progress before failing
            os.lseek(src_fd, 0, os.SEEK_SET)
            os.ftruncate(tmp.fd, 0)
            os.lseek(tmp.fd, 0, os.SEEK_SET)
        while b := os.read(src_fd, _LOCAL_BLOB_COPY_CHUNK_SIZE):
            tmp.write(b)

    def copy(self, src: str, dst: str, *, cond: ta.Optional[BlobWritePrecondition] = None) -> BlobVersion:
        check_blob_copy_keys(src, dst)
        check_blob_capabilities(self.capabilities(), blob_copy_capability(cond))
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
                    while b := os.read(src_fd, _LOCAL_BLOB_COPY_CHUNK_SIZE):
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

    def _delete(self, key: str, cond: ta.Optional[BlobIfMatch]) -> None:
        dirs, path = self._paths(key)
        self._ensure_dirs()
        with self._locks.lock(key):
            if cond is not None:
                st = self._stat_final(path)
                if st is None or _local_blob_version_of(st) != cond.version:
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

    def delete(self, key: str, *, cond: ta.Optional[BlobIfMatch] = None) -> None:
        check_blob_key(key)
        check_blob_capabilities(self.capabilities(), blob_delete_capability(cond))
        self._delete(key, cond)

    def delete_many(self, keys: ta.Iterable[str]) -> None:
        ks = [check_blob_key(k) for k in keys]
        for k in ks:
            self._paths(k)
        errors: ta.Dict[str, BlobStoreError] = {}
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
            now: ta.Optional[datetime.datetime] = None,
    ) -> int:
        """
        Removes tmp files left behind by crashed writers. A tmp file's mtime is when it was last written to, so
        older_than must comfortably exceed how long any live writer may sit idle.
        """

        if now is None:
            now = datetime.datetime.now(tz=datetime.timezone.utc)
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
