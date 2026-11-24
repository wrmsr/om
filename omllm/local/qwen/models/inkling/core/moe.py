# ruff: noqa: N803 N806
"""
Inkling 2's mixture of experts (INKLING.md, "Mixture of experts"): a sigmoid router -- a correction bias moves which
experts are picked, never their weights -- and experts whose gate and up activations are softcapped:

    s = sigmoid(W_r x)                               float32, over every expert
    picked = top-k of s + bias
    w = route_scale * s[picked] / sum(s[picked])     so a token's weights sum to `route_scale`, not to one
    expert(x) = W_down ((c_g tanh(g / c_g)) * sigmoid(g) * (c_u tanh(u / c_u))),  [g | u] = W_gate_up x

The sigmoid reads the gate as it is, not its capped value. There is no shared expert. The experts are stacked weights
through `Ops.expert_linear`, as Flash-Next's are (models/qwen/core/moe.py): each expert's `gate_up` [2 I, hidden] with
the gate rows first.
"""
from ....core.mixing import FeedForward
from ....ops.base import Array
from ....ops.base import Ops
from ....ops.base import Weight
from ..ops.backends import inkling2_ops


##


class Inkling2MoE(FeedForward):
    def __init__(
            self,
            *,
            router: Array,
            bias: Array,
            gate_up: Weight,
            down: Weight,
            intermediate: int,
            top_k: int,
            route_scale: float,
            gate_softcap: float,
            up_softcap: float,
    ) -> None:
        super().__init__()

        self._router = router  # [E, hidden] float32
        self._bias = bias  # [E] float32
        self._gate_up = gate_up
        self._down = down
        self._intermediate = intermediate
        self._top_k = top_k
        self._route_scale = route_scale
        self._gate_softcap = gate_softcap
        self._up_softcap = up_softcap

    def route(self, ops: Ops, x: Array) -> tuple[Array, Array]:
        """For x [N, hidden]: each token's experts [N, k] and their weights [N, k] (float32)."""

        return inkling2_ops(ops).sigmoid_route(
            ops.linear(ops.f32(x), self._router),
            self._bias,
            self._top_k,
            total=self._route_scale,
        )

    def __call__(self, ops: Ops, x: Array) -> Array:
        B, T, H = x.shape
        k = self._top_k

        x2 = ops.reshape(x, (B * T, H))
        idx, w = self.route(ops, x2)
        eids = ops.reshape(idx, (B * T * k,))  # row (token, slot)

        h = ops.expert_linear(x2, self._gate_up, eids, k)  # [N k, 2I]
        a = inkling2_ops(ops).capped_gate(h, gate_cap=self._gate_softcap, up_cap=self._up_softcap)

        y = ops.expert_linear(a, self._down, eids)  # [N k, hidden]
        y = inkling2_ops(ops).weighted_rows(ops.reshape(y, (B * T, k, H)), w, x.dtype)

        return ops.reshape(y, (B, T, H))
