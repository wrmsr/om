# ruff: noqa: N806
"""
What a DSpark drafter makes of the past (drafter.py): each of its readers -- a layer, the head -- has a mix of its
own of the target's states at a position, and a layer turns its mix straight into that position's key and value. No
layer is run over the past, and nothing here looks at another position.
"""
import typing as ta

from .....ops.base import Array
from .....ops.base import Ops
from .....ops.base import Weight
from ...ops.backends import inkling2_ops


##


class DsparkTapMix:
    """A convex mix of the target's states at a position, RMS-normed: one reader's view of it."""

    def __init__(
            self,
            *,
            weights: Array,
            norm: Array,
            eps: float,
            dtype: ta.Any,
    ) -> None:
        super().__init__()

        self._weights = weights  # [n] float32, summing to one
        self._norm = norm
        self._eps = eps
        self._dtype = dtype

    def __call__(self, ops: Ops, taps: Array) -> Array:
        """taps [..., n, H] -> [..., H] in the model's dtype; mixed and normed in float32."""

        mix = ops.sum(ops.f32(taps) * self._weights[:, None], -2)
        return inkling2_ops(ops).rms_norm_to(mix, self._norm, self._eps, self._dtype)


class DsparkContext:
    """A layer's key and value for a past position, from its mix of the target's states there."""

    def __init__(
            self,
            *,
            mix: DsparkTapMix,
            k: Weight,
            v: Weight,
            k_norm: Array,
            num_kv_heads: int,
            head_dim: int,
            eps: float,
            dtype: ta.Any,
    ) -> None:
        super().__init__()

        self._mix = mix
        self._k = k
        self._v = v
        self._k_norm = k_norm  # [D]: over each head's components, the same weight for every head
        self._kv = num_kv_heads
        self._d = head_dim
        self._eps = eps
        self._dtype = dtype

    def __call__(
            self,
            ops: Ops,
            taps: Array,
            cos: Array,
            sin: Array,
    ) -> tuple[Array, Array]:
        """
        taps [T, n, H] at T positions, cos / sin [T, D] their rotary rows -> k, v [1, KV, T, D]: the keys normed
        per head and rotated (in float32), the values as projected.
        """

        T = taps.shape[0]
        c = self._mix(ops, taps)

        def heads(x: Array) -> Array:
            return ops.transpose(ops.reshape(x, (1, T, self._kv, self._d)), (0, 2, 1, 3))

        k = ops.rms_norm(ops.f32(heads(ops.linear(c, self._k))), self._k_norm, self._eps)
        k = ops.cast(ops.rope_with(k, cos, sin), self._dtype)
        return k, heads(ops.linear(c, self._v))
