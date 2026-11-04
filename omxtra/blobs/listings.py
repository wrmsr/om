# ruff: noqa: UP006 UP007 UP045
# @om-lite
import typing as ta

from omcore.lite.check import check

from .types import BlobInfo
from .types import BlobPrefix


##


def shallow_list_blobs(
        infos: ta.Iterable[BlobInfo],
        *,
        prefix: str,
        delimiter: str,
) -> ta.Iterator[ta.Union[BlobInfo, BlobPrefix]]:
    """Folds an ordered deep listing of keys under prefix into S3-style common prefixes."""

    check.non_empty_str(delimiter)
    last: ta.Optional[str] = None
    for info in infos:
        if not info.key.startswith(prefix):
            continue
        if (i := info.key.find(delimiter, len(prefix))) < 0:
            yield info
        elif (p := info.key[:i + len(delimiter)]) != last:
            # Keys sharing a prefix are contiguous in sorted order, so one lookbehind suffices.
            last = p
            yield BlobPrefix(p)
