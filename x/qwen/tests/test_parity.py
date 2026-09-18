# ruff: noqa: N806 N812
"""
Cross-backend parity: the same synthetic model, the same tokens, every backend against the numpy float64 golden.

  * per-layer taps (embed, each block's mixer and output, final norm, logits) agree to f32 precision
  * cached incremental decode == one-shot forward, per backend
  * quantized weights: each backend's `qweight` + `linear` / `embedding` reproduce numpy's dequant exactly (f32), and
    each backend's own on-device `quantize` lands within int8 rounding of numpy's
  * whole-model quantized forward agrees across backends

Run:  python -m pytest x/qwen/tests -q      or      python -m x.qwen.tests.test_parity
"""
import pathlib
import tempfile

import numpy as np

from ..model import Cache
from ..model import Qwen35
from ..ops import NumpyOps
from ..ops import Ops
from ..quant import quantize as quantize_np
from ..weights import GGUFSource
from ..weights import Qwen35Config
from .test_synthetic import CFG
from .test_synthetic import make_hf_params
from .test_synthetic import write_gguf


##


def backends() -> list[Ops]:
    out: list[Ops] = []

    try:
        from ..torch_ops import TorchOps
        out.append(TorchOps('cpu'))
    except ImportError:
        print('torch not installed; skipping')

    try:
        from ..mlx_ops import MlxOps
        out.append(MlxOps())
    except ImportError:
        print('mlx not installed; skipping')

    return out


def rel_err(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.abs(a - b).max() / (np.abs(b).max() + 1e-12))


def synthetic_source() -> tuple[Qwen35Config, dict, GGUFSource]:
    tmp = pathlib.Path(tempfile.mkdtemp())
    cfg = Qwen35Config(**CFG)  # type: ignore
    hf = make_hf_params(cfg)
    write_gguf(tmp / 'tiny.gguf', cfg, hf, quantize=False)
    return cfg, hf, GGUFSource(tmp / 'tiny.gguf')


##


def test_forward_parity():
    cfg, hf, src = synthetic_source()
    ids = np.random.default_rng(0).integers(0, 256, (2, 9))

    gold_ops = NumpyOps()
    gold_ops.taps = {}
    gold = Qwen35.from_source(src, gold_ops, dtype='f32', verbose=False)
    gold.forward(ids)
    gold_taps = gold_ops.taps

    for ops in backends():
        ops.taps = {}
        model = Qwen35.from_source(src, ops, dtype='f32', verbose=False)
        model.forward(ids)
        assert set(ops.taps) == set(gold_taps), (ops.name, set(ops.taps) ^ set(gold_taps))
        worst = ('', 0.0)
        for name in gold_taps:
            e = rel_err(ops.taps[name], gold_taps[name])
            assert e < 2e-4, (ops.name, name, e)
            if e > worst[1]:
                worst = (name, e)
        print(f'{ops.name}: {len(gold_taps)} taps match golden (worst {worst[0]} rel err {worst[1]:.1e})')
        ops.taps = None

        # cached incremental decode == one-shot, against the golden
        cache = Cache(cfg)
        parts = [ops.numpy(model.forward(ids[:, :4], cache))]
        for t in range(4, ids.shape[1]):
            parts.append(ops.numpy(model.forward(ids[:, t:t + 1], cache)))
        inc = np.concatenate(parts, axis=1)
        e = rel_err(inc, gold_taps['logits'])
        assert e < 2e-4, (ops.name, e)
        # snapshot / prefix reuse
        snap = Cache(cfg)
        model.forward(ids[:, :5], snap)
        snap2 = snap.snapshot(ops)
        a = ops.numpy(model.forward(ids[:, 5:], snap))
        b = ops.numpy(model.forward(ids[:, 5:], snap2))
        assert np.abs(a - b).max() < 1e-5
        print(f'{ops.name}: incremental decode + snapshot OK (rel err {e:.1e})')


def test_qweight_parity():
    rng = np.random.default_rng(1)
    w = (rng.standard_normal((96, 256)) * 0.05).astype(np.float32)
    x = (rng.standard_normal((2, 5, 256)) * 0.5).astype(np.float32)
    ids = np.array([[3, 95], [0, 42]])
    for bits in (8, 4):
        qw = quantize_np(w, bits, 64)
        ref_w = qw.dequantize()
        ref_y = x @ ref_w.T
        for ops in backends():
            f32 = ops.dtype('f32')
            bw = ops.qweight(qw, f32)
            y = ops.numpy(ops.linear(ops.array(x), bw))
            e = rel_err(y, ref_y)
            assert e < 1e-5, (ops.name, bits, e)
            emb = ops.numpy(ops.embedding(ops.array(ids), bw, f32))
            assert np.allclose(emb, ref_w[ids], atol=1e-6), (ops.name, bits)
            # the backend's own quantizer should agree with numpy's up to rounding ties
            own = ops.quantize(w, bits, 64, f32)
            y2 = ops.numpy(ops.linear(ops.array(x), own))
            e2 = rel_err(y2, ref_y)
            assert e2 < (0.02 if bits == 8 else 0.15), (ops.name, bits, e2)
            print(f'{ops.name} int{bits}: adopted qweight rel err {e:.1e}; own quantizer rel err {e2:.1e}')


def test_model_quant_parity():
    cfg, hf, src = synthetic_source()
    ids = np.random.default_rng(2).integers(0, 256, (1, 7))
    gold = Qwen35.from_source(src, NumpyOps(), dtype='f32', quant='int8', verbose=False)
    gl = gold.forward(ids)
    for ops in backends():
        m = Qwen35.from_source(src, ops, dtype='f32', quant='int8', verbose=False)
        lg = ops.numpy(m.forward(ids))
        e = rel_err(lg, gl)
        assert e < 0.05, (ops.name, e)  # backends use their own quantizer; only rounding ties differ
        print(f'{ops.name} int8 model vs numpy int8 model: rel err {e:.1e}')


if __name__ == '__main__':
    test_forward_parity()
    test_qweight_parity()
    test_model_quant_parity()
