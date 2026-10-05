import heapq
import typing as ta

from .records import LsmRecord


##


async def merge_newest_wins(sources: ta.Sequence[ta.AsyncIterator[LsmRecord]]) -> ta.AsyncIterator[LsmRecord]:
    """
    Merges sorted sources, ordered newest first, into one sorted stream holding only the newest record for each key.
    Tombstones are passed through - callers drop them as appropriate.
    """

    heap: list[tuple[bytes, int, LsmRecord]] = []
    for rank, src in enumerate(sources):
        if (r := await anext(src, None)) is not None:
            heapq.heappush(heap, (r.key, rank, r))

    last: bytes | None = None
    while heap:
        key, rank, rec = heapq.heappop(heap)
        if (nxt := await anext(sources[rank], None)) is not None:
            if nxt.key <= key:
                raise ValueError(f'source {rank} is not strictly increasing: {nxt.key!r} after {key!r}')
            heapq.heappush(heap, (nxt.key, rank, nxt))
        if key == last:
            continue
        last = key
        yield rec


async def drop_tombstones(records: ta.AsyncIterator[LsmRecord]) -> ta.AsyncIterator[LsmRecord]:
    async for r in records:
        if r.value is not None:
            yield r
