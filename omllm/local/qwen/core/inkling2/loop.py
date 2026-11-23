"""
Inkling 2's loop as entries of the model's execution order (INKLING.md, "The loop"): the looped layers appear in it
once per pass -- the same sublayers, a slot of decode state per appearance -- with these between them. Neither has
weights or state; they act on the residual stream alone (depth.py).

    layers before | LoopEntry | pass 1 | LoopRestart | pass 2 | LoopRestart | pass 3 | layers after

Every pass starts from the stream as the loop was entered. What a pass leaves for the next is its own blocks' sums:
the next pass's sublayers read their messages from those (messages.py), and from nothing older.
"""
import typing as ta

from omcore import check

from ...ops.base import Ops
from ..mixing import EmptyStateLayout
from ..mixing import Layer
from ..mixing import StateLayout
from ..mixing import StepContext
from .depth import DepthStream
from .depth import unit_rms


##


class LoopEntry(Layer):
    """Remembers the stream at the loop's entry, for the restarts."""

    def __init__(self) -> None:
        super().__init__()

        self._state = EmptyStateLayout()

    @property
    def state(self) -> StateLayout:
        return self._state

    def _enter(self, r: DepthStream) -> DepthStream:
        return r._replace(entry=(r.completed, r.partial))

    def __call__(
            self,
            ops: Ops,
            r: ta.Any,
            pos: int,
            state: ta.Any,
            ids: ta.Any = None,
    ) -> tuple[ta.Any, ta.Any]:
        return self._enter(r), ()

    def step(self, ops: Ops, r: ta.Any, ctx: StepContext, state: ta.Any) -> tuple[ta.Any, ta.Any]:
        return self._enter(r), ()


class LoopRestart(Layer):
    """
    Between two passes: the stream goes back to what the loop was entered with, and the pass just finished leaves its
    blocks' sums as the next one's message sources -- the blocks it completed past the entry's own sum, and the one it
    ended in.
    """

    def __init__(self, *, eps: float) -> None:
        super().__init__()

        self._eps = eps
        self._state = EmptyStateLayout()

    @property
    def state(self) -> StateLayout:
        return self._state

    def _restart(self, ops: Ops, r: DepthStream) -> DepthStream:
        entry = check.not_none(r.entry)
        completed, partial = entry

        return DepthStream(
            completed,
            partial,
            entry,
            (*r.completed[len(completed) + 1:], unit_rms(ops, r.partial, self._eps)),
        )

    def __call__(
            self,
            ops: Ops,
            r: ta.Any,
            pos: int,
            state: ta.Any,
            ids: ta.Any = None,
    ) -> tuple[ta.Any, ta.Any]:
        return self._restart(ops, r), ()

    def step(self, ops: Ops, r: ta.Any, ctx: StepContext, state: ta.Any) -> tuple[ta.Any, ta.Any]:
        return self._restart(ops, r), ()
