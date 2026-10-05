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


FILE_SUFFIX = '.file'
DIR_SUFFIX = '.dir'

NAME_MAX = 255

_HEX = '0123456789abcdef'


def _is_plain(c: str) -> bool:
    return (0x20 <= ord(c) <= 0x7e) and c != '%' and not ('A' <= c <= 'Z')


def encode_segment(seg: str) -> str:
    out: list[str] = []
    for c in seg:
        if _is_plain(c):
            out.append(c)
        else:
            out.extend(f'%{b:02x}' for b in c.encode('utf-8'))
    return ''.join(out)


def decode_segment(enc: str) -> str | None:
    """Returns None for anything that is not the canonical encoding of some segment."""

    buf = bytearray()
    i = 0
    n = len(enc)
    while i < n:
        c = enc[i]
        if c == '%':
            h = enc[i + 1:i + 3]
            if len(h) != 2 or any(x not in _HEX for x in h):
                return None
            buf.append(int(h, 16))
            i += 3
        elif _is_plain(c):
            buf.append(ord(c))
            i += 1
        else:
            return None
    try:
        seg = buf.decode('utf-8')
    except UnicodeDecodeError:
        return None
    if encode_segment(seg) != enc:
        return None
    return seg


def _checked_name(name: str, key: str) -> str:
    if len(name.encode('utf-8')) > NAME_MAX:
        raise InvalidBlobKeyError(f'key segment too long for a local filesystem: {key!r}')
    return name


def dir_name(seg: str, key: str = '') -> str:
    return _checked_name(encode_segment(seg) + DIR_SUFFIX, key or seg)


def file_name(seg: str, key: str = '') -> str:
    return _checked_name(encode_segment(seg) + FILE_SUFFIX, key or seg)


def decode_name(name: str) -> tuple[str, bool] | None:
    """Returns (segment, is_dir), or None for foreign names."""

    if name.endswith(FILE_SUFFIX):
        enc, is_dir = name[:-len(FILE_SUFFIX)], False
    elif name.endswith(DIR_SUFFIX):
        enc, is_dir = name[:-len(DIR_SUFFIX)], True
    else:
        return None
    if (seg := decode_segment(enc)) is None or seg in ('', '.', '..'):
        return None
    return seg, is_dir


def key_to_path(key: str) -> tuple[ta.Sequence[str], str]:
    """Returns the directory names and the file name for an already-validated key."""

    segs = key.split('/')
    return [dir_name(s, key) for s in segs[:-1]], file_name(segs[-1], key)
