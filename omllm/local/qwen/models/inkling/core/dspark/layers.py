# ruff: noqa: N806
import typing as ta

from .....ops.base import Array
from .....ops.base import Ops
from .....ops.base import Weight
from ...ops.backends import inkling2_ops
from .config import DsparkConfig
from .memory import DsparkContext


##


class DsparkSpan(ta.NamedTuple):
    """
    The past a layer's block attends: keys and values [1, KV, L, D] and the stretch lo <= index < hi of them that is
    seen (0-d int arrays), with ar = arange(L). A plain tuple: it is built inside captured steps.
    """

    k: Array
    v: Array
    lo: Array
    hi: Array
    ar: Array


class DsparkLayer:
    """
    One layer of a DSpark drafter over a block's slots: pre-norm grouped-query attention -- queries and keys normed
    per head and rotated, every slot seeing the layer's span of the past and every slot of the block, later ones
    included -- then a pre-norm SwiGLU. The residual is carried in float32.
    """

    def __init__(
            self,
            *,
            cfg: DsparkConfig,
            context: DsparkContext,
            window: int | None,
            attn_norm: Array,
            q: Weight,
            k: Weight,
            v: Weight,
            q_norm: Array,
            k_norm: Array,
            o: Weight,
            mlp_norm: Array,
            gate: Weight,
            up: Weight,
            down: Weight,
            dtype: ta.Any,
    ) -> None:
        super().__init__()

        self._cfg = cfg
        self.context = context  # what a past position is to this layer
        self.window = window  # the past positions it sees: the last so many, or None for all
        self._attn_norm = attn_norm
        self._q = q
        self._k = k
        self._v = v
        self._q_norm = q_norm
        self._k_norm = k_norm
        self._o = o
        self._mlp_norm = mlp_norm
        self._gate = gate
        self._up = up
        self._down = down
        self._dtype = dtype

    def __call__(
            self,
            ops: Ops,
            h: Array,
            cos: Array,
            sin: Array,
            span: DsparkSpan,
    ) -> Array:
        """h [T, H] float32, the block's slots at the positions of cos / sin's rows [T, D] -> the same, a layer on."""

        c = self._cfg
        T = h.shape[0]
        D = c.head_dim
        eps = c.rms_eps
        dtype = self._dtype

        def heads(x: Array, n: int) -> Array:
            return ops.transpose(ops.reshape(x, (1, T, n, D)), (0, 2, 1, 3))

        def rotated(x: Array, norm: Array) -> Array:
            return ops.cast(ops.rope_with(ops.rms_norm(ops.f32(x), norm, eps), cos, sin), dtype)

        u = inkling2_ops(ops).rms_norm_to(h, self._attn_norm, eps, dtype)
        q = rotated(heads(ops.linear(u, self._q), c.num_heads), self._q_norm)
        k = rotated(heads(ops.linear(u, self._k), c.num_kv_heads), self._k_norm)
        v = heads(ops.linear(u, self._v), c.num_kv_heads)

        scale = D ** -.5
        a = ops.sdpa_merge(
            [
                ops.sdpa_span_partials(q, span.k, span.v, span.lo, span.hi, span.ar, scale),
                ops.sdpa_partials(q, k, v, scale),
            ],
            None,
            dtype,
        )
        a = ops.reshape(ops.transpose(a, (0, 2, 1, 3)), (T, c.num_heads * D))
        h = h + ops.f32(ops.linear(a, self._o))

        m = inkling2_ops(ops).rms_norm_to(h, self._mlp_norm, eps, dtype)
        act = ops.silu(ops.f32(ops.linear(m, self._gate))) * ops.f32(ops.linear(m, self._up))
        return h + ops.f32(ops.linear(ops.cast(act, dtype), self._down))
