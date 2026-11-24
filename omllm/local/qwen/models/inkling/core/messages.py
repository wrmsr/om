# ruff: noqa: N803 N806
"""
Messages across the loop's passes (INKLING.md, "The loop"): from its second pass on, each of a looped layer's inputs
-- its attention's query, key and value inputs, its feed-forward's -- is blended with a message read from the block
sums the previous pass left, by a query of that input's own:

    u = [rms(x) | rms(m)]                     x the input as the stream gave it, m its message
    z = W_down u                              rank `loop_gate_rank`
    x' = (1 - tanh(W_forget z)) x + tanh(W_gain z) m

Gates by tanh, so not a convex blend. The two gate projections and the blend are float32.
"""
import typing as ta

from ....ops.base import Array
from ....ops.base import Ops
from ....ops.base import Weight
from ..ops.backends import inkling2_ops


##


class MessageGate:
    def __init__(
            self,
            *,
            down: Weight,
            forget: Array,
            gain: Array,
            eps: float,
            dtype: ta.Any,
    ) -> None:
        super().__init__()

        self._down = down  # [rank, 2 hidden], in the model's dtype
        self._forget = forget  # [hidden, rank] float32
        self._gain = gain
        self._eps = eps
        self._dtype = dtype

    def __call__(self, ops: Ops, x: Array, m: Array) -> Array:
        """x, m: [B, T, hidden] float32 -> the blend, float32."""

        return inkling2_ops(ops).bottleneck_blend(
            x,
            m,
            self._down,
            self._forget,
            self._gain,
            eps=self._eps,
            dtype=self._dtype,
        )


class MessageReader:
    """
    One connection's messages: a query and a gate per input it hands its sublayer. `read` blends each input with its
    message from the previous pass's block sums.
    """

    def __init__(self, *, queries: Array, gates: ta.Sequence[MessageGate]) -> None:
        super().__init__()

        if int(queries.shape[0]) != len(gates):
            raise ValueError('a message query per gate')

        self._queries = queries  # [n, hidden] float32
        self._gates = list(gates)

    def __len__(self) -> int:
        return len(self._gates)

    def read(self, ops: Ops, sources: ta.Sequence[Array], xs: ta.Sequence[Array]) -> list[Array]:
        """`xs`: the inputs, one per gate -- or one for all of them."""

        m = inkling2_ops(ops).depth_mix(self._queries, sources)  # [B, T, n, hidden]
        return [
            gate(ops, xs[i if len(xs) > 1 else 0], m[:, :, i])
            for i, gate in enumerate(self._gates)
        ]
