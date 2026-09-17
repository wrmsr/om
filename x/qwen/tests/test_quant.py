"""
Quantized-weight path tests (see quant.py). Reuses the synthetic model builders from test_synthetic.py.

Run:
    python -m pytest x/qwen/tests -q
or
    python -m x.qwen.tests.test_quant
"""
import pathlib
import tempfile

import numpy as np

from ..weights import GGUFSource
from ..weights import OllamaTensorSource
from ..weights import Qwen35Config
from ..weights import mlx_affine_dequant
from .test_synthetic import CFG
from .test_synthetic import effective
from .test_synthetic import make_hf_params
from .test_synthetic import mlx_affine_quant
from .test_synthetic import write_gguf
from .test_synthetic import write_ollama_tensor_model


##


def _torch():
    try:
        import torch
    except ImportError:
        print('torch not installed; skipping quant tests')
        return None
    return torch


def test_quantize_roundtrip():
    torch = _torch()
    if torch is None:
        return
    from ..quant import quantize

    torch.manual_seed(0)
    w = torch.randn(96, 256) * 0.05
    for bits, tol in ((8, 2e-3), (4, 2e-2)):
        qw = quantize(w, bits, 64, torch.float32)
        assert qw.q.dtype == torch.uint8 and qw.q.shape == (96, 256 // (8 // bits))
        back = qw.dequant(torch.float32)
        err = (back - w).abs().max().item()
        # per-group step is (max - min) / (2^bits - 1); error should be at most half a step + storage rounding
        assert err < tol, (bits, err)
        # row-slice dequant and embedding gather agree with the full dequant
        assert torch.equal(qw.dequant(torch.float32, slice(10, 20)), back[10:20])
        ids = torch.tensor([[3, 95], [0, 42]])
        assert torch.equal(qw.embed(ids, torch.float32), back[ids])
        # chunked linear == unchunked
        x = torch.randn(2, 5, 256)
        a = qw.linear(x)
        b = qw.linear(x, chunk_rows=32)
        assert (a - b).abs().max().item() < 1e-5
        assert (a - x @ back.T).abs().max().item() < 1e-4
    print('quantize roundtrip OK')


def test_native_repack_matches_mlx():
    """Bit-exact: values packed by MLX's layout, unpacked by OllamaTensorSource, wrapped by from_native."""

    torch = _torch()
    if torch is None:
        return
    from ..quant import from_native

    rng = np.random.default_rng(1)
    w = (rng.standard_normal((48, 192)) * 0.05).astype(np.float32)
    for bits in (8, 4):
        packed, scale, bias = mlx_affine_quant(w, bits, 64)
        ref = mlx_affine_dequant(packed, scale, bias, bits, 64)
        per_word = 32 // bits
        vals = packed.view(np.uint8)
        if bits == 4:
            vals = np.stack([vals & 0xF, vals >> 4], axis=-1).reshape(48, 192)
        assert vals.shape == (48, packed.shape[1] * per_word)
        qw = from_native(
            torch.from_numpy(vals.copy()),
            torch.from_numpy(scale),
            torch.from_numpy(bias),
            bits,
            64,
            torch.float32,
        )
        back = qw.dequant(torch.float32).numpy()
        assert np.array_equal(back, ref), bits
    print('native MLX re-pack OK')


def test_model_quant():
    torch = _torch()
    if torch is None:
        return
    from ..model import Qwen35
    from ..quant import QWeight

    tmp = pathlib.Path(tempfile.mkdtemp())
    cfg = Qwen35Config(**CFG)
    hf = make_hf_params(cfg)
    write_gguf(tmp / 'tiny.gguf', cfg, hf, quantize=False)
    src = GGUFSource(tmp / 'tiny.gguf')

    ref = Qwen35.from_source(src, device='cpu', dtype=torch.float32, verbose=False)
    ids = torch.randint(0, 256, (1, 12))
    ref_logits = ref.forward(ids)
    ref_lp = torch.log_softmax(ref_logits, -1)

    # loose bounds: this random model has no structure to hide quantization noise in (int8 lands ~2x bf16's own rounding
    # error, int4 ~30x); exactness of the QWeight plumbing itself is covered by the re-pack test below
    for quant, tol in (('int8', 0.3), ('int4', 2.5)):
        m = Qwen35.from_source(src, device='cpu', dtype=torch.float32, verbose=False, quant=quant)
        # the big 2-D weights are QWeights; norms / A / dt_bias / conv / in_proj_{a,b} are not
        assert isinstance(m.embed, QWeight) and isinstance(m.lm_head, QWeight)
        blk = m.blocks[0].mixer
        assert isinstance(blk.w_qkv, QWeight) and not isinstance(blk.w_a, QWeight)
        assert not isinstance(m.blocks[0].ln1, QWeight)
        assert m.nbytes < ref.nbytes
        lp = torch.log_softmax(m.forward(ids), -1)
        err = (lp - ref_lp).abs().max().item()
        assert err < tol, (quant, err)
        # cached decode still consistent with one-shot
        from ..model import Cache

        cache = Cache(cfg)
        a = torch.cat([m.forward(ids[:, :5], cache), m.forward(ids[:, 5:], cache)], dim=1)
        assert (a - m.forward(ids)).abs().max().item() < 1e-4
        gen = m.generate(ids[0].tolist(), max_new_tokens=4)
        assert len(gen) == 4
        print(f'model {quant}: {m.nbytes / 1e6:.2f} MB vs {ref.nbytes / 1e6:.2f} MB f32, max |delta logprob| {err:.3f}')

    # tensor-blob source: MLX int8 blobs are re-packed, not requantized -> bit-identical to the dequantized f32 path for
    # every natively quantized tensor (the f32-stored ones, e.g. the embedding, get quantized fresh)
    om = write_ollama_tensor_model(tmp / 'ollama', cfg, hf)
    tsrc = OllamaTensorSource(om)
    m_f32 = Qwen35.from_source(tsrc, device='cpu', dtype=torch.float32, verbose=False)
    m_q8 = Qwen35.from_source(tsrc, device='cpu', dtype=torch.float32, verbose=False, quant='int8')
    assert tsrc.get_quant('layers.0.mlp.gate_proj.weight') is not None
    assert tsrc.get_quant('layers.0.input_layernorm.weight') is None
    n_native = 0
    for i, blk in enumerate(m_q8.blocks):
        for attr in ('wg', 'wu', 'wd'):
            qw = getattr(blk.mlp, attr)
            assert isinstance(qw, QWeight)
            assert torch.equal(qw.dequant(torch.float32), getattr(m_f32.blocks[i].mlp, attr))
            n_native += 1
    assert torch.equal(m_q8.lm_head.dequant(torch.float32), m_f32.lm_head)
    err = (m_q8.forward(ids) - m_f32.forward(ids)).abs().max().item()
    assert err < 0.3, err
    print(f'tensor-blob: {n_native + 1} native int8 tensors re-packed bit-exactly (model max err {err:.3f})')


if __name__ == '__main__':
    test_quantize_roundtrip()
    test_native_repack_matches_mlx()
    test_model_quant()
