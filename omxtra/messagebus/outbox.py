import collections
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .types import Message
from .types import OutgoingMessage
from .types import WorkerId


##


@dc.dataclass(frozen=True)
class Batch:
    messages: tuple[Message, ...]

    # The complete seqs map as it will stand once this batch commits - the whole thing, since the row is rewritten.
    seqs_after: ta.Mapping[WorkerId, int]

    @property
    def dst_ids(self) -> ta.AbstractSet[WorkerId]:
        return {m.dst_id for m in self.messages}


class Outbox:
    """
    Owns the per-dst seq counters. Everything but `enqueue` runs on the loop thread.

    Seqs advance in memory only after the batch that used them commits, and they're written to the worker row in that
    same transaction. So after any reconnect the row says exactly whether an in-flight batch landed, and it can be
    dropped or retried with certainty - no dedup needed on the far side.
    """

    def __init__(self, src_id: WorkerId) -> None:
        super().__init__()

        self._src_id = src_id

        self._pending: collections.deque[OutgoingMessage] = collections.deque()  # append / popleft are atomic
        self._seqs: dict[WorkerId, int] = {}
        self._inflight: Batch | None = None

    def enqueue(self, msg: OutgoingMessage) -> None:
        self._pending.append(msg)

    def has_pending(self) -> bool:
        return bool(self._pending)

    def reconcile(self, loaded: ta.Mapping[WorkerId, int]) -> None:
        self._seqs = dict(loaded)

        if (b := self._inflight) is None:
            return
        self._inflight = None

        if all(loaded.get(d, 0) >= b.seqs_after[d] for d in b.dst_ids):
            return  # it committed before the connection died

        # It didn't. Back to the head so per-dst ordering holds; take_batch will re-sequence it from `loaded`.
        self._pending.extendleft(OutgoingMessage(m.dst_id, m.payload) for m in reversed(b.messages))

    def take_batch(self, max_size: int) -> Batch:
        check.none(self._inflight)

        seqs = dict(self._seqs)
        msgs: list[Message] = []
        while self._pending and len(msgs) < max_size:
            om = self._pending.popleft()
            seqs[om.dst_id] = seq = seqs.get(om.dst_id, 0) + 1
            msgs.append(Message(om.dst_id, self._src_id, seq, om.payload))

        b = Batch(tuple(msgs), seqs)
        self._inflight = b
        return b

    def commit(self, batch: Batch) -> None:
        check.state(batch is self._inflight)

        self._seqs = dict(batch.seqs_after)
        self._inflight = None
