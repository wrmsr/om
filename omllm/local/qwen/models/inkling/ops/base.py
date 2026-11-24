# ruff: noqa: N803 N806
"""
The operations Inkling 2's layers and its draft model are made of that nothing else computes (INKLING.md 8): each
defined here once, composed from the seam's (ops/base.py), which is its reference -- what any backend runs, and what a
backend's kernel for it is held to (tests/). The torch backend's are in torch.py, over the Triton kernels of
torchkernels.py; `inkling2_ops` (backends.py) gives a backend's.
"""
import typing as ta

from ....ops.base import Array
from ....ops.base import OpsExtension
from ....ops.base import Weight


##


class Inkling2Ops(OpsExtension):
    def unit_rms(self, x: Array, eps: float) -> Array:
        """x / sqrt(mean(x^2) + eps) over the last axis, float32: an RMS norm with no weight."""

        xf = self.ops.f32(x)
        return xf * self.ops.rsqrt(self.ops.mean(xf * xf, -1, keepdims=True) + eps)

    def rms_norm_to(self, x: Array, w: Array, eps: float, dtype: ta.Any) -> Array:
        """`Ops.rms_norm` with one weight [D], handed over in `dtype` (a float32 stream's read, in the model's)."""

        return self.ops.cast(self.ops.rms_norm(x, w, eps), dtype)

    def sum_to(self, a: Array, b: Array, dtype: ta.Any) -> Array:
        """a + b, two arrays of one shape and any dtypes, added in float32 and handed over in `dtype`."""

        return self.ops.cast(self.ops.f32(a) + self.ops.f32(b), dtype)

    def sigmoid_gated(self, x: Array, g: Array, dtype: ta.Any) -> Array:
        """x * sigmoid(g), two arrays of one shape and any dtypes, in float32 and handed over in `dtype`."""

        return self.ops.cast(self.ops.f32(x) * self.ops.sigmoid(self.ops.f32(g)), dtype)

    def l2_clip(
            self,
            x: Array,
            threshold: float,
            *,
            scale: Array | None = None,
            after: Array | None = None,
    ) -> Array:
        """
        The vectors along x's last axis held to an l2 norm: v min(1, threshold / (|v| + 1e-6)), in x's dtype, where v
        is x -- or with `scale` (broadcast against x) x * scale, in x's dtype. With `after`, a float32 factor for each
        row of x [B, T, ...] ([T]), the clipped vectors -- rounded to x's dtype first -- times their row's.
        """

        if scale is not None:
            x = x * scale

        xf = self.ops.f32(x)
        norm = self.ops.sqrt(self.ops.sum(xf * xf, -1, keepdims=True))
        y = self.ops.cast(xf * self.ops.minimum(threshold / (norm + 1e-6), 1.0), x.dtype)

        if after is not None:
            y = self.ops.cast(self.ops.f32(y) * self.ops.reshape(after, (1, -1, *([1] * (len(x.shape) - 2)))), x.dtype)

        return y

    def depth_mix(
            self,
            queries: Array,
            sources: ta.Sequence[Array],
            *,
            raw: int = 0,
            eps: float = 0.,
    ) -> Array:
        """
        `queries` [Q, H] float32 over `sources`, each [B, T, H]: for each query, the sources' softmax(q . source /
        sqrt(H))-weighted sum, [B, T, Q, H] float32. The sources are taken at unit RMS: the last `raw` of them are
        given as they are and brought to it here (an RMS norm with no weight, `eps` under its root); the rest are at
        it already. Nothing here sees another position.
        """

        n = len(sources)
        srcs = [self.unit_rms(s, eps) if i >= n - raw else self.ops.f32(s) for i, s in enumerate(sources)]

        z = self.ops.stack(srcs, 2)  # [B, T, N, H]
        w = self.ops.softmax(self.ops.linear(z, queries) * (int(z.shape[-1]) ** -0.5), 2)  # [B, T, N, Q]
        return self.ops.transpose(w, (0, 1, 3, 2)) @ z

    def bottleneck_blend(
            self,
            x: Array,
            m: Array,
            down: Weight,
            forget: Array,
            gain: Array,
            *,
            eps: float,
            dtype: ta.Any,
    ) -> Array:
        """
        Two inputs [..., H] float32 blended by gates computed through a narrow bottleneck from both: with u =
        [unit_rms(x) | unit_rms(m)] and z = down u (down [R, 2 H], applied in `dtype`), the blend is (1 - tanh(forget
        z)) x + tanh(gain z) m (forget, gain [H, R] float32). float32. Nothing here sees another position.
        """

        u = self.ops.concat([self.unit_rms(x, eps), self.unit_rms(m, eps)], -1)
        z = self.ops.f32(self.ops.linear(self.ops.cast(u, dtype), down))

        f = self.ops.tanh(self.ops.linear(z, forget))
        g = self.ops.tanh(self.ops.linear(z, gain))

        return (1 - f) * x + g * m

    def sigmoid_route(self, logits: Array, bias: Array, k: int, *, total: float) -> tuple[Array, Array]:
        """
        A sigmoid router's pick: for `logits` [N, E] float32, each row's scores are their sigmoids; its k experts
        are the largest by score + `bias` [E], largest first; and their weights are their own scores -- not the
        biased ones the pick was made on -- scaled to sum to `total`. (indices [N, k] int, weights [N, k] float32).
        """

        f32 = self.ops.dtype('f32')

        scores = self.ops.sigmoid(self.ops.f32(logits))
        _, idx = self.ops.topk(scores + bias, k)

        # the picked experts' own scores: a one-hot sum, exact
        picked = self.ops.cast(idx[..., None] == self.ops.arange(int(scores.shape[-1])), f32)  # [N, k, E]
        sel = self.ops.sum(scores[:, None, :] * picked, -1)

        return idx, sel * (total / (self.ops.sum(sel, -1, keepdims=True) + 1e-20))

    def capped_gate(self, h: Array, *, gate_cap: float, up_cap: float) -> Array:
        """
        A gated activation with soft caps: for h [R, 2 I], its halves g | u, (gate_cap tanh(g / gate_cap))
        sigmoid(g) (up_cap tanh(u / up_cap)) -- the sigmoid reads the gate as it is, not its capped value. [R, I] in
        h's dtype, computed in float32.
        """

        n = int(h.shape[-1]) // 2
        g, u = self.ops.split(self.ops.f32(h), [n, n], -1)
        a = (self.ops.tanh(g / gate_cap) * gate_cap) * self.ops.sigmoid(g) * (self.ops.tanh(u / up_cap) * up_cap)
        return self.ops.cast(a, h.dtype)

    def weighted_rows(self, y: Array, w: Array, dtype: ta.Any) -> Array:
        """y [N, K, H] summed over K with weights w [N, K] float32, in float32; [N, H] in `dtype`."""

        return self.ops.cast(self.ops.sum(self.ops.f32(y) * w[..., None], 1), dtype)
