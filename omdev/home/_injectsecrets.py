#!/usr/bin/env python3
# @om-lite
# @om-script
# ruff: noqa: UP006 UP045
"""
inject_secret.py -- atomically set one top-level key in a JSON object file, safely in the presence of concurrent
invocations of itself.

    printf '%s' "$DB_PASSWORD" | inject_secret.py /etc/app/config.json db_password

Guarantees (Linux only; needs nothing newer than flock(2), link(2), rename(2)):

  * Nobody ever observes a partial, empty or invalid file at the path. The path is only ever populated by link(2)
    (create) or rename(2) (replace) of a fully written and fsync'd temp file in the same directory.
  * Concurrent invocations never lose each other's updates, whether or not the file exists beforehand.

How the lock and the atomic replace are combined:

  flock(2) locks an *inode*, not a path, and rename(2) swaps the inode behind the path. A writer that holds the lock on
  the old inode and renames a new file into place therefore leaves waiters holding a lock on a stale inode. The fix:
  after acquiring the lock, compare fstat(fd) with stat(path); if they differ, release and start over against the
  current file. Every replacement is performed by the holder of the lock on the inode currently at the path, so writers
  are fully serialized.

  Creation: rename(2) clobbers unconditionally, so bootstrapping via rename could overwrite a file a concurrent writer
  just populated. link(2) fails with EEXIST if the target exists, so it is the atomic create-if-absent.

Exit status: 0 ok, 1 error, 2 usage, 3 lock timeout.
"""
import argparse
import errno
import fcntl
import json
import os
import random
import stat
import sys
import tempfile
import time
import typing as ta


##


# seconds; jittered so waiters don't wake in lockstep
POLL_MIN = 0.005
POLL_MAX = 0.05

# mode for a file we create; existing files keep theirs
NEW_FILE_MODE = 0o600


def write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        view = view[os.write(fd, view):]


def read_all(fd: int) -> bytes:
    chunks: ta.List[bytes] = []
    while True:
        chunk = os.read(fd, 1 << 16)
        if not chunk:
            return b''.join(chunks)
        chunks.append(chunk)


def fsync_dir(dirname: str) -> None:
    """Persist the directory entry (the link/rename itself) after a crash."""

    fd = os.open(dirname, os.O_RDONLY)
    try:
        os.fsync(fd)
    except OSError:
        pass  # some filesystems refuse fsync on directories; not fatal
    finally:
        os.close(fd)


def write_temp(
        dirname: str,
        basename: str,
        data: bytes,
        mode: int,
        *,
        uid_gid: ta.Optional[ta.Tuple[int, int]] = None,
) -> str:
    """Write data to a fresh, fsync'd temp file next to the target. Returns its path."""

    fd, tmp = tempfile.mkstemp(prefix='.' + basename + '.', suffix='.tmp', dir=dirname)
    try:
        if uid_gid is not None:
            uid, gid = uid_gid
            try:
                os.fchown(fd, uid, gid)
            except PermissionError:
                pass  # not root; the file keeps our ownership
        os.fchmod(fd, mode)
        write_all(fd, data)
        os.fsync(fd)
    except BaseException:
        os.close(fd)
        os.unlink(tmp)
        raise
    os.close(fd)
    return tmp


def load(raw: bytes) -> ta.Any:
    text = raw.decode('utf-8')
    if not text.strip():
        return {}  # tolerate an empty/whitespace-only file (e.g. `touch`ed)
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError('top-level JSON value is not an object')  # noqa
    return data


def dump(data: ta.Any) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def try_create(
        path: str,
        dirname: str,
        basename: str,
        data: ta.Any,
) -> bool:
    """Atomically create `path` with `data` iff it does not exist. True on success."""

    tmp = write_temp(
        dirname,
        basename,
        dump(data),
        NEW_FILE_MODE,
    )
    try:
        os.link(tmp, path)
    except FileExistsError:
        return False  # someone beat us to it; caller will lock and update that file
    except OSError as e:
        if e.errno in (errno.EPERM, errno.EOPNOTSUPP, errno.EXDEV, errno.EMLINK):
            raise OSError(
                e.errno,
                f'filesystem does not allow hard links, which are needed to create the file atomically: {e.strerror}',
                path,
            ) from None
        raise
    finally:
        os.unlink(tmp)
    fsync_dir(dirname)
    return True


def inject(
        path: str,
        key: str,
        value: str,
        timeout: float,
) -> None:
    path = os.path.realpath(path)  # operate on the real file if `path` is a symlink
    dirname, basename = os.path.split(path)
    deadline = time.monotonic() + timeout

    while True:
        try:
            fd = os.open(path, os.O_RDONLY)
        except FileNotFoundError:
            if try_create(path, dirname, basename, {key: value}):
                return
            continue  # lost the create race; lock whatever exists now

        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(f'timed out waiting for lock on {path}') from None
                time.sleep(random.uniform(POLL_MIN, POLL_MAX))
                continue

            # We hold a lock on *an* inode. Make sure it is still the one at `path`: a concurrent writer may have
            # rename()d a new file over it while we waited.
            st = os.fstat(fd)
            try:
                cur = os.stat(path)
            except FileNotFoundError:
                continue  # deleted underneath us; go recreate
            if (st.st_dev, st.st_ino) != (cur.st_dev, cur.st_ino):
                continue  # stale inode; retry against the current file
            if not stat.S_ISREG(st.st_mode):
                raise OSError(errno.EINVAL, 'not a regular file', path)

            data = load(read_all(fd))
            if key in data and data[key] == value:
                return  # already set; don't churn the file
            data[key] = value

            tmp = write_temp(
                dirname,
                basename,
                dump(data),
                stat.S_IMODE(st.st_mode),
                uid_gid=(st.st_uid, st.st_gid),
            )
            try:
                os.rename(tmp, path)  # atomic replace, done while holding the lock
            except BaseException:
                os.unlink(tmp)
                raise
            fsync_dir(dirname)
            return
        finally:
            os.close(fd)  # releases the flock


def main(argv: ta.Any = None) -> None:
    ap = argparse.ArgumentParser(
        description='Atomically set a top-level key in a JSON file; value is read from stdin.',
    )
    ap.add_argument(
        'file',
        help='JSON file to update (created if missing)',
    )
    ap.add_argument(
        'key',
        help='top-level key to set',
    )
    ap.add_argument(
        '--timeout',
        type=float,
        default=30.0,
        help='max seconds to wait for the lock (default: 30)',
    )
    ap.add_argument(
        '--raw',
        action='store_true',
        help='keep a trailing newline on the value (default: strip one)',
    )
    args = ap.parse_args(argv)

    try:
        value = sys.stdin.buffer.read().decode('utf-8')
    except UnicodeDecodeError as e:
        print(f'error: value on stdin is not valid UTF-8: {e}', file=sys.stderr)
        return 1
    if not args.raw:
        if value.endswith('\r\n'):
            value = value[:-2]
        elif value.endswith('\n'):
            value = value[:-1]

    try:
        inject(args.file, args.key, value, args.timeout)
    except TimeoutError as e:
        print(f'error: {e}', file=sys.stderr)
        return 3
    except (OSError, ValueError) as e:
        print(f'error: {e}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
