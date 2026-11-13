# ruff: noqa: N803 N806
"""Flash-Next's mixture-of-experts feed-forward (transformers' Qwen4ExpTextSparseMoeBlock; FLASHNEXT.md §0, §4.1)."""
from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from .mixing import FeedForward


##


class MoE(FeedForward):
    """
    A router over `E` experts picks `k` per token -- softmax over all of them in float32, top-k, renormalised -- and
    the token's output is the weighted sum of those experts' SwiGLUs, plus a shared expert scaled by
    `sigmoid(shared_gate . x)`.

    The experts are stacked weights (Ops.expert_weights): `gate_up`, each expert's [2I, hidden] with the gate rows
    first, and `down`, [hidden, I]. Every (token, slot) row runs against its own expert through `Ops.expert_linear`:
    a gather of the selected experts in the composed reference, and on CUDA, for quantized experts, the expert GEMV
    kernel (backends/torch_triton.py) reading only the selected experts' weights. Fixed shapes either way, so it runs
    inside a captured step.
    """

    def __init__(
            self,
            *,
            router: Weight,
            gate_up: Weight,
            down: Weight,
            intermediate: int,
            shared: FeedForward,
            shared_gate: Weight,
            top_k: int,
            norm_topk: bool = True,
    ) -> None:
        super().__init__()

        self.router = router  # [E, hidden]
        self.gate_up = gate_up
        self.down = down
        self.intermediate = intermediate
        self.shared = shared
        self.shared_gate = shared_gate  # [1, hidden]
        self.top_k = top_k
        self.norm_topk = norm_topk

    def route(self, ops: Ops, x: Array) -> tuple[Array, Array]:
        """For x [N, hidden]: each token's experts [N, k] and their weights [N, k] (float32)."""

        probs = ops.softmax(ops.f32(ops.linear(x, self.router)), -1)
        w, idx = ops.topk(probs, self.top_k)
        if self.norm_topk:
            w = w / ops.sum(w, -1, keepdims=True)
        return idx, w

    def __call__(self, ops: Ops, x: Array) -> Array:
        B, T, H = x.shape
        I = self.intermediate  # noqa: E741
        k = self.top_k

        x2 = ops.reshape(x, (B * T, H))
        idx, w = self.route(ops, x2)
        eids = ops.reshape(idx, (B * T * k,))  # row (token, slot)

        h = ops.expert_linear(x2, self.gate_up, eids, k)  # [N k, 2I]
        g, u = ops.split(h, [I, I], -1)
        y = ops.expert_linear(ops.silu(g) * u, self.down, eids)  # [N k, hidden]
        y = ops.sum(ops.reshape(y, (B * T, k, H)) * ops.cast(w, y.dtype)[..., None], 1)

        y = y + self.shared(ops, x2) * ops.sigmoid(ops.linear(x2, self.shared_gate))
        return ops.reshape(y, (B, T, H))
