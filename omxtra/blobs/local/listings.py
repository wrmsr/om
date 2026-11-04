# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
Ordered walks of the on-disk layout. Within each directory, files sort by their segment and directories by their segment
plus '/', and since every key beneath a directory `p/` starts with `p/`, a depth-first walk in that order yields keys in
global code point order (`a` < `a-c` < `a/b`).
"""
import dataclasses as dc
import os
import typing as ta

from ..errors import InvalidBlobKeyError
from .paths import local_blob_decode_name
from .paths import local_blob_dir_name


##


@dc.dataclass(frozen=True)
class LocalBlobEntry:
    key: str  # for directories, the key prefix including the trailing '/'
    path: str
    is_dir: bool
    stat: ta.Optional[os.stat_result]


def _local_blob_scan(dir_path: str, key_prefix: str) -> ta.List[LocalBlobEntry]:
    try:
        it = os.scandir(dir_path)
    except (FileNotFoundError, NotADirectoryError):
        return []
    out: ta.List[LocalBlobEntry] = []
    with it:
        for e in it:
            if (d := local_blob_decode_name(e.name)) is None:
                continue
            seg, is_dir = d
            try:
                if is_dir:
                    if not e.is_dir(follow_symlinks=False):
                        continue
                    out.append(LocalBlobEntry(key_prefix + seg + '/', e.path, True, None))
                else:
                    if not e.is_file(follow_symlinks=False):
                        continue
                    out.append(LocalBlobEntry(key_prefix + seg, e.path, False, e.stat(follow_symlinks=False)))
            except FileNotFoundError:
                continue
    out.sort(key=lambda le: le.key)
    return out


def _local_blob_base(root: str, prefix: str) -> ta.Optional[ta.Tuple[str, str]]:
    """Returns the deepest directory, and its key prefix, fully determined by a listing prefix."""

    dir_segs = prefix.split('/')[:-1]
    try:
        names = [local_blob_dir_name(s) for s in dir_segs]
    except InvalidBlobKeyError:
        return None
    if any(s in ('', '.', '..') for s in dir_segs):
        return None
    return os.path.join(root, *names), ''.join(s + '/' for s in dir_segs)


def local_blob_walk_files(
        root: str,
        *,
        prefix: str = '',
        start_after: ta.Optional[str] = None,
) -> ta.Iterator[LocalBlobEntry]:
    if (b := _local_blob_base(root, prefix)) is None:
        return

    def rec(dir_path: str, key_prefix: str) -> ta.Iterator[LocalBlobEntry]:
        for e in _local_blob_scan(dir_path, key_prefix):
            if e.is_dir:
                if not (e.key.startswith(prefix) or prefix.startswith(e.key)):
                    continue
                if start_after is not None and start_after > e.key and not start_after.startswith(e.key):
                    # Every key beneath e is less than start_after.
                    continue
                yield from rec(e.path, e.key)
            else:
                if not e.key.startswith(prefix):
                    continue
                if start_after is not None and e.key <= start_after:
                    continue
                yield e

    yield from rec(*b)


def local_blob_has_file(dir_path: str) -> bool:
    return any(not e.is_dir or local_blob_has_file(e.path) for e in _local_blob_scan(dir_path, ''))


def local_blob_walk_shallow(root: str, *, prefix: str = '') -> ta.Iterator[LocalBlobEntry]:
    """
    Files directly beneath prefix's directory, and directories which contain at least one file somewhere beneath them,
    as for a '/'-delimited shallow listing.
    """

    if (b := _local_blob_base(root, prefix)) is None:
        return
    for e in _local_blob_scan(*b):
        if not e.key.startswith(prefix):
            continue
        if e.is_dir and not local_blob_has_file(e.path):
            continue
        yield e
