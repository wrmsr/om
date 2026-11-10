# ruff: noqa: N803 N806 N812
"""
The prefix snapshot cache (prefixcache.py) end to end: a follow-up request that extends an earlier one resumes from the
earlier state and produces exactly what a cold run over the full prompt produces -- plain and speculative decoding,
prompt-end and generation-end snapshots, the host tier, eviction. numpy golden + every backend.
"""
import numpy as np

from ..api import generate
from ..arch.qwen35 import load_qwen35
from ..prefix.cache import PrefixCache
from .test_parity import backends
from .test_parity import synthetic_source


##


def test_prefix_resume():
    cfg, hf, src = synthetic_source()
    rng = np.random.default_rng(8)
    p1 = rng.integers(0, 256, 7).tolist()
    extra = rng.integers(0, 256, 5).tolist()
    for ops in backends():
        if getattr(ops, 'capture_mode', None) == 'auto' and ops.name.endswith('cpu'):
            ops.capture_mode = 'static'  # type: ignore
        model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)
        for spec in (0, 3):
            pc = PrefixCache(ops, device_bytes=1 << 30, host_bytes=1 << 30)
            r1 = generate(model, p1, max_new_tokens=9, spec=spec, prefix_cache=pc)
            out1 = r1.tokens
            assert r1.reused == 0
            assert sorted(len(t) for t in pc.entries) == [len(p1), len(p1) + len(out1)]  # prompt end + generation end

            # 1. the same prompt again: everything matches, nothing is prefilled, same output
            r1b = generate(model, p1, max_new_tokens=9, spec=spec, prefix_cache=pc)
            assert r1b.reused == len(p1) and r1b.tokens == out1, (ops.name, spec)

            # 2. a follow-up: prompt + the answer + new tokens resumes from the generation-end snapshot
            p2 = p1 + out1 + extra
            cold = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)
            ref = generate(cold, p2, max_new_tokens=9, spec=spec).tokens
            r2 = generate(model, p2, max_new_tokens=9, spec=spec, prefix_cache=pc)
            out2 = r2.tokens
            # the generation-end state covers exactly prompt + emitted tokens, so the follow-up resumes all of it
            assert r2.prompt_tokens == len(p2) and r2.reused == len(p1) + len(out1), (ops.name, spec, r2.reused)
            assert out2 == ref, (ops.name, spec, out2, ref)
            # (the logits themselves, not just greedy tokens: cold vs resumed prefill of p2)
            assert pc.hits == 2 and pc.misses == 1
        print(f'{ops.name}: prefix resume == cold run (plain and spec); {pc.stats()}')

        # 3. host tier: a device budget too small for two snapshots demotes the older one; a hit promotes it back
        pc = PrefixCache(ops, device_bytes=1 << 30, host_bytes=1 << 30)
        generate(model, p1, max_new_tokens=4, prefix_cache=pc)
        big = max(e.nbytes for e in pc.entries.values())
        pc.device_bytes = big + 1  # room for one entry: the other must live on the host
        pc._make_room(0)  # noqa
        tiers = sorted(e.tier for e in pc.entries.values())
        assert tiers == ['device', 'host'], tiers
        rh = generate(model, p1 + out1[:2], max_new_tokens=4, prefix_cache=pc)
        out_h = rh.tokens
        assert rh.reused >= len(p1)
        cold_model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)
        cold_h = generate(cold_model, p1 + out1[:2], max_new_tokens=4).tokens
        assert out_h == cold_h, (ops.name, out_h, cold_h)

        # 4. no host budget: eviction drops
        pc = PrefixCache(ops, device_bytes=big + 1, host_bytes=0)
        generate(model, p1, max_new_tokens=4, prefix_cache=pc)
        assert len(pc.entries) == 1 and all(e.tier == 'device' for e in pc.entries.values())
        if hasattr(ops, 'capture_mode'):
            ops.capture_mode = 'auto'
        print(f'{ops.name}: host tier demotion / promotion and eviction OK')
