# ruff: noqa: N803 N806
"""
GGML's NVFP4 layout against ours: bytes regrouped one way come back the other, and the values llama.cpp's own decode
(the vendored `gguf.quants.NVFP4`) gives a GGML tensor are the ones the regrouped weight decodes to.
"""
import numpy as np
import pytest

from ...models.inkling.load.tests.ggufwriters import ggml_nvfp4_blocks
from ...ops.microscaled import MicroscaledWeight
from ..gguf.constants import GGMLQuantizationType
from ..gguf.quants import dequantize
from ..ggufmicroscaled import microscaled_from_ggml_nvfp4


##


def _nvfp4(rng: np.random.Generator, E: int, N: int, K: int) -> MicroscaledWeight:
    """Every code, block scales between 1/4 and 4 (an exponent of 5..8 and any mantissa), a factor per matrix."""

    exp = rng.integers(5, 9, (E, N, K // 16), dtype=np.uint8)
    man = rng.integers(0, 8, (E, N, K // 16), dtype=np.uint8)
    return MicroscaledWeight(
        'nvfp4',
        rng.integers(0, 256, (E, N, K // 2), dtype=np.uint8),
        (exp << 3) | man,
        rng.uniform(0.01, 0.1, E).astype(np.float32),
        (E, N, K),
    )


def test_regrouping():
    E, N, K = 3, 5, 192
    want = _nvfp4(np.random.default_rng(0), E, N, K)
    outer = np.asarray(want.outer)
    blocks = ggml_nvfp4_blocks(want.codes, want.scales)
    assert blocks.dtype == np.uint8 and blocks.shape == (E, N, K // 64 * 36)

    got = microscaled_from_ggml_nvfp4(blocks, outer)
    assert (got.fmt, got.shape) == ('nvfp4', (E, N, K))
    assert np.array_equal(got.codes, want.codes) and np.array_equal(got.scales, want.scales)
    assert got.outer is not None and np.array_equal(got.outer, outer)

    # one weight's code in the stored bytes: weight 9 of the second block of 16 is the high nibble of that block's
    # second code byte, after the super-block's four scale bytes
    codes = np.zeros((1, 1, 32), dtype=np.uint8)
    codes[0, 0, (16 + 9) // 2] = 0xB0  # (weight 25: an odd weight, so its byte's high nibble)
    scales = np.arange(1, 5, dtype=np.uint8).reshape(1, 1, 4)
    stored = ggml_nvfp4_blocks(codes, scales)[0, 0]
    assert stored[:4].tolist() == [1, 2, 3, 4]
    assert np.flatnonzero(stored[4:]).tolist() == [8 + 1] and stored[4 + 8 + 1] == 0xB0

    # the upstream decode of the stored bytes, times each matrix's factor, is the regrouped weight's decode
    theirs = dequantize(blocks, GGMLQuantizationType.NVFP4) * outer[:, None, None]
    ours = got.dequantize()
    assert ours.shape == theirs.shape == (E, N, K) and np.abs(ours).max() > 0.1
    np.testing.assert_allclose(ours, theirs, rtol=1e-6, atol=0)


def test_refuses_what_is_not_super_blocks():
    outer = np.ones(2, dtype=np.float32)

    with pytest.raises(RuntimeError, match='super-blocks'):
        microscaled_from_ggml_nvfp4(np.zeros((2, 3, 40), dtype=np.uint8), outer)
    with pytest.raises(RuntimeError, match='shape'):
        microscaled_from_ggml_nvfp4(np.zeros((3, 36), dtype=np.uint8), outer)
    with pytest.raises(RuntimeError, match='dtype'):
        microscaled_from_ggml_nvfp4(np.zeros((2, 3, 36), dtype=np.float32), outer)
