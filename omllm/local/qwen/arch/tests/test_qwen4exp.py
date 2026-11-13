"""
Qwen3.8-Flash-Next (`qwen4_exp`) against its reference implementation in transformers, on a tiny random checkpoint
written by transformers itself: every component on (gated residual, MoE with a shared expert, QSA with a budget the
prompt exceeds, the n-gram layer, an EOS mid-prompt for its segment logic). The functional forward must give the
reference's logits at every position, on every backend; prefilling in two chunks through the cache must give the
one-shot logits (each component's state carried); the n-gram hash parameters must be the reference's.
"""
import os
import tempfile
import typing as ta

import numpy as np
import pytest

from ...api import generate
from ...arch.qwen35 import load_qwen35
from ...core.cache import Cache
from ...core.config import Qwen4ExpConfig
from ...core.ple import NGramLayerEmbedding
from ...load.weights import open_source
from ...ops.reference import NumpyOps
from ...tests.test_parity import backends


##


def _checkpoint(path: str, **overrides: ta.Any) -> ta.Any:
    torch = pytest.importorskip('torch')
    transformers = pytest.importorskip('transformers')
    if not hasattr(transformers, 'Qwen4ExpForCausalLM'):
        pytest.skip('transformers without qwen4_exp')

    cfg = transformers.Qwen4ExpTextConfig(**{**dict(
        vocab_size=256,
        hidden_size=64,
        num_hidden_layers=4,
        num_attention_heads=4,
        num_key_value_heads=2,
        head_dim=32,
        linear_num_key_heads=2,
        linear_num_value_heads=4,
        linear_key_head_dim=16,
        linear_value_head_dim=16,
        num_experts=8,
        num_experts_per_tok=2,
        moe_intermediate_size=32,
        shared_expert_intermediate_size=32,
        hc_count=4,
        hc_lowrank=8,
        ple_layer_ids=[2],
        ple_embed_dim=64,
        ngram_vocab_size_base=1000,
        split_ngram_parts=2,
        indexer_n_heads=4,
        indexer_kv_heads=1,
        indexer_head_dim=16,
        indexer_budget=6,
        indexer_compress_ratio=2,
        rope_parameters={'rope_type': 'default', 'rope_theta': 10000.0, 'partial_rotary_factor': 0.25},
        eos_token_id=1,
        max_position_embeddings=512,
        tie_word_embeddings=False,
    ), **overrides})
    torch.manual_seed(0)
    model = transformers.Qwen4ExpForCausalLM(cfg).eval()
    with torch.no_grad():
        for p in model.parameters():  # off the init's zeros and ones: every weight matters
            p.add_(torch.randn_like(p) * 0.1)
    model.save_pretrained(path)
    return model


def test_qwen4exp_matches_the_reference():
    torch = pytest.importorskip('torch')

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'qwen4exp')
        ref_model = _checkpoint(path)

        prompt = np.random.default_rng(5).integers(2, 256, 24)
        prompt[11] = 1  # an EOS: the n-gram hash restarts its segment after it
        ids = prompt.reshape(1, -1)
        with torch.no_grad():
            ref = ref_model(torch.from_numpy(ids)).logits.float().numpy()

        src = open_source(path)
        cfg = src.config
        assert isinstance(cfg, Qwen4ExpConfig), type(cfg)
        assert cfg.layer_types == ['linear', 'linear', 'linear', 'indexed'] and cfg.ple_layers == [1]
        assert len(prompt) // cfg.indexer_compress_ratio > cfg.block_topk  # QSA selects (it is not dense here)

        # the n-gram hash parameters are the reference's
        ple = ref_model.model.layers[1].ple.ple_embedding
        for ops in backends()[:1]:
            m = load_qwen35(src, ops, dtype='f32', verbose=False)
            emb = m.blocks[1].embedding
            assert isinstance(emb, NGramLayerEmbedding)
            assert emb.multipliers == ple.layer_multipliers.tolist()
            assert emb.sizes == ple.ngram_heads_vocab_sizes.tolist()
            assert emb.offsets == ple.ngram_heads_offsets.tolist()

        for ops in [NumpyOps(), *backends()]:
            model = load_qwen35(src, ops, dtype='f32', verbose=False)
            got = ops.numpy(model.forward(ids))
            err = float(np.abs(got - ref).max() / np.abs(ref).max())
            assert err < 1e-4, (ops.name, err)

            # two chunks through the functional cache == one pass (the second chunk crosses into QSA's selection)
            cache = Cache(model.cfg)
            a = ops.numpy(model.forward(ids[:, :9], cache))
            b = ops.numpy(model.forward(ids[:, 9:], cache))
            err2 = float(np.abs(np.concatenate([a, b], 1) - ref).max() / np.abs(ref).max())
            assert err2 < 1e-4, (ops.name, 'chunked', err2)
            print(f'{ops.name}: qwen4_exp == reference ({err:.1e}; chunked {err2:.1e})')

        # greedy generation against the reference's own (its cached decode path): the functional decoder, the static
        # one (captured steps: QSA selecting, the n-gram hash on the device), and the static one verifying
        # prompt-lookup drafts (T-token steps whose per-token states a commit selects from)
        with torch.no_grad():
            want = ref_model.generate(
                torch.from_numpy(ids[:, :10]),
                max_new_tokens=12,
                do_sample=False,
                eos_token_id=None,
                pad_token_id=0,
            )[0, 10:].tolist()
        for ops in backends()[:1]:
            if getattr(ops, 'capture_mode', None) == 'auto':
                ops.capture_mode = 'static'  # type: ignore[attr-defined]
            model = load_qwen35(src, ops, dtype='f32', verbose=False)
            p = ids[0, :10].tolist()
            for kw in (dict(static=False), dict(static=True), dict(lookup_ngram=1, lookup_k=3)):
                res = generate(model, p, max_new_tokens=12, **kw)
                assert res.tokens == want, (ops.name, kw, res.tokens, want)
            assert res.drafted, 'no lookup rounds: nothing verified'


def test_qwen4exp_compiles_whole():
    """
    On CUDA, compiled and graph-captured, in both KV formats: every step traces as one graph (QSA's selection, the
    experts' gather, the n-gram hash in int64 included), a prompt of another length compiles nothing, and the tokens
    -- plain and verifying prompt-lookup drafts -- are the functional path's.
    """

    torch = pytest.importorskip('torch')
    if not torch.cuda.is_available():
        pytest.skip('no CUDA')

    import torch._dynamo as dynamo
    from torch._dynamo.utils import counters

    from ...backends.torch import TorchOps

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'qwen4exp')
        _checkpoint(path)
        src = open_source(path)
        prompt = list(range(5, 35))

        for kv in ('bf16', 'fp8'):
            dynamo.reset()
            counters.clear()
            ops = TorchOps('cuda', compile=True, kv_dtype=kv)
            model = load_qwen35(src, ops, dtype='f32', verbose=False)
            want = generate(model, prompt, max_new_tokens=16, static=False).tokens

            with dynamo.error_on_graph_break(True):
                plain = generate(model, prompt, max_new_tokens=16, capacity=128)
                looked = generate(model, prompt, max_new_tokens=16, capacity=128, lookup_ngram=1, lookup_k=3)
            assert plain.tokens == want and looked.tokens == want, (kv, plain.tokens, looked.tokens, want)
            assert looked.drafted, kv

            graphs = counters['stats']['unique_graphs']
            generate(model, prompt[:7], max_new_tokens=16, capacity=128)
            assert counters['stats']['unique_graphs'] == graphs, (kv, 'recompiled')


def test_qwen4exp_resumes_and_injects():
    """
    A follow-up resumed from a prefix snapshot (every component's state exported and restored: the n-gram context and
    conv, QSA's indexer keys) equals a cold run of the whole prompt; and the injector assembles the same model.
    """

    pytest.importorskip('torch')
    from omcore import inject as inj

    from ...backends.inject import BackendConfig
    from ...backends.torch import TorchOps
    from ...decode.inject import DecodeConfig
    from ...decode.runners import GenerationParams
    from ...decode.runners import GenerationRunner
    from ...inject.inject import bind_qwen
    from ...load.inject import LoadConfig
    from ...prefix.cache import PrefixCache
    from ...prefix.inject import PrefixConfig
    from ...spec.inject import SpecConfig

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'qwen4exp')
        _checkpoint(path)
        src = open_source(path)
        p1 = list(range(5, 25))

        ops = TorchOps('cpu', capture_mode='static')
        model = load_qwen35(src, ops, dtype='f32', verbose=False)
        pc = PrefixCache(ops, 1 << 30, 0)
        r1 = generate(model, p1, max_new_tokens=6, prefix_cache=pc)
        p2 = [*p1, *r1.tokens, 1, 7, 8, 9]  # (an EOS in the follow-up's new tokens)
        r2 = generate(model, p2, max_new_tokens=8, prefix_cache=pc)
        cold = generate(model, p2, max_new_tokens=8)
        assert r2.reused == len(p1) + len(r1.tokens), r2.reused
        assert r2.tokens == cold.tokens, (r2.tokens, cold.tokens)

        injector = inj.create_injector(bind_qwen(
            backend=BackendConfig(backend='torch', device='cpu'),
            load=LoadConfig(model=path, dtype='f32'),
            decode=DecodeConfig(capacity=64),
            spec=SpecConfig(),
            prefix=PrefixConfig(enabled=False),
        ))
        got = injector[GenerationRunner].run(GenerationParams(prompt=p2, max_new_tokens=8))
        assert got.tokens == cold.tokens, (got.tokens, cold.tokens)


def test_qwen4exp_quantized_experts():
    """
    With int4 weights the experts are stacked quantized (Ops.expert_weights) and run through the expert GEMV on CUDA:
    its logits equal the CPU's (which dequantizes the selected experts), and the compiled, captured static decode
    traces whole and gives the functional path's tokens.
    """

    torch = pytest.importorskip('torch')
    if not torch.cuda.is_available():
        pytest.skip('no CUDA')

    import torch._dynamo as dynamo

    from ...backends.torch import TorchOps
    from ...backends.torch import TorchQExperts

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'qwen4exp')
        _checkpoint(path, moe_intermediate_size=64, shared_expert_intermediate_size=64)  # (group 64 divides it)
        src = open_source(path)
        ids = np.asarray([list(range(5, 29))])

        logits = {}
        for dev in ('cpu', 'cuda'):
            ops = TorchOps(dev, compile=dev == 'cuda')
            model = load_qwen35(src, ops, dtype='f32', quant='int4', verbose=False)
            assert isinstance(model.blocks[0].ffn.gate_up, TorchQExperts)  # type: ignore[attr-defined]
            logits[dev] = ops.numpy(model.forward(ids))
        err = float(np.abs(logits['cuda'] - logits['cpu']).max() / np.abs(logits['cpu']).max())
        assert err < 1e-4, err

        want = generate(model, ids[0].tolist(), max_new_tokens=12, static=False).tokens
        dynamo.reset()
        with dynamo.error_on_graph_break(True):
            got = generate(model, ids[0].tolist(), max_new_tokens=12, capacity=64).tokens
        assert got == want, (got, want)
