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


class OracleDraftSource(DraftSource):
    """
    Drafts from a function of the committed ids: `fn(ids, k) -> tokens` gives the drafts that follow `ids` (prompt +
    emitted + the pending token), as point masses (q one-hot, so the target accepts exactly the drafts it would have
    sampled). Feeding it a reference transcript, possibly corrupted at chosen positions, forces full rounds and every
    rejection position -- what the synthetic model's random draft head almost never produces. Also the shape of prompt
    lookup drafting: a function of the ids.
    """

    def __init__(
            self,
            ops: Ops,
            *,
            vocab_size: int,
            k: int,
            fn: ta.Callable[[ta.Sequence[int], int], ta.Sequence[int]],
    ) -> None:
        super().__init__()

        self._ops = ops
        self._vocab_size = vocab_size
        self._k = k
        self._fn = fn

    @property
    def max_drafts(self) -> int:
        return self._k

    def accepts(self, resume: Snapshot) -> bool:
        return True

    def start(
            self,
            gen: Generation,
            *,
            hidden: Array,
            start: int,
            tokens: ta.Sequence[int],
            state: tuple[Array, ...] | None,
    ) -> None:
        pass

    def propose(self, gen: Generation) -> Drafts | None:
        k = self._k
        toks = [int(t) for t in self._fn([*gen.ids, check.not_none(gen.pending)], k)][:k]
        if not toks:
            return None

        return point_drafts(self._ops, self._vocab_size, toks)

    def on_commit(self, gen: Generation, rnd: Round, n: int) -> None:
        pass

    def export(self, gen: Generation) -> tuple[Array, ...] | None:
        return None
