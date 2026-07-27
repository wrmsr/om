# ruff: noqa: UP006 UP045
# @om-lite
import typing as ta

from ...lite.abstract import Abstract
from .types import ByteStreamBufferLike


##


class BaseByteStreamBufferLike(ByteStreamBufferLike, Abstract):
    def _norm_slice(self, start: int, end: ta.Optional[int]) -> ta.Tuple[int, int]:
        if start == 0 and end is None:
            # The overwhelmingly common case - skip slice.indices().
            return 0, len(self)
        s, e, _ = slice(start, end, 1).indices(len(self))
        return (s, s) if e < s else (s, e)
