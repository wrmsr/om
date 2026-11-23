# ruff: noqa: N803 N806
"""
Inkling 2's mixture of experts (INKLING.md, "Mixture of experts"): a sigmoid router -- a correction bias moves which
experts are picked, never their weights -- and experts whose gate and up activations are softcapped:

    s = sigmoid(W_r x)                               float32, over every expert
    picked = top-k of s + bias
    w = route_scale * s[picked] / sum(s[picked])     so a token's weights sum to `route_scale`, not to one
    expert(x) = W_down ((c_g tanh(g / c_g)) * sigmoid(g) * (c_u tanh(u / c_u))),  [g | u] = W_gate_up x

The sigmoid reads the gate as it is, not its capped value. There is no shared expert. The experts are stacked weights
through `Ops.expert_linear`, as Flash-Next's are (core/moe.py): each expert's `gate_up` [2 I, hidden] with the gate
rows first.
"""
from ...ops.base import Array
from ...ops.base import Ops
from ...ops.base import Weight
from ..mixing import FeedForward


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

        f32 = ops.dtype('f32')

        scores = ops.sigmoid(ops.linear(ops.f32(x), self._router))  # [N, E]
        _, idx = ops.topk(scores + self._bias, self._top_k)

        # the picked experts' own scores (not the biased ones the pick was made on): a one-hot sum, exact
        picked = ops.cast(idx[..., None] == ops.arange(int(scores.shape[-1])), f32)  # [N, k, E]
        sel = ops.sum(scores[:, None, :] * picked, -1)

        return idx, sel * (self._route_scale / (ops.sum(sel, -1, keepdims=True) + 1e-20))

    def __call__(self, ops: Ops, x: Array) -> Array:
        B, T, H = x.shape
        I = self._intermediate  # noqa: E741
        k = self._top_k
        cg = self._gate_softcap
        cu = self._up_softcap

        x2 = ops.reshape(x, (B * T, H))
        idx, w = self.route(ops, x2)
        eids = ops.reshape(idx, (B * T * k,))  # row (token, slot)

        h = ops.expert_linear(x2, self._gate_up, eids, k)  # [N k, 2I]
        g, u = ops.split(ops.f32(h), [I, I], -1)
        a = (ops.tanh(g / cg) * cg) * ops.sigmoid(g) * (ops.tanh(u / cu) * cu)

        y = ops.f32(ops.expert_linear(ops.cast(a, h.dtype), self._down, eids))  # [N k, hidden]
        y = ops.sum(ops.reshape(y, (B * T, k, H)) * w[..., None], 1)

        return ops.reshape(ops.cast(y, x.dtype), (B, T, H))
