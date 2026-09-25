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

from .quant import QWeight
from .quant import quantize as quantize_np


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


##


Array: ta.TypeAlias = ta.Any  # a backend array (np.ndarray, torch.Tensor, mx.array, ...)
Weight: ta.TypeAlias = ta.Any  # a backend dense array or a backend-adopted QWeight

DTYPE_NAMES = (
    'f32',
    'f16',
    'bf16',
    'i32',
)


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
    def weight(self, w: np.ndarray, dtype: ta.Any) -> Weight:
        """Adopt a dense parameter."""

    @abc.abstractmethod
    def qweight(self, qw: QWeight, dtype: ta.Any) -> Weight:
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
    ) -> Weight:
        """Quantize + adopt (see quant.quantize for `search`). Backends may override to quantize on-device."""

        return self.qweight(quantize_np(w, bits, group, search), dtype)

    def export_qweight(self, w: Weight) -> QWeight:
        """
        The inverse of `qweight`: a backend-adopted quantized weight back to numpy (for the parameter cache). Backends
        that cannot raise NotImplementedError and the caller quantizes on the host instead.
        """

        raise NotImplementedError

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

    gdn_fused_max_t: int = 8  # up to this many tokens the model calls `gdn_step` (fusable); beyond, the chunked path

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


##


class NumpyOps(Ops):
    """
    Reference backend. Every dtype name maps to `precision` (float64 by default) so it doubles as the golden oracle;
    quantized weights are dequantized at adoption time.
    """

    name = 'numpy'

    def __init__(self, precision: ta.Any = 'float64') -> None:
        super().__init__()

        self.precision = np.dtype(precision)

    def dtype(self, name):
        if name not in DTYPE_NAMES:
            raise ValueError(name)
        if name == 'i32':
            return np.int32
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

    def arange(self, n):
        return np.arange(n, dtype=np.int32)

    def scalar(self, v):
        return np.array(v, dtype=np.int32)

    def kv_write(self, buf, pos, x):
        buf[:, :, int(pos)] = x[:, :, 0]
        return buf

    def cumsum(self, x, axis):
        return np.cumsum(x, axis=axis)

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

    def log(self, x):
        return np.log(x)

    def argmax(self, x, axis):
        return np.argmax(x, axis=axis).astype(np.int32)

    def amax(self, x, axis, keepdims=False):
        return np.amax(x, axis=axis, keepdims=keepdims)

    def topk(self, x, k):
        idx = np.argsort(-x, axis=-1, kind='stable')[..., :k]
        return np.take_along_axis(x, idx, axis=-1), idx.astype(np.int32)

    def seed(self, seed):
        self.rng = np.random.default_rng(seed)

    def random_uniform(self, shape):
        if not hasattr(self, 'rng'):
            self.rng = np.random.default_rng(0)
        return self.rng.random(shape, dtype=np.float32)

    def index_add(self, x, idx, vals):
        out = np.array(x, copy=True)
        np.add.at(out, np.asarray(idx, dtype=np.int64), np.asarray(vals, dtype=out.dtype))
        return out

    def weight(self, w, dtype):
        return np.asarray(w, dtype=dtype)

    def qweight(self, qw, dtype):
        return np.asarray(qw.dequantize(), dtype=dtype)

    def linear(self, x, w):
        return x @ w.T

    def embedding(self, ids, w, dtype):
        return np.asarray(w[ids], dtype=dtype)
