# ruff: noqa: N803 N806 N812
"""
Weight-only affine quantization, backend-agnostic.

    w ≈ q * scale + bias        q: unsigned `bits`-bit, one (scale, bias) per `group` consecutive inputs

This is exactly MLX's `mx.quantize` affine layout (int4/int8, group 64), so Ollama tensor blobs that are already
MLX-quantized are re-packed bit-for-bit, and the MLX backend hands the words straight to `mx.quantized_matmul`.

A `QWeight` is plain numpy; each backend adopts it into its own container (see `Ops.qweight`). Storage per parameter:
int8 = 1 byte, int4 = 0.5 byte, plus 2 * sizeof(dtype) / group for scale + bias (~0.06 byte at group 64, bf16). A 27B
model lands at ~28 GB (int8) or ~15 GB (int4).
"""
import numpy as np

from omcore import check
from omcore import dataclasses as dc


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


# range-shrink candidates tried per group by the error-minimising quantizer (1.0 is plain min/max)
SEARCH_SHRINKS = (1.0, 0.975, 0.95, 0.925, 0.9, 0.875, 0.85, 0.825, 0.8)

# rows per work item when a tensor is quantized on several threads (numpy releases the GIL inside its loops)
SEARCH_ROW_BLOCK = 256


def quantize(
        w: np.ndarray,
        bits: int,
        group: int = DEFAULT_GROUP,
        search: bool = True,
        threads: int | None = None,
) -> QWeight:
    """
    Asymmetric affine quantization of a 2-D weight along its input dim, `group` inputs per scale.

    search=False is plain min/max round-to-nearest. search=True (the default) does what llama.cpp's k-quants do per
    group: try several shrunken ranges (more resolution for the bulk, the extremes clip), and for each one re-fit scale
    and bias to the resulting codes by least squares -- the optimal affine map for those codes is a linear regression of
    the weights on their codes -- keeping the candidate with the least squared error, then one more round of codes +
    refit from the winner. ~13-15% less error than min/max at int4 for the same bytes, nothing at inference time.

    This numpy implementation is the canonical one: every backend uses it for the search (torch can opt into an
    on-device version, see TorchOps.quant_native), and it uses only IEEE arithmetic and numpy's fixed-order reductions,
    so the same source quantizes to the same bytes on every machine -- a parameter cache built on a CUDA box and one
    built on a Mac are identical (`python -m ...paramcache DIR` prints a checksum to prove it). Rows are independent, so
    the work is split into blocks across `threads` (default: the machine's cores).
    """

    if w.ndim != 2:
        raise ValueError(f'expected 2-D weight, got {w.shape}')
    out, inn = w.shape
    if inn % group:
        raise ValueError(f'in_features {inn} not a multiple of group {group}')
    if bits not in (4, 8):
        raise ValueError(bits)
    if search and out > SEARCH_ROW_BLOCK:
        import concurrent.futures as cf
        import os

        n_threads = threads if threads is not None else max(1, min(32, os.cpu_count() or 1))
        blocks = list(range(0, out, SEARCH_ROW_BLOCK))
        if n_threads > 1 and len(blocks) > 1:
            with cf.ThreadPoolExecutor(n_threads) as ex:
                parts = list(ex.map(lambda r: _quantize_rows(w[r:r + SEARCH_ROW_BLOCK], bits, group, True), blocks))
        else:
            parts = [_quantize_rows(w[r:r + SEARCH_ROW_BLOCK], bits, group, True) for r in blocks]
        return QWeight(
            np.concatenate([p.q for p in parts], 0),
            np.concatenate([p.scale for p in parts], 0),
            np.concatenate([p.bias for p in parts], 0),
            bits,
            group,
            (out, inn),
        )
    return _quantize_rows(w, bits, group, search)


def _quantize_rows(w: np.ndarray, bits: int, group: int, search: bool) -> QWeight:
    out, inn = w.shape
    qmax = (1 << bits) - 1
    g = np.ascontiguousarray(w, dtype=np.float32).reshape(out, inn // group, group)
    lo = g.min(-1)
    hi = g.max(-1)
    scale = (hi - lo) / qmax
    scale = np.where(scale == 0, np.float32(1), scale).astype(np.float32)
    bias = lo.astype(np.float32)
    if not search:
        q = np.rint((g - bias[..., None]) / scale[..., None])
        q = np.clip(q, 0, qmax).astype(np.uint8).reshape(out, inn)
        return QWeight(pack(q, bits), scale, bias, bits, group, (out, inn))
    n = np.float32(group)
    sx = g.sum(-1)
    tmp = np.empty_like(g)
    np.multiply(g, g, out=tmp)
    sxx = tmp.sum(-1)
    q = np.empty_like(g)
    best_err = None
    best_q = None
    best_s = scale
    best_b = bias
    mid = (hi + lo) * np.float32(0.5)
    half = (hi - lo) * np.float32(0.5)

    def codes(s, b):
        # q = clip(rint((g - b) / s)) with in-place passes: one multiply, one subtract, rint, clip
        inv = (np.float32(1) / s).astype(np.float32)
        np.multiply(g, inv[..., None], out=q)
        np.subtract(q, (b * inv)[..., None], out=q)
        np.rint(q, out=q)
        np.clip(q, 0, qmax, out=q)

    def refit(s0, b0):
        # least-squares (scale, bias) for the codes in q, and the error from the sufficient statistics alone
        sq = q.sum(-1)
        np.multiply(q, q, out=tmp)
        sqq = tmp.sum(-1)
        np.multiply(q, g, out=tmp)
        sqx = tmp.sum(-1)
        den = n * sqq - sq * sq
        ok = den > np.float32(1e-6)
        s = np.where(ok, (n * sqx - sq * sx) / np.where(ok, den, np.float32(1)), s0).astype(np.float32)
        b = np.where(ok, (sx - s * sq) / n, b0).astype(np.float32)
        err = sxx - 2 * s * sqx - 2 * b * sx + s * s * sqq + 2 * s * b * sq + n * b * b
        return s, b, err

    for shrink in SEARCH_SHRINKS:
        s = np.maximum(2 * half * np.float32(shrink) / qmax, np.float32(1e-12)).astype(np.float32)
        b = (mid - half * np.float32(shrink)).astype(np.float32)
        codes(s, b)
        s2, b2, err = refit(s, b)
        if best_err is None:
            best_err = err
            best_q = q.copy()
            best_s = s2
            best_b = b2
        else:
            better = err < best_err
            best_err = np.where(better, err, best_err)
            best_q = np.where(better[..., None], q, check.not_none(best_q))
            best_s = np.where(better, s2, best_s)
            best_b = np.where(better, b2, best_b)
    codes(best_s, best_b)
    s2, b2, err = refit(best_s, best_b)
    better = err < best_err
    best_q = np.where(better[..., None], q, check.not_none(best_q))
    best_s = np.where(better, s2, best_s).astype(np.float32)
    best_b = np.where(better, b2, best_b).astype(np.float32)
    q8 = best_q.astype(np.uint8).reshape(out, inn)
    return QWeight(pack(q8, bits), best_s, best_b, bits, group, (out, inn))


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
