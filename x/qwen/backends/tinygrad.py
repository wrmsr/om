# ruff: noqa: N806 N812
"""
tinygrad backend for `Ops`.

tinygrad is lazy: every op appends to a graph and nothing runs until `.realize()` / `.numpy()`. `eval()` forces it. Like
MLX, the per-token `gated_delta` reference builds a T-step graph, so a chunked prefill (behind `Ops.gated_delta`) is
required for long prompts here, not just an optimisation. `TinyJit` around the decode step is the other bolt-on.

Overrides: sdpa (Tensor.scaled_dot_product_attention), conv1d_causal (grouped conv2d). Everything else is the composed
reference. Quantized weights are unpacked and expanded per matmul (as on torch).
"""
import dataclasses as dc
import math
import typing as ta

import numpy as np
from tinygrad import Device
from tinygrad import Tensor
from tinygrad import dtypes

from ..ops import Ops
from ..quant import QWeight


##


DTYPES = {'f32': dtypes.float32, 'f16': dtypes.float16, 'bf16': dtypes.bfloat16}


@dc.dataclass()
class TinyQWeight:
    q: Tensor  # uint8, packed as in quant.QWeight
    scale: Tensor  # compute dtype
    bias: Tensor
    bits: int
    group: int
    shape: tuple[int, int]

    def nbytes(self) -> int:
        return self.q.nbytes() + self.scale.nbytes() + self.bias.nbytes()

    def dequant(self, dtype: ta.Any, rows: slice | Tensor | None = None) -> Tensor:
        q = self.q if rows is None else self.q[rows]
        s = self.scale if rows is None else self.scale[rows]
        b = self.bias if rows is None else self.bias[rows]
        if self.bits == 4:
            q = Tensor.stack(q & 0xF, q >> 4, dim=-1).reshape(q.shape[0], -1)
        n = q.shape[0]
        x = q.reshape(n, -1, self.group).cast(dtype)
        x = x * s[..., None].cast(dtype) + b[..., None].cast(dtype)
        return x.reshape(n, self.shape[1])

    def linear(self, x: Tensor, chunk_rows: int = 16384) -> Tensor:
        out = self.shape[0]
        if out <= chunk_rows:
            return x @ self.dequant(x.dtype).T
        return Tensor.cat(
            *[x @ self.dequant(x.dtype, slice(i, i + chunk_rows)).T for i in range(0, out, chunk_rows)],
            dim=-1,
        )


class TinygradOps(Ops):
    name = 'tinygrad'

    def __init__(self, device: str | None = None) -> None:
        super().__init__()

        self.device = device or Device.DEFAULT
        self.name = f'tinygrad:{self.device}'

    def dtype(self, name):
        return DTYPES[name]

    def array(self, a, dtype=None):
        a = np.ascontiguousarray(a)
        if not a.flags.writeable:
            a = a.copy()
        t = Tensor(a, device=self.device)
        if dtype is not None and t.dtype != dtype:
            t = t.cast(dtype)
        return t

    def numpy(self, x):
        if x.dtype in (dtypes.bfloat16, dtypes.float16):
            x = x.cast(dtypes.float32)
        return x.numpy()

    def cast(self, x, dtype):
        return x.cast(dtype)

    def copy(self, x):
        return x.clone()

    def zeros(self, shape, dtype):
        return Tensor.zeros(*shape, dtype=dtype, device=self.device)

    def eval(self, *xs):
        if xs:
            Tensor.realize(*xs)

    def nbytes(self, w):
        if isinstance(w, TinyQWeight):
            return w.nbytes()
        return w.nbytes()

    def reshape(self, x, shape):
        return x.reshape(shape)

    def transpose(self, x, axes):
        return x.permute(axes)

    def concat(self, xs, axis):
        xs = list(xs)
        return Tensor.cat(*xs, dim=axis)

    def stack(self, xs, axis):
        xs = list(xs)
        return Tensor.stack(*xs, dim=axis)

    def split(self, x, sizes, axis):
        return list(x.split(list(sizes), dim=axis))

    def repeat(self, x, n, axis):
        return x.repeat_interleave(n, dim=axis)

    def cumsum(self, x, axis):
        return x.cumsum(axis)

    def exp(self, x):
        return x.exp()

    def rsqrt(self, x):
        return x.rsqrt()

    def sum(self, x, axis, keepdims=False):
        return x.sum(axis, keepdim=keepdims)

    def mean(self, x, axis, keepdims=False):
        return x.mean(axis, keepdim=keepdims)

    def sigmoid(self, x):
        return x.sigmoid()

    def softplus(self, x):
        return x.softplus()

    def silu(self, x):
        return x.silu()

    def softmax(self, x, axis):
        return x.softmax(axis)

    # weights

    def weight(self, w, dtype):
        return self.array(w, dtype).realize()

    def qweight(self, qw: QWeight, dtype):
        return TinyQWeight(
            self.array(qw.q).realize(),
            self.array(qw.scale, dtype).realize(),
            self.array(qw.bias, dtype).realize(),
            qw.bits,
            qw.group,
            qw.shape,
        )

    def linear(self, x, w):
        if isinstance(w, TinyQWeight):
            return w.linear(x)
        return x @ w.T

    def embedding(self, ids, w, dtype):
        if isinstance(w, TinyQWeight):
            return w.dequant(dtype, ids.reshape(-1)).reshape(*ids.shape, w.shape[1])
        return w[ids].cast(dtype)

    # fused overrides

    def sdpa(
            self,
            q,
            k,
            v,
            scale,
            past,
    ):
        B, H, T, D = q.shape
        KV, L = k.shape[1], k.shape[2]
        if abs(scale * math.sqrt(D) - 1.0) > 1e-6:  # tinygrad's SDPA has no scale argument
            return super().sdpa(q, k, v, scale, past)
        if KV != H:
            k = k.repeat_interleave(H // KV, dim=1)
            v = v.repeat_interleave(H // KV, dim=1)
        if T == 1:
            return q.scaled_dot_product_attention(k, v)
        mask = self.array(np.tril(np.ones((T, L), dtype=bool), k=past))
        return q.scaled_dot_product_attention(k, v, attn_mask=mask)

    def conv1d_causal(self, x, w):
        C, K = w.shape
        return x.conv2d(w.reshape(C, 1, K), groups=C)

    def rope(
            self,
            x,
            offset,
            dims,
            theta,
    ):
        key = (offset, x.shape[2], dims, theta, x.dtype)
        tabs = self.__dict__.setdefault('_rope_cache', {})
        if key not in tabs:
            if len(tabs) > 256:
                tabs.clear()
            cos_np, sin_np = self.rope_tables(offset, x.shape[2], dims, theta)
            tabs[key] = (self.array(cos_np, x.dtype).realize(), self.array(sin_np, x.dtype).realize())
        cos, sin = tabs[key]
        xr, xp = x[..., :dims], x[..., dims:]
        half = dims // 2
        rot = Tensor.cat(-xr[..., half:], xr[..., :half], dim=-1)
        return Tensor.cat(xr * cos[None, None] + rot * sin[None, None], xp, dim=-1)
