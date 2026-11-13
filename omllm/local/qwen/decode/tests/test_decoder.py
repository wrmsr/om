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
    for chunk in (5, 64):
        ll, last = model.prefill(ids, Cache(cfg), chunk=chunk, all_hidden=False)
        assert tuple(last.shape[:2]) == (1, 1)
        if chunk == 5:
            assert np.array_equal(ops.numpy(last), ops.numpy(hidden[:, -1:]))
            assert np.array_equal(ops.numpy(ll), ops.numpy(logits))
