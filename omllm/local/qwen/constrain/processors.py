import typing as ta

from ..decode.generation import Generation
from ..decode.processors import Contribution
from ..decode.processors import LogitProcessor
from ..ops.base import Array
from ..ops.base import Ops
from .grammar import JsonConstraint
from .grammar import MaskCache
from .grammar import ToolConstraint


##


class GrammarProcessor(LogitProcessor):
    """
    A grammar controller (tool calls, JSON mode) as a logit processor: each row's mask is the set of tokens that keep
    the text a valid prefix. Verify rows get the masks for their own positions by looking ahead on a clone of the
    controller fed the drafts before them -- which needs the drafts on the host, the one extra read of a constrained
    round. A draft that breaks the grammar has zero target probability at its row and is rejected there; rows past it
    are never committed.
    """

    def __init__(
            self,
            ops: Ops,
            *,
            vocab_size: int,
            constraint: ToolConstraint | JsonConstraint,
    ) -> None:
        super().__init__()

        self._ops = ops
        self._constraint = constraint
        self._masks = MaskCache(ops, vocab_size)  # allocates nothing until handed a real set

    def rows(self, gen: Generation, drafts: Array | None, n_rows: int) -> Contribution:
        cons = self._constraint

        if n_rows == 1:
            m = self._masks.mask(cons.allowed())
            return Contribution(mask=None if m is None else m[None, :])

        drafts_h = self._ops.numpy(drafts).tolist()[:n_rows - 1]
        look = cons.clone()
        sets: list[ta.Any] = [look.allowed()]
        for d in drafts_h:
            if sets[-1] is not None and d not in sets[-1]:
                sets.extend([sets[-1]] * (n_rows - len(sets)))  # rows past a violation are never committed
                break
            look.feed(d)
            sets.append(look.allowed())

        return Contribution(mask=self._masks.rows(sets[:n_rows]))

    def after(self, gen: Generation, tokens: ta.Sequence[int], arr: Array) -> None:
        for t in tokens:
            self._constraint.feed(t)
