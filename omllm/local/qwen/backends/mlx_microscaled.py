# ruff: noqa: N803 N806 N812
"""
Experts stored in a microscaled float format (ops/microscaled.py), packed, for the MLX backend: the checkpoint's bytes
on the device as they are and the composed decode of the experts a matmul reads, a table lookup per byte -- the torch
container's decode (backends/torch.py: TorchMicroscaledExperts). MLX's quantized matmul reads affine codes, not
these.

Decoded at load, Inkling 2 Mini's experts are 49 GB at bfloat16; packed, the checkpoint's 17.

Nothing below names an MLX function: the decode is indexing and arithmetic that numpy spells the same way, which is
how tests/test_microscaled.py holds it to the reference decode where MLX is not installed.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..ops.microscaled import MicroscaledWeight
from ..ops.microscaled import e2m1_pair_values
from ..ops.microscaled import e4m3_values
from ..ops.microscaled import pow2_scale_values


if ta.TYPE_CHECKING:
    import mlx.core as mx  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import numpy as np  # type: ignore[import-not-found,import-untyped,unused-ignore]
else:
    mx = lang.proxy_import('mlx.core')
    np = lang.proxy_import('numpy')


##


@dc.dataclass()
class MlxMicroscaledExperts:
    """
    E experts as the checkpoint has them: `codes` uint8 [E, N, K / 2] (nvfp4: two 4-bit codes a byte, low nibble
    first) or [E, N, K] (mxfp8), `scales` uint8 [E, N, K / block], `outer` float32 [E] (nvfp4). The tables turn a
    byte into its value(s), float32: `code_values` [256, 2] or [256, 1], `scale_values` [256, 1].
    """

    fmt: str
    codes: mx.array
    scales: mx.array
    outer: mx.array | None
    code_values: mx.array
    scale_values: mx.array
    block: int
    shape: tuple[int, int]  # one expert's (N, K)

    def nbytes(self) -> int:
        return self.codes.nbytes + self.scales.nbytes + (self.outer.nbytes if self.outer is not None else 0)

    def dequant(self, dtype: ta.Any, experts: slice | mx.array) -> mx.array:
        """
        The given experts' weights, [R, N, K] in `dtype`: a slice of the stack, or a row's expert each (an int
        array). Decoded in float32 (the products exact), then rounded.
        """

        n, k = self.shape

        x = self.code_values[self.codes[experts]]  # [R, N, K / per byte, per byte]: a byte is its row of the table
        s = self.scale_values[self.scales[experts]]  # [R, N, K / block, 1]
        if self.outer is not None:
            s = s * self.outer[experts][:, None, None, None]

        r = x.shape[0]
        return (x.reshape(r, n, k // self.block, self.block) * s).reshape(r, n, k).astype(dtype)

    def products(self, rows: mx.array, eids: mx.array, step: int) -> list[mx.array]:
        """
        Every row of `rows` [R, K] against its own expert (`eids` [R], int), `step` rows at a time: the pieces
        [<= step, N] in the rows' order, in the rows' dtype. A row's expert decoded is N K float32 before it is
        rounded (21 MB for Inkling 2 Mini's), and a step's rows are that many experts each: decoded together they
        are gigabytes, a few at a time they are not.
        """

        return [
            (self.dequant(rows.dtype, eids[a:a + step]) @ rows[a:a + step, :, None])[..., 0]
            for a in range(0, rows.shape[0], step)
        ]


def mlx_microscaled_experts(
        mw: MicroscaledWeight,
        array: ta.Callable[[np.ndarray], ta.Any],
) -> MlxMicroscaledExperts:
    """
    `mw` adopted: its bytes and the tables that decode them, through `array`, which puts a numpy array on the device
    in the dtype it has (MlxOps.array; a test's is numpy's own).
    """

    nvfp4 = mw.fmt == 'nvfp4'
    scale_values = e4m3_values() if nvfp4 else pow2_scale_values()

    return MlxMicroscaledExperts(
        fmt=mw.fmt,
        codes=array(mw.codes),
        scales=array(mw.scales),
        outer=array(np.asarray(mw.outer, dtype=np.float32)) if mw.outer is not None else None,
        code_values=array(e2m1_pair_values() if nvfp4 else e4m3_values()[:, None]),
        scale_values=array(scale_values[:, None]),
        block=mw.block,
        shape=(mw.shape[1], mw.shape[2]),
    )
