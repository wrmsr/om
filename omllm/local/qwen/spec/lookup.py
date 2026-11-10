import typing as ta

from omcore import check

from ..decode.drafts import DraftSource
from ..decode.drafts import point_drafts
from ..decode.generation import Generation
from ..decode.rounds import Drafts
from ..decode.rounds import Round
from ..decode.state import Snapshot
from ..ops.base import Array
from ..ops.base import Ops


##


class LookupDraftSource(DraftSource):
    """
    Prompt-lookup drafting (NEXT.md 1.1): when the last `ngram` tokens -- the pending one included -- occurred earlier
    in the context, the tokens that followed them there are the draft. Free to produce, and accepted most of the time on
    the spans an agent copies: a file rewritten after a small edit, a quoted function, an echoed tool result. When
    nothing matches, it asks the source it wraps (the MTP head, or no drafts on a model without one).

    Drafts are point masses (decode/drafts.py point_drafts): the output distribution is unchanged. It always proposes
    `k` drafts, at least as many as the source it wraps would, padding a short continuation with its last token, so a
    lookup round has one verify shape. A `k` above the wrapped source's buys longer copied runs at the price of a
    second verify shape (and, over the MTP head, a second refresh shape); the decode attention kernel bounds it (5.1 of
    UNTANGLING.md: G * (k + 1) <= 32, so k <= 4 on the 27B, k <= 7 on qwen3.5:4b).
    """

    def __init__(
            self,
            ops: Ops,
            *,
            vocab_size: int,
            wrapped: DraftSource,
            ngram: int = 3,
            k: int = 3,
    ) -> None:
        super().__init__()

        if ngram < 1:
            raise ValueError(f'ngram must be >= 1, got {ngram}')

        self._ops = ops
        self._vocab_size = vocab_size
        self._wrapped = wrapped
        self._ngram = ngram
        self._k = max(k, wrapped.max_drafts)

        self._ids: list[int] = []  # the committed ids, as indexed
        self._index: dict[tuple[int, ...], int] = {}  # n-gram -> the position just after its latest occurrence

        self.hits = 0  # rounds drafted by lookup rather than by the wrapped source

    def _extend(self, ids: ta.Sequence[int]) -> None:
        n = self._ngram
        base = self._ids
        for t in ids:
            base.append(int(t))
            if len(base) >= n:
                self._index[tuple(base[-n:])] = len(base)

    def _lookup(self, tail: tuple[int, ...]) -> list[int] | None:
        at = self._index.get(tail)
        if at is None or at >= len(self._ids):
            return None
        cont = self._ids[at:at + self._k]
        return cont + [cont[-1]] * (self._k - len(cont))

    # DraftSource

    @property
    def max_drafts(self) -> int:
        return self._k

    def accepts(self, resume: Snapshot) -> bool:
        return self._wrapped.accepts(resume)

    def start(
            self,
            gen: Generation,
            *,
            hidden: Array,
            start: int,
            tokens: ta.Sequence[int],
            state: tuple[Array, ...] | None,
    ) -> None:
        self._ids = []
        self._index = {}
        self._extend(gen.prompt)
        self._wrapped.start(
            gen,
            hidden=hidden,
            start=start,
            tokens=tokens,
            state=state,
        )

    def propose(self, gen: Generation) -> Drafts | None:
        # the pending token is not committed yet, so the tail's own n-gram is not in the index: a match is earlier
        n = self._ngram
        tail = (*self._ids[max(0, len(self._ids) - n + 1):], check.not_none(gen.pending))
        toks = self._lookup(tail) if len(tail) == n else None
        if toks is None:
            return self._wrapped.propose(gen)

        self.hits += 1
        return point_drafts(self._ops, self._vocab_size, toks)

    def on_commit(self, gen: Generation, rnd: Round, n: int) -> None:
        self._extend(rnd.tokens[:n])
        self._wrapped.on_commit(gen, rnd, n)

    def export(self, gen: Generation) -> tuple[Array, ...] | None:
        return self._wrapped.export(gen)
