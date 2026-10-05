from .errors import InvalidBlobKeyError


##


MAX_BLOB_KEY_BYTES = 1024

# Not representable in XML 1.0, and so not listable by S3 without url encoding.
_XML_INVALID_CHARS = frozenset(['\ufffe', '\uffff'])


def check_blob_key(key: str) -> str:
    """
    Keys are the intersection of what S3, R2, a POSIX filesystem, and XML 1.0 can all represent: non-empty, at most 1024
    UTF-8 bytes, no control characters or XML-invalid characters, and '/'-separated segments which are neither empty
    nor '.' or '..'.
    """

    try:
        n = len(key.encode('utf-8'))
    except UnicodeEncodeError:
        raise InvalidBlobKeyError(key) from None
    if not 0 < n <= MAX_BLOB_KEY_BYTES:
        raise InvalidBlobKeyError(key)
    if any(ord(c) < 0x20 or c == '\x7f' or c in _XML_INVALID_CHARS for c in key):
        raise InvalidBlobKeyError(key)
    if any(s in ('', '.', '..') for s in key.split('/')):
        raise InvalidBlobKeyError(key)
    return key
