# ruff: noqa: N803 N806 N812
"""Quantized-weight path tests (see quant.py). Reuses the synthetic model builders from test_synthetic.py."""
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

    from ..backends.torch import TorchOps
    from ..backends.torch import TorchQWeight
    from ..model import Cache
    from ..model import Qwen35

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

    # loose bounds: this random model has no structure to hide quantization noise in (int8 lands ~2x bf16's own rounding
    # error, int4 ~30x); exactness of the QWeight plumbing itself is covered by test_parity
    for quant, tol in (('int8', 0.3), ('int4', 2.5)):
        m = Qwen35.from_source(src, ops, dtype='f32', verbose=False, quant=quant)
        # the big 2-D weights are QWeights; norms / A / dt_bias / conv / in_proj_{a,b} are not
        assert isinstance(m.embed, TorchQWeight) and isinstance(m.lm_head, TorchQWeight)
        blk = m.blocks[0].mixer
        assert (
            isinstance(blk.w_qkvz, TorchQWeight) and  # type: ignore
            isinstance(blk.w_ab, TorchQWeight) and  # type: ignore
            blk.w_ab.bits == 8  # type: ignore
        )
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

    # tensor-blob source: MLX int8 blobs are re-packed, not requantized -> bit-identical to the dequantized f32 path for
    # every natively quantized tensor (the f32-stored ones, e.g. the embedding, get quantized fresh)
    om = write_ollama_tensor_model(tmp / 'ollama', cfg, hf)
    tsrc = OllamaTensorSource(om)
    m_f32 = Qwen35.from_source(tsrc, ops, dtype='f32', verbose=False)
    m_q8 = Qwen35.from_source(tsrc, ops, dtype='f32', verbose=False, quant='int8')
    assert tsrc.get_quant('layers.0.mlp.gate_proj.weight') is not None
    assert tsrc.get_quant('layers.0.input_layernorm.weight') is None
    n_native = 0
    for i, blk in enumerate(m_q8.blocks):  # type: ignore
        for attr in ('wgu', 'wd'):
            qw = getattr(blk.mlp, attr)  # type: ignore
            assert isinstance(qw, TorchQWeight)
            assert torch.equal(qw.dequant(torch.float32), getattr(m_f32.blocks[i].mlp, attr))
            n_native += 1
    assert torch.equal(m_q8.lm_head.dequant(torch.float32), m_f32.lm_head)  # type: ignore
    err = np.abs(ops.numpy(m_q8.forward(ids)) - ops.numpy(m_f32.forward(ids))).max()
    assert err < 0.3, err
    print(f'tensor-blob: {n_native + 1} native int8 tensors re-packed bit-exactly (model max err {err:.3f})')


def test_param_cache():
    """
    A cached load reproduces the uncached one exactly (dense f32 and exported QWeights), later loads hit, a
    later mtp=True load only adds the draft head, and torn entries are treated as misses.
    """

    try:
        import torch  # noqa
    except ImportError:
        print('torch not installed; skipping')
        return

    from ..backends.torch import TorchOps
    from ..backends.torch import TorchQWeight
    from ..model import Qwen35
    from ..paramcache import ParamCache
    from ..paramcache import source_identity

    ops = TorchOps('cpu')
    tmp = pathlib.Path(tempfile.mkdtemp())
    cfg = Qwen35Config(**CFG)  # type: ignore
    hf = make_hf_params(cfg)
    write_gguf(tmp / 'tiny.gguf', cfg, hf, quantize=False)
    src = GGUFSource(tmp / 'tiny.gguf')
    cdir = tmp / 'cache'
    ids = np.random.default_rng(0).integers(0, 256, (1, 6))

    a = Qwen35.from_source(src, ops, dtype='f32', quant='int4', verbose=False)
    b = Qwen35.from_source(src, ops, dtype='f32', quant='int4', verbose=False, cache_dir=cdir)  # fills
    c = Qwen35.from_source(src, ops, dtype='f32', quant='int4', verbose=False, cache_dir=cdir)  # hits
    root = ParamCache.open(cdir, src, 'int4', 64, 's').root  # (default: search on, uniform policy)
    n_meta = len(list(root.glob('*.json')))
    from ..model import fusion_of

    def n_entries(names):  # fused projections are cached under their fused name
        return len({(f[0] if (f := fusion_of(n)) else n) for n in names})

    n_expect = n_entries([n for n in src.names() if not n.startswith('mtp.')])
    assert n_meta == n_expect, (n_meta, n_expect)
    for m in (b, c):
        assert torch.equal(m.blocks[0].mlp.wgu.q, a.blocks[0].mlp.wgu.q)  # type: ignore
        assert torch.equal(m.blocks[0].mlp.wgu.scale, a.blocks[0].mlp.wgu.scale)  # type: ignore
        assert torch.equal(m.blocks[0].ln1, a.blocks[0].ln1)
        assert torch.equal(m.forward(ids), a.forward(ids))
    # a later load with the draft head adds only its entries
    d = Qwen35.from_source(src, ops, dtype='f32', quant='int4', verbose=False, cache_dir=cdir, mtp=True)
    assert d.mtp is not None and isinstance(d.mtp.fc, TorchQWeight)
    assert len(list(root.glob('*.json'))) == n_entries(src.names())
    e = Qwen35.from_source(src, ops, dtype='f32', quant='int4', verbose=False, cache_dir=cdir, mtp=True)
    assert torch.equal(e.mtp.fc.q, d.mtp.fc.q)  # type: ignore
    # a torn entry (sidecar present, array missing) is a miss and gets rewritten
    victim = 'layers.1.mlp.gate_up_proj.weight'  # (the fused entry)
    (root / (victim + '.q.npy')).unlink()
    f = Qwen35.from_source(src, ops, dtype='f32', quant='int4', verbose=False, cache_dir=cdir)
    assert torch.equal(f.blocks[1].mlp.wgu.q, a.blocks[1].mlp.wgu.q)  # type: ignore
    assert (root / (victim + '.q.npy')).exists()
    assert source_identity(src) == source_identity(GGUFSource(tmp / 'tiny.gguf'))
    print(f'param cache OK ({n_meta} entries, {ParamCache(root).nbytes() / 1e6:.2f} MB)')


def test_quantize_search():
    """The error-minimising quantizer beats min/max on every row-group family and the torch twin agrees."""

    rng = np.random.default_rng(3)
    ws = {
        'gaussian': rng.standard_normal((64, 512)).astype(np.float32) * 0.02,
        'heavy': (rng.standard_t(3, (64, 512)) * 0.02).astype(np.float32),
    }
    for name, w in ws.items():
        for bits in (4, 8):
            rtn = quantize(w, bits, 64, search=False)
            best = quantize(w, bits, 64, search=True)
            e_r = ((rtn.dequantize() - w) ** 2).mean()
            e_s = ((best.dequantize() - w) ** 2).mean()
            assert e_s < e_r, (name, bits, e_s, e_r)
            if bits == 4:
                assert e_s < 0.92 * e_r, (name, e_s / e_r)
            try:
                import torch

                from ..backends.torch import TorchOps
            except ImportError:
                continue
            tq = TorchOps('cpu').quantize(w, bits, 64, torch.float32, search=True)
            e_t = ((tq.dequant(torch.float32).numpy() - w) ** 2).mean()
            assert abs(e_t - e_s) < 1e-3 * e_s + 1e-12, (name, bits, e_t, e_s)
    print('quantizer search: less error than min/max, torch twin agrees')


def test_precision_policy():
    """'km' keeps v_proj / edge down_proj / lm_head at int8 (unfusing qkv), loads through the cache, and runs."""

    try:
        import torch  # noqa
    except ImportError:
        print('torch not installed; skipping')
        return

    from ..backends.torch import TorchOps
    from ..model import Qwen35

    ops = TorchOps('cpu')
    tmp = pathlib.Path(tempfile.mkdtemp())
    cfg = Qwen35Config(**CFG)  # type: ignore
    hf = make_hf_params(cfg)
    write_gguf(tmp / 'tiny.gguf', cfg, hf, quantize=False)
    src = GGUFSource(tmp / 'tiny.gguf')
    ids = np.random.default_rng(0).integers(0, 256, (1, 6))
    ref = Qwen35.from_source(src, ops, dtype='f32', verbose=False)
    for cache_dir in (None, tmp / 'cache'):
        m = Qwen35.from_source(src, ops, dtype='f32', quant='int4', verbose=False, policy='km', cache_dir=cache_dir)
        attn = m.blocks[3].mixer
        assert attn.wqkv is None and attn.wv.bits == 8 and attn.wq.bits == 4  # type: ignore
        down_bits = [m.blocks[i].mlp.wd.bits for i in (0, 1, 3)]
        assert down_bits == [8, 4, 8], down_bits
        assert m.lm_head.bits == 8  # type: ignore
        assert m.blocks[0].mixer.w_ab.bits == 8 and m.blocks[0].mixer.w_qkvz.bits == 4  # type: ignore
        err = np.abs(ops.numpy(m.forward(ids)) - ops.numpy(ref.forward(ids))).max()
        assert np.isfinite(err)
    m2 = Qwen35.from_source(src, ops, dtype='f32', quant='int4', verbose=False, policy='km', cache_dir=tmp / 'cache')
    assert torch.equal(m2.lm_head.q, m.lm_head.q)  # type: ignore
    print('precision policy km OK (cached and uncached)')


def test_kl_harness():
    """entrypoints.kl: log-probs of a model vs itself is 0 KL / 100% agreement; int4 vs int8 is > 0."""

    try:
        import torch  # noqa
    except ImportError:
        print('torch not installed; skipping')
        return

    from ..backends.torch import TorchOps
    from ..entrypoints.kl import compare
    from ..entrypoints.kl import logprobs
    from ..model import Qwen35

    ops = TorchOps('cpu')
    tmp = pathlib.Path(tempfile.mkdtemp())
    cfg = Qwen35Config(**CFG)  # type: ignore
    hf = make_hf_params(cfg)
    write_gguf(tmp / 'tiny.gguf', cfg, hf, quantize=False)
    src = GGUFSource(tmp / 'tiny.gguf')
    ids = np.random.default_rng(1).integers(0, 256, 40).tolist()
    m8 = Qwen35.from_source(src, ops, dtype='f32', quant='int8', verbose=False)
    m4 = Qwen35.from_source(src, ops, dtype='f32', quant='int4', verbose=False)
    lp8 = logprobs(m8, ids, chunk=16)
    lp8b = logprobs(m8, ids, chunk=40)  # chunking must not change the numbers
    assert np.abs(lp8.astype(np.float32) - lp8b.astype(np.float32)).max() < 1e-2
    same = compare(lp8, lp8, ids)
    assert same['kl_mean'] < 1e-6 and same['top1_agreement'] == 1.0
    diff = compare(lp8, logprobs(m4, ids, chunk=16), ids)
    assert diff['kl_mean'] > 0 and diff['tokens'] == 39 and diff['ppl_ref'] > 0
    print(f"kl harness OK (int4 vs int8 on the synthetic model: KL {diff['kl_mean']:.3f}, "
          f"top-1 {diff['top1_agreement']:.0%})")
