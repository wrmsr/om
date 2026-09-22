# ruff: noqa: N806 N812
"""
Cross-backend parity: the same synthetic model, the same tokens, every backend against the numpy float64 golden.

  * per-layer taps (embed, each block's mixer and output, final norm, logits) agree to f32 precision
  * cached incremental decode == one-shot forward, per backend
  * quantized weights: each backend's `qweight` + `linear` / `embedding` reproduce numpy's dequant exactly (f32), and
    each backend's own on-device `quantize` lands within int8 rounding of numpy's
  * whole-model quantized forward agrees across backends
"""
import pathlib
import tempfile
import typing as ta

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


DISABLED_BACKENDS: ta.Any = {
    # 'torch',
    # 'mlx',
    'tinygrad',
}


def backends() -> list[Ops]:
    out: list[Ops] = []

    if 'torch' not in DISABLED_BACKENDS:
        try:
            from ..backends.torch import TorchOps

            out.append(TorchOps('cpu'))
        except ImportError:
            print('torch not installed; skipping')

    if 'mlx' not in DISABLED_BACKENDS:
        try:
            from ..backends.mlx import MlxOps

            out.append(MlxOps())
        except ImportError:
            print('mlx not installed; skipping')

    if 'tinygrad' not in DISABLED_BACKENDS:
        try:
            from ..backends.tinygrad import TinygradOps

            out.append(TinygradOps())
        except ImportError:
            print('tinygrad not installed; skipping')

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


def test_gated_delta_parity():
    """
    Chunked (several chunks, padded tail, non-zero initial state) == the numpy f64 recurrence, per backend; and
    `gated_delta` dispatches to the recurrence for T == 1.
    """

    rng = np.random.default_rng(3)
    B = 2
    H = 4
    T = 150
    d = 16
    q = rng.standard_normal((B, H, T, d))
    q /= np.linalg.norm(q, axis=-1, keepdims=True) * d**0.5
    k = rng.standard_normal((B, H, T, d))
    k /= np.linalg.norm(k, axis=-1, keepdims=True)
    v = rng.standard_normal((B, H, T, d))
    g = -rng.random((B, H, T)) * 2
    beta = rng.random((B, H, T))
    s0 = rng.standard_normal((B, H, d, d)) * 0.3

    gold_ops = NumpyOps()
    ins = [gold_ops.array(x) for x in (q, k, v, g, beta, s0)]
    gold_out, gold_state = gold_ops.gated_delta_recurrent(*ins)
    for chunk in (64, 16, 7):
        out, state = gold_ops.gated_delta_chunked(*ins, chunk)  # type: ignore
        assert rel_err(out, gold_out) < 1e-12 and rel_err(state, gold_state) < 1e-12, chunk

    for ops in backends():
        f32 = ops.dtype('f32')
        ins = [ops.array(x, f32) for x in (q, k, v, g, beta, s0)]
        out, state = ops.gated_delta(*ins)
        e_out, e_state = rel_err(ops.numpy(out), gold_out), rel_err(ops.numpy(state), gold_state)
        assert e_out < 2e-5 and e_state < 2e-5, (ops.name, e_out, e_state)
        out1, state1 = ops.gated_delta(*[x[:, :, :1] if x.ndim in (3, 4) and x.shape[2] == T else x for x in ins])
        g1 = gold_ops.gated_delta_recurrent(*[
            x[:, :, :1] if x.ndim in (3, 4) and x.shape[2] == T else x
            for x in [gold_ops.array(y) for y in (q, k, v, g, beta, s0)]
        ])
        assert rel_err(ops.numpy(out1), g1[0]) < 2e-5 and rel_err(ops.numpy(state1), g1[1]) < 2e-5, ops.name
        print(f'{ops.name}: chunked gated delta vs f64 recurrence: out {e_out:.1e}, state {e_state:.1e}')


def test_static_decode_parity():
    """The captured fixed-capacity decode step == the functional cached decode == the numpy golden one-shot
    forward, per backend, including a capacity doubling mid-sequence and snapshot/restore."""

    from ..model import Decoder

    cfg, hf, src = synthetic_source()
    ids = np.random.default_rng(4).integers(0, 256, (1, 14))
    n_prompt = 5
    gold = Qwen35.from_source(src, NumpyOps(), dtype='f32', verbose=False)
    gold_logits = gold.forward(ids)[0]  # [T, V]

    for ops in backends():
        if getattr(ops, 'capture_mode', None) == 'auto' and ops.name.endswith('cpu'):
            ops.capture_mode = 'static'  # exercise the CUDA-graph static-input protocol without a GPU
        model = Qwen35.from_source(src, ops, dtype='f32', verbose=False)
        cache = Cache(cfg)
        model.forward(ids[:, :n_prompt], cache)
        dec = Decoder(model, cache, capacity=8)  # 5 prompt tokens; grows past 8 partway through
        got = []
        for t in range(n_prompt, ids.shape[1]):
            if t == n_prompt + 2:
                snap = dec.snapshot()
            got.append(ops.numpy(dec.step(int(ids[0, t]))))
        got = np.concatenate(got, 0)  # logits after tokens n_prompt .. T-1
        e = rel_err(got, gold_logits[n_prompt:])
        assert e < 2e-4, (ops.name, e)
        # restore the snapshot and re-run the tail: identical
        dec.restore(snap)
        again = [ops.numpy(dec.step(int(ids[0, t]))) for t in range(n_prompt + 2, ids.shape[1])]
        assert np.abs(np.concatenate(again, 0) - got[2:]).max() < 1e-5, ops.name
        print(f'{ops.name}: static decode step vs golden rel err {e:.1e} (capacity grew to {dec.capacity})')

        # generate() static path == generate() functional path
        a = model.generate(ids[0, :n_prompt].tolist(), max_new_tokens=6, static=True)
        b = model.generate(ids[0, :n_prompt].tolist(), max_new_tokens=6, static=False)
        assert a == b, (ops.name, a, b)
        if hasattr(ops, 'capture_mode'):
            ops.capture_mode = 'auto'


def test_spec_decode_parity():
    """
    Speculative decoding must reproduce plain greedy decoding token for token whatever the drafts are. Checked
    with the real (random, hence useless) draft head, and with an oracle draft function that returns the true
    continuation corrupted at a chosen index so every acceptance length 0..k gets exercised -- that pins down
    verify, commit (DeltaNet state selection, KV masking) and the draft-head refresh. Also: the draft head's
    static step == its functional pass.
    """

    from ..model import Sampler
    from ..model import SpecDecoder

    cfg, hf, src = synthetic_source()
    prompt = np.random.default_rng(6).integers(0, 256, 6).tolist()
    n_new = 24
    k = 3
    for ops in backends():
        if getattr(ops, 'capture_mode', None) == 'auto' and ops.name.endswith('cpu'):
            ops.capture_mode = 'static'
        model = Qwen35.from_source(src, ops, dtype='f32', verbose=False, mtp=True)
        ref = model.generate(prompt, max_new_tokens=n_new, static=True)
        full = prompt + ref

        # (a) the real draft head
        out = model.generate(prompt, max_new_tokens=n_new, spec=k)
        assert out == ref, (ops.name, out, ref)

        # (b) oracle drafts, corrupted at index m in turn: exactly m drafts must be accepted each round
        cache = Cache(cfg)
        logits, hidden = model.forward(np.array([prompt]), cache, return_hidden=True)
        sd = SpecDecoder(model, cache, prompt, logits, hidden, k, Sampler(), capacity=len(full) + k + 2)
        pattern = [3, 0, 1, 2, 3, 3]
        expected: list[int] = []

        def oracle(n, next_tok, kk):
            assert next_tok == full[n], (n, next_tok, full[n])
            d = list(full[n + 1:n + 1 + kk])
            d += [0] * (kk - len(d))
            m = pattern[len(expected) % len(pattern)]
            if m < kk:
                d[m] = (d[m] + 1) % cfg.vocab_size
            expected.append(min(m, len(full) - n - 1))
            return d

        sd.draft_fn = oracle
        got: list[int] = []
        while len(got) < n_new:
            before = sd.accepted
            got.extend(sd.round())
            assert sd.accepted - before == expected[-1], (ops.name, sd.rounds, sd.accepted - before, expected[-1])
        assert got[:n_new] == ref, (ops.name, got[:n_new], ref)
        print(f'{ops.name}: spec decode == greedy (real head + oracle drafts; {sd.rounds} oracle rounds, '
              f'{sd.accepted} accepted)')

        # (c) draft-head static step vs functional pass over the same 4 entries from an empty cache
        mtp = model.mtp
        assert mtp is not None
        T = 4
        toks = np.array([full[1:1 + T]], dtype=np.int32)
        cache = Cache(cfg)
        _, hid = model.forward(np.array([full[:T]]), cache, return_hidden=True)
        f_logits, f_d, (fk, fv) = mtp.prefill(toks, hid, 0)
        dec = sd.dec
        B, KV, _, D = fk.shape
        zeros = ops.zeros((B, KV, dec.capacity, D), fk.dtype)
        fn = mtp.step_fn(T)
        s_logits, s_d, sk, sv = fn(ops.array(toks), hid, ops.scalar(0), *dec.tables(), zeros, ops.copy(zeros))
        assert rel_err(ops.numpy(s_logits), ops.numpy(f_logits)) < 2e-5, ops.name
        assert rel_err(ops.numpy(s_d), ops.numpy(f_d)) < 2e-5, ops.name
        assert rel_err(ops.numpy(sk[:, :, :T]), ops.numpy(fk)) < 2e-5, ops.name
        if hasattr(ops, 'capture_mode'):
            ops.capture_mode = 'auto'


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
