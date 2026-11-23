# ruff: noqa: N806
"""
GGML's NVFP4 tensors as the microscaled weights the engine holds (ops/microscaled.py). The two layouts carry the same
bytes, grouped differently:

    ggml    a row is super-blocks of 64 weights in 36 bytes: four scale bytes, one per 16 weights, then for each 16
            weights eight code bytes -- weights 0..7 in the bytes' low nibbles, weights 8..15 in their high nibbles
    ours    a row's codes two a byte in order, the low nibble first, and its scale bytes in an array of their own

A scale byte is the same E4M3 code in both and a nibble the same E2M1 code, so regrouping is all there is to do: no
value is decoded, and a file written from a checkpoint's own NVFP4 comes back as that checkpoint's bytes. The factor a
matrix has of its own (`outer`) is a tensor a GGUF keeps beside the weight, `<name>.scale`.

Written from the format's layout as llama.cpp reads it (the vendored `gguf.quants.NVFP4` decodes the same bytes).
"""
import typing as ta

from omcore import check
from omcore import lang

from ..ops.microscaled import MicroscaledWeight


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


##


GGML_NVFP4_WEIGHTS = 64  # a super-block's weights
GGML_NVFP4_BYTES = 36  # ... and its bytes
GGML_NVFP4_BLOCKS = 4  # ... and its blocks of 16 weights, a scale each


def microscaled_from_ggml_nvfp4(blocks: np.ndarray, outer: np.ndarray) -> MicroscaledWeight:
    """
    `blocks` uint8 [E, N, K / 64 * 36]: a stack of E matrices [N, K] as a GGUF stores them (and as the vendored
    reader hands an NVFP4 tensor: its bytes, memory-mapped); `outer` float32 [E]. Regrouped a matrix at a time: a
    model's stack is hundreds of megabytes, and one matrix's bytes stay in cache through the passes over them.
    """

    check.arg(blocks.dtype == np.uint8 and blocks.ndim == 3, f'{blocks.dtype=} {blocks.shape=}')
    E, N, B = (int(d) for d in blocks.shape)
    check.arg(B % GGML_NVFP4_BYTES == 0, f'{blocks.shape=} is not whole NVFP4 super-blocks')
    S = B // GGML_NVFP4_BYTES
    K = S * GGML_NVFP4_WEIGHTS

    codes = np.empty((E, N, K // 2), dtype=np.uint8)
    scales = np.empty((E, N, S * GGML_NVFP4_BLOCKS), dtype=np.uint8)

    for e in range(E):
        sb = np.asarray(blocks[e]).reshape(N, S, GGML_NVFP4_BYTES)
        scales[e] = sb[:, :, :GGML_NVFP4_BLOCKS].reshape(N, -1)

        # a block's eight code bytes, as four pairs: weights 2j and 2j + 1 are the low nibbles of pair j's two bytes,
        # weights 8 + 2j and 9 + 2j their high nibbles
        pairs = sb[:, :, GGML_NVFP4_BLOCKS:].reshape(N, S * GGML_NVFP4_BLOCKS, 4, 2)
        first = pairs[..., 0]
        second = pairs[..., 1]
        low = (first & 0x0F) | (second << 4)  # (uint8: the shift drops the second byte's high nibble)
        high = (first >> 4) | (second & 0xF0)
        codes[e] = np.concatenate([low, high], -1).reshape(N, K // 2)

    return MicroscaledWeight(
        'nvfp4',
        codes,
        scales,
        np.ascontiguousarray(outer, dtype=np.float32),
        (E, N, K),
    )
