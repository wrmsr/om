# ruff: noqa: N803 N806
"""An attention layer's keys and values as decode state: their layout, and the functional form's extension of them."""
import typing as ta

from ..ops.base import Array
from ..ops.base import Ops
from .cache import FullState
from .mixing import StateLayout


##


class KvStateLayout(StateLayout):
    """
    An attention layer's KV state, in whatever format the backend keeps it (`Ops.kv_arity` arrays: bf16 (k, v), or fp8
    codes plus scales). The static decoder holds it in capacity-sized buffers that need no rollback: positions past the
    sequence are masked by `pos` and rewritten by the next step.
    """

    def __init__(self, *, num_kv_heads: int, head_dim: int) -> None:
        super().__init__()

        self._num_kv_heads = num_kv_heads
        self._head_dim = head_dim

    def arity(self, ops: Ops) -> int:
        return ops.kv_arity

    def empty(self, ops: Ops, dtype: ta.Any) -> tuple[Array, ...]:
        z = ops.zeros((1, self._num_kv_heads, 0, self._head_dim), dtype)
        return ops.kv_new(z, z)

    def adapt(self, ops: Ops, state: tuple[Array, ...], dtype: ta.Any) -> tuple[Array, ...]:
        return ops.kv_adapt(state, dtype)

    def pad(self, ops: Ops, state: tuple[Array, ...], capacity: int) -> tuple[Array, ...]:
        return ops.kv_pad(state, capacity)

    def reserve(
            self,
            ops: Ops,
            state: tuple[Array, ...],
            capacity: int,
            into: tuple[Array, ...] | None = None,
    ) -> tuple[Array, ...]:
        return ops.kv_reserve(ops.kv_adapt(state), capacity, into)  # (adapted as the functional form adapts it)

    def export(self, ops: Ops, state: tuple[Array, ...], seq_len: int) -> tuple[Array, ...]:
        return ops.kv_slice(state, seq_len)

    def commit(self, ops: Ops, state: tuple[Array, ...], n: Array, stacked: bool) -> tuple[Array, ...]:
        return state

    def capacity(self, ops: Ops, state: tuple[Array, ...]) -> int | None:
        return ops.kv_len(state)


def extend_kv(
        ops: Ops,
        state: FullState | None,
        pos: int,
        k: Array,
        v: Array,
) -> tuple[FullState, FullState, int]:
    """
    A functional KV state taken past T new positions' keys and values [B, KV, T, D] at positions pos..: the new
    state, what attention sees of it (its pos + T positions), and how many of those were there before.
    """

    T = k.shape[2]
    past = 0
    if state is None:
        state = seen = ops.kv_new(k, v)
    else:
        state = ops.kv_adapt(state)
        past = ops.kv_len(state)
        if past >= pos + T:
            # A reserved state (StateLayout.reserve): `pos` positions and room past them. The new keys and values
            # are written into the room in place, where concatenating would re-copy the whole KV into an
            # ever-larger allocation every chunk of a long prefill; attention sees the filled part.
            past = pos
            state = ops.kv_write_tokens(state, ops.scalar(pos), k, v)
            seen = ops.kv_window(state, pos + T)
        else:
            if past > pos:  # room, but not enough of it: back to an exact-length state
                past = pos
                state = ops.kv_slice(state, pos)
            state = seen = ops.kv_concat(state, k, v)

    return state, seen, past
