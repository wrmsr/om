# ruff: noqa: N806
"""
Inkling 2 from a GGUF: the same synthetic checkpoint read as the lab releases it and as llama.cpp's converter lays it
out (inkling2ggufs.py) gives the same config, the same canonical parameters name for name -- the packed experts'
bytes among them -- the same tokenization and the same logits. And what a GGUF may hold that the checkpoint does not:
tensors of quantized types, a factor beside a weight, metadata this code refuses.
"""
import os.path
import tempfile
import typing as ta

import numpy as np
import pytest

from omcore import dataclasses as dc

from ...api import generate
from ...arch.qwen35 import load_qwen35
from ...arch.registry import architecture_for
from ...arch.tests.inkling2checkpoints import RELEASED_CONFIG
from ...arch.tests.inkling2checkpoints import inkling2_test_config
from ...arch.tests.inkling2checkpoints import write_inkling2_checkpoint
from ...core.inkling2.config import Inkling2Config
from ...core.inkling2.config import inkling2_config_from_gguf
from ...core.inkling2.config import inkling2_config_from_hf
from ...ops.reference import NumpyOps
from ...tests.tritonmodes import triton_modes
from ...tokenizer import Tokenizer
from ..gguf.constants import GGMLQuantizationType
from ..gguf.quants import dequantize
from ..gguf.quants import quantize
from ..inkling2 import Inkling2HFSource
from ..inkling2gguf import Inkling2GgufSource
from ..weights import open_source
from .comparesources import compare_configs
from .comparesources import compare_tensor
from .comparesources import compare_tokenizers
from .inkling2ggufs import RELEASED_GGUF_METADATA
from .inkling2ggufs import write_inkling2_gguf


##


MXFP8_LAYERS = 2


def _f32(v: float) -> float:
    return float(np.float32(v))


def _config() -> dict[str, ta.Any]:
    """
    The test config with what a GGUF asks of it: expert rows of 64 inputs (GGML's NVFP4 is super-blocks of 64 weights),
    and floats that are float32 values (a GGUF's metadata keeps them so), which is what lets the two sources' configs
    be equal and their logits the same to the bit.
    """

    return inkling2_test_config(
        moe_intermediate_size=64,
        qk_l2_clip_threshold=_f32(22.627416997969522),
        log_scaling_alpha=_f32(0.1),
        rms_norm_eps=_f32(1e-6),
    )


def _write(tmp: str, **kw: ta.Any) -> tuple[str, str]:
    """A synthetic checkpoint under `tmp` and the GGUF converted from it: their paths."""

    checkpoint = os.path.join(tmp, 'checkpoint')
    if not os.path.exists(checkpoint):
        write_inkling2_checkpoint(checkpoint, _config(), mxfp8_layers=MXFP8_LAYERS)

    path = os.path.join(tmp, f'model-{len(os.listdir(tmp))}.gguf')
    write_inkling2_gguf(path, checkpoint, **kw)
    return checkpoint, path


def _sources(tmp: str, **kw: ta.Any) -> tuple[Inkling2HFSource, Inkling2GgufSource]:
    checkpoint, path = _write(tmp, **kw)
    hf = open_source(checkpoint)
    src = open_source(path)
    assert isinstance(hf, Inkling2HFSource) and isinstance(src, Inkling2GgufSource)
    return hf, src


def _logits(src: ta.Any, ids: np.ndarray) -> np.ndarray:
    ops = NumpyOps()
    return np.asarray(ops.numpy(load_qwen35(src, ops, dtype='f32', verbose=False).forward(ids)))


def test_same_parameters():
    with tempfile.TemporaryDirectory() as tmp:
        hf, src = _sources(tmp)

        cfg = src.config
        assert isinstance(cfg, Inkling2Config)
        assert dc.replace(cfg, extra={}) == dc.replace(hf.config, extra={})
        assert cfg.extra['format'] == 'gguf' and cfg.draft is None
        assert src.path.endswith('.gguf')

        names = architecture_for(cfg).param_names(cfg)  # type: ignore[attr-defined]
        assert set(src.names()) == set(names) == set(hf.names())
        assert all(src.has(n) for n in names) and not src.has('layers.0.attn_queries')

        for name in names:
            got, want = src.get(name), hf.get(name)
            assert got.dtype == np.float32 and got.shape == want.shape, name
            assert np.array_equal(got, want), name

        # the experts the checkpoint packs as NVFP4 are handed over packed, its own bytes; the last layers', which a
        # GGUF holds decoded, are not
        for i in range(cfg.num_layers):
            for part in ('gate_up', 'down'):
                name = f'layers.{i}.mlp.experts.{part}'
                packed, theirs = src.get_microscaled(name), hf.get_microscaled(name)
                assert theirs is not None

                if i >= cfg.num_layers - MXFP8_LAYERS:
                    assert theirs.fmt == 'mxfp8' and packed is None
                    continue

                assert packed is not None and packed.fmt == theirs.fmt == 'nvfp4' and packed.shape == theirs.shape
                assert np.array_equal(packed.codes, theirs.codes) and np.array_equal(packed.scales, theirs.scales)
                assert packed.outer is not None and theirs.outer is not None
                assert packed.outer.dtype == np.float32 and np.array_equal(packed.outer, theirs.outer)

        assert src.get_microscaled('layers.0.attn.wq_du.weight') is None


def test_same_tokenizer():
    with tempfile.TemporaryDirectory() as tmp:
        hf, src = _sources(tmp)

        assert src.tokenizer_spec['kind'] == 'gguf' and src.tokenizer_spec['ignore_merges'] is True

        want = Tokenizer.from_spec(hf.tokenizer_spec)
        got = Tokenizer.from_spec(src.tokenizer_spec)
        assert got.tokens == want.tokens and got.special == want.special
        assert (got.pre, got.ignore_merges, got.eos_id, got.bos_id, got.add_bos) == ('inkling2', True, 266, None, False)
        assert (want.pre, want.ignore_merges, want.eos_id, want.bos_id, want.add_bos) == ('inkling2', True, 266, None, False)  # noqa

        for text in (
                'the thin thing in the theatre\n\n  then: 1234567 + 0.5',
                '<|message_user|>in the<|content_text|>what is the time?<|end_message|>',
                'naïve café, \u65e5\u672c\u8a9e, \U0001f600 and <| not a marker |>',
        ):
            assert got.encode(text) == want.encode(text), text
            assert got.decode(got.encode(text)) == text


def test_same_logits():
    ids = np.random.default_rng(0).integers(0, 300, (1, 24))

    with tempfile.TemporaryDirectory() as tmp:
        hf, src = _sources(tmp)

        want = _logits(hf, ids)
        got = _logits(src, ids)
        assert got.shape == (1, 24, 300) and np.abs(want).max() > 1
        assert np.array_equal(got, want)

        # a GGUF of the model holds no draft model: asking for one fails as it does for a checkpoint without one
        with pytest.raises(ValueError, match='no draft model'):
            load_qwen35(src, NumpyOps(), dtype='f32', verbose=False, mtp=True)


@triton_modes('compiled', timeout_s=120)
def test_cuda_kernels_over_packed_and_dense_experts():
    """
    A GGUF's experts are of two kinds in one model, which a checkpoint's never are: the NVFP4 stacks, read packed by
    the expert kernel, and the last layers' dense ones. On CUDA with the Triton kernels on, the logits are the CPU's
    and the checkpoint's, and the static decode -- captured steps over both kinds -- gives the functional path's
    tokens, plain and verifying drafts. (It executes Triton kernels, so it runs in a child process:
    tests/tritonmodes.py.)
    """

    from ...backends.torch import TorchMicroscaledExperts
    from ...backends.torch import TorchOps

    ids = np.random.default_rng(2).integers(0, 300, (1, 24))
    prompt = ids[0, :10].tolist()

    def load(src: ta.Any, ops: ta.Any) -> ta.Any:
        return load_qwen35(src, ops, dtype='f32', verbose=False)

    def experts(model: ta.Any, visit: int) -> ta.Any:
        return model.blocks[visit].sublayers[1][0]._inner._ffn._gate_up  # noqa

    with tempfile.TemporaryDirectory() as tmp:
        hf, src = _sources(tmp)

        cpu = load(src, TorchOps('cpu', triton=False))
        want_logits = cpu.ops.numpy(cpu.forward(ids))

        ops = TorchOps('cuda')
        assert ops.triton
        model = load(src, ops)
        assert isinstance(experts(model, 0), TorchMicroscaledExperts)
        assert not isinstance(experts(model, -1), TorchMicroscaledExperts)

        theirs = load(hf, ops)
        assert isinstance(experts(theirs, -1), TorchMicroscaledExperts)

        for m in (model, theirs):
            got = ops.numpy(m.forward(ids))
            err = float(np.abs(got - want_logits).max() / np.abs(want_logits).max())
            assert err < 2e-4, err

        want = list(generate(model, prompt, max_new_tokens=14, static=False).tokens)
        assert list(generate(theirs, prompt, max_new_tokens=14, static=False).tokens) == want
        for gen_kw in (dict(capacity=128), dict(capacity=128, lookup_ngram=1, lookup_k=3)):
            got_tokens = list(generate(model, prompt, max_new_tokens=14, **gen_kw).tokens)  # type: ignore[arg-type]
            assert got_tokens == want, (gen_kw, got_tokens, want)


def test_quantized_tensors():
    """
    A smaller file's types: projections and tables as Q8_0, the last layers' experts as Q8_0 too. They are read
    through the vendored quantizers and held dense; the NVFP4 experts stay the checkpoint's bytes.
    """

    Q8_0 = GGMLQuantizationType.Q8_0
    ids = np.random.default_rng(1).integers(0, 300, (1, 16))

    def requantized(x: np.ndarray) -> np.ndarray:
        return dequantize(quantize(x, Q8_0), Q8_0)

    with tempfile.TemporaryDirectory() as tmp:
        hf, src = _sources(tmp, dense_type=Q8_0, expert_type=Q8_0)
        L = src.config.num_layers

        changed = 0
        for name in hf.names():
            got, want = src.get(name), hf.get(name)
            if np.array_equal(got, want):
                continue
            changed += 1
            assert got.shape == want.shape and np.array_equal(got, requantized(want)), name
            assert np.abs(got - want).max() < 0.01 * np.abs(want).max(), name
        # the two tables, six projections a layer, and the last layers' experts
        assert changed == 2 + 6 * L + 2 * MXFP8_LAYERS

        for i in range(L):
            packed = src.get_microscaled(f'layers.{i}.mlp.experts.down')
            assert (packed is not None) == (i < L - MXFP8_LAYERS)

        # (the model runs on them; how far its logits move says nothing here, where random experts amplify any change)
        got = _logits(src, ids)
        assert got.shape == (1, 16, 300) and np.isfinite(got).all()
        assert not np.array_equal(got, _logits(hf, ids))


def test_a_factor_beside_a_weight():
    """A `.scale` tensor beside a weight multiplies what its bytes decode to: one factor, or one per matrix."""

    factors = np.linspace(0.5, 2.0, 8, dtype=np.float32)

    with tempfile.TemporaryDirectory() as tmp:
        hf, src = _sources(tmp, tensors={
            'blk.0.attn_q.scale': np.asarray([3.0], dtype=np.float32),
            'blk.7.ffn_down_exps.scale': factors,
            'blk.0.ffn_down_exps.scale': None,
        })

        assert np.array_equal(src.get('layers.0.attn.wq_du.weight'), hf.get('layers.0.attn.wq_du.weight') * 3)
        assert np.array_equal(
            src.get('layers.7.mlp.experts.down'),
            hf.get('layers.7.mlp.experts.down') * factors[:, None, None],
        )
        assert np.array_equal(src.get('layers.0.attn.wk_dv.weight'), hf.get('layers.0.attn.wk_dv.weight'))

        # an NVFP4 stack with no factors beside it is its codes times its block scales
        bare = src.get_microscaled('layers.0.mlp.experts.down')
        packed = hf.get_microscaled('layers.0.mlp.experts.down')
        assert bare is not None and bare.outer is not None and packed is not None
        assert np.array_equal(bare.outer, np.ones(8)) and np.array_equal(bare.codes, packed.codes)

        _, path = _write(tmp, tensors={'blk.7.ffn_down_exps.scale': factors[:3]})
        with pytest.raises(ValueError, match='3 factors for 8 matrices'):
            open_source(path).get('layers.7.mlp.experts.down')


def test_comparing_sources():
    """What compares a real GGUF with the checkpoint it was made from (comparesources.py), on the synthetic two."""

    Q8_0 = GGMLQuantizationType.Q8_0

    with tempfile.TemporaryDirectory() as tmp:
        hf, src = _sources(tmp)

        assert compare_configs(src.config, hf.config) == []

        results = [compare_tensor(src, hf, name) for name in src.names()]
        assert all(c.equal and c.max_abs == 0 for c in results)
        assert {c.how for c in results} == {'packed nvfp4', 'float32', 'float32 (dense / mxfp8)'}

        tokenizers = (Tokenizer.from_spec(src.tokenizer_spec), Tokenizer.from_spec(hf.tokenizer_spec))
        assert compare_tokenizers(*tokenizers, ['the thin thing', 'in']) == (True, 9)

        # a file that is not the checkpoint, and a config that is not its
        _, path = _write(tmp, dense_type=Q8_0)
        lossy = compare_tensor(open_source(path), hf, 'layers.0.attn.wq_du.weight')
        assert not lossy.equal and 0 < lossy.max_abs < 0.01

        rounded = dc.replace(hf.config, log_scale_alpha=0.1, window=7)
        assert [line.split(':')[0] for line in compare_configs(src.config, rounded)] == ['window', 'log_scale_alpha']
        assert [line.rsplit(' ', 1)[-1] for line in compare_configs(src.config, rounded)] == ['DIFFERENT', 'float32)']


def test_config():
    # the released files' metadata gives the released checkpoint's config, its floats as float32 holds them
    released = inkling2_config_from_hf(RELEASED_CONFIG)
    metadata = RELEASED_GGUF_METADATA

    c = inkling2_config_from_gguf(metadata.get, eos_id=200006)
    assert (c.vocab_size, c.embed_size, c.num_layers, c.num_visits) == (200058, 201024, 24, 48)
    assert [i for i in range(24) if not c.is_local(i)] == [5, 11, 17, 23]

    rounded = ('qk_clip', 'log_scale_alpha', 'rms_eps')
    for f in dc.fields(c):
        got, want = getattr(c, f.name), getattr(released, f.name)
        assert (got == _f32(want) != want) if f.name in rounded else (got == want), f.name

    # what is refused: by the checkpoint's parser, or as what only a GGUF can say
    for bad, error, why in (
            ({'loop.varying': True}, ValueError, 'variable-pass loop'),
            ({'loop.start': 3}, ValueError, 'whole blocks'),
            ({'attention.head_count': [24] * 23 + [12]}, ValueError, 'differs between layers'),
            ({'attention.value_length': 64}, ValueError, 'one width'),
            ({'attention.key_length_swa': 64}, ValueError, 'one width'),
            ({'rope.dimension_count': 64}, ValueError, 'rotary'),
            ({'attention.relative_extent': None}, KeyError, 'attention.relative_extent'),
    ):
        with pytest.raises(error, match=why):
            inkling2_config_from_gguf({**metadata, **bad}.get)

    # a scalar where the released files keep a value per layer, and the experts' width under its older key
    plain = {**metadata, 'attention.head_count': 24, 'expert_feed_forward_length': None}
    assert dc.replace(inkling2_config_from_gguf(plain.get, eos_id=200006), extra={}) == dc.replace(c, extra={})


def test_refused_files():
    with tempfile.TemporaryDirectory() as tmp:
        _, path = _write(tmp, metadata={'loop.varying': ('bool', True)})
        with pytest.raises(ValueError, match='variable-pass loop'):
            open_source(path)

        _, path = _write(tmp, pre='qwen35')
        with pytest.raises(ValueError, match='pre-tokenizer'):
            open_source(path)

        # read directly, a file of another architecture is not taken for this one
        _, path = _write(tmp, architecture='inkling2')
        with pytest.raises(ValueError, match="'inkling2', not inkling2_loop"):
            Inkling2GgufSource(path)
