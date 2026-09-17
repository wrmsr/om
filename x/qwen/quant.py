"""
Weight-only affine quantization, kept quantized on the device and dequantized per matmul.

    w ≈ q * scale + bias        q: unsigned `bits`-bit, one (scale, bias) per `group` consecutive inputs

This is exactly MLX's `mx.quantize` affine layout (int4/int8, group 64), so Ollama tensor blobs that are already
MLX-quantized are re-packed bit-for-bit instead of being dequantized and requantized. GGUF sources are dequantized
(k-quants -> f32) and requantized here, which costs a little extra error on top of the file's own quantization.

Storage per parameter: int8 = 1 byte, int4 = 0.5 byte, plus 2 * sizeof(dtype) / group for scale + bias (~0.06 byte at
group 64, bf16). A 27B model lands at ~28 GB (int8) or ~15 GB (int4).

Compute: a QWeight is expanded to the activation dtype right before `F.linear` (chunked by rows for the lm_head so the
transient never exceeds `chunk_rows` rows). That trades ~2x decode bandwidth for 2-4x less memory; a fused int4 kernel
(torch._weight_int4pack_mm, or your own) is the next step if decode speed matters.
"""
import dataclasses as dc

import torch
import torch.nn.functional as F


##


QUANT_BITS = {
    'int8': 8,
    'int4': 4,
}
DEFAULT_GROUP = 64


@dc.dataclass()
class QWeight:
    q: torch.Tensor      # uint8 [out, in] (int8) or [out, in // 2] (int4, low nibble first)
    scale: torch.Tensor  # [out, in // group], compute dtype
    bias: torch.Tensor   # [out, in // group], compute dtype
    bits: int
    group: int
    shape: tuple[int, int]  # (out, in)

    @property
    def dtype(self) -> torch.dtype:
        return self.scale.dtype

    @property
    def device(self) -> torch.device:
        return self.q.device

    def nbytes(self) -> int:
        return self.q.numel() + self.scale.numel() * self.scale.element_size() * 2

    def to(self, device) -> QWeight:
        return QWeight(
            self.q.to(device),
            self.scale.to(device),
            self.bias.to(device),
            self.bits,
            self.group,
            self.shape,
        )

    # dequant

    def dequant(
            self,
            dtype: torch.dtype | None = None,
            rows: slice | torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Expand (a row-slice of) the weight to `dtype` [rows, in]."""

        q = self.q if rows is None else self.q[rows]
        s = self.scale if rows is None else self.scale[rows]
        b = self.bias if rows is None else self.bias[rows]
        if self.bits == 4:
            q = torch.stack([q & 0xF, q >> 4], dim=-1).reshape(q.shape[0], -1)
        n_rows = q.shape[0]
        x = q.reshape(n_rows, -1, self.group).to(dtype or self.dtype)
        x = x * s[..., None].to(x.dtype) + b[..., None].to(x.dtype)
        return x.reshape(n_rows, self.shape[1])

    def linear(
            self,
            x: torch.Tensor,
            chunk_rows: int = 16384,
    ) -> torch.Tensor:
        out = self.shape[0]
        if out <= chunk_rows:
            return F.linear(x, self.dequant(x.dtype))
        return torch.cat(
            [
                F.linear(x, self.dequant(x.dtype, slice(i, i + chunk_rows)))
                for i in range(0, out, chunk_rows)
            ],
            dim=-1,
        )

    def embed(
            self,
            ids: torch.Tensor,
            dtype: torch.dtype,
    ) -> torch.Tensor:
        """Row gather + dequant: [..., in]."""

        flat = ids.reshape(-1)
        return self.dequant(dtype, flat).reshape(*ids.shape, self.shape[1])


##


def quantize(
        w: torch.Tensor,
        bits: int,
        group: int = DEFAULT_GROUP,
        dtype: torch.dtype | None = None,
) -> QWeight:
    """Asymmetric min/max affine quantization of a 2-D weight along its input dim, `group` inputs per scale."""

    if w.ndim != 2:
        raise ValueError(f'expected 2-D weight, got {tuple(w.shape)}')
    out, inn = w.shape
    if inn % group:
        raise ValueError(f'in_features {inn} not a multiple of group {group}')
    if bits not in (4, 8):
        raise ValueError(bits)
    dtype = dtype or (w.dtype if w.dtype in (torch.bfloat16, torch.float16) else torch.bfloat16)
    qmax = (1 << bits) - 1
    g = w.float().reshape(out, inn // group, group)
    lo = g.amin(-1)
    hi = g.amax(-1)
    scale = (hi - lo) / qmax
    scale = torch.where(scale == 0, torch.ones_like(scale), scale)
    # round-trip the scale/bias through the storage dtype *before* quantizing so q is optimal for what is stored
    scale_s = scale.to(dtype)
    bias_s = lo.to(dtype)
    q = torch.round((g - bias_s.float()[..., None]) / scale_s.float()[..., None])
    q = q.clamp_(0, qmax).to(torch.uint8).reshape(out, inn)
    if bits == 4:
        q = q[:, 0::2] | (q[:, 1::2] << 4)
    return QWeight(
        q.contiguous(),
        scale_s,
        bias_s,
        bits,
        group,
        (out, inn),
    )


def from_native(
    q_values: torch.Tensor,
    scale: torch.Tensor,
    bias: torch.Tensor,
    bits: int,
    group: int,
    dtype: torch.dtype,
) -> QWeight:
    """Wrap already-quantized values (uint8 [out, in], one value per element) without touching them."""

    out, inn = q_values.shape
    q = q_values.to(torch.uint8)
    if bits == 4:
        q = q[:, 0::2] | (q[:, 1::2] << 4)
    return QWeight(
        q.contiguous(),
        scale.to(dtype),
        bias.to(dtype),
        bits,
        group,
        (out, inn),
    )


##


def linear(
        x: torch.Tensor,
        w: torch.Tensor | QWeight,
) -> torch.Tensor:
    if isinstance(w, QWeight):
        return w.linear(x)
    return F.linear(x, w)


def embedding(
        ids: torch.Tensor,
        w: torch.Tensor | QWeight,
        dtype: torch.dtype,
) -> torch.Tensor:
    if isinstance(w, QWeight):
        return w.embed(ids, dtype)
    return F.embedding(ids, w)


def param_nbytes(p: torch.Tensor | QWeight) -> int:
    if isinstance(p, QWeight):
        return p.nbytes()
    return p.numel() * p.element_size()
