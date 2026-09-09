#!/usr/bin/env python3
# @om-lite
# @om-script
# ruff: noqa: UP006 UP045
"""
inject_secret.py -- atomically upsert keys into a JSON object file, safely in the presence of concurrent invocations of
itself.

    printf '{"db_password": "%s", "legacy_token": null}' "$DB_PASSWORD" | inject_secret.py /etc/app/config.json

Stdin is a JSON object, shallowly merged into the file (which must hold a JSON object, or not exist yet): each key is
upserted wholesale -- values can be anything, but dicts and lists are replaced, never merged -- and a null value removes
the key.

Key order records modification order: keys not mentioned on stdin are written in the order they were read, followed by
every key set on stdin -- whether or not its value actually changed -- in the order they appear there. Removed keys are
simply dropped. If the result is identical to the current contents (same keys, values and order, compared by JSON
serialization, so 1, 1.0 and true are distinct) the file is not rewritten.

Output is pretty-printed with a two space indent, except that an empty object is written as exactly `{}`.

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
import collections
import errno
import fcntl
import json
import os
import random
import stat
import tempfile
import time
import typing as ta


##

# seconds
DEFAULT_TIMEOUT = 30.0

# seconds; jittered so waiters don't wake in lockstep
POLL_MIN = 0.005
POLL_MAX = 0.05

# mode for a file we create; existing files keep theirs
NEW_FILE_MODE = 0o600

JsonObject = ta.OrderedDict[str, ta.Any]  # ta.TypeAlias


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


def parse_object(text: str) -> JsonObject:
    data = json.loads(text, object_pairs_hook=collections.OrderedDict)
    if not isinstance(data, collections.OrderedDict):
        raise ValueError('top-level JSON value is not an object')  # noqa
    return data


def load(raw: bytes) -> JsonObject:
    text = raw.decode('utf-8')
    if not text.strip():
        return collections.OrderedDict()  # tolerate an empty/whitespace-only file (e.g. `touch`ed)
    return parse_object(text)


def dump(data: JsonObject) -> bytes:
    if not data:
        return b'{}'
    return (json.dumps(data, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def values_equal(a: ta.Any, b: ta.Any) -> bool:
    """Compare by JSON serialization: 1, 1.0 and true are all distinct, and key order within nested objects matters."""

    return json.dumps(a) == json.dumps(b)


def merge(
        existing: JsonObject,
        update: JsonObject,
) -> ta.Tuple[JsonObject, bool]:
    """
    Shallowly apply `update` to `existing`: a None value removes the key, any other value replaces it wholesale. Returns
    the merged object -- keys not in `update` first, in their existing order, then every key set by `update` in `update`
    order, even if its value is unchanged -- and whether the result differs from `existing` at all.
    """

    merged: JsonObject = collections.OrderedDict(
        (k, v) for k, v in existing.items() if k not in update
    )
    merged.update((k, v) for k, v in update.items() if v is not None)
    return merged, not values_equal(merged, existing)


def try_create(
        path: str,
        dirname: str,
        basename: str,
        data: JsonObject,
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


def inject_secrets(
        path: str,
        update: JsonObject,
        *,
        timeout: float = DEFAULT_TIMEOUT,
) -> None:
    path = os.path.realpath(path)  # operate on the real file if `path` is a symlink
    dirname, basename = os.path.split(path)
    deadline = time.monotonic() + timeout

    while True:
        try:
            fd = os.open(path, os.O_RDONLY)

        except FileNotFoundError:
            merged, _ = merge(collections.OrderedDict(), update)

            if try_create(
                    path,
                    dirname,
                    basename,
                    merged,
            ):
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

            try:
                existing = load(read_all(fd))
            except ValueError as e:
                raise ValueError(f'{path}: {e}') from None

            merged, changed = merge(existing, update)
            if not changed:
                return  # nothing to do; don't churn the file

            tmp = write_temp(
                dirname,
                basename,
                dump(merged),
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


def main(argv: ta.Any = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        description='Atomically upsert keys into a JSON object file; the update is a JSON object read from stdin.',
    )

    ap.add_argument(
        'file',
        help='JSON file to update (created if missing)',
    )
    ap.add_argument(
        '--timeout',
        type=float,
        default=DEFAULT_TIMEOUT,
        help='max seconds to wait for the lock (default: 30)',
    )
    ap.add_argument(
        '--description',
        help='ignored; only serves as a note in process listings and execution logs',
    )

    args = ap.parse_args(argv)

    #

    import sys

    try:
        update = parse_object(sys.stdin.buffer.read().decode('utf-8'))
    except ValueError as e:  # covers UnicodeDecodeError and json.JSONDecodeError
        print(f'error: stdin is not a JSON object: {e}', file=sys.stderr)
        return 1

    try:
        inject_secrets(
            args.file,
            update,
            timeout=args.timeout,
        )
    except TimeoutError as e:
        print(f'error: {e}', file=sys.stderr)
        return 3

    except (OSError, ValueError) as e:
        print(f'error: {e}', file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
