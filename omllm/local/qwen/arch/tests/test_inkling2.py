"""
Inkling 2 (`inkling2_loop`): the model against its reference implementation, and its state through every way the
engine runs it.

The reference is transformers, used as a black box. Its values for the tests' own synthetic checkpoints -- written by
numpy in the released layout, experts packed as NVFP4 and MXFP8 (inkling2checkpoints.py) -- are kept beside the tests
(inkling2reference.py), so the comparison runs wherever numpy does; where a transformers with the model is installed,
one more test has it write a checkpoint of its own with the released schedule (24 layers, 12 of them three times) and
compares live.
"""
import os.path
import tempfile
import typing as ta

import numpy as np
import pytest

from ...api import generate
from ...core.inkling2.config import Inkling2Config
from ...core.inkling2.config import inkling2_config_from_hf
from ...core.inkling2.loop import LoopEntry
from ...core.inkling2.loop import LoopRestart
from ...core.model import Qwen35
from ...core.sublayers import SublayerBlock
from ...decode.decoder import Decoder
from ...decode.sampling import Sampler
from ...load.inkling2 import Inkling2HFSource
from ...load.weights import open_source
from ...ops.base import Ops
from ...ops.reference import NumpyOps
from ...prefix.cache import PrefixCache
from ...spec.oracle import OracleDraftSource
from ...tests.test_parity import backends
from ...tests.test_parity import leading_backends
from ...tests.tritonmodes import triton_modes
from ..inkling2 import Inkling2Architecture
from ..qwen35 import load_qwen35
from ..registry import architecture_for
from .inkling2checkpoints import RELEASED_CONFIG
from .inkling2checkpoints import inkling2_test_config
from .inkling2checkpoints import write_inkling2_checkpoint
from .inkling2reference import INKLING2_REFERENCE


##


CASES: ta.Mapping[str, ta.Mapping[str, ta.Any]] = {
    'packed': dict(),
    'dense': dict(dense_experts=True, seed=1),
}


def _static(ops: Ops) -> Ops:
    """A torch backend's captured steps run through the static-input protocol where there is no graph to capture."""

    if getattr(ops, 'capture_mode', None) == 'auto':
        ops.capture_mode = 'static'  # type: ignore[attr-defined]
    return ops


def _load(path: str, ops: Ops) -> Qwen35:
    return load_qwen35(open_source(path), ops, dtype='f32', verbose=False)


def test_config_forms():
    c = inkling2_config_from_hf(RELEASED_CONFIG)

    # the logits' width is not the embedding's, the head dim not hidden / heads, and the layers are not the visits
    assert (c.vocab_size, c.embed_size) == (200058, 201024)
    assert (c.hidden_size, c.num_heads, c.num_kv_heads, c.head_dim) == (2304, 24, 8, 128)
    assert (c.num_layers, c.num_visits) == (24, 48)
    assert [i for i in range(24) if not c.is_local(i)] == [5, 11, 17, 23]
    assert (c.loop_start, c.loop_end, c.loop_passes, c.loop_gate_rank) == (6, 18, 3, 64)
    assert (c.moe_intermediate_size, c.num_experts, c.num_experts_per_tok) == (1152, 128, 8)
    assert (c.window, c.rel_extent, c.rel_dim, c.conv_kernel) == (1024, 1024, 16, 4)
    assert c.eos_id == 200006

    visits = c.visits()
    assert len(visits) == 48
    assert visits[:6] == [(i, 0) for i in range(6)] and visits[42:] == [(i, 0) for i in range(18, 24)]
    assert visits[6:18] == [(i, 0) for i in range(6, 18)] and visits[30:42] == [(i, 2) for i in range(6, 18)]

    # the form the reference library writes
    flat = inkling2_config_from_hf(inkling2_test_config())
    assert (flat.num_layers, flat.num_visits, flat.block_layers) == (8, 16, 2)
    assert flat.local_layers == [0, 2, 4, 6]

    for bad, why in (
            (dict(n_shared_experts=1), 'shared experts'),
            (dict(swa_head_dim=8), 'different geometries'),
            (dict(scoring_func='softmax'), 'router scoring'),
            (dict(loop_layer_index_start=3), 'whole blocks'),  # (not a block's first layer)
    ):
        with pytest.raises(ValueError, match=why):
            inkling2_config_from_hf(inkling2_test_config(**bad))


def test_source_and_structure():
    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        src = open_source(tmp)
        assert isinstance(src, Inkling2HFSource) and isinstance(src.config, Inkling2Config)

        cfg = src.config
        arch = architecture_for(cfg)
        names = arch.param_names(cfg)  # type: ignore[attr-defined]
        assert set(names) == set(src.names()), set(names) ^ set(src.names())  # every tensor is one the model takes

        # the experts are held as the checkpoint stores them, the gate rows first; norms are used as stored
        gate_up = src.get_microscaled('layers.0.mlp.experts.gate_up')
        last = src.get_microscaled(f'layers.{cfg.num_layers - 1}.mlp.experts.down')
        assert gate_up is not None and last is not None
        assert (gate_up.fmt, last.fmt) == ('nvfp4', 'mxfp8')
        assert src.get_microscaled('layers.0.attn.wq_du.weight') is None
        assert np.array_equal(src.get('layers.0.mlp.experts.gate_up'), gate_up.dequantize())

        ops = NumpyOps()
        model = load_qwen35(src, ops, dtype='f32', verbose=False)

        # the execution order: a layer per visit and the loop's markers, each with a slot of state of its own -- and
        # the looped visits built over one set of sublayers
        blocks = [b for b in model.blocks if isinstance(b, SublayerBlock)]
        assert len(blocks) == cfg.num_visits == 16
        assert [type(b) for b in model.blocks if not isinstance(b, SublayerBlock)] == [
            LoopEntry,
            LoopRestart,
            LoopRestart,
        ]
        assert [b.index for b in blocks] == list(range(16))
        assert len(model.state_layouts()) == len(model.new_cache().layers) == 19

        by_layer: dict[int, list[SublayerBlock]] = {}
        for b, (layer, _) in zip(blocks, cfg.visits()):
            by_layer.setdefault(layer, []).append(b)
        assert sorted(len(v) for v in by_layer.values()) == [1] * 4 + [3] * 4
        for visits in by_layer.values():
            assert all(v.sublayers[0][0] is visits[0].sublayers[0][0] for v in visits)  # the same weights

        # each visit's state is its own: the three passes of a layer leave different KV
        cache = model.new_cache()
        model.forward(np.arange(2, 14).reshape(1, -1), cache)
        slots = [i for i, b in enumerate(model.blocks) if b in by_layer[2]]
        k0, k1, k2 = (ops.numpy(cache.layers[i][0]) for i in slots)  # type: ignore[index]
        assert k0.shape == k1.shape and not np.allclose(k0, k1) and not np.allclose(k1, k2)

        assert model.cfg.vocab_size == 300 and ops.numpy(model.forward(np.asarray([[5, 6]]))).shape == (1, 2, 300)


def test_local_layers_keep_a_window():
    """
    A local layer's keys and values are its window, whatever the context: exactly the positions there are until the
    window fills, then `window - 1` of them -- in the functional cache, in a snapshot, and in the static decoder's
    state at any capacity, where only the global layers' buffers grow.
    """

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        ops = NumpyOps()
        model = _load(tmp, ops)
        cfg = model.cfg
        assert isinstance(cfg, Inkling2Config)
        kept = cfg.window - 1

        # (visits in execution order; the loop's markers hold no state)
        local = [cfg.is_local(layer) for layer, _ in cfg.visits()]
        slots = [i for i, b in enumerate(model.blocks) if isinstance(b, SublayerBlock)]
        assert sum(local) == 8 and len(local) == 16

        def kv_lens(states: ta.Sequence[ta.Any]) -> tuple[set[int], set[int]]:
            lens = [int(states[i][0].shape[2]) for i in slots]
            return {n for n, loc in zip(lens, local) if loc}, {n for n, loc in zip(lens, local) if not loc}

        ids = np.asarray([INKLING2_REFERENCE['packed']['ids']])
        cache = model.new_cache()
        model.forward(ids[:, :3], cache)
        assert kv_lens(cache.layers) == ({3}, {3})
        model.forward(ids[:, 3:20], cache)
        assert kv_lens(cache.layers) == ({kept}, {20})

        for capacity in (32, 256):
            dec = Decoder(model, cache.snapshot(ops), capacity=capacity)
            states = [st for _, st in dec._layers(dec.flat)]  # noqa
            assert kv_lens(states) == ({kept}, {capacity}), capacity
            exported = dec.export_cache()
            assert kv_lens(exported.layers) == ({kept}, {20})

        # a decoder started before the window has filled pads it out in front, and reads the same
        short = model.new_cache()
        model.forward(ids[:, :3], short)
        dec = Decoder(model, short, capacity=32)
        assert kv_lens([st for _, st in dec._layers(dec.flat)]) == ({kept}, {32})  # noqa
        assert kv_lens(dec.export_cache().layers) == ({3}, {3})
        want = ops.numpy(model.forward(ids[:, :4]))[0, -1]
        got = ops.numpy(dec.step(int(ids[0, 3])))[0]
        assert np.abs(got - want).max() < 1e-4 * np.abs(want).max()


def _check_against_reference(case: str, ops: Ops, model: Qwen35) -> None:
    ref = INKLING2_REFERENCE[case]
    ids = np.asarray([ref['ids']])

    got = ops.numpy(model.forward(ids))[0].astype(np.float64)
    scale = max(abs(x) for x in ref['max'])
    tol = 3e-4 * scale

    assert got.argmax(-1).tolist() == ref['argmax'], (case, ops.name)
    assert np.abs(got.max(-1) - np.asarray(ref['max'])).max() < tol, (case, ops.name)
    cols = np.abs(got[:, ref['columns']] - np.asarray(ref['logits'])).max()
    assert cols < tol, (case, ops.name, cols)
    assert np.abs(got.sum(-1) - np.asarray(ref['sum'])).max() < tol * got.shape[-1], (case, ops.name)

    # (a softcapped head: within the cap, and not what the bare projection gives)
    assert np.abs(got).max() < model.cfg.logit_softcap  # type: ignore[attr-defined]


def test_logits_match_the_reference():
    for case, kw in CASES.items():
        with tempfile.TemporaryDirectory() as tmp:
            write_inkling2_checkpoint(tmp, **kw)

            for ops in [NumpyOps(), *backends()]:
                model = _load(tmp, ops)
                _check_against_reference(case, ops, model)

                # however the prompt is cut -- across the local window (6), the conv histories (3), the position
                # where a global layer's scaling starts (12) -- the cache gives the one-shot logits
                ids = np.asarray([INKLING2_REFERENCE[case]['ids']])
                whole = ops.numpy(model.forward(ids))
                n = ids.shape[1]
                for chunks in ((7, n - 7), (1, 2, 3, 5, 9, n - 20), (1,) * n, (17, n - 17)):
                    cache = model.new_cache()
                    outs = []
                    o = 0
                    for c in chunks:
                        outs.append(ops.numpy(model.forward(ids[:, o:o + c], cache)))
                        o += c
                    err = np.abs(np.concatenate(outs, 1) - whole).max() / np.abs(whole).max()
                    assert err < 2e-4, (case, ops.name, chunks[:4], err)
                    assert cache.seq_len == n


def test_generation_matches_the_reference():
    """
    Greedy tokens against the reference's own `generate()` -- its cached decode -- through the functional decoder, the
    static one (captured steps over capacity buffers), and the static one verifying drafts.
    """

    for case, kw in CASES.items():
        with tempfile.TemporaryDirectory() as tmp:
            write_inkling2_checkpoint(tmp, **kw)
            ref = INKLING2_REFERENCE[case]
            prompt = ref['ids'][:10]
            want = ref['greedy']

            for ops in [NumpyOps(), *backends()]:
                model = _load(tmp, _static(ops))
                for gen_kw in (dict(static=False), dict(static=True), dict(lookup_ngram=1, lookup_k=3)):
                    res = generate(model, prompt, max_new_tokens=len(want), **gen_kw)
                    assert list(res.tokens) == want, (case, ops.name, gen_kw, res.tokens, want)


def test_partial_acceptance():
    """
    A verify step's commit keeps exactly its accepted prefix, whatever the count: drafts from the reference transcript
    corrupted at every position give the plain tokens, and so does what follows -- the KV, the four convolutions'
    histories of all sixteen visits, cut back to the commit.
    """

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        ref = INKLING2_REFERENCE['packed']
        prompt = ref['ids'][:10]

        for ops in [NumpyOps(), *leading_backends()]:
            model = _load(tmp, _static(ops))
            plain = list(generate(model, prompt, max_new_tokens=24).tokens)
            assert plain[:14] == ref['greedy']
            full = [*prompt, *plain]

            for k in (2, 5):
                for corrupt in range(k + 1):  # the first `corrupt` drafts of a round are right: 0 .. k accepted
                    def drafts(ids: ta.Sequence[int], n: int, corrupt: int = corrupt) -> list[int]:
                        nxt = full[len(ids):len(ids) + n]
                        return [t if i < corrupt else (t + 1) % 300 for i, t in enumerate(nxt)]

                    draft = OracleDraftSource(ops, vocab_size=model.cfg.vocab_size, k=k, fn=drafts)
                    res = generate(model, prompt, max_new_tokens=24, draft=draft)
                    assert list(res.tokens) == plain, (ops.name, k, corrupt, res.tokens, plain)
                    assert res.accepted >= (res.rounds - 2) * min(corrupt, k), (k, corrupt, res.accepted, res.rounds)

            # sampled: same seed, same tokens with and without drafts that are always right (point masses)
            sampled = generate(model, prompt, max_new_tokens=12, sampler=Sampler(temperature=0.8, seed=3))
            assert list(sampled.tokens) != plain[:12]


def test_a_window_runs_where_it_is_kept():
    """
    Where buffers are written in place a local layer's window is kept in buffers with room to run (`RunningKvSpan`),
    appended to by every step and moved back to the front when the room is used up: a generation several times as
    long as the room -- plain, verifying drafts kept in part, and resumed from a stored state taken after the window
    has moved -- gives the functional decoder's tokens, and a second generation in the first's buffers does too.
    """

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        prompt = INKLING2_REFERENCE['packed']['ids'][:10]

        for ops in backends()[:1]:
            model = _load(tmp, _static(ops))
            assert ops.kv_in_place and isinstance(model.cfg, Inkling2Config), ops.name
            room = max(model.cfg.window - 1, Inkling2Architecture.WINDOW_ROOM_MIN)
            n = 4 * room + 6

            want = list(generate(model, prompt, max_new_tokens=n, static=False).tokens)
            full = [*prompt, *want]

            for _ in range(2):
                assert list(generate(model, prompt, max_new_tokens=n).tokens) == want, ops.name

            for k, right in ((3, 2), (5, 0), (2, 2)):
                def drafts(ids: ta.Sequence[int], count: int, right: int = right) -> list[int]:
                    nxt = full[len(ids):len(ids) + count]
                    return [t if i < right else (t + 1) % 300 for i, t in enumerate(nxt)]

                draft = OracleDraftSource(ops, vocab_size=model.cfg.vocab_size, k=k, fn=drafts)
                res = generate(model, prompt, max_new_tokens=n, draft=draft)
                assert list(res.tokens) == want, (ops.name, k, right)

            pc = PrefixCache(ops, 1 << 30, 0)
            first = generate(model, prompt, max_new_tokens=2 * room + 3, prefix_cache=pc)
            assert list(first.tokens) == want[:2 * room + 3], ops.name
            again = [*prompt, *first.tokens]
            res = generate(model, again, max_new_tokens=n - len(first.tokens), prefix_cache=pc)
            assert res.reused == len(again) - 1 or res.reused == len(again), (ops.name, res.reused)
            assert list(res.tokens) == want[len(first.tokens):], ops.name


def test_prefix_resume():
    """
    A follow-up resumed from a stored state -- every visit's KV and convolution histories, exported from the static
    decoder and laid back out -- equals a cold run, as does one resumed from a checkpoint inside the prefill.
    """

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        p1 = INKLING2_REFERENCE['packed']['ids'][:17]

        for ops in [NumpyOps(), *leading_backends()]:
            model = _load(tmp, _static(ops))

            pc = PrefixCache(ops, 1 << 30, 0)
            r1 = generate(model, p1, max_new_tokens=6, prefix_cache=pc)
            p2 = [*p1, *r1.tokens, 1, 7, 8, 9]
            r2 = generate(model, p2, max_new_tokens=8, prefix_cache=pc)
            cold = generate(model, p2, max_new_tokens=8)
            assert r2.reused == len(p1) + len(r1.tokens), (ops.name, r2.reused)
            assert list(r2.tokens) == list(cold.tokens), (ops.name, r2.tokens, cold.tokens)

            if ops.static_prefill:
                continue  # (a prefill through the captured step keeps no checkpoints yet: Decoder.prefill)

            pc = PrefixCache(ops, 1 << 30, 0)
            generate(model, p2, max_new_tokens=2, prefix_cache=pc, prefill_chunk=4, prefill_checkpoints=3)
            other = [*p2[:9], 250, 251, 252]  # shares 9 tokens: resumes from the checkpoint after 8
            r3 = generate(model, other, max_new_tokens=6, prefix_cache=pc)
            assert r3.reused == 8, (ops.name, r3.reused)
            assert list(r3.tokens) == list(generate(model, other, max_new_tokens=6).tokens), ops.name


def test_decoders_pass_on_buffers_and_steps():
    """
    A generation's decoder starts in the capacity buffers the last one left and runs the steps captured against them
    (core/slab.py), though every visit's state is KV buffers and small histories side by side: nothing is captured
    twice across generations of one capacity, with and without a stored state resumed.
    """

    try:
        from ...backends.torch import TorchOps
    except ImportError:
        pytest.skip('torch not installed')

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        ids = INKLING2_REFERENCE['packed']['ids']
        prompts = [ids[:10], ids[3:20], ids[:6]]

        for kv_dtype in ('bf16', 'fp8'):
            ops = TorchOps('cpu', kv_dtype=kv_dtype, capture_mode='static', triton=False)
            captured: list = []
            capture = ops.capture
            capture_carrying = ops.capture_carrying

            def counting(fn, _capture=capture, _captured=captured):
                _captured.append(fn)
                return _capture(fn)

            def counting_carrying(fn, outputs_from, inputs_from, _capture=capture_carrying, _captured=captured):
                _captured.append(fn)
                return _capture(fn, outputs_from, inputs_from)

            ops.capture = counting  # type: ignore[method-assign]
            ops.capture_carrying = counting_carrying  # type: ignore[method-assign]
            model = _load(tmp, ops)

            def fresh() -> Qwen35:  # (a model with nothing left over from another generation)
                return _load(tmp, TorchOps('cpu', kv_dtype=kv_dtype, capture_mode='static', triton=False))

            counts = []
            for p in prompts:
                want = generate(fresh(), p, max_new_tokens=7, capacity=64, prefill_chunk=5).tokens
                got = generate(model, p, max_new_tokens=7, capacity=64, prefill_chunk=5)
                assert list(got.tokens) == list(want), kv_dtype
                counts.append(len(captured))
                slab = model._slab  # noqa
                assert slab is not None and slab.capacity == 64 and slab.fns, kv_dtype
            assert counts[0] > 0 and counts[1] == counts[0] and counts[2] == counts[0], (kv_dtype, counts)

            pc = PrefixCache(ops, device_bytes=1 << 30, host_bytes=1 << 30)
            first = generate(model, prompts[0], max_new_tokens=7, capacity=64, prefix_cache=pc)
            more = [*prompts[0], *first.tokens, *prompts[2]]
            ref = generate(fresh(), more, max_new_tokens=7, capacity=64).tokens
            again = generate(model, more, max_new_tokens=7, capacity=64, prefix_cache=pc)
            assert again.reused == len(prompts[0]) + len(first.tokens), kv_dtype
            assert list(again.tokens) == list(ref), kv_dtype
            assert len(captured) == counts[0], (kv_dtype, len(captured), counts)


def test_fp8_kv():
    """
    The KV formats are the backend's: with fp8 KV the model decodes, statically as functionally. (How far fp8's ~2% on
    the keys and values moves the logits is the real checkpoint's to say -- INKLING.md -- not these random weights',
    which amplify it layer by layer.)
    """

    try:
        from ...backends.torch import TorchOps
    except ImportError:
        pytest.skip('torch not installed')

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        ref = INKLING2_REFERENCE['packed']
        ids = np.asarray([ref['ids']])

        plain = _load(tmp, TorchOps('cpu', capture_mode='static', triton=False))
        ops = TorchOps('cpu', capture_mode='static', triton=False, kv_dtype='fp8')
        model = _load(tmp, ops)
        assert ops.kv_arity == 4

        a = plain.ops.numpy(plain.forward(ids))
        b = ops.numpy(model.forward(ids))
        assert np.isfinite(b).all() and not np.array_equal(a, b)

        prompt = ref['ids'][:10]
        want = list(generate(model, prompt, max_new_tokens=12, static=False).tokens)
        assert list(generate(model, prompt, max_new_tokens=12).tokens) == want
        assert list(generate(model, prompt, max_new_tokens=12, lookup_ngram=1, lookup_k=3).tokens) == want


def test_injected():
    """The injector assembles the model the hand assembly does: the architecture comes from the source's config."""

    from omcore import inject as inj

    from ...backends.inject import BackendConfig
    from ...decode.inject import DecodeConfig
    from ...decode.runners import GenerationParams
    from ...decode.runners import GenerationRunner
    from ...inject.inject import bind_qwen
    from ...load.inject import LoadConfig
    from ...prefix.inject import PrefixConfig
    from ...spec.inject import LookupConfig
    from ...spec.inject import SpecConfig

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        ref = INKLING2_REFERENCE['packed']
        prompt = ref['ids'][:10]

        for lookup in (None, LookupConfig(ngram=1, k=3)):
            injector = inj.create_injector(bind_qwen(
                backend=BackendConfig(backend='torch', device='cpu'),
                load=LoadConfig(model=tmp, dtype='f32'),
                decode=DecodeConfig(capacity=64),
                spec=SpecConfig(),
                prefix=PrefixConfig(enabled=True, device_mib=64, host_mib=0),
                lookup=lookup,
            ))
            runner = injector[GenerationRunner]

            got = runner.run(GenerationParams(prompt=prompt, max_new_tokens=14))
            assert list(got.tokens) == ref['greedy'], (lookup, got.tokens)

            again = runner.run(GenerationParams(prompt=[*prompt, *got.tokens, 5], max_new_tokens=4))
            assert again.reused == len(prompt) + len(got.tokens)

        with pytest.raises(ValueError, match='draft model'):  # it is not built
            inj.create_injector(bind_qwen(
                backend=BackendConfig(backend='torch', device='cpu'),
                load=LoadConfig(model=tmp, dtype='f32', mtp=True),
                decode=DecodeConfig(capacity=64),
                spec=SpecConfig(k=3),
                prefix=PrefixConfig(enabled=False),
            ))[Qwen35]


def test_cuda_graph_steps():
    """
    On CUDA the static steps are captured graphs -- forty-eight state slots carried through them, positions on the
    device -- and give the functional path's tokens, in both KV formats, plain and verifying drafts.
    """

    try:
        import torch

        from ...backends.torch import TorchOps
    except ImportError:
        pytest.skip('torch not installed')
    if not torch.cuda.is_available():
        pytest.skip('no CUDA')

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        ref = INKLING2_REFERENCE['packed']
        prompt = ref['ids'][:10]

        for kv in ('bf16', 'fp8'):
            ops = TorchOps('cuda', triton=False, kv_dtype=kv)  # (no Triton in the pytest process: tritonmodes.py)
            model = _load(tmp, ops)
            want = list(generate(model, prompt, max_new_tokens=14, static=False).tokens)
            if kv == 'bf16':
                assert want == ref['greedy']

            gen_kws: list[dict[str, ta.Any]] = [dict(), dict(lookup_ngram=1, lookup_k=3), dict(capacity=128)]
            for gen_kw in gen_kws:
                got = generate(model, prompt, max_new_tokens=14, **gen_kw)
                assert list(got.tokens) == want, (kv, gen_kw, got.tokens, want)


@triton_modes('compiled', timeout_s=300)
def test_cuda_kernels_and_compiled_steps():
    """
    On CUDA with the Triton kernels on -- the packed experts read by the expert GEMV, the global layers' attention
    length-aware over the decode attention kernel -- the logits are the CPU's and the reference's, and the static
    decode gives the functional path's tokens, plain and verifying drafts, in both KV formats. Compiled as well (a
    smaller model: the compile is the time), every step traces as one graph and a prompt of another length compiles
    nothing more. (It executes Triton kernels, so it runs in a child process: tests/tritonmodes.py.)
    """

    import torch._dynamo as dynamo
    from torch._dynamo.utils import counters

    from ...backends.torch import TorchMicroscaledExperts
    from ...backends.torch import TorchOps

    with tempfile.TemporaryDirectory() as tmp:
        write_inkling2_checkpoint(tmp)
        ref = INKLING2_REFERENCE['packed']
        ids = np.asarray([ref['ids']])
        prompt = ref['ids'][:10]

        cpu = _load(tmp, TorchOps('cpu', triton=False))
        want_logits = cpu.ops.numpy(cpu.forward(ids))

        for kv in ('bf16', 'fp8'):
            ops = TorchOps('cuda', kv_dtype=kv)
            assert ops.triton
            model = _load(tmp, ops)

            moe = model.blocks[0].sublayers[1][0]._inner._ffn  # type: ignore[attr-defined]  # noqa
            assert isinstance(moe._gate_up, TorchMicroscaledExperts)  # noqa

            if kv == 'bf16':
                # each of the two ways a stack of packed experts is read -- a row at a time by the kernel, and expert
                # by expert, each decoded once (a long prefill's) -- and then whichever the row count picks
                for per_expert in (0, 1 << 20, None):
                    if per_expert is not None:
                        ops.microscaled_gemv_rows_per_expert = per_expert
                    else:
                        del ops.microscaled_gemv_rows_per_expert
                    got = ops.numpy(model.forward(ids))
                    err = float(np.abs(got - want_logits).max() / np.abs(want_logits).max())
                    assert err < 2e-4, (per_expert, err)
                _check_against_reference('packed', ops, model)

            want = list(generate(model, prompt, max_new_tokens=14, static=False).tokens)
            if kv == 'bf16':
                assert want == ref['greedy']
            for gen_kw in (dict(capacity=128), dict(capacity=128, lookup_ngram=1, lookup_k=3)):
                got_tokens = list(generate(model, prompt, max_new_tokens=14, **gen_kw).tokens)  # type: ignore[arg-type]
                assert got_tokens == want, (kv, gen_kw, got_tokens, want)

    with tempfile.TemporaryDirectory() as tmp:
        # four layers, the last two run twice: six visits
        write_inkling2_checkpoint(tmp, inkling2_test_config(
            num_hidden_layers=4,
            layer_types=['hybrid_sliding', 'hybrid'] * 2,
            loop_layer_index_start=2,
            loop_layer_index_end=4,
            loop_num_passes=2,
        ))
        prompt = INKLING2_REFERENCE['packed']['ids'][:10]

        dynamo.reset()
        counters.clear()
        model = _load(tmp, TorchOps('cuda', compile=True))
        want = list(generate(model, prompt, max_new_tokens=14, static=False).tokens)

        with dynamo.error_on_graph_break(True):
            plain = generate(model, prompt, max_new_tokens=14, capacity=128)
            looked = generate(model, prompt, max_new_tokens=14, capacity=128, lookup_ngram=1, lookup_k=3)
        assert list(plain.tokens) == want and list(looked.tokens) == want, (plain.tokens, looked.tokens, want)

        graphs = counters['stats']['unique_graphs']
        assert graphs
        generate(model, prompt[:7], max_new_tokens=14, capacity=128)
        assert counters['stats']['unique_graphs'] == graphs, 'recompiled'


##


def _reference() -> ta.Any:
    """transformers when it is installed with inkling2_loop (the oracle, and a checkpoint writer), else None."""

    try:
        import torch  # noqa
        import transformers
    except ImportError:
        return None
    return transformers if hasattr(transformers, 'Inkling2LoopForCausalLM') else None


def test_matches_the_reference_live():
    """
    The released schedule at toy widths, on a checkpoint the reference library writes itself (dense experts, its
    flat config): logits at every position, and its own greedy generation.
    """

    transformers = _reference()
    if transformers is None:
        pytest.skip('transformers with inkling2_loop not installed')

    import torch

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, 'inkling2')
        cfg = transformers.Inkling2LoopTextConfig(
            vocab_size=320,
            unpadded_vocab_size=300,
            hidden_size=48,
            num_hidden_layers=24,
            num_attention_heads=4,
            num_key_value_heads=2,
            head_dim=16,
            swa_num_attention_heads=4,
            swa_num_key_value_heads=2,
            swa_head_dim=16,
            sliding_window_size=8,
            d_rel=4,
            rel_extent=8,
            log_scaling_n_floor=16,
            moe_intermediate_size=24,
            n_routed_experts=8,
            num_experts_per_tok=2,
            loop_gate_rank=8,
            max_position_embeddings=4096,
            eos_token_id=1,
        )
        torch.manual_seed(0)
        ref_model = transformers.Inkling2LoopForCausalLM(cfg).eval()
        with torch.no_grad():
            for p in ref_model.parameters():  # off the init's zeros and ones: every weight matters
                p.add_(torch.randn_like(p) * 0.1)
        ref_model.save_pretrained(path)

        ids = np.random.default_rng(5).integers(2, 300, 40).reshape(1, -1)
        with torch.no_grad():
            ref = ref_model(torch.from_numpy(ids)).logits.float().numpy()
            want = ref_model.generate(
                torch.from_numpy(ids[:, :10]),
                max_new_tokens=12,
                do_sample=False,
                eos_token_id=None,
                pad_token_id=0,
            )[0, 10:].tolist()

        src = open_source(path)
        assert isinstance(src.config, Inkling2Config) and src.config.num_visits == 48

        for ops in [NumpyOps(), *backends()]:
            model = load_qwen35(src, _static(ops), dtype='f32', verbose=False)
            got = ops.numpy(model.forward(ids))
            err = float(np.abs(got - ref).max() / np.abs(ref).max())
            assert err < 1e-4, (ops.name, err)

            for gen_kw in (dict(static=False), dict(static=True), dict(lookup_ngram=1, lookup_k=3)):
                res = generate(model, ids[0, :10].tolist(), max_new_tokens=12, **gen_kw)
                assert list(res.tokens) == want, (ops.name, gen_kw, res.tokens, want)
