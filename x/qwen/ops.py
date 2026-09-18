# ruff: noqa: N806 N812
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

import numpy as np

from .quant import QWeight
from .quant import quantize as quantize_np


##


Array = ta.Any  # a backend array (np.ndarray, torch.Tensor, mx.array, ...)
Weight = ta.Any  # a backend dense array or a backend-adopted QWeight

DTYPE_NAMES = ('f32', 'f16', 'bf16')


class Ops(abc.ABC):
    name: str = '?'

    def __init__(self) -> None:
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

    @abc.abstractmethod
    def cast(self, x: Array, dtype: ta.Any) -> Array:
        pass

    def f32(self, x: Array) -> Array:
        return self.cast(x, self.dtype('f32'))

    @abc.abstractmethod
    def copy(self, x: Array) -> Array:
        pass

    @abc.abstractmethod
    def zeros(self, shape: tuple[int, ...], dtype: ta.Any) -> Array:
        pass

    def eval(self, *xs: Array) -> None:
        """Force computation on lazy backends; no-op elsewhere."""

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

    @abc.abstractmethod
    def stack(self, xs: ta.Sequence[Array], axis: int) -> Array:
        pass

    @abc.abstractmethod
    def split(self, x: Array, sizes: ta.Sequence[int], axis: int) -> list[Array]:
        pass

    @abc.abstractmethod
    def repeat(self, x: Array, n: int, axis: int) -> Array:
        """repeat_interleave: each slice along `axis` repeated `n` times consecutively."""

    # elementwise / reductions

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
    def softmax(self, x: Array, axis: int) -> Array:
        pass

    # weights

    @abc.abstractmethod
    def weight(self, w: np.ndarray, dtype: ta.Any) -> Weight:
        """Adopt a dense parameter."""

    @abc.abstractmethod
    def qweight(self, qw: QWeight, dtype: ta.Any) -> Weight:
        """Adopt an already-quantized parameter (scale/bias stored in `dtype`)."""

    def quantize(self, w: np.ndarray, bits: int, group: int, dtype: ta.Any) -> Weight:
        """Quantize + adopt. Backends may override to quantize on-device."""

        return self.qweight(quantize_np(w, bits, group), dtype)

    @abc.abstractmethod
    def linear(self, x: Array, w: Weight) -> Array:
        """x @ w.T for a dense or quantized weight."""

    @abc.abstractmethod
    def embedding(self, ids: Array, w: Weight, dtype: ta.Any) -> Array:
        """Row gather -> [..., in] in `dtype`."""

    # fused-able model primitives (reference implementations)

    def rms_norm(self, x: Array, w: Array, eps: float) -> Array:
        xf = self.f32(x)
        y = xf * self.rsqrt(self.mean(xf * xf, -1, keepdims=True) + eps)
        return self.cast(y * self.f32(w), x.dtype)

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
        cos = self.array(cos_np, x.dtype)
        sin = self.array(sin_np, x.dtype)
        xr, xp = x[..., :dims], x[..., dims:]
        half = dims // 2
        x1, x2 = xr[..., :half], xr[..., half:]
        rot = self.concat([-x2, x1], axis=-1)
        xr = xr * cos[None, None] + rot * sin[None, None]
        return self.concat([xr, xp], axis=-1)

    def sdpa(self, q: Array, k: Array, v: Array, scale: float, past: int) -> Array:
        """Causal attention. q: [B, H, T, D]; k, v: [B, KV, past + T, D] (GQA when KV < H). Query i sees keys
        <= past + i."""

        B, H, T, D = q.shape
        KV, L = k.shape[1], k.shape[2]
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

    def gated_delta(self, q: Array, k: Array, v: Array, g: Array, beta: Array, state: Array) -> tuple[Array, Array]:
        """
        Per-token gated delta rule (reference). All float32.

        q, k:  [B, H, T, dk] (already l2-normed; q already scaled by 1/sqrt(dk))
        v:     [B, H, T, dv]
        g:     [B, H, T]  log decay (<= 0);   beta: [B, H, T] in (0, 1)
        state: [B, H, dk, dv]
        returns out [B, H, T, dv], new state
        """

        T = q.shape[2]
        S = state
        outs = []
        for t in range(T):
            q_t, k_t, v_t = q[:, :, t], k[:, :, t], v[:, :, t]  # [B,H,dk] / [B,H,dv]
            S = S * self.exp(g[:, :, t])[..., None, None]  # decay
            mem = self.sum(S * k_t[..., None], -2)  # k^T S -> [B,H,dv]
            delta = (v_t - mem) * beta[:, :, t][..., None]
            S = S + k_t[..., None] * delta[..., None, :]  # rank-1 update
            outs.append(self.sum(S * q_t[..., None], -2))  # q^T S
        return self.stack(outs, 2), S

    # instrumentation

    def tap(self, name: str, x: Array) -> None:
        if self.taps is not None:
            self.taps[name] = self.numpy(x)


##


class NumpyOps(Ops):
    """Reference backend. Every dtype name maps to `precision` (float64 by default) so it doubles as the golden
    oracle; quantized weights are dequantized at adoption time."""

    name = 'numpy'

    def __init__(self, precision: ta.Any = np.float64) -> None:
        super().__init__()
        self.precision = np.dtype(precision)

    def dtype(self, name):
        if name not in DTYPE_NAMES:
            raise ValueError(name)
        return self.precision

    def array(self, a, dtype=None):
        return np.asarray(a, dtype=dtype if dtype is not None else (self.precision if np.issubdtype(a.dtype, np.floating) else None))  # noqa

    def numpy(self, x):
        return np.asarray(x)

    def cast(self, x, dtype):
        return np.asarray(x, dtype=dtype)

    def copy(self, x):
        return np.array(x, copy=True)

    def zeros(self, shape, dtype):
        return np.zeros(shape, dtype=dtype)

    def nbytes(self, w):
        return w.nbytes

    def reshape(self, x, shape):
        return np.reshape(x, shape)

    def transpose(self, x, axes):
        return np.transpose(x, axes)

    def concat(self, xs, axis):
        return np.concatenate(list(xs), axis=axis)

    def stack(self, xs, axis):
        return np.stack(list(xs), axis=axis)

    def split(self, x, sizes, axis):
        return np.split(x, np.cumsum(sizes)[:-1], axis=axis)

    def repeat(self, x, n, axis):
        return np.repeat(x, n, axis=axis)

    def exp(self, x):
        return np.exp(x)

    def rsqrt(self, x):
        return 1.0 / np.sqrt(x)

    def sum(self, x, axis, keepdims=False):
        return np.sum(x, axis=axis, keepdims=keepdims)

    def mean(self, x, axis, keepdims=False):
        return np.mean(x, axis=axis, keepdims=keepdims)

    def sigmoid(self, x):
        return 1.0 / (1.0 + np.exp(-x))

    def softplus(self, x):
        return np.logaddexp(x, 0.0)

    def softmax(self, x, axis):
        m = np.max(x, axis=axis, keepdims=True)
        e = np.exp(x - m)
        return e / np.sum(e, axis=axis, keepdims=True)

    def weight(self, w, dtype):
        return np.asarray(w, dtype=dtype)

    def qweight(self, qw, dtype):
        return np.asarray(qw.dequantize(), dtype=dtype)

    def linear(self, x, w):
        return x @ w.T

    def embedding(self, ids, w, dtype):
        return np.asarray(w[ids], dtype=dtype)
