import typing as ta

from omcore import dataclasses as dc

from ..ops.base import Array
from ..ops.base import Ops


##


@dc.dataclass()
class Snapshot:
    """
    A resumable decode state at a request boundary: what a state store keeps and a token source resumes from. The
    target's part is explicit; the draft source's part is opaque arrays only it knows how to read.
    """

    tokens: tuple[int, ...]  # the n tokens the state has processed
    cache: ta.Any  # core.cache.Cache with seq_len == n
    logits: Array  # [1, V] float32: the target's logits for position n
    hidden: Array  # [1, 1, hidden]: the target's final-normed hidden state at position n-1
    draft: tuple[Array, ...] | None  # the draft source's exported state (the MTP head's KV for entries 0..n-2), if any

    # Checkpoints: complete states at earlier positions of the same tokens, taken during the prefill that led here
    # (VerifyTokenSource's `prefill_checkpoints`). How a token source hands them to a store, which keeps them as
    # states of their own -- so they are not part of this one's `arrays`, and `map` does not carry them.
    earlier: ta.Sequence[Snapshot] = ()

    @property
    def n(self) -> int:
        return len(self.tokens)

    def arrays(self) -> list[Array]:
        out: list[Array] = [self.logits, self.hidden]
        for st in self.cache.layers:
            if st is not None:
                out.extend(st)
        if self.draft is not None:
            out.extend(self.draft)
        return out

    def map(self, fn: ta.Callable[[Array], Array]) -> Snapshot:
        """A new Snapshot with `fn` applied to every array (copy, to_host, from_host)."""

        cache = type(self.cache).__new__(type(self.cache))  # type: ignore[call-overload]
        cache.seq_len = self.cache.seq_len
        cache.layers = [None if st is None else tuple(fn(a) for a in st) for st in self.cache.layers]
        return Snapshot(
            self.tokens,
            cache,
            fn(self.logits),
            fn(self.hidden),
            None if self.draft is None else tuple(fn(a) for a in self.draft),
        )

    def nbytes(self, ops: Ops) -> int:
        return sum(ops.nbytes(a) for a in self.arrays())
