# ruff: noqa: N806 N812
"""
MLX backend for `Ops`, talking to `mlx.core` directly (no mlx-lm / mlx.nn).

Overrides: rms_norm (mx.fast.rms_norm), rope (mx.fast.rope), sdpa (mx.fast.scaled_dot_product_attention, GQA native),
quantized linear (mx.quantized_matmul -- our QWeight *is* MLX's affine layout, so the packed words go in untouched),
on-device quantize (mx.quantize). `gated_delta` uses the composed reference; an `mx.fast.metal_kernel` for the per-token
step and `mx.compile` around the decode step are the next steps.

MLX is lazy: nothing runs until something is evaluated. `eval()` forces it; `numpy()` does implicitly.
"""
import dataclasses as dc

import mlx.core as mx
import numpy as np

from ..ops import Ops
from ..quant import QWeight


##


DTYPES = {
    'f32': mx.float32,
    'f16': mx.float16,
    'bf16': mx.bfloat16,
}


@dc.dataclass()
class MlxQWeight:
    w: mx.array  # uint32 [out, in * bits // 32], MLX packed layout
    scales: mx.array  # [out, in // group], compute dtype
    biases: mx.array
    bits: int
    group: int
    shape: tuple[int, int]

    def nbytes(self) -> int:
        return self.w.nbytes + self.scales.nbytes + self.biases.nbytes

    def linear(self, x: mx.array) -> mx.array:
        return mx.quantized_matmul(
            x.astype(self.scales.dtype),
            self.w,
            self.scales,
            self.biases,
            transpose=True,
            group_size=self.group,
            bits=self.bits,
        )

    def dequant(self, rows: mx.array | None = None) -> mx.array:
        if rows is None:
            return mx.dequantize(
                self.w,
                self.scales,
                self.biases,
                self.group,
                self.bits,
            )

        else:
            return mx.dequantize(
                self.w[rows],
                self.scales[rows],
                self.biases[rows],
                self.group,
                self.bits,
            )


class MlxOps(Ops):
    name = 'mlx'

    def __init__(self) -> None:
        super().__init__()

        self.name = f'mlx:{mx.default_device()}'

    def dtype(self, name):
        return DTYPES[name]

    def array(self, a, dtype=None):
        a = np.ascontiguousarray(a)
        return mx.array(a, dtype=dtype) if dtype is not None else mx.array(a)

    def numpy(self, x):
        if x.dtype in (mx.bfloat16, mx.float16):
            x = x.astype(mx.float32)
        return np.array(x)

    def cast(self, x, dtype):
        return x.astype(dtype)

    def copy(self, x):
        return mx.array(x)

    def zeros(self, shape, dtype):
        return mx.zeros(shape, dtype=dtype)

    def eval(self, *xs):
        mx.eval(*xs)

    def nbytes(self, w):
        if isinstance(w, MlxQWeight):
            return w.nbytes()
        return w.nbytes

    def reshape(self, x, shape):
        return mx.reshape(x, shape)

    def transpose(self, x, axes):
        return mx.transpose(x, axes)

    def concat(self, xs, axis):
        return mx.concatenate(list(xs), axis=axis)

    def stack(self, xs, axis):
        return mx.stack(list(xs), axis=axis)

    def split(self, x, sizes, axis):
        return list(mx.split(x, np.cumsum(sizes)[:-1].tolist(), axis=axis))

    def repeat(self, x, n, axis):
        return mx.repeat(x, n, axis=axis)

    def arange(self, n):
        return mx.arange(n, dtype=mx.int32)

    def scalar(self, v):
        return mx.array(v, dtype=mx.int32)

    def kv_write(self, buf, pos, x):
        # item assignment on a preallocated buffer is what mlx-lm's KVCache does; MLX updates in place when it
        # can and `mx.compile` treats `pos` as a runtime input (checked)
        buf[:, :, pos] = x[:, :, 0].astype(buf.dtype)
        return buf

    def cumsum(self, x, axis):
        return mx.cumsum(x, axis=axis)

    def exp(self, x):
        return mx.exp(x)

    def rsqrt(self, x):
        return mx.rsqrt(x)

    def sum(self, x, axis, keepdims=False):
        return mx.sum(x, axis=axis, keepdims=keepdims)

    def mean(self, x, axis, keepdims=False):
        return mx.mean(x, axis=axis, keepdims=keepdims)

    def sigmoid(self, x):
        return mx.sigmoid(x)

    def softplus(self, x):
        return mx.logaddexp(x, 0.0)

    def softmax(self, x, axis):
        return mx.softmax(x, axis=axis)

    # weights

    def weight(self, w, dtype):
        return self.array(w, dtype)

    def qweight(self, qw: QWeight, dtype):
        return MlxQWeight(
            mx.array(qw.words()),
            self.array(qw.scale, dtype),
            self.array(qw.bias, dtype),
            qw.bits,
            qw.group,
            qw.shape,
        )

    def quantize(
            self,
            w,
            bits,
            group,
            dtype,
    ):
        wq, scales, biases = mx.quantize(
            self.array(w, mx.float32),
            group_size=group,
            bits=bits,
        )
        return MlxQWeight(wq, scales.astype(dtype), biases.astype(dtype), bits, group, tuple(w.shape))

    def export_qweight(self, w):
        if not isinstance(w, MlxQWeight):
            raise NotImplementedError
        words = np.array(w.w)  # uint32, MLX packed layout == quant.QWeight's bytes (first value in the low bits)
        return QWeight(
            np.ascontiguousarray(words).view(np.uint8),
            np.array(w.scales.astype(mx.float32)),
            np.array(w.biases.astype(mx.float32)),
            w.bits,
            w.group,
            w.shape,
        )

    def linear(self, x, w):
        if isinstance(w, MlxQWeight):
            return w.linear(x)
        return x @ w.T

    def embedding(self, ids, w, dtype):
        if isinstance(w, MlxQWeight):
            return w.dequant(ids.reshape(-1)).reshape(*ids.shape, w.shape[1]).astype(dtype)
        return w[ids].astype(dtype)

    # fused overrides

    def rms_norm(self, x, w, eps):
        return mx.fast.rms_norm(x.astype(mx.float32), w.astype(mx.float32), eps).astype(x.dtype)

    def rope(self, x, offset, dims, theta):
        return mx.fast.rope(
            x,
            dims,
            traditional=False,
            base=theta,
            scale=1.0,
            offset=offset,
        )

    def capture(self, fn):
        cf = mx.compile(fn)

        def run(*args):
            out = cf(*args)
            mx.eval(*out)
            return out

        return run

    def sdpa(self, q, k, v, scale, past):
        T, L = q.shape[2], k.shape[2]
        if T == 1:
            return mx.fast.scaled_dot_product_attention(q, k, v, scale=scale)
        if past == 0 and T == L:
            return mx.fast.scaled_dot_product_attention(q, k, v, scale=scale, mask='causal')
        mask = mx.array(np.tril(np.ones((T, L), dtype=bool), k=past))
        return mx.fast.scaled_dot_product_attention(q, k, v, scale=scale, mask=mask)
