"""
The vendored gguf quantizers: every one consistent with the size table it is registered under, the ones upstream
added after the fork was first taken (Q1_0, Q2_0, F8_E4M3) against what they are defined to be, and the fork as a
whole against the `gguf` package it was restyled from, where that is installed.
"""
import numpy as np
import pytest

from ....ops.microscaled import e4m3_values
from ..constants import GGML_QUANT_SIZES
from ..constants import GGMLQuantizationType
from ..quants import _TYPE_TRAITS
from ..quants import dequantize
from ..quants import np_roundf
from ..quants import quantize


##


def _rows(qtype: GGMLQuantizationType, seed: int = 0) -> np.ndarray:
    block_size, _ = GGML_QUANT_SIZES[qtype]
    n = max(block_size, 256) * 2
    return np.random.default_rng(seed).standard_normal((3, n)).astype(np.float32)


def test_every_quantizer_keeps_to_its_sizes():
    assert {GGMLQuantizationType.Q1_0, GGMLQuantizationType.Q2_0, GGMLQuantizationType.F8_E4M3} <= set(_TYPE_TRAITS)

    for qtype, cls in _TYPE_TRAITS.items():
        block_size, type_size = GGML_QUANT_SIZES[qtype]
        assert (cls.block_size, cls.type_size) == (block_size, type_size), qtype.name

        x = _rows(qtype)
        try:
            q = quantize(x, qtype)
        except NotImplementedError:  # (types that are only read: F8_E4M3, most of the IQ family)
            q = np.zeros((3, x.shape[1] // block_size * type_size), dtype=np.uint8)

        assert q.dtype == np.uint8 and q.shape == (3, x.shape[1] // block_size * type_size), qtype.name

        d = dequantize(q, qtype)
        assert d.dtype == np.float32 and d.shape == x.shape, qtype.name


def test_q1_0():
    x = _rows(GGMLQuantizationType.Q1_0, 1)
    got = dequantize(quantize(x, GGMLQuantizationType.Q1_0), GGMLQuantizationType.Q1_0)

    # a sign a weight, and a block's mean magnitude
    blocks = x.reshape(-1, 128)
    scale = np.abs(blocks).mean(-1, keepdims=True).astype(np.float16).astype(np.float32)
    want = np.where(blocks >= 0, scale, -scale).reshape(x.shape)
    assert np.allclose(got, want, rtol=1e-3)
    assert np.array_equal(np.sign(got), np.where(x >= 0, 1., -1.))


def test_q2_0():
    x = _rows(GGMLQuantizationType.Q2_0, 2)
    got = dequantize(quantize(x, GGMLQuantizationType.Q2_0), GGMLQuantizationType.Q2_0)

    # two bits a weight: a level of -1, 0 or 1 (2 has a code and is never chosen) times the block's largest magnitude
    blocks = x.reshape(-1, 64)
    d = np.abs(blocks).max(-1, keepdims=True)
    level = np.clip(np_roundf(blocks / d) + 1, 0, 3) - 1
    want = (level * d.astype(np.float16).astype(np.float32)).reshape(x.shape)
    assert np.array_equal(got, want.astype(np.float32))
    assert set(np.unique(level).tolist()) == {-1., 0., 1.}


def test_f8_e4m3_is_the_e4m3_table():
    codes = np.arange(256, dtype=np.uint8).reshape(1, 256)
    got = dequantize(codes, GGMLQuantizationType.F8_E4M3)[0]
    want = e4m3_values()

    assert got.dtype == np.float32
    assert np.flatnonzero(np.isnan(got)).tolist() == np.flatnonzero(np.isnan(want)).tolist() == [0x7F, 0xFF]
    assert np.array_equal(got, want, equal_nan=True)
    assert got[0x38] == 1. and got[0xB8] == -1. and got[0x7E] == 448. and got[0x01] == 2. ** -9


def test_np_roundf_keeps_the_sign_of_a_temporary():
    x = np.array([-2.5, -1.5, -0.5, -0.4, 0.4, 0.5, 1.5, 2.5], dtype=np.float32)
    assert np_roundf(x * np.float32(1)).tolist() == [-3., -2., -1., -0., 0., 1., 2., 3.]


def test_against_the_package():
    """
    Byte for byte against the `gguf` package for every type both can quantize, and the same values for every type
    both can read.
    """

    gguf = pytest.importorskip('gguf')

    n_quantized = 0
    n_read = 0
    for qtype in _TYPE_TRAITS:
        theirs = getattr(gguf.GGMLQuantizationType, qtype.name, None)
        if theirs is None:
            continue

        x = _rows(qtype, 3)
        try:
            want_q = gguf.quants.quantize(x, theirs)
        except NotImplementedError:
            want_q = None
        if want_q is not None:
            assert np.array_equal(quantize(x, qtype), want_q), qtype.name
            n_quantized += 1

        block_size, type_size = GGML_QUANT_SIZES[qtype]
        q = want_q
        if q is None:
            n_bytes = x.shape[1] // block_size * type_size
            q = np.random.default_rng(4).integers(0, 256, (3, n_bytes)).astype(np.uint8)
        with np.errstate(invalid='ignore', over='ignore'):  # (random bytes: some scales decode to inf)
            try:
                want_d = gguf.quants.dequantize(q, theirs)
            except NotImplementedError:
                continue
            assert np.array_equal(dequantize(q, qtype), want_d, equal_nan=True), qtype.name
        n_read += 1

    assert n_quantized >= 8 and n_read >= 20, (n_quantized, n_read)
