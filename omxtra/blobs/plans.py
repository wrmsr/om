"""
Sans-IO helpers splitting one large transfer into independent operations which a caller runs concurrently - in any
order, sync or async - and then finalizes. Not part of any store interface.
"""
import typing as ta

from omcore import dataclasses as dc

from .asyncs import AsyncBlobStore
from .errors import BlobStoreError
from .types import Blob
from .types import BlobInfo
from .types import BlobVersion
from .types import IfMatch
from .types import OffsetBlobRange


##


class BlobPlanError(BlobStoreError):
    """A plan was finished with missing, extra, or mismatched parts."""


@dc.dataclass(frozen=True, kw_only=True)
class ParallelGetPart:
    index: int
    byte_range: OffsetBlobRange

    @property
    def length(self) -> int:
        return (self.byte_range.stop or 0) - self.byte_range.start


@dc.dataclass(frozen=True, kw_only=True)
class ParallelGetPlan:
    key: str
    version: BlobVersion
    size: int
    parts: ta.Sequence[ParallelGetPart]


def plan_parallel_get(info: BlobInfo, *, part_size: int) -> ParallelGetPlan:
    """Plans ranged gets of a whole object, all pinned to info's version. The info comes from a head or a first get."""

    if part_size < 1:
        raise ValueError(part_size)
    return ParallelGetPlan(
        key=info.key,
        version=info.version,
        size=info.size,
        parts=[
            ParallelGetPart(index=i, byte_range=OffsetBlobRange(s, min(info.size, s + part_size)))
            for i, s in enumerate(range(0, info.size, part_size))
        ],
    )


def get_part(store: AsyncBlobStore, plan: ParallelGetPlan, part: ParallelGetPart) -> ta.Awaitable[Blob]:
    return store.get(plan.key, byte_range=part.byte_range, cond=IfMatch(plan.version))


def finish_parallel_get(plan: ParallelGetPlan, blobs: ta.Mapping[int, Blob]) -> bytes:
    if set(blobs) != {p.index for p in plan.parts}:
        raise BlobPlanError(f'parts mismatch for {plan.key!r}: {sorted(blobs)}')
    out: list[bytes] = []
    for p in plan.parts:
        b = blobs[p.index]
        if b.info.version != plan.version or len(b.data) != p.length:
            raise BlobPlanError(f'part {p.index} of {plan.key!r} does not match the plan')
        out.append(b.data)
    return b''.join(out)
