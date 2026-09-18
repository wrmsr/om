# ruff: noqa: N806 N812
"""
Quantized-weight path tests (see quant.py). Reuses the synthetic model builders from test_synthetic.py.

Run:  python -m pytest x/qwen/tests -q      or      python -m x.qwen.tests.test_quant
"""
import pathlib
import tempfile

import numpy as np

from ..quant import from_native
from ..quant import quantize
from ..weights import GGUFSource
from ..weights import OllamaTensorSource
from ..weights import Qwen35Config
from ..weights import mlx_affine_dequant
from .test_synthetic import CFG
from .test_synthetic import make_hf_params
from .test_synthetic import mlx_affine_quant
from .test_synthetic import write_gguf
from .test_synthetic import write_ollama_tensor_model


##


def test_quantize_roundtrip():
    rng = np.random.default_rng(0)
    w = (rng.standard_normal((96, 256)) * 0.05).astype(np.float32)
    for bits, tol in ((8, 2e-3), (4, 2e-2)):
        qw = quantize(w, bits, 64)
        assert qw.q.dtype == np.uint8 and qw.q.shape == (96, 256 // (8 // bits))
        back = qw.dequantize()
        err = np.abs(back - w).max()
        # per-group step is (max - min) / (2^bits - 1); error should be at most half a step
        assert err < tol, (bits, err)
        assert np.array_equal(qw.dequantize(slice(10, 20)), back[10:20])
        assert np.array_equal(qw.dequantize(np.array([3, 95])), back[[3, 95]])
        assert qw.words().shape == (96, 256 * bits // 32)
    print('quantize roundtrip OK')


def test_native_repack_matches_mlx():
    """Bit-exact: values packed by MLX's layout -> from_native -> words() reproduces the original words."""

    rng = np.random.default_rng(1)
    w = (rng.standard_normal((48, 192)) * 0.05).astype(np.float32)
    for bits in (8, 4):
        packed, scale, bias = mlx_affine_quant(w, bits, 64)
        ref = mlx_affine_dequant(packed, scale, bias, bits, 64)
        vals = packed.view(np.uint8)
        if bits == 4:
            vals = np.stack([vals & 0xF, vals >> 4], axis=-1).reshape(48, 192)
        qw = from_native(vals, scale, bias, bits, 64)
        assert np.array_equal(qw.words(), packed), bits
        assert np.array_equal(qw.dequantize(), ref), bits
    print('native MLX re-pack OK')


def test_model_quant():
    try:
        import torch  # noqa
    except ImportError:
        print('torch not installed; skipping model tests')
        return

    from ..model import Cache
    from ..model import Qwen35
    from ..torch_ops import TorchOps
    from ..torch_ops import TorchQWeight

    ops = TorchOps('cpu')
    tmp = pathlib.Path(tempfile.mkdtemp())
    cfg = Qwen35Config(**CFG)  # type: ignore
    hf = make_hf_params(cfg)
    write_gguf(tmp / 'tiny.gguf', cfg, hf, quantize=False)
    src = GGUFSource(tmp / 'tiny.gguf')

    ref = Qwen35.from_source(src, ops, dtype='f32', verbose=False)
    ids = np.random.default_rng(0).integers(0, 256, (1, 12))
    ref_lg = ops.numpy(ref.forward(ids))
    ref_lp = ref_lg - np.log(np.exp(ref_lg).sum(-1, keepdims=True))

    # loose bounds: this random model has no structure to hide quantization noise in (int8 lands ~2x bf16's own
    # rounding error, int4 ~30x); exactness of the QWeight plumbing itself is covered by test_parity
    for quant, tol in (('int8', 0.3), ('int4', 2.5)):
        m = Qwen35.from_source(src, ops, dtype='f32', verbose=False, quant=quant)
        # the big 2-D weights are QWeights; norms / A / dt_bias / conv / in_proj_{a,b} are not
        assert isinstance(m.embed, TorchQWeight) and isinstance(m.lm_head, TorchQWeight)
        blk = m.blocks[0].mixer
        assert isinstance(blk.w_qkv, TorchQWeight) and not isinstance(blk.w_a, TorchQWeight)  # type: ignore
        assert not isinstance(m.blocks[0].ln1, TorchQWeight)
        assert m.nbytes < ref.nbytes
        lg = ops.numpy(m.forward(ids))
        lp = lg - np.log(np.exp(lg).sum(-1, keepdims=True))
        err = np.abs(lp - ref_lp).max()
        assert err < tol, (quant, err)
        cache = Cache(cfg)
        a = np.concatenate([ops.numpy(m.forward(ids[:, :5], cache)), ops.numpy(m.forward(ids[:, 5:], cache))], 1)
        assert np.abs(a - lg).max() < 1e-4
        gen = m.generate(ids[0].tolist(), max_new_tokens=4)
        assert len(gen) == 4
        print(f'model {quant}: {m.nbytes / 1e6:.2f} MB vs {ref.nbytes / 1e6:.2f} MB f32, max |delta logprob| {err:.3f}')

    # tensor-blob source: MLX int8 blobs are re-packed, not requantized -> bit-identical to the dequantized f32 path
    # for every natively quantized tensor (the f32-stored ones, e.g. the embedding, get quantized fresh)
    om = write_ollama_tensor_model(tmp / 'ollama', cfg, hf)
    tsrc = OllamaTensorSource(om)
    m_f32 = Qwen35.from_source(tsrc, ops, dtype='f32', verbose=False)
    m_q8 = Qwen35.from_source(tsrc, ops, dtype='f32', verbose=False, quant='int8')
    assert tsrc.get_quant('layers.0.mlp.gate_proj.weight') is not None
    assert tsrc.get_quant('layers.0.input_layernorm.weight') is None
    n_native = 0
    for i, blk in enumerate(m_q8.blocks):  # type: ignore
        for attr in ('wg', 'wu', 'wd'):
            qw = getattr(blk.mlp, attr)  # type: ignore
            assert isinstance(qw, TorchQWeight)
            assert torch.equal(qw.dequant(torch.float32), getattr(m_f32.blocks[i].mlp, attr))
            n_native += 1
    assert torch.equal(m_q8.lm_head.dequant(torch.float32), m_f32.lm_head)  # type: ignore
    err = np.abs(ops.numpy(m_q8.forward(ids)) - ops.numpy(m_f32.forward(ids))).max()
    assert err < 0.3, err
    print(f'tensor-blob: {n_native + 1} native int8 tensors re-packed bit-exactly (model max err {err:.3f})')


if __name__ == '__main__':
    test_quantize_roundtrip()
    test_native_repack_matches_mlx()
    test_model_quant()
