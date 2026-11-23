# ruff: noqa: N803 N806
"""
Microscaled floating-point weights as checkpoints store them, backend-agnostic: small float codes with a scale per
short block of each row, the two layouts NVIDIA's NVFP4 and the OCP MXFP8 formats define --

    nvfp4   w = e2m1(code) * e4m3(scale) * outer      4-bit codes, two a byte (low nibble first), a scale byte per 16
                                                      consecutive inputs of a row, one `outer` factor per matrix
    mxfp8   w = e4m3(code) * 2 ** (scale - 127)       8-bit codes, a power-of-two scale byte per 32 inputs of a row

where e2m1 and e4m3 are the 4- and 8-bit float encodings (sign, exponent, mantissa: `e2m1_values`, `e4m3_values`). The
weights are exactly those products: nothing here is a quantizer. A `MicroscaledWeight` is plain numpy over the
checkpoint's own bytes (memory-mapped, when the source maps them); each backend adopts it into a container of its own
(`Ops.microscaled`) and decodes what a matmul reads, when it reads it. `dequantize` is the reference decode.

The formats are public (the OCP Microscaling Formats specification, NVIDIA's NVFP4 description); the tables below are
written from the encodings' definitions.
"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


##


MICROSCALED_BLOCKS: ta.Mapping[str, int] = {
    'nvfp4': 16,
    'mxfp8': 32,
}


@lang.cached_function
def e2m1_values() -> np.ndarray:
    """float32 [16]: the value of each 4-bit E2M1 code (sign, 2 exponent bits, 1 mantissa bit; no infinities)."""

    mag = np.array([0., .5, 1., 1.5, 2., 3., 4., 6.], dtype=np.float32)
    return np.concatenate([mag, -mag])


@lang.cached_function
def e4m3_values() -> np.ndarray:
    """
    float32 [256]: the value of each 8-bit E4M3 code (sign, 4 exponent bits biased by 7, 3 mantissa bits; subnormals
    at exponent 0, no infinities, and the one NaN at S.1111.111, which no stored weight or scale is).
    """

    code = np.arange(256, dtype=np.int64)
    sign = np.where(code & 0x80, -1., 1.)
    exp = (code >> 3) & 0xF
    man = (code & 0x7).astype(np.float64)
    val = np.where(exp == 0, man / 8. * 2. ** -6, (1. + man / 8.) * 2. ** (exp.astype(np.float64) - 7))
    out = (sign * val).astype(np.float32)
    out[[0x7F, 0xFF]] = np.nan
    return out


@lang.cached_function
def e2m1_pair_values() -> np.ndarray:
    """float32 [256, 2]: the two values a byte of packed E2M1 codes holds, low nibble first."""

    code = np.arange(256, dtype=np.int64)
    v = e2m1_values()
    return np.stack([v[code & 0xF], v[code >> 4]], -1)


@lang.cached_function
def pow2_scale_values() -> np.ndarray:
    """float32 [256]: 2 ** (byte - 127), MXFP8's block scales (exact in float32 down to its subnormals)."""

    with np.errstate(over='ignore'):  # (byte 255 is 2 ** 128: past float32, as past any scale a checkpoint stores)
        return np.ldexp(np.float64(1.), np.arange(256, dtype=np.int64) - 127).astype(np.float32)


@dc.dataclass(frozen=True)
class MicroscaledWeight:
    """
    A stack of E matrices [N, K] in one of the formats above, as stored: `codes` uint8 [E, N, K / 2] (nvfp4) or
    [E, N, K] (mxfp8); `scales` uint8 [E, N, K / block]; `outer` float32 [E] (nvfp4: each matrix's factor) or None.
    """

    fmt: str
    codes: np.ndarray
    scales: np.ndarray
    outer: np.ndarray | None
    shape: tuple[int, int, int]  # (E, N, K)

    def __post_init__(self) -> None:
        E, N, K = self.shape
        block = MICROSCALED_BLOCKS[self.fmt]
        per_byte = 2 if self.fmt == 'nvfp4' else 1
        check.state(K % block == 0, f'{self.shape=} is not whole blocks of {block}')
        check.state(tuple(self.codes.shape) == (E, N, K // per_byte), f'{self.codes.shape=} for {self.shape=}')
        check.state(tuple(self.scales.shape) == (E, N, K // block), f'{self.scales.shape=} for {self.shape=}')
        check.state((self.outer is not None) == (self.fmt == 'nvfp4'))

    @property
    def block(self) -> int:
        return MICROSCALED_BLOCKS[self.fmt]

    def nbytes(self) -> int:
        return self.codes.nbytes + self.scales.nbytes + (self.outer.nbytes if self.outer is not None else 0)

    def rows(self, order: np.ndarray) -> MicroscaledWeight:
        """The same matrices with their output rows reordered: row n is row order[n] (blocks run along the inputs)."""

        return dc.replace(
            self,
            codes=self.codes[:, order],
            scales=self.scales[:, order],
        )

    def dequantize(self, experts: slice | np.ndarray | None = None) -> np.ndarray:
        """float32 [experts, N, K]: the weights, exactly."""

        codes = self.codes
        scales = self.scales
        outer = self.outer
        if experts is not None:
            codes = codes[experts]
            scales = scales[experts]
            outer = outer[experts] if outer is not None else None

        E, N, K = codes.shape[0], self.shape[1], self.shape[2]
        if self.fmt == 'nvfp4':
            x = e2m1_pair_values()[codes].reshape(E, N, K)
            s = e4m3_values()[scales] * np.asarray(check.not_none(outer), dtype=np.float32).reshape(E, 1, 1)
        else:
            x = e4m3_values()[codes]
            s = pow2_scale_values()[scales]

        x = x.reshape(E, N, K // self.block, self.block) * s[..., None]
        return np.ascontiguousarray(x.reshape(E, N, K), dtype=np.float32)
