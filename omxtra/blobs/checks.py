# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta

from .errors import BlobStreamLengthError
from .keys import check_blob_key


##


def check_blob_copy_keys(src: str, dst: str) -> None:
    check_blob_key(src)
    check_blob_key(dst)
    if src == dst:
        raise ValueError(f'cannot copy a blob onto itself: {src!r}')


def check_blob_stream_length(actual: int, expected: ta.Optional[int]) -> None:
    if expected is not None and actual != expected:
        raise BlobStreamLengthError(f'expected {expected} bytes, got {actual}')
