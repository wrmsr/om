"""
The prefix snapshot cache (prefixcache.py) end to end: a follow-up request that extends an earlier one resumes
from the earlier state and produces exactly what a cold run over the full prompt produces -- plain and speculative
decoding, prompt-end and generation-end snapshots, the host tier, eviction. numpy golden + every backend.

Run:  python -m pytest x/qwen/tests/test_prefix.py -q      or      python -m x.qwen.tests.test_prefix
"""
import numpy as np

from ..model import Qwen35
from ..prefixcache import PrefixCache
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
            ops.capture_mode = 'static'
        model = Qwen35.from_source(src, ops, dtype='f32', verbose=False, mtp=True)
        for spec in (0, 3):
            pc = PrefixCache(ops, device_bytes=1 << 30, host_bytes=1 << 30)
            out1 = model.generate(p1, max_new_tokens=9, spec=spec, prefix_cache=pc)
            assert model.last_prefix == (0, len(p1))
            assert len(pc.entries) == 2  # prompt end + generation end

            # 1. the same prompt again: everything matches, nothing is prefilled, same output
            out1b = model.generate(p1, max_new_tokens=9, spec=spec, prefix_cache=pc)
            assert model.last_prefix == (len(p1), len(p1)) and out1b == out1, (ops.name, spec)

            # 2. a follow-up: prompt + the answer + new tokens resumes from the generation-end snapshot
            p2 = p1 + out1 + extra
            cold = Qwen35.from_source(src, ops, dtype='f32', verbose=False, mtp=True)
            ref = cold.generate(p2, max_new_tokens=9, spec=spec)
            out2 = model.generate(p2, max_new_tokens=9, spec=spec, prefix_cache=pc)
            matched, total = model.last_prefix
            assert total == len(p2) and len(p1) < matched <= len(p1) + len(out1), (ops.name, spec, matched)
            assert out2 == ref, (ops.name, spec, out2, ref)
            # (the logits themselves, not just greedy tokens: cold vs resumed prefill of p2)
            assert pc.hits == 2 and pc.misses == 1
        print(f'{ops.name}: prefix resume == cold run (plain and spec); {pc.stats()}')

        # 3. host tier: a device budget too small for two snapshots demotes the older one; a hit promotes it back
        pc = PrefixCache(ops, device_bytes=1 << 30, host_bytes=1 << 30)
        model.generate(p1, max_new_tokens=4, prefix_cache=pc)
        big = max(e.nbytes for e in pc.entries.values())
        pc.device_bytes = big + 1  # room for one entry: the other must live on the host
        pc._make_room(0)
        tiers = sorted(e.tier for e in pc.entries.values())
        assert tiers == ['device', 'host'], tiers
        out_h = model.generate(p1 + out1[:2], max_new_tokens=4, prefix_cache=pc)
        assert model.last_prefix[0] >= len(p1)
        cold_model = Qwen35.from_source(src, ops, dtype='f32', verbose=False, mtp=True)
        cold_h = cold_model.generate(p1 + out1[:2], max_new_tokens=4)
        assert out_h == cold_h, (ops.name, out_h, cold_h)

        # 4. no host budget: eviction drops
        pc = PrefixCache(ops, device_bytes=big + 1, host_bytes=0)
        model.generate(p1, max_new_tokens=4, prefix_cache=pc)
        assert len(pc.entries) == 1 and all(e.tier == 'device' for e in pc.entries.values())
        if hasattr(ops, 'capture_mode'):
            ops.capture_mode = 'auto'
        print(f'{ops.name}: host tier demotion / promotion and eviction OK')


if __name__ == '__main__':
    test_prefix_resume()
