# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
Mapping between blob keys and on-disk paths. Every key segment but the last becomes a `<enc>.dir` directory, and the
last becomes a `<enc>.file` file, so keys `a/b` and `a/b/c` can coexist. Segments are escaped unconditionally to pure
lowercase ASCII so that case- and normalization-insensitive filesystems can never merge distinct keys: `%`, `A`-`Z`,
control characters, and all non-ASCII characters become lowercase `%xx` of their UTF-8 bytes. Names which end in neither
suffix, or which do not decode canonically, are foreign and ignored.
"""
import typing as ta

from ..errors import InvalidBlobKeyError


##


LOCAL_BLOB_FILE_SUFFIX = '.file'
LOCAL_BLOB_DIR_SUFFIX = '.dir'

LOCAL_BLOB_NAME_MAX = 255

_LOCAL_BLOB_HEX = '0123456789abcdef'


def _local_blob_is_plain(c: str) -> bool:
    return (0x20 <= ord(c) <= 0x7e) and c != '%' and not ('A' <= c <= 'Z')


def local_blob_encode_segment(seg: str) -> str:
    out: ta.List[str] = []
    for c in seg:
        if _local_blob_is_plain(c):
            out.append(c)
        else:
            out.extend(f'%{b:02x}' for b in c.encode('utf-8'))
    return ''.join(out)


def local_blob_decode_segment(enc: str) -> ta.Optional[str]:
    """Returns None for anything that is not the canonical encoding of some segment."""

    buf = bytearray()
    i = 0
    n = len(enc)
    while i < n:
        c = enc[i]
        if c == '%':
            h = enc[i + 1:i + 3]
            if len(h) != 2 or any(x not in _LOCAL_BLOB_HEX for x in h):
                return None
            buf.append(int(h, 16))
            i += 3
        elif _local_blob_is_plain(c):
            buf.append(ord(c))
            i += 1
        else:
            return None
    try:
        seg = buf.decode('utf-8')
    except UnicodeDecodeError:
        return None
    if local_blob_encode_segment(seg) != enc:
        return None
    return seg


def _local_blob_checked_name(name: str, key: str) -> str:
    if len(name.encode('utf-8')) > LOCAL_BLOB_NAME_MAX:
        raise InvalidBlobKeyError(f'key segment too long for a local filesystem: {key!r}')
    return name


def local_blob_dir_name(seg: str, key: str = '') -> str:
    return _local_blob_checked_name(local_blob_encode_segment(seg) + LOCAL_BLOB_DIR_SUFFIX, key or seg)


def local_blob_file_name(seg: str, key: str = '') -> str:
    return _local_blob_checked_name(local_blob_encode_segment(seg) + LOCAL_BLOB_FILE_SUFFIX, key or seg)


def local_blob_decode_name(name: str) -> ta.Optional[ta.Tuple[str, bool]]:
    """Returns (segment, is_dir), or None for foreign names."""

    if name.endswith(LOCAL_BLOB_FILE_SUFFIX):
        enc, is_dir = name[:-len(LOCAL_BLOB_FILE_SUFFIX)], False
    elif name.endswith(LOCAL_BLOB_DIR_SUFFIX):
        enc, is_dir = name[:-len(LOCAL_BLOB_DIR_SUFFIX)], True
    else:
        return None
    if (seg := local_blob_decode_segment(enc)) is None or seg in ('', '.', '..'):
        return None
    return seg, is_dir


def local_blob_key_to_path(key: str) -> ta.Tuple[ta.Sequence[str], str]:
    """Returns the directory names and the file name for an already-validated key."""

    segs = key.split('/')
    return [local_blob_dir_name(s, key) for s in segs[:-1]], local_blob_file_name(segs[-1], key)
