"""
Ordered walks of the on-disk layout. Within each directory, files sort by their segment and directories by their segment
plus '/', and since every key beneath a directory `p/` starts with `p/`, a depth-first walk in that order yields keys in
global code point order (`a` < `a-c` < `a/b`).
"""
import os
import typing as ta

from omcore import dataclasses as dc

from ..errors import InvalidBlobKeyError
from .paths import decode_name
from .paths import dir_name


##


@dc.dataclass(frozen=True)
class LocalEntry:
    key: str  # for directories, the key prefix including the trailing '/'
    path: str
    is_dir: bool
    stat: os.stat_result | None


def _scan(dir_path: str, key_prefix: str) -> list[LocalEntry]:
    try:
        it = os.scandir(dir_path)
    except (FileNotFoundError, NotADirectoryError):
        return []
    out: list[LocalEntry] = []
    with it:
        for e in it:
            if (d := decode_name(e.name)) is None:
                continue
            seg, is_dir = d
            try:
                if is_dir:
                    if not e.is_dir(follow_symlinks=False):
                        continue
                    out.append(LocalEntry(key_prefix + seg + '/', e.path, True, None))
                else:
                    if not e.is_file(follow_symlinks=False):
                        continue
                    out.append(LocalEntry(key_prefix + seg, e.path, False, e.stat(follow_symlinks=False)))
            except FileNotFoundError:
                continue
    out.sort(key=lambda le: le.key)
    return out


def _base(root: str, prefix: str) -> tuple[str, str] | None:
    """Returns the deepest directory, and its key prefix, fully determined by a listing prefix."""

    dir_segs = prefix.split('/')[:-1]
    try:
        names = [dir_name(s) for s in dir_segs]
    except InvalidBlobKeyError:
        return None
    if any(s in ('', '.', '..') for s in dir_segs):
        return None
    return os.path.join(root, *names), ''.join(s + '/' for s in dir_segs)


def walk_files(root: str, *, prefix: str = '', start_after: str | None = None) -> ta.Iterator[LocalEntry]:
    if (b := _base(root, prefix)) is None:
        return

    def rec(dir_path: str, key_prefix: str) -> ta.Iterator[LocalEntry]:
        for e in _scan(dir_path, key_prefix):
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


def has_file(dir_path: str) -> bool:
    return any(not e.is_dir or has_file(e.path) for e in _scan(dir_path, ''))


def walk_shallow(root: str, *, prefix: str = '') -> ta.Iterator[LocalEntry]:
    """
    Files directly beneath prefix's directory, and directories which contain at least one file somewhere beneath them,
    as for a '/'-delimited shallow listing.
    """

    if (b := _base(root, prefix)) is None:
        return
    for e in _scan(*b):
        if not e.key.startswith(prefix):
            continue
        if e.is_dir and not has_file(e.path):
            continue
        yield e
