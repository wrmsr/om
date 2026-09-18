"""
Weight-only affine quantization, backend-agnostic.

    w ≈ q * scale + bias        q: unsigned `bits`-bit, one (scale, bias) per `group` consecutive inputs

This is exactly MLX's `mx.quantize` affine layout (int4/int8, group 64), so Ollama tensor blobs that are already
MLX-quantized are re-packed bit-for-bit, and the MLX backend hands the words straight to `mx.quantized_matmul`.

A `QWeight` is plain numpy; each backend adopts it into its own container (see `Ops.qweight`). Storage per parameter:
int8 = 1 byte, int4 = 0.5 byte, plus 2 * sizeof(dtype) / group for scale + bias (~0.06 byte at group 64, bf16). A 27B
model lands at ~28 GB (int8) or ~15 GB (int4).
"""
import dataclasses as dc

import numpy as np


##


QUANT_BITS = {'int8': 8, 'int4': 4}
DEFAULT_GROUP = 64


@dc.dataclass()
class QWeight:
    q: np.ndarray  # uint8 [out, in] (int8) or [out, in // 2] (int4, low nibble first)
    scale: np.ndarray  # float32 [out, in // group]
    bias: np.ndarray  # float32 [out, in // group]
    bits: int
    group: int
    shape: tuple[int, int]  # (out, in)

    def nbytes(self, scale_bytes: int = 2) -> int:
        return self.q.nbytes + 2 * self.scale.size * scale_bytes

    def unpacked(self) -> np.ndarray:
        """uint8 [out, in], one value per element."""

        if self.bits == 8:
            return self.q
        return np.stack([self.q & 0xF, self.q >> 4], axis=-1).reshape(self.shape)

    def words(self) -> np.ndarray:
        """uint32 [out, in * bits // 32] in MLX's packed layout (little-endian, first value in the low bits)."""

        return np.ascontiguousarray(self.q).view(np.uint32)

    def dequantize(self, rows: slice | np.ndarray | None = None) -> np.ndarray:
        """float32 [rows, in]."""

        q = self.unpacked()
        s = self.scale
        b = self.bias
        if rows is not None:
            q = q[rows]
            s = s[rows]
            b = b[rows]
        n = q.shape[0]
        x = q.reshape(n, -1, self.group).astype(np.float32)
        x = x * s[..., None] + b[..., None]
        return x.reshape(n, self.shape[1])


##


def pack(values: np.ndarray, bits: int) -> np.ndarray:
    """uint8 values [out, in] -> storage layout."""

    v = values.astype(np.uint8)
    if bits == 8:
        return np.ascontiguousarray(v)
    return np.ascontiguousarray(v[:, 0::2] | (v[:, 1::2] << 4))


def quantize(w: np.ndarray, bits: int, group: int = DEFAULT_GROUP) -> QWeight:
    """Asymmetric min/max affine quantization of a 2-D weight along its input dim, `group` inputs per scale."""

    if w.ndim != 2:
        raise ValueError(f'expected 2-D weight, got {w.shape}')
    out, inn = w.shape
    if inn % group:
        raise ValueError(f'in_features {inn} not a multiple of group {group}')
    if bits not in (4, 8):
        raise ValueError(bits)
    qmax = (1 << bits) - 1
    g = w.astype(np.float32).reshape(out, inn // group, group)
    lo = g.min(-1)
    hi = g.max(-1)
    scale = (hi - lo) / qmax
    scale = np.where(scale == 0, np.float32(1), scale).astype(np.float32)
    q = np.rint((g - lo[..., None]) / scale[..., None])
    q = np.clip(q, 0, qmax).astype(np.uint8).reshape(out, inn)
    return QWeight(pack(q, bits), scale, lo.astype(np.float32), bits, group, (out, inn))


def from_native(values: np.ndarray, scale: np.ndarray, bias: np.ndarray, bits: int, group: int) -> QWeight:
    """Wrap already-quantized values (uint8 [out, in], one per element) without touching them."""

    out, inn = values.shape
    return QWeight(
        pack(values, bits),
        np.ascontiguousarray(scale, dtype=np.float32),
        np.ascontiguousarray(bias, dtype=np.float32),
        bits,
        group,
        (out, inn),
    )
