# ruff: noqa: N803 N806 N812
"""
The backend seam.

`model.py` is written once against `Ops`. Everything that is plain array algebra (reshape, slicing, `+ * @`,
broadcasting) is done directly on backend arrays, which numpy, torch, MLX and tinygrad all spell the same way. The
handful of places where backends differ, or have fused fast paths, go through `Ops` methods:

  * abstract:  the irreducible primitives every backend must provide (array in/out, cast, exp, sum, concat, ...)
  * concrete:  the fused-able model primitives (rms_norm, rope, sdpa, conv1d_causal, gated_delta, ...) with a
               *reference implementation composed from the abstract ones*. A new backend works as soon as the
               abstract set exists; it gets faster as it overrides these.

Rules for code that runs on any backend (i.e. all of model.py):
  * no item assignment, no in-place ops, no `.view` -- build lists and `ops.stack` / `ops.concat`
  * state is functional: `mixer(x, state) -> (y, state)`; a backend may hand back the buffer it wrote into
  * precision is explicit: `ops.f32(x)` before anything that must accumulate in float32
  * data-dependent Python control flow only on shapes, never on values (graph capture needs that later)

`NumpyOps` is the reference backend: float64 by default, used as the golden oracle in the parity tests.
"""
import abc
import typing as ta

from omcore import lang

from .microscaled import MicroscaledWeight
from .quant import QWeight
from .quant import quantize as quantize_np


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


Array: ta.TypeAlias = ta.Any  # a backend array (np.ndarray, torch.Tensor, mx.array, ...)
Weight: ta.TypeAlias = ta.Any  # a backend dense array or a backend-adopted QWeight


##


DTYPE_NAMES = (
    'f32',
    'f16',
    'bf16',
    'i32',
    'i64',
)


class Ops(lang.Abstract):
    name: str = '?'

    def __init__(self) -> None:
        super().__init__()

        self.taps: dict[str, np.ndarray] | None = None  # set to {} to record `tap()`ed activations

    # dtypes

    @abc.abstractmethod
    def dtype(self, name: str) -> ta.Any:
        """'f32' | 'f16' | 'bf16' -> backend dtype object."""

    # host <-> backend

    @abc.abstractmethod
    def array(self, a: np.ndarray, dtype: ta.Any = None) -> Array:
        pass

    @abc.abstractmethod
    def numpy(self, x: Array) -> np.ndarray:
        pass

    def numpy_later(self, x: Array) -> ta.Callable[[], np.ndarray]:
        """
        Start bringing a small array to the host: the returned call gives it. On a backend that queues its work the
        call waits only for what was queued before this -- not for what is launched in between, which is the point:
        the device has that to work on while the host reads and decides. Default: the read happens at the call.
        """

        return lambda: self.numpy(x)

    @abc.abstractmethod
    def cast(self, x: Array, dtype: ta.Any) -> Array:
        pass

    def f32(self, x: Array) -> Array:
        return self.cast(x, self.dtype('f32'))

    @abc.abstractmethod
    def copy(self, x: Array) -> Array:
        """
        x in a buffer of its own, densely laid out in row-major order whatever x's strides were (state handed to a
        compiled step is copied so: the step is guarded on its inputs' strides).
        """

        raise NotImplementedError

    def assign(self, dst: Array, src: Array) -> Array:
        """
        An array holding `src`'s values in `dst`'s place: on a backend that writes in place, `dst` itself, written --
        so that what is bound to it (a captured step: `capture`) finds the values -- and on one that does not, `src`.
        The two are of one shape and dtype.
        """

        return src

    def to_host(self, x: Array) -> ta.Any:
        """
        Move an array to host memory for the prefix cache's host tier, in a form `from_host` brings back. Default: the
        array itself (unified-memory and CPU backends have no tiers to speak of).
        """

        return x

    def from_host(self, h: ta.Any) -> Array:
        return h

    @abc.abstractmethod
    def zeros(self, shape: tuple[int, ...], dtype: ta.Any) -> Array:
        pass

    def eval(self, *xs: Array) -> None:
        """Force computation on lazy backends; no-op elsewhere."""

    def materialize(self, *xs: Array) -> None:
        """
        A point past which a lazy backend's graph should not grow: the model calls it per layer of a prefill with the
        layer's output and state. A backend whose scheduling cost or memory depends on the size of the pending graph
        evaluates here; everything else (torch, numpy) does nothing, so this is not a device sync.
        """

    def nbytes(self, w: Weight) -> int:
        raise NotImplementedError

    # structural

    @abc.abstractmethod
    def reshape(self, x: Array, shape: tuple[int, ...]) -> Array:
        pass

    @abc.abstractmethod
    def transpose(self, x: Array, axes: tuple[int, ...]) -> Array:
        pass

    @abc.abstractmethod
    def concat(self, xs: ta.Sequence[Array], axis: int) -> Array:
        pass

    def rows_buffer(self, like: Array, total: int) -> Array | None:
        """
        An uninitialised array shaped like `like` [B, n, ...] but with `total` rows, for `rows_write` to fill -- or
        None, the default, where arrays are not written in place: the caller then collects its pieces and `concat`s
        them, which holds the pieces and the result together for a moment (gigabytes, for a long prompt's hidden
        states).
        """

        return None

    def rows_write(self, buf: Array, start: int, x: Array) -> Array:
        """x [B, n, ...] written into a `rows_buffer` at rows start..start+n-1; returns the buffer."""

        raise NotImplementedError

    @abc.abstractmethod
    def stack(self, xs: ta.Sequence[Array], axis: int) -> Array:
        pass

    @abc.abstractmethod
    def split(self, x: Array, sizes: ta.Sequence[int], axis: int) -> list[Array]:
        pass

    @abc.abstractmethod
    def repeat(self, x: Array, n: int, axis: int) -> Array:
        """repeat_interleave: each slice along `axis` repeated `n` times consecutively."""

    @abc.abstractmethod
    def arange(self, n: int) -> Array:
        """int32 [n]."""

    @abc.abstractmethod
    def scalar(self, v: int) -> Array:
        """A 0-d int32 array (a position index that lives on the device, so a captured step can read it)."""

    def kv_write(self, buf: Array, pos: Array, x: Array) -> Array:
        """
        Write x [B, KV, 1, D] into buf [B, KV, L, D] at position `pos` (0-d int array) and return the buffer that
        now holds it. Backends with mutable buffers write in place and return the same object; functional
        backends return a new array. Callers must use the return value. The reference is a masked blend, which
        is graph-safe everywhere but touches the whole buffer.
        """

        L = buf.shape[2]
        oh = self.cast(self.arange(L) == pos, buf.dtype)[None, None, :, None]
        return buf * (1 - oh) + self.cast(x, buf.dtype) * oh

    # elementwise / reductions

    @abc.abstractmethod
    def cumsum(self, x: Array, axis: int) -> Array:
        pass

    @abc.abstractmethod
    def exp(self, x: Array) -> Array:
        pass

    @abc.abstractmethod
    def rsqrt(self, x: Array) -> Array:
        pass

    @abc.abstractmethod
    def sum(self, x: Array, axis: int, keepdims: bool = False) -> Array:
        pass

    @abc.abstractmethod
    def mean(self, x: Array, axis: int, keepdims: bool = False) -> Array:
        pass

    @abc.abstractmethod
    def sigmoid(self, x: Array) -> Array:
        pass

    @abc.abstractmethod
    def softplus(self, x: Array) -> Array:
        pass

    def silu(self, x: Array) -> Array:
        return x * self.sigmoid(x)

    @abc.abstractmethod
    def log(self, x: Array) -> Array:
        pass

    def tanh(self, x: Array) -> Array:
        return 2 * self.sigmoid(2 * x) - 1

    def sqrt(self, x: Array) -> Array:
        return 1.0 / self.rsqrt(x)  # (0 -> 1 / inf -> 0, where x * rsqrt(x) would be a NaN)

    def unit_rms(self, x: Array, eps: float) -> Array:
        """x / sqrt(mean(x^2) + eps) over the last axis, float32: an RMS norm with no weight."""

        xf = self.f32(x)
        return xf * self.rsqrt(self.mean(xf * xf, -1, keepdims=True) + eps)

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

        xf = self.f32(x)
        norm = self.sqrt(self.sum(xf * xf, -1, keepdims=True))
        y = self.cast(xf * self.minimum(threshold / (norm + 1e-6), 1.0), x.dtype)

        if after is not None:
            y = self.cast(self.f32(y) * self.reshape(after, (1, -1, *([1] * (len(x.shape) - 2)))), x.dtype)

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
        srcs = [self.unit_rms(s, eps) if i >= n - raw else self.f32(s) for i, s in enumerate(sources)]

        z = self.stack(srcs, 2)  # [B, T, N, H]
        w = self.softmax(self.linear(z, queries) * (int(z.shape[-1]) ** -0.5), 2)  # [B, T, N, Q]
        return self.transpose(w, (0, 1, 3, 2)) @ z

    def sigmoid_route(self, logits: Array, bias: Array, k: int, *, total: float) -> tuple[Array, Array]:
        """
        A sigmoid router's pick: for `logits` [N, E] float32, each row's scores are their sigmoids; its k experts
        are the largest by score + `bias` [E], largest first; and their weights are their own scores -- not the
        biased ones the pick was made on -- scaled to sum to `total`. (indices [N, k] int, weights [N, k] float32).
        """

        f32 = self.dtype('f32')

        scores = self.sigmoid(self.f32(logits))
        _, idx = self.topk(scores + bias, k)

        # the picked experts' own scores: a one-hot sum, exact
        picked = self.cast(idx[..., None] == self.arange(int(scores.shape[-1])), f32)  # [N, k, E]
        sel = self.sum(scores[:, None, :] * picked, -1)

        return idx, sel * (total / (self.sum(sel, -1, keepdims=True) + 1e-20))

    def capped_gate(self, h: Array, *, gate_cap: float, up_cap: float) -> Array:
        """
        A gated activation with soft caps: for h [R, 2 I], its halves g | u, (gate_cap tanh(g / gate_cap))
        sigmoid(g) (up_cap tanh(u / up_cap)) -- the sigmoid reads the gate as it is, not its capped value. [R, I] in
        h's dtype, computed in float32.
        """

        n = int(h.shape[-1]) // 2
        g, u = self.split(self.f32(h), [n, n], -1)
        a = (self.tanh(g / gate_cap) * gate_cap) * self.sigmoid(g) * (self.tanh(u / up_cap) * up_cap)
        return self.cast(a, h.dtype)

    def weighted_rows(self, y: Array, w: Array, dtype: ta.Any) -> Array:
        """y [N, K, H] summed over K with weights w [N, K] float32, in float32; [N, H] in `dtype`."""

        return self.cast(self.sum(self.f32(y) * w[..., None], 1), dtype)

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

        u = self.concat([self.unit_rms(x, eps), self.unit_rms(m, eps)], -1)
        z = self.f32(self.linear(self.cast(u, dtype), down))

        f = self.tanh(self.linear(z, forget))
        g = self.tanh(self.linear(z, gain))

        return (1 - f) * x + g * m

    def short_conv(
            self,
            x: Array,
            hist: Array | None,
            weight: Array,
            *,
            scale: float,
            all_states: bool = False,
    ) -> tuple[Array, Array]:
        """
        A causal convolution over time, a channel at a time, with a residual: for x [B, T, C] and each channel's K
        taps `weight` [C, K] float32, oldest first, y[t] = (x[t] + sum_a w[a] x[t - (K - 1) + a]) * scale in x's
        dtype, the K - 1 inputs before x[0] being `hist` [B, C, K - 1] float32 (zeros for None). And the history
        after: the last K - 1 inputs, [B, C, K - 1] float32 -- or, with `all_states`, as it stands after each of the
        T tokens, [T, B, C, K - 1].
        """

        B, T, C = x.shape
        K = int(weight.shape[-1])
        f32 = self.dtype('f32')

        xf = self.transpose(self.f32(x), (0, 2, 1))
        if hist is None:
            hist = self.zeros((B, C, K - 1), f32)
        inp = self.concat([hist, xf], -1)  # [B, C, K - 1 + T]
        y = (xf + self.conv1d_causal(inp, weight)) * scale

        if all_states:
            after = self.stack([inp[..., t + 1:t + K] for t in range(T)], 0)
        else:
            # a dense copy, not a slice of the input (which a view would keep alive, with strides that depend on T)
            after = self.copy(inp[..., -(K - 1):])

        return self.cast(self.transpose(y, (0, 2, 1)), x.dtype), after

    def short_conv_dynamic(
            self,
            x: Array,
            hist: Array | None,
            weight: Array,
            dyn: Array,
            *,
            scale: float,
            all_states: bool = False,
    ) -> tuple[Array, Array]:
        """
        `short_conv` whose taps a position adds to: `weight` [K, C] float32 the channels' own, by backward lag (0:
        the current input), and `dyn` [B, T, G, K] float32 each position's, by lag too, a group's shared by its C / G
        channels. y[t] = (x[t] + sum_lag (weight[lag] + dyn[t, lag]) x[t - lag]) * scale; the histories as
        `short_conv`'s.
        """

        B, T, C = x.shape
        K = int(weight.shape[0])
        G = int(dyn.shape[2])
        f32 = self.dtype('f32')

        xf = self.transpose(self.f32(x), (0, 2, 1))
        if hist is None:
            hist = self.zeros((B, C, K - 1), f32)
        inp = self.concat([hist, xf], -1)  # [B, C, K - 1 + T]

        acc = None
        for lag in range(K):
            at = K - 1 - lag
            tap = weight[lag][None, :, None] + self.repeat(self.transpose(dyn[..., lag], (0, 2, 1)), C // G, 1)
            term = tap * inp[..., at:at + T]
            acc = term if acc is None else acc + term
        y = (xf + acc) * scale

        if all_states:
            after = self.stack([inp[..., t + 1:t + K] for t in range(T)], 0)
        else:
            after = self.copy(inp[..., -(K - 1):])

        return self.cast(self.transpose(y, (0, 2, 1)), x.dtype), after

    def maximum(self, x: Array, v: float) -> Array:
        """max(x, v) elementwise against a scalar, in x's dtype (integer arrays included)."""

        m = self.cast(x > v, x.dtype)
        return x * m + v * (1 - m)

    def minimum(self, x: Array, v: float) -> Array:
        """min(x, v) elementwise against a scalar, in x's dtype (integer arrays included)."""

        m = self.cast(x < v, x.dtype)
        return x * m + v * (1 - m)

    # sampling primitives (see model.Sampler: everything runs on the device, one small int array leaves it)

    @abc.abstractmethod
    def argmax(self, x: Array, axis: int) -> Array:
        """Integer array."""

    @abc.abstractmethod
    def amax(self, x: Array, axis: int, keepdims: bool = False) -> Array:
        pass

    @abc.abstractmethod
    def topk(self, x: Array, k: int) -> tuple[Array, Array]:
        """The k largest along the last axis, sorted descending: (values, integer indices)."""

    @abc.abstractmethod
    def seed(self, seed: int) -> None:
        pass

    @abc.abstractmethod
    def random_uniform(self, shape: tuple[int, ...]) -> Array:
        """float32 in [0, 1)."""

    def select(self, x: Array, i: int) -> Array:
        """x[i]: the entry at a static index along the first axis, that axis dropped (a commit's per-token state)."""

        return x[i]

    def select_at(self, x: Array, i: Array) -> Array:
        """
        `select` for an index held on the device (a 0-d int array): what a captured function picks a per-token state
        with, as it cannot read the index.
        """

        return x[self.reshape(i, (1,))][0]

    def gather_rows(self, probs: Array, toks: Array) -> Array:
        """probs[i, toks[i]] for each row i of [T, V] -> [T]. Reference: a one-hot sum, O(T V)."""

        V = probs.shape[1]
        oh = self.cast(self.arange(V)[None, :] == toks[:, None], probs.dtype)
        return self.sum(probs * oh, -1)

    def index_add(self, x: Array, idx: Array, vals: Array) -> Array:
        """
        x [V] with vals [n] added at idx [n] (duplicates accumulate); returns the updated array. Reference: a one-hot
        sum, O(n V).
        """

        oh = self.cast(self.arange(x.shape[0])[None, :] == idx[:, None], x.dtype)  # [n, V]
        return x + self.sum(oh * self.cast(vals, x.dtype)[:, None], 0)

    @abc.abstractmethod
    def softmax(self, x: Array, axis: int) -> Array:
        pass

    # weights

    @abc.abstractmethod
    def weight(self, w: np.ndarray, dtype: ta.Any, name: str | None = None) -> Weight:
        """Adopt a dense parameter. `name` is its canonical name, for a backend that places parameters by it."""

    @abc.abstractmethod
    def qweight(self, qw: QWeight, dtype: ta.Any, name: str | None = None) -> Weight:
        """Adopt an already-quantized parameter (scale/bias stored in `dtype`)."""

    def head_rows(self, w: Weight, n: int) -> Weight:
        """
        The first n output rows of a weight (dense or adopted QWeight) as a weight: a cheap view where the backend
        allows it. Used for a draft head restricted to the first n vocabulary ids.
        """

        return w[:n]

    def quantize(
            self,
            w: np.ndarray,
            bits: int,
            group: int,
            dtype: ta.Any,
            search: bool = True,
            name: str | None = None,
    ) -> Weight:
        """Quantize + adopt (see quant.quantize for `search`). Backends may override to quantize on-device."""

        return self.qweight(quantize_np(w, bits, group, search), dtype, name)

    def export_qweight(self, w: Weight) -> QWeight:
        """
        The inverse of `qweight`: a backend-adopted quantized weight back to numpy (for the parameter cache). Backends
        that cannot raise NotImplementedError and the caller quantizes on the host instead.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def linear(self, x: Array, w: Weight) -> Array:
        """x @ w.T for a dense or quantized weight."""

    def expert_weights(self, parts: ta.Sequence[ta.Sequence[Weight]]) -> Weight:
        """
        Per-expert weights stacked into one for `expert_linear`: expert e's weight is parts[e] concatenated along the
        output rows (gate then up, say). Default: a dense [E, N, K] array (a backend stacks its quantized weights).
        """

        return self.stack([self.concat(list(p), 0) if len(p) > 1 else p[0] for p in parts], 0)

    def microscaled(self, mw: MicroscaledWeight, dtype: ta.Any, name: str | None = None) -> Weight:
        """
        Adopt a stack of experts stored in a microscaled float format (ops/microscaled.py) as a weight for
        `expert_linear`. Default: decoded once, dense in `dtype` -- the reference, and what a backend without a
        container for the packed form does; a backend that has one keeps the checkpoint's bytes and decodes the
        experts a step reads.
        """

        return self.weight(mw.dequantize(), dtype, name)

    def expert_dense(self, w: Weight, e: int, dtype: ta.Any) -> Array:
        """One expert of a stacked weight as a plain [N, K] array in `dtype`."""

        return self.cast(w[e], dtype)

    # Past this many rows `expert_linear`'s reference goes expert by expert (`expert_linear_grouped`) instead of
    # gathering a matrix per row: a prefill chunk's rows are thousands and share a hundred experts, a step's are a
    # few each with its own. A captured step stays under it (the grouped form reads the experts chosen on the host).
    expert_gather_max_rows: int = 256

    def expert_linear(self, x: Array, w: Weight, eids: Array, x_div: int = 1) -> Array:
        """
        [R, N]: row r is x[r // x_div] @ w[eids[r]].T -- every row against its own expert of a stacked weight
        (`expert_weights`; x_div = k when a token's k expert slots share its input row). The composed reference
        gathers each row's expert; a kernel reads the selected experts in place.
        """

        rows = self.repeat(x, x_div, 0) if x_div > 1 else x
        if rows.shape[0] > self.expert_gather_max_rows:
            return self.expert_linear_grouped(rows, w, eids)
        return (w[eids] @ rows[:, :, None])[..., 0]

    def expert_linear_grouped(self, rows: Array, w: Weight, eids: Array) -> Array:
        """
        `expert_linear` for many rows, [R, K] each against its own expert: the rows sorted by expert, one dense
        matmul per expert present (`expert_dense`), and the results put back in order. Which experts are present is
        read on the host, so this is for a prefill, not a captured step.
        """

        ids = np.asarray(self.numpy(eids)).reshape(-1).astype(np.int64)
        order = np.argsort(ids, kind='stable')
        inverse = np.empty_like(order)
        inverse[order] = np.arange(order.shape[0])
        sorted_ids = ids[order]
        starts = np.flatnonzero(np.r_[True, sorted_ids[1:] != sorted_ids[:-1]])
        ends = np.r_[starts[1:], sorted_ids.shape[0]]

        sorted_rows = rows[self.array(order.astype(np.int32))]
        outs = [
            self.linear(sorted_rows[int(a):int(b)], self.expert_dense(w, int(sorted_ids[a]), rows.dtype))
            for a, b in zip(starts, ends)
        ]
        out = outs[0] if len(outs) == 1 else self.concat(outs, 0)
        return out[self.array(inverse.astype(np.int32))]

    @abc.abstractmethod
    def embedding(self, ids: Array, w: Weight, dtype: ta.Any) -> Array:
        """Row gather -> [..., in] in `dtype`."""

    # fused-able model primitives (reference implementations)

    def rms_norm(self, x: Array, w: Array, eps: float) -> Array:
        """
        Over x's last dim, times w -- [D], or a weight per group, [G, D] over x [..., G, D] (Flash-Next's per-branch
        norms; a backend's fused kernel may take only the former).
        """

        xf = self.f32(x)
        y = xf * self.rsqrt(self.mean(xf * xf, -1, keepdims=True) + eps)
        return self.cast(y * self.f32(w), x.dtype)

    def sigmoid_gated(self, x: Array, g: Array, dtype: ta.Any) -> Array:
        """x * sigmoid(g), two arrays of one shape and any dtypes, in float32 and handed over in `dtype`."""

        return self.cast(self.f32(x) * self.sigmoid(self.f32(g)), dtype)

    def sum_to(self, a: Array, b: Array, dtype: ta.Any) -> Array:
        """a + b, two arrays of one shape and any dtypes, added in float32 and handed over in `dtype`."""

        return self.cast(self.f32(a) + self.f32(b), dtype)

    def rms_norm_to(self, x: Array, w: Array, eps: float, dtype: ta.Any) -> Array:
        """`rms_norm` with one weight [D], handed over in `dtype` (a float32 stream's read, in the model's)."""

        return self.cast(self.rms_norm(x, w, eps), dtype)

    def l2_norm(self, x: Array, eps: float = 1e-6) -> Array:
        # FLA-style: x / sqrt(sum(x^2) + eps)   (llama.cpp: rms_norm(x, eps/n) / sqrt(n) -- identical)
        return x * self.rsqrt(self.sum(x * x, -1, keepdims=True) + eps)

    def rope_tables(self, offset: int, n: int, dims: int, theta: float) -> tuple[np.ndarray, np.ndarray]:
        """Host-side cos/sin [n, dims] for positions offset .. offset+n (NeoX layout: [f0..f_{d/2}, f0..f_{d/2}])."""

        pos = np.arange(offset, offset + n, dtype=np.float64)
        inv = 1.0 / (theta ** (np.arange(0, dims, 2, dtype=np.float64) / dims))
        f = pos[:, None] * inv[None, :]
        emb = np.concatenate([f, f], axis=-1)
        return np.cos(emb), np.sin(emb)

    def rope(self, x: Array, offset: int, dims: int, theta: float) -> Array:
        """NeoX rotate-half on the first `dims` of x: [B, H, T, D], positions offset .. offset+T."""

        cos_np, sin_np = self.rope_tables(offset, x.shape[2], dims, theta)
        return self.rope_with(x, self.array(cos_np, x.dtype), self.array(sin_np, x.dtype))

    def rope_with(self, x: Array, cos: Array, sin: Array) -> Array:
        """rotate-half with explicit tables cos, sin: [T, dims] (T == x.shape[2])."""

        dims = cos.shape[-1]
        xr = x[..., :dims]
        xp = x[..., dims:]
        half = dims // 2
        x1 = xr[..., :half]
        x2 = xr[..., half:]
        rot = self.concat([-x2, x1], axis=-1)
        xr = xr * cos[None, None] + rot * sin[None, None]
        return self.concat([xr, xp], axis=-1)

    def sdpa(self, q: Array, k: Array, v: Array, scale: float, past: int) -> Array:
        """
        Causal attention. q: [B, H, T, D]; k, v: [B, KV, past + T, D] (GQA when KV < H). Query i sees keys <= past + i.
        """

        B, H, T, D = q.shape
        KV = k.shape[1]
        L = k.shape[2]
        if KV != H:
            k = self.repeat(k, H // KV, 1)
            v = self.repeat(v, H // KV, 1)
        scores = (q @ self.transpose(k, (0, 1, 3, 2))) * scale
        if T > 1:
            keep = np.tril(np.ones((T, L), dtype=bool), k=past)
            mask = self.array(np.where(keep, 0.0, -np.inf), scores.dtype)
            scores = scores + mask[None, None]
        return self.softmax(scores, -1) @ v

    def conv1d_causal(self, x: Array, w: Array) -> Array:
        """Depthwise causal conv. x: [B, C, L] where L already includes the K-1 history; w: [C, K] -> [B, C, L-K+1]."""

        K = w.shape[-1]
        n = x.shape[-1] - (K - 1)
        out = None
        for j in range(K):
            term = x[:, :, j:j + n] * w[:, j][None, :, None]
            out = term if out is None else out + term
        return out

    # gated delta rule
    #
    #   q, k:  [B, H, T, dk] (already l2-normed; q already scaled by 1/sqrt(dk))
    #   v:     [B, H, T, dv]
    #   g:     [B, H, T]  log decay (<= 0);   beta: [B, H, T] in (0, 1)
    #   state: [B, H, dk, dv]
    #   returns out [B, H, T, dv], new state
    #
    # All float32. `gated_delta` is the entry point the model calls; it dispatches between the per-token form (decode, T
    # == 1) and the chunked form (prefill). Backends override whichever they have a kernel for.

    gdn_chunk: int = 64

    def gated_delta(
            self,
            q: Array,
            k: Array,
            v: Array,
            g: Array,
            beta: Array,
            state: Array,
    ) -> tuple[Array, Array]:
        if q.shape[2] == 1:
            return self.gated_delta_recurrent(
                q,
                k,
                v,
                g,
                beta,
                state,
            )

        return self.gated_delta_chunked(
            q,
            k,
            v,
            g,
            beta,
            state,
            self.gdn_chunk,
        )

    def gated_delta_recurrent(
            self,
            q: Array,
            k: Array,
            v: Array,
            g: Array,
            beta: Array,
            state: Array,
    ) -> tuple[Array, Array]:
        """Per-token form: O(T) sequential steps, each a handful of small ops. The reference."""

        out, states = self.gated_delta_states(q, k, v, g, beta, state)
        return out, states[-1]

    def gated_delta_states(
            self,
            q: Array,
            k: Array,
            v: Array,
            g: Array,
            beta: Array,
            state: Array,
    ) -> tuple[Array, Array]:
        """
        The recurrence, also returning the state after every token: [T, B, H, dk, dv]. Speculative verify runs T = k + 1
        tokens and then keeps the state after however many were accepted.
        """

        T = q.shape[2]
        S = state
        outs = []
        states = []
        for t in range(T):
            # [B,H,dk] / [B,H,dv]
            q_t = q[:, :, t]
            k_t = k[:, :, t]
            v_t = v[:, :, t]
            S = S * self.exp(g[:, :, t])[..., None, None]  # decay
            mem = self.sum(S * k_t[..., None], -2)  # k^T S -> [B,H,dv]
            delta = (v_t - mem) * beta[:, :, t][..., None]
            S = S + k_t[..., None] * delta[..., None, :]  # rank-1 update
            outs.append(self.sum(S * q_t[..., None], -2))  # q^T S
            states.append(S)
        return self.stack(outs, 2), self.stack(states, 0)

    # up to this many tokens the model calls `gdn_step` (fusable); beyond, the chunked path. A backend whose fused
    # kernel takes any T (torch's Triton one) raises it, and its prefill goes through `gdn_step` too
    gdn_fused_max_t: int = 8

    def gdn_step(
            self,
            q: Array,
            k: Array,
            v: Array,
            a: Array,
            b: Array,
            A: Array,
            dt_bias: Array,
            state: Array,
            all_states: bool,
            eps: float = 1e-6,
    ) -> tuple[Array, Array]:
        """
        The whole DeltaNet token step from the projections' outputs, for T <= gdn_fused_max_t: l2-normalise q, k (and
        scale q by 1/sqrt(dk)), broadcast the Hk key heads over the Hv value heads, beta = sigmoid(b), g = A *
        softplus(a + dt_bias), then the recurrence. Layouts are the projections' natural ones -- q, k: [B, T, Hk, dk];
        v: [B, T, Hv, dv]; a, b: [B, T, Hv]; A, dt_bias: [Hv]; state: [B, Hv, dk, dv] -- and the output is [B, T, Hv,
        dv], so no transposes or head repeats are needed around it. Returns (out, state) or, with all_states, (out,
        states [T, B, Hv, dk, dv]). One op so a backend can replace the ~25 small kernels of this composition with a
        single fused one (see torch_triton.gdn_step).
        """

        B, T, Hk, dk = q.shape
        Hv = v.shape[2]
        dv = v.shape[3]  # noqa
        qn = self.transpose(self.l2_norm(q, eps), (0, 2, 1, 3)) * (dk**-0.5)  # [B,Hk,T,dk]
        kn = self.transpose(self.l2_norm(k, eps), (0, 2, 1, 3))
        vt = self.transpose(v, (0, 2, 1, 3))  # [B,Hv,T,dv]
        if Hv != Hk:
            qn = self.repeat(qn, Hv // Hk, 1)
            kn = self.repeat(kn, Hv // Hk, 1)
        beta = self.transpose(self.sigmoid(b), (0, 2, 1))  # [B,Hv,T]
        g = self.transpose(A[None, None, :] * self.softplus(a + dt_bias), (0, 2, 1))
        if all_states:
            out, st = self.gated_delta_states(qn, kn, vt, g, beta, state)
        else:
            out, st = self.gated_delta(qn, kn, vt, g, beta, state)
        return self.transpose(out, (0, 2, 1, 3)), st

    def gated_delta_chunked(
            self,
            q: Array,
            k: Array,
            v: Array,
            g: Array,
            beta: Array,
            state: Array,
            chunk: int = 64,
    ) -> tuple[Array, Array]:
        """
        Chunkwise (WY-representation) form, Yang et al. 2024 -- the algorithm behind FLA's `chunk_gated_delta_rule` and
        HF's `torch_chunk_gated_delta_rule`, composed from the primitives so it runs (and is graph-friendly) on every
        backend. Within a chunk everything is a batched matmul; across chunks the state is carried sequentially, so cost
        is O(T/chunk) sequential steps instead of O(T).

        The per-chunk triangular inverse (I + A)^-1, A strictly lower, is computed as a Neumann product (I + N)(I +
        N^2)(I + N^4)... with N = -A, which is exact because N is nilpotent -- log2(chunk) matmuls and no item
        assignment, versus a forward-substitution loop.
        """

        B, H, T, dk = q.shape
        dv = v.shape[-1]
        C = chunk
        f32 = q.dtype
        pad = (C - T % C) % C
        if pad:
            q, k, v = [self.concat([x, self.zeros((B, H, pad, x.shape[-1]), f32)], 2) for x in (q, k, v)]
            g, beta = [self.concat([x, self.zeros((B, H, pad), f32)], 2) for x in (g, beta)]
        L = T + pad
        n = L // C
        q, k, v = [self.reshape(x, (B, H, n, C, x.shape[-1])) for x in (q, k, v)]
        g, beta = [self.reshape(x, (B, H, n, C)) for x in (g, beta)]

        tril = self.array(np.tril(np.ones((C, C))), f32)  # i >= j
        strict = self.array(np.tril(np.ones((C, C)), -1), f32)  # i > j
        eye = self.array(np.eye(C), f32)

        gcum = self.cumsum(g, -1)  # [B,H,n,C], decreasing
        # exp(gcum_i - gcum_j) for i >= j (<= 1), 0 above the diagonal; the exponent is masked *before* exp so the
        # positive upper-triangle exponents never overflow
        decay = self.exp((gcum[..., :, None] - gcum[..., None, :]) * tril) * tril  # [B,H,n,C,C]
        kb = k * beta[..., None]
        vb = v * beta[..., None]
        A = (kb @ self.transpose(k, (0, 1, 2, 4, 3))) * decay * strict  # strictly lower
        # (I + A)^-1 by forward substitution, row by row: T_i = e_i - A_i,<i @ T_<i. The Neumann product
        # (I+N)(I+N^2)(I+N^4)... is the same matrix in exact arithmetic but squares the intermediate powers, and
        # with correlated keys and beta near 1 (a repeated token) those powers are huge with cancelling signs:
        # unusable even in float64. Substitution reuses computed rows and is as stable as the recurrence itself.
        Tm = eye[0:1] + A[..., 0:1, :] * 0  # T_0 = e_0, broadcast to [B,H,n,1,C]
        for i in range(1, C):
            Tm = self.concat([Tm, eye[i:i + 1] - A[..., i:i + 1, :i] @ Tm], -2)  # append T_i; Tm has i rows
        W = Tm @ (kb * self.exp(gcum)[..., None])  # [B,H,n,C,dk]
        U = Tm @ vb  # [B,H,n,C,dv]

        S = state
        outs = []
        for i in range(n):
            # [B,H,C,dk]
            q_i = q[:, :, i]
            k_i = k[:, :, i]
            gc = gcum[:, :, i]  # [B,H,C]
            u = U[:, :, i] - W[:, :, i] @ S  # [B,H,C,dv]   v - (decayed) k S
            intra = (q_i @ self.transpose(k_i, (0, 1, 3, 2))) * decay[:, :, i]
            outs.append((q_i * self.exp(gc)[..., None]) @ S + intra @ u)
            g_last = gc[..., -1]  # [B,H]
            k_dec = k_i * self.exp(g_last[..., None] - gc)[..., None]  # [B,H,C,dk]
            S = S * self.exp(g_last)[..., None, None] + self.transpose(k_dec, (0, 1, 3, 2)) @ u
        out = self.reshape(self.stack(outs, 2), (B, H, L, dv))
        if pad:
            out = out[:, :, :T]
        return out, S

    # A backend whose eager path is costly (tinygrad schedules each graph in milliseconds of Python, a prefill in
    # tens of seconds) asks the engine to prefill through the captured static step instead of `forward`: see
    # `Decoder.prefill` and `Qwen35.generate`
    static_prefill: bool = False

    # The attention layers' KV state is a tuple of `kv_arity` arrays whose meaning only the backend knows: the default
    # is (k, v) in the compute dtype, [B, KV, L, D] each; a backend may store something else (torch: fp8 codes plus
    # per-token scales, four arrays). Model code goes through these methods and never looks inside.
    kv_arity: int = 2

    def kv_new(self, k: Array, v: Array) -> tuple[Array, ...]:
        """A state holding the given [B, KV, T, D] keys and values."""

        return (k, v)

    def kv_adapt(self, state: tuple[Array, ...], dtype: ta.Any = None) -> tuple[Array, ...]:
        """
        A state in this backend's format (converting one made with another format, e.g. a prefix snapshot taken at
        another KV dtype; `dtype` is the compute dtype for a conversion that needs one). Default: only the (k, v) format
        exists.
        """

        if len(state) != self.kv_arity:
            raise ValueError(f'cannot adapt a {len(state)}-array KV state to this backend')
        return state

    def kv_len(self, state: tuple[Array, ...]) -> int:
        return state[0].shape[2]

    def kv_concat(self, state: tuple[Array, ...], k: Array, v: Array) -> tuple[Array, ...]:
        """The state extended by new keys and values along the sequence (functional prefill)."""

        return (self.concat([state[0], k], 2), self.concat([state[1], v], 2))

    def kv_slice(self, state: tuple[Array, ...], n: int) -> tuple[Array, ...]:
        """Copies of the first n positions."""

        return tuple(self.copy(a[:, :, :n]) for a in state)

    def kv_window(self, state: tuple[Array, ...], n: int) -> tuple[Array, ...]:
        """Views of the first n positions (no copy), for bucketed attention."""

        return tuple(a[:, :, :n] for a in state)

    def kv_range(self, state: tuple[Array, ...], start: int, stop: int) -> tuple[Array, ...]:
        """Copies of the positions start .. stop - 1, as a state of their own."""

        return tuple(self.copy(a[:, :, start:stop]) for a in state)

    def kv_take(self, state: tuple[Array, ...], positions: Array) -> tuple[Array, ...]:
        """The positions `positions` [N] (an int array, on the device) of a state, as a state of their own."""

        return tuple(a[:, :, positions] for a in state)

    def kv_move(self, state: tuple[Array, ...], src: int, dst: int, n: int) -> tuple[Array, ...]:
        """
        The state with its n positions from `src` on moved to `dst` on (a window brought back to the front of the
        buffers it runs in: core/kvspans.py). A backend that writes buffers in place moves them there and returns
        the same arrays; the default builds new ones.
        """

        out = []
        for a in state:
            out.append(self.concat([a[:, :, :dst], a[:, :, src:src + n], a[:, :, dst + n:]], 2))
        return tuple(out)

    def kv_join(self, a: tuple[Array, ...], b: tuple[Array, ...]) -> tuple[Array, ...]:
        """Two states of one format end to end: a's positions, then b's."""

        return tuple(self.concat([x, y], 2) for x, y in zip(a, b))

    def kv_pad(self, state: tuple[Array, ...], capacity: int) -> tuple[Array, ...]:
        """The state zero-padded to `capacity` positions."""

        out = []
        for a in state:
            n = a.shape[2]
            if n < capacity:
                shape = list(a.shape)
                shape[2] = capacity - n
                a = self.concat([a, self.zeros(tuple(shape), a.dtype)], 2)
            elif n > capacity:
                raise ValueError(f'KV longer ({n}) than capacity ({capacity})')
            out.append(a)
        return tuple(out)

    # Whether buffer writes are in place (`kv_write` returns its argument) and `capture` binds a step to the arrays it
    # is first called with: what makes it worth prefilling into capacity buffers (`kv_reserve`) and keeping a
    # decoder's buffers and captured steps for the next one (core/slab.py).
    kv_in_place: bool = False

    def kv_reserve(
            self,
            state: tuple[Array, ...],
            capacity: int,
            into: tuple[Array, ...] | None = None,
    ) -> tuple[Array, ...]:
        """
        A functional state given room for `capacity` positions, where that pays: a backend whose `kv_write_tokens`
        writes in place returns capacity buffers here (`kv_pad`), and a prefill then fills them chunk by chunk instead
        of concatenating an ever-longer state (see Model.prefill). `into`: buffers of that capacity to use rather
        than new ones (an earlier decoder's: core/slab.py) -- the state's positions are copied in, and what the rest
        of them holds does not matter. The default has no in-place write to gain from and returns the state as it is.
        """

        return state

    def kv_write_state(self, state: tuple[Array, ...], pos: Array, k: Array, v: Array) -> tuple[Array, ...]:
        """The static-buffer write of one position's k, v ([B, KV, 1, D]) at `pos` (see kv_write)."""

        return (self.kv_write(state[0], pos, k), self.kv_write(state[1], pos, v))

    def kv_write_tokens(self, state: tuple[Array, ...], pos: Array, k: Array, v: Array) -> tuple[Array, ...]:
        """
        The static-buffer write of a step's T consecutive positions, k and v [B, KV, T, D], starting at `pos`: what a
        T-token step does with its new keys and values. Default: one position at a time (`kv_write_state`); a backend
        with an indexed write does all T at once, which is T times fewer small ops in every verify step.
        """

        for i in range(k.shape[2]):
            state = self.kv_write_state(state, pos + i, k[:, :, i:i + 1], v[:, :, i:i + 1])
        return state

    def sdpa_state(self, q: Array, state: tuple[Array, ...], scale: float, past: int) -> Array:
        """Prefill attention of q [B, H, T, D] over a state holding past + T positions."""

        return self.sdpa(q, state[0], state[1], scale, past)

    def kv_dense(self, state: tuple[Array, ...], dtype: ta.Any) -> tuple[Array, Array]:
        """The state's keys and values as plain [B, KV, L, D] arrays (a quantized format is dequantized to `dtype`)."""

        return state[0], state[1]

    def kv_gather(self, state: tuple[Array, ...], positions: Array, dtype: ta.Any) -> tuple[Array, Array]:
        """
        Keys and values at `positions` [N] (int) of a batch-1 state: [KV, N, D] each, plain in `dtype` -- a quantized
        format dequantizes only the gathered rows.
        """

        k, v = self.kv_dense(state, dtype)
        return k[0][:, positions], v[0][:, positions]

    def sdpa_masked(self, q: Array, k: Array, v: Array, scale: float, keep: Array) -> Array:
        """
        Attention of q [B, H, T, D] over k, v [B, KV, L, D] where `keep` [B, T, L] (1 / 0) says which keys each query
        sees: QSA's selection (core/qsa.py). The composed reference -- every key scored, the rest masked -- which a
        sparse kernel replaces.
        """

        H = q.shape[1]
        KV = k.shape[1]
        if KV != H:
            k = self.repeat(k, H // KV, 1)
            v = self.repeat(v, H // KV, 1)
        scores = self.f32(q @ self.transpose(k, (0, 1, 3, 2))) * scale  # [B, H, T, L]
        scores = scores + (1 - self.f32(keep))[:, None] * -1e30
        return self.cast(self.softmax(scores, -1), v.dtype) @ v

    def sdpa_sink(self, q: Array, k: Array, v: Array, scale: float, bias: Array, sink: Array) -> Array:
        """
        Attention of q [B, H, T, D] over k, v [B, KV, L, D] (GQA when KV < H: query head h reads kv head h // (H / KV))
        with an additive float32 `bias` [B, H, T, L] on the scores -- a learned relative term and the mask together,
        -1e30 where a query does not see a key -- and a `sink` [B, H, T]: one more logit in each query's softmax,
        with nothing behind it. A query's output is its keys' values weighted by a distribution the sink takes its
        share of, not renormalized over the keys. The composed reference, softmaxed in float32.
        """

        H = q.shape[1]
        KV = k.shape[1]
        L = k.shape[2]
        if KV != H:
            k = self.repeat(k, H // KV, 1)
            v = self.repeat(v, H // KV, 1)
        scores = self.f32(q @ self.transpose(k, (0, 1, 3, 2))) * scale + bias  # [B, H, T, L]
        p = self.softmax(self.concat([scores, self.f32(sink)[..., None]], -1), -1)
        return self.cast(p[..., :L], v.dtype) @ v

    def sdpa_partials(
            self,
            q: Array,
            k: Array,
            v: Array,
            scale: float,
            bias: Array | None = None,
    ) -> tuple[Array, Array, Array]:
        """
        Attention short of its normalization, so that one softmax can run over several sets of keys scored in
        different ways (`sdpa_merge`): for q [B, H, T, D] over k, v [B, KV, L, D], with an optional additive float32
        `bias` [B, H, T, L] on the scores, each query's largest score m [B, H, T], and relative to it the scores'
        exponentials' sum l [B, H, T] and the values weighted by them o [B, H, T, D], all float32. Grouped-query
        heads (query head h reads kv head h // (H / KV)) are folded into the matmul's rows, so the keys and values
        are never repeated. L > 0.
        """

        B, H, T, D = q.shape
        KV = k.shape[1]
        G = H // KV

        def rows(x: Array) -> Array:  # [B, H, T, ...] -> [B, KV, T * G, ...]: row t * G + g
            x = self.reshape(x, (B, KV, G, T, *x.shape[3:]))
            return self.reshape(self.transpose(x, (0, 1, 3, 2, *range(4, len(x.shape)))), (B, KV, T * G, *x.shape[4:]))

        def heads(x: Array) -> Array:  # ... and back
            x = self.reshape(x, (B, KV, T, G, *x.shape[3:]))
            return self.reshape(self.transpose(x, (0, 1, 3, 2, *range(4, len(x.shape)))), (B, H, T, *x.shape[4:]))

        s = self.f32(rows(q) @ self.transpose(k, (0, 1, 3, 2))) * scale  # [B, KV, T * G, L]
        if bias is not None:
            s = s + rows(bias)
        m = self.amax(s, -1, keepdims=True)
        p = self.exp(s - m)
        l = self.sum(p, -1)
        o = self.f32(self.cast(p, v.dtype) @ v)

        return heads(m[..., 0]), heads(l), heads(o)

    # the float32 scores a composed attention holds at a time, as (head, query, key) triples: its queries go through
    # in tiles of that many
    sdpa_tile: int = 1 << 26

    def sdpa_causal_partials(self, q: Array, k: Array, v: Array, last: int, scale: float) -> tuple[Array, Array, Array]:
        """
        `sdpa_partials` for T queries in order, of which query t sees the keys at indices 0 .. last + t of k, v
        [B, KV, L, D] and no others. `last` may be negative: a query that sees no key has m = -1e30 (and an l and o
        that weigh nothing against any finite score). The composed reference scores every key up to a tile of
        queries' last for each of them; a kernel reads each query's own.
        """

        B, H, T, D = q.shape
        f32 = self.dtype('f32')

        ms, ls, os_ = [], [], []
        tile = max(1, self.sdpa_tile // (H * max(1, min(int(k.shape[2]), last + T))))
        for a in range(0, T, tile):
            b = min(a + tile, T)
            n = min(int(k.shape[2]), last + b)
            if n <= 0:
                ms.append(self.zeros((B, H, b - a), f32) - 1e30)
                ls.append(self.zeros((B, H, b - a), f32))
                os_.append(self.zeros((B, H, b - a, D), f32))
                continue

            unseen = (
                self.array(np.arange(n, dtype=np.int32))[None, :] >
                self.array(np.arange(last + a, last + b, dtype=np.int32))[:, None]
            )
            bias = self.cast(unseen, f32)[None, None] * -1e30 + self.zeros((B, H, 1, 1), f32)
            m, l, o = self.sdpa_partials(q[:, :, a:b], k[:, :, :n], v[:, :, :n], scale, bias)
            ms.append(m)
            ls.append(l)
            os_.append(o)

        if len(ms) == 1:
            return ms[0], ls[0], os_[0]
        return self.concat(ms, 2), self.concat(ls, 2), self.concat(os_, 2)

    def sdpa_span_partials(
            self,
            q: Array,
            kbuf: Array,
            vbuf: Array,
            lo: Array,
            hi: Array,
            ar: Array,
            scale: float,
    ) -> tuple[Array, Array, Array]:
        """
        `sdpa_partials` of T queries that all see the same stretch of a fixed-capacity KV buffer: q [B, H, T, D];
        kbuf, vbuf [B, KV, L, D]; the keys at lo <= index < hi (0-d int arrays) seen and no others, ar = arange(L).
        No order among the queries -- a block drafter's (core/dspark/) -- and every shape independent of the stretch,
        so a backend can capture the step around it. An empty stretch gives m = -1e30, which weighs nothing against
        any finite score in `sdpa_merge`.
        """

        B, H, T, D = q.shape
        KV = kbuf.shape[1]
        G = H // KV
        f32 = self.dtype('f32')

        def rows(x: Array) -> Array:  # [B, H, T, ...] -> [B, KV, T * G, ...]: row t * G + g
            x = self.reshape(x, (B, KV, G, T, *x.shape[3:]))
            return self.reshape(self.transpose(x, (0, 1, 3, 2, *range(4, len(x.shape)))), (B, KV, T * G, *x.shape[4:]))

        def heads(x: Array) -> Array:  # ... and back
            x = self.reshape(x, (B, KV, T, G, *x.shape[3:]))
            return self.reshape(self.transpose(x, (0, 1, 3, 2, *range(4, len(x.shape)))), (B, H, T, *x.shape[4:]))

        seen = self.cast(ar >= lo, f32) * self.cast(ar < hi, f32)  # [L]
        s = self.f32(rows(q) @ self.transpose(kbuf, (0, 1, 3, 2))) * scale + (1 - seen) * -1e30  # [B, KV, T * G, L]
        m = self.amax(s, -1, keepdims=True)
        p = self.exp(s - m) * seen
        l = self.sum(p, -1)
        o = self.f32(self.cast(p, vbuf.dtype) @ vbuf)

        return heads(m[..., 0]), heads(l), heads(o)

    def sdpa_merge(self, parts: ta.Sequence[tuple[Array, Array, Array]], sink: Array | None, dtype: ta.Any) -> Array:
        """
        The attention output [B, H, T, D] in `dtype` of one softmax over the sets of keys whose `sdpa_partials` are
        `parts`, and -- with `sink` [B, H, T] -- one more logit with nothing behind it (`sdpa_sink`).
        """

        f32 = self.dtype('f32')
        ms = [m for m, _, _ in parts]
        if sink is not None:
            sink = self.cast(sink, f32)
            ms.append(sink)
        top = ms[0]
        for m in ms[1:]:
            top = self.maximum_of(top, m)

        num: ta.Any = None
        den: ta.Any = None
        for m, l, o in parts:
            w = self.exp(m - top)
            num = w[..., None] * o if num is None else num + w[..., None] * o
            den = w * l if den is None else den + w * l
        if sink is not None:
            den = den + self.exp(sink - top)

        return self.cast(num / den[..., None], dtype)

    def maximum_of(self, a: Array, b: Array) -> Array:
        """Elementwise maximum of two arrays of a shape (composed: a + relu(b - a))."""

        return a + self.maximum(b - a, 0.)

    def sdpa_window_rel(
            self,
            q: Array,
            k: Array,
            v: Array,
            pos: Array,
            *,
            scale: float,
            rel: Array,
            rel_proj: Weight,
            sink: Array,
            window: int,
            more: ta.Sequence[tuple[Array, Array, Array]] = (),
    ) -> Array:
        """
        Attention of T queries q [B, H, T, D] at positions pos.. over a window's keys and values k, v [B, KV, N, D]
        (plain arrays), slot j standing for position pos + T - N + j -- no position where that is negative. A query
        sees the keys 0 <= d < `window` positions back. Each score has a relative term, rel[t, h] . rel_proj[d] for a
        key d back (`rel` [T, H, R], `rel_proj` [E, R]; nothing for d >= E), and each softmax one more logit, `sink`
        [B, H, T], with nothing behind it (`sdpa_sink`). [B, H, T, D] in q's dtype. Batch 1.

        `more`: other sets of keys under the same softmax, as their `sdpa_partials` -- the keys of a layer that sees
        everything which lie further back than the window, scored without the term.
        """

        f32 = self.dtype('f32')
        T = q.shape[2]
        N = k.shape[2]

        table = self.f32(self.linear(rel, rel_proj))  # [T, H, E]: each query's term by distance
        qpos = self.reshape(pos, (1,)) + self.arange(T)
        kpos = (self.reshape(pos, (1,)) + (T - N)) + self.arange(N)
        delta = qpos[:, None] - kpos[None, :]
        seen = self.cast(delta >= 0, f32) * self.cast(delta < window, f32) * self.cast(kpos >= 0, f32)[None, :]
        bias = self.rel_bias(table, qpos, kpos) + ((1 - seen) * -1e30)[..., None]  # [T, N, H]
        bias = self.transpose(bias, (2, 0, 1))[None]

        if not more:
            return self.sdpa_sink(q, k, v, scale, bias, sink)
        return self.sdpa_merge([self.sdpa_partials(q, k, v, scale, bias), *more], sink, q.dtype)

    def sdpa_window_rel_at(
            self,
            q: Array,
            state: tuple[Array, ...],
            base: Array,
            slots: int,
            pos: Array,
            *,
            scale: float,
            rel: Array,
            rel_proj: Weight,
            sink: Array,
            window: int,
    ) -> Array:
        """
        `sdpa_window_rel` over a window kept inside a KV state: the state's `slots` positions from `base` on (a 0-d
        int array), slot j of them standing for position pos + T - slots + j. The composed form gathers them, plain
        in q's dtype; a backend's kernel reads them where they are, and the window is then never moved to be read.
        """

        k, v = self.kv_gather(state, self.reshape(base, (1,)) + self.arange(slots), q.dtype)
        return self.sdpa_window_rel(
            q,
            k[None],
            v[None],
            pos,
            scale=scale,
            rel=rel,
            rel_proj=rel_proj,
            sink=sink,
            window=window,
        )

    def rel_bias(self, rel: Array, qpos: Array, kpos: Array) -> Array:
        """
        A relative term on attention scores: `rel` [t, H, E] float32 is each of t queries' bias, per head, for a key
        d = 0 .. E - 1 positions back; `qpos` [t] and `kpos` [n] are integer positions on the device. [t, n, H]
        float32: rel[i, h, qpos[i] - kpos[j]] where that distance is one of the E, 0 where it is not.
        """

        f32 = self.dtype('f32')
        t, H, E = (int(d) for d in rel.shape)

        delta = qpos[:, None] - kpos[None, :]  # [t, n]
        within = self.cast(delta >= 0, f32) * self.cast(delta < E, f32)

        # each query's row gathered by distance: a row index into the [t * E, H] table
        rows = self.minimum(self.maximum(delta, 0), E - 1) + (self.arange(t) * E)[:, None]
        table = self.reshape(self.transpose(rel, (0, 2, 1)), (t * E, H))
        return self.embedding(rows, table, f32) * within[..., None]

    def sdpa_static_rel(
            self,
            q: Array,
            state: tuple[Array, ...],
            pos: Array,
            ar: Array,
            scale: float,
            rel: Array,
            rel_proj: Weight,
            sink: Array,
    ) -> Array:
        """
        Decode attention for T new tokens against fixed-capacity KV buffers (as `sdpa_static_state`: q [B, H, T, D]
        at positions pos..pos+T-1, `state` holding positions 0..pos+T-1, `ar` = arange over the buffer) with a
        relative term and a sink. Query t's score for the key d positions back is q . k * scale, plus rel[t, h] .
        rel_proj[d] for the d < E nearest (`rel` [T, H, R], `rel_proj` [E, R]: as `sdpa_window_rel`); each softmax
        has one more logit, `sink` [B, H, T], with nothing behind it (`sdpa_sink`). Batch 1. The composed reference
        reads the whole buffer; a kernel reads the positions in use.
        """

        f32 = self.dtype('f32')
        T = q.shape[2]
        n = self.kv_len(state)

        kd, vd = self.kv_dense(state, q.dtype)
        qpos = self.reshape(pos, (1,)) + self.arange(T)
        kpos = ar[:n]

        table = self.f32(self.linear(rel, rel_proj))  # [T, H, E]: each query's term by distance back
        unseen = self.cast(kpos[None, :] > qpos[:, None], f32) * -1e30  # [T, n]
        bias = self.rel_bias(table, qpos, kpos) + unseen[..., None]
        return self.sdpa_sink(q, kd, vd, scale, self.transpose(bias, (2, 0, 1))[None], sink)

    def sdpa_static_state(self, q: Array, state: tuple[Array, ...], pos: Array, ar: Array, scale: float) -> Array:
        """Decode attention of q over the static buffers (see sdpa_static)."""

        return self.sdpa_static(q, state[0], state[1], pos, ar, scale)

    # False when `sdpa_static` does work proportional to `pos` on its own (a length-aware kernel reading `pos` inside
    # one fixed graph); True when it reads whatever buffer it is given, so the Decoder should hand it a
    # power-of-two-sized slice ("bucket") and capture a step per bucket
    attn_bucketed: bool = True

    def sdpa_static(self, q: Array, kbuf: Array, vbuf: Array, pos: Array, ar: Array, scale: float) -> Array:
        """
        Attention for T new tokens against a fixed-capacity KV buffer. q: [B, H, T, D] for positions pos..pos+T-1; kbuf,
        vbuf: [B, KV, L, D] with positions 0..pos+T-1 valid; ar: arange(L); pos: 0-d int array. Query i sees keys <= pos
        + i. Grouped-query heads are folded into the matmul batch so the buffer is never repeated. Scores are masked
        additively and softmaxed in float32; every shape is independent of `pos`, which is what lets a backend capture
        the whole step. T == 1 is decode, T == k + 1 is speculative verify.
        """

        B, H, T, D = q.shape
        KV = kbuf.shape[1]
        L = kbuf.shape[2]
        G = H // KV
        qg = self.reshape(self.transpose(self.reshape(q, (B, KV, G, T, D)), (0, 1, 3, 2, 4)), (B, KV, T * G, D))
        scores = self.f32(qg @ self.transpose(kbuf, (0, 1, 3, 2))) * scale  # [B, KV, T*G, L]
        f32 = self.dtype('f32')
        qpos = pos + self.arange(T)  # [T]
        mask = self.cast(ar[None, :] > qpos[:, None], f32) * -1e30  # [T, L]
        mask = self.reshape(self.repeat(mask, G, 0), (1, 1, T * G, L))  # row t*G + g
        p = self.softmax(scores + mask, -1)
        o = self.cast(p, vbuf.dtype) @ vbuf  # [B, KV, T*G, D]
        o = self.transpose(self.reshape(o, (B, KV, T, G, D)), (0, 1, 3, 2, 4))  # [B, KV, G, T, D]
        return self.reshape(o, (B, H, T, D))

    def compile_fn(self, fn: ta.Callable[..., tuple[Array, ...]]) -> ta.Callable[..., tuple[Array, ...]]:
        """
        Trace-and-fuse a pure step function once, independent of which buffers it will later run on (torch:
        `torch.compile`). Called once per step shape by the model; `capture` then wraps the result per Decoder. Default:
        identity.
        """

        return fn

    def capture_carrying(
            self,
            fn: ta.Callable[..., tuple[Array, ...]],
            outputs_from: int,
            inputs_from: int,
    ) -> ta.Callable[..., tuple[Array, ...]]:
        """
        `capture` for a step whose outputs from index `outputs_from` on are what its next call takes as its arguments
        from `inputs_from` on -- a state that goes round, the same arrays in shape. A backend may then carry it forward
        itself, and hand back as those outputs arrays that the next call takes as they are. Default: `capture`.
        """

        return self.capture(fn)

    # Whether `capture` takes a function that draws tokens (`Sampler.probs` / `draw` on noise passed in) between
    # model steps as well as it takes one step: the draft head then drafts a run of tokens in one captured call
    # (spec/mtp.py) rather than a step and a dozen sampling launches a token.
    capture_sampling: bool = False

    def capture(self, fn: ta.Callable[..., tuple[Array, ...]]) -> ta.Callable[..., tuple[Array, ...]]:
        """
        Make a static-shape step callable fast: CUDA graphs on torch, `mx.compile` on MLX, `TinyJit` on tinygrad. `fn`
        takes and returns flat tuples of arrays and must be pure apart from `kv_write`. Returned arrays are only valid
        until the next call. The default is the identity.
        """

        return fn

    # instrumentation

    def tap(self, name: str, x: Array) -> None:
        if self.taps is not None:
            self.taps[name] = self.numpy(x)
