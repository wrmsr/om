# ruff: noqa: N803 N806 N812
import typing as ta

from omcore import lang

from .base import DTYPE_NAMES
from .base import Ops


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


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

    def weight(self, w, dtype, name=None):
        return np.asarray(w, dtype=dtype)

    def qweight(self, qw, dtype, name=None):
        return np.asarray(qw.dequantize(), dtype=dtype)

    def linear(self, x, w):
        return x @ w.T

    def embedding(self, ids, w, dtype):
        return np.asarray(w[ids], dtype=dtype)
