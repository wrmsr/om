import numpy as np

from ...api import generate
from ...arch.qwen35 import load_qwen35
from ...backends.torch import TorchOps
from ...core.cache import Cache
from ...prefix.cache import PrefixCache
from ...tests.test_parity import synthetic_source
from ..decoder import Decoder


##


def test_decoder_consumes_its_cache():
    """
    A decoder built with `consume` takes the cache's state layer by layer (a long context's KV is then never held
    twice) and decodes exactly as one built from a cache it leaves alone.
    """

    cfg, _, src = synthetic_source()
    ids = np.random.default_rng(3).integers(0, cfg.vocab_size, (1, 12))
    for kv_dtype in ('bf16', 'fp8'):
        ops = TorchOps('cpu', kv_dtype=kv_dtype, capture_mode='static')
        model = load_qwen35(src, ops, dtype='f32', verbose=False)

        kept = Cache(cfg)
        model.forward(ids[:, :8], kept)
        given = Cache(cfg)
        model.forward(ids[:, :8], given)

        a = Decoder(model, kept, capacity=32)
        b = Decoder(model, given, capacity=32, consume=True)
        assert all(st is not None for st in kept.layers)
        assert all(st is None for st in given.layers)

        for t in ids[0, 8:]:
            la = ops.numpy(a.step(int(t)))
            lb = ops.numpy(b.step(int(t)))
            assert np.array_equal(la, lb), kv_dtype


def test_prefill_into_reserved_buffers():
    """
    A prefill told the capacity it is filling (`reserve`) writes the KV into buffers of that size from its second chunk
    on: the same logits, hidden states and states as the prefill that grows them, bit for bit; a decoder of that
    capacity adopts the buffers as they are; and a reserve the prompt outgrows goes back to growing.
    """

    cfg, _, src = synthetic_source()
    ids = np.random.default_rng(5).integers(0, cfg.vocab_size, 20).tolist()
    n = 14
    for kv_dtype in ('bf16', 'fp8'):
        ops = TorchOps('cpu', kv_dtype=kv_dtype, capture_mode='static')
        model = load_qwen35(src, ops, dtype='f32', verbose=False)
        layouts = model.state_layouts()

        grown = Cache(cfg)
        logits, hidden = model.prefill(ids[:n], grown, chunk=5)
        ref = Decoder(model, grown, capacity=32)
        ref_steps = [ops.numpy(ref.step(t)) for t in ids[n:]]

        for reserve in (32, 8):
            cache = Cache(cfg)
            lr, hr = model.prefill(ids[:n], cache, chunk=5, reserve=reserve)
            assert np.array_equal(ops.numpy(lr), ops.numpy(logits)), (kv_dtype, reserve)
            assert np.array_equal(ops.numpy(hr), ops.numpy(hidden)), (kv_dtype, reserve)
            assert cache.seq_len == n

            kv: list = []
            for a, b, layout in zip(grown.layers, cache.layers, layouts):
                assert a is not None and b is not None
                cap = layout.capacity(ops, b)
                if cap is not None:
                    assert cap == (reserve if reserve > n else n), (kv_dtype, reserve, cap)
                    kv.extend(b)
                for x, y in zip(layout.export(ops, a, n), layout.export(ops, b, n)):
                    assert np.array_equal(ops.numpy(ops.f32(x)), ops.numpy(ops.f32(y))), (kv_dtype, reserve)
            assert kv

            dec = Decoder(model, cache, capacity=32, consume=True)
            if reserve == 32:  # the buffers the prefill filled are the decoder's: nothing was copied
                assert all(any(a is b for b in dec.flat) for a in kv), kv_dtype
            for t, want in zip(ids[n:], ref_steps):
                assert np.array_equal(ops.numpy(dec.step(t)), want), (kv_dtype, reserve)


def test_generation_through_a_chunked_prefill():
    """
    Generation over a prompt of several prefill chunks -- the static decoder's KV prefilled into its buffers, cold and
    resumed from a prefix snapshot, plain and speculative -- produces the functional decoder's tokens.
    """

    cfg, _, src = synthetic_source()
    rng = np.random.default_rng(6)
    p1 = rng.integers(0, cfg.vocab_size, 7).tolist()
    p2 = p1 + rng.integers(0, cfg.vocab_size, 16).tolist()
    for kv_dtype in ('bf16', 'fp8'):
        ops = TorchOps('cpu', kv_dtype=kv_dtype, capture_mode='static')
        model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)
        ref = generate(model, p2, max_new_tokens=9, static=False, prefill_chunk=5).tokens
        for spec in (0, 3):
            cold = generate(model, p2, max_new_tokens=9, spec=spec, prefill_chunk=5, capacity=64)
            assert cold.tokens == ref, (kv_dtype, spec)

            pc = PrefixCache(ops, device_bytes=1 << 30, host_bytes=1 << 30)
            generate(model, p1, max_new_tokens=1, spec=spec, prefill_chunk=5, capacity=64, prefix_cache=pc)
            warm = generate(model, p2, max_new_tokens=9, spec=spec, prefill_chunk=5, capacity=64, prefix_cache=pc)
            assert warm.reused == len(p1), (kv_dtype, spec, warm.reused)
            assert warm.tokens == ref, (kv_dtype, spec)


def test_prefill_keeps_only_the_hidden_states_asked_for():
    """Without `all_hidden` a prefill returns the last position's hidden state alone: the same one."""

    cfg, _, src = synthetic_source()
    ids = np.random.default_rng(9).integers(0, cfg.vocab_size, 14).tolist()
    ops = TorchOps('cpu', capture_mode='static')
    model = load_qwen35(src, ops, dtype='f32', verbose=False)

    logits, hidden = model.prefill(ids, Cache(cfg), chunk=5)
    assert tuple(hidden.shape[:2]) == (1, 14)

    # (every position's, written into one buffer as the chunks come: the chunks' own, joined)
    by_hand = Cache(cfg)
    parts = [
        model.forward(np.asarray([ids[s:s + 5]], dtype=np.int32), by_hand, last_only=True, return_hidden=True)[1]
        for s in range(0, 14, 5)
    ]
    assert np.array_equal(ops.numpy(hidden), ops.numpy(ops.concat(parts, 1)))
    for chunk in (5, 64):
        ll, last = model.prefill(ids, Cache(cfg), chunk=chunk, all_hidden=False)
        assert tuple(last.shape[:2]) == (1, 1)
        if chunk == 5:
            assert np.array_equal(ops.numpy(last), ops.numpy(hidden[:, -1:]))
            assert np.array_equal(ops.numpy(ll), ops.numpy(logits))


def test_decoders_pass_on_buffers_and_steps():
    """
    A generation's decoder starts in the capacity buffers the last one left and runs the steps captured against them
    (core/slab.py): nothing is captured twice -- the target's steps or the draft head's -- across generations of one
    capacity, what is generated is what a model with nothing left over generates, and another capacity starts afresh.
    """

    cfg, _, src = synthetic_source()
    rng = np.random.default_rng(13)
    prompts = [rng.integers(0, cfg.vocab_size, n).tolist() for n in (9, 14, 6)]
    for kv_dtype in ('bf16', 'fp8'):
        for spec in (0, 3):
            ops = TorchOps('cpu', kv_dtype=kv_dtype, capture_mode='static')
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
            model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)

            want = []
            for p in prompts:
                fresh = load_qwen35(src, TorchOps('cpu', kv_dtype=kv_dtype, capture_mode='static'), dtype='f32',
                                    verbose=False, mtp=True)
                want.append(generate(fresh, p, max_new_tokens=7, spec=spec, capacity=64, prefill_chunk=5).tokens)

            counts = []
            for p, w in zip(prompts, want):
                got = generate(model, p, max_new_tokens=7, spec=spec, capacity=64, prefill_chunk=5)
                assert got.tokens == w, (kv_dtype, spec)
                counts.append(len(captured))
                slab = model._slab  # noqa
                assert slab is not None and slab.capacity == 64 and slab.fns, (kv_dtype, spec)
            assert counts[0] > 0 and counts[1] == counts[0] and counts[2] == counts[0], (kv_dtype, spec, counts)

            # with a prefix cache: a follow-up resumed from a stored state lands in the same buffers
            pc = PrefixCache(ops, device_bytes=1 << 30, host_bytes=1 << 30)
            first = generate(model, prompts[0], max_new_tokens=7, spec=spec, capacity=64, prefix_cache=pc)
            more = prompts[0] + first.tokens + prompts[2]
            ref = generate(fresh, more, max_new_tokens=7, spec=spec, capacity=64).tokens
            again = generate(model, more, max_new_tokens=7, spec=spec, capacity=64, prefix_cache=pc)
            assert again.reused == len(prompts[0]) + len(first.tokens) and again.tokens == ref, (kv_dtype, spec)
            assert len(captured) == counts[0], (kv_dtype, spec, len(captured), counts)

            # another capacity: new buffers, new captures, and the old slab is not kept beside them
            generate(model, prompts[0], max_new_tokens=7, spec=spec, capacity=128)
            assert len(captured) > counts[0], (kv_dtype, spec)
            assert model._slab is not None and model._slab.capacity == 128, (kv_dtype, spec)  # noqa


def test_short_prefills_through_the_captured_step():
    """
    With `step_prefill_max` a prefill of at most that many tokens -- a short prompt, or what is left of one resumed
    from a stored state -- runs through the decoder's captured step: in the buffers and with the steps the last
    decoder left, generating what the eager prefill generates; a longer one takes the eager forward as before.
    """

    cfg, _, src = synthetic_source()
    rng = np.random.default_rng(17)
    short = rng.integers(0, cfg.vocab_size, 9).tolist()
    more = rng.integers(0, cfg.vocab_size, 21).tolist()
    long = rng.integers(0, cfg.vocab_size, 40).tolist()
    for kv_dtype in ('bf16', 'fp8'):
        for spec in (0, 3):
            ops = TorchOps('cpu', kv_dtype=kv_dtype, capture_mode='static')
            model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)
            eager_forwards: list = []
            forward = model.forward

            def counting(*a, _forward=forward, _seen=eager_forwards, **kw):
                _seen.append(a[0].shape[1])
                return _forward(*a, **kw)

            model.forward = counting  # type: ignore[method-assign]
            kw: dict = dict(max_new_tokens=6, spec=spec, capacity=128)

            fresh = load_qwen35(src, TorchOps('cpu', kv_dtype=kv_dtype, capture_mode='static'), dtype='f32',
                                verbose=False, mtp=True)
            for prompt in (short, short + more, long):
                want = generate(fresh, prompt, **kw).tokens
                eager_forwards.clear()
                got = generate(model, prompt, step_prefill_max=32, **kw)
                assert got.tokens == want, (kv_dtype, spec, len(prompt))
                assert bool(eager_forwards) == (len(prompt) > 32), (kv_dtype, spec, len(prompt), eager_forwards)

            # a follow-up to a stored conversation: only its new tokens are prefilled, through the step
            pc = PrefixCache(ops, device_bytes=1 << 30, host_bytes=1 << 30)
            first = generate(model, long, prefix_cache=pc, step_prefill_max=32, **kw)
            follow = long + first.tokens + short
            want = generate(fresh, follow, **kw).tokens
            eager_forwards.clear()
            again = generate(model, follow, prefix_cache=pc, step_prefill_max=32, **kw)
            assert again.reused == len(long) + len(first.tokens) and again.tokens == want, (kv_dtype, spec)
            assert not eager_forwards, (kv_dtype, spec, eager_forwards)
            assert model._slab is not None and model._slab.fns  # noqa


def test_cuda_graph_steps_carry_the_state():
    """
    On CUDA the steps are graphs. A plain step's state goes round inside its graph (`Ops.capture_carrying`: the graph
    ends by writing it back into its own inputs), and a commit picks its state out of a verify step's outputs only when
    the next step asks: plain steps, verify steps kept in part, and plain steps again must leave the logits the same
    steps on the CPU leave, and export the same state.
    """

    try:
        import torch
    except ImportError:
        return
    if not torch.cuda.is_available():
        print('no CUDA device; skipping')
        return

    from ...tests.test_parity import rel_err

    cfg, hf, src = synthetic_source()
    ids = np.random.default_rng(12).integers(0, cfg.vocab_size, (1, 30))

    outs = {}
    for device in ('cpu', 'cuda'):
        ops = TorchOps(device)
        model = load_qwen35(src, ops, dtype='f32', verbose=False)
        cache = Cache(cfg)
        model.forward(ids[:, :5], cache)
        dec = Decoder(model, cache, capacity=64)

        logits = [ops.numpy(dec.step(int(t))) for t in ids[0, 5:11]]
        for at in (11, 17):
            verified = dec.verify(ops.array(ids[:, at:at + 4].astype(np.int32)))
            logits.append(ops.numpy(verified.logits)[0, :2])
            dec.commit(verified, 2)  # (and the next step is what picks the state out)
            logits.extend(ops.numpy(dec.step(int(t))) for t in ids[0, at + 2:at + 6])
        assert dec.seq_len == 23

        exported = [a for st in dec.export_cache().layers if st is not None for a in st]
        logits.append(ops.numpy(dec.step(int(ids[0, 23]))))  # (the export is a copy: this step leaves it alone)
        outs[device] = (np.concatenate(logits, 0), [ops.numpy(a) for a in exported])

    e = rel_err(outs['cuda'][0], outs['cpu'][0])
    assert e < 1e-4, e
    for a, b in zip(outs['cuda'][1], outs['cpu'][1]):
        assert a.shape == b.shape and rel_err(a, b) < 1e-3, rel_err(a, b)
    print(f'CUDA graph steps vs CPU: logits rel err {e:.1e}')


def test_a_static_prefill_keeps_every_chunks_hidden_states():
    """
    A prompt through the captured step (`Decoder.prefill`) is several runs of it, and what a run hands back is good
    until the next: the hidden states of every chunk but the last have to be kept as they come. On CUDA, where a
    step's outputs are its graph's own buffers, a 40-token prompt's first 32 rows were not the prompt's.
    """

    try:
        import torch
    except ImportError:
        return

    from ...tests.test_parity import rel_err

    cfg, hf, src = synthetic_source()
    prompt = np.random.default_rng(17).integers(0, cfg.vocab_size, 40).tolist()

    for device in ('cpu', 'cuda'):
        if device == 'cuda' and not torch.cuda.is_available():
            print('no CUDA device; skipping')
            continue

        ops = TorchOps(device, capture_mode='static') if device == 'cpu' else TorchOps(device)
        model = load_qwen35(src, ops, dtype='f32', verbose=False)
        want_logits, want = model.forward(np.asarray([prompt]), return_hidden=True)

        logits, hidden = Decoder(model, model.new_cache(), capacity=64).prefill(prompt)
        assert hidden.shape == want.shape
        for a in range(0, len(prompt), Decoder.PREFILL_T):
            b = a + Decoder.PREFILL_T
            assert rel_err(ops.numpy(hidden[:, a:b]), ops.numpy(want[:, a:b])) < 1e-4, (device, a)
        assert rel_err(ops.numpy(logits), ops.numpy(want_logits[:, -1:])) < 1e-4, device
