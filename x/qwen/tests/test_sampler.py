"""
The device-side sampler (model.Sampler) against exact probabilities, on every backend.

Run:  python -m pytest x/qwen/tests/test_sampler.py -q      or      python -m x.qwen.tests.test_sampler
"""
import numpy as np

from ..model import Sampler
from .test_parity import backends


##


def expected_dist(l: np.ndarray, temperature: float, top_k: int, top_p: float, min_p: float) -> np.ndarray:
    """What Sampler.sample is supposed to draw from, computed plainly in float64."""

    V = l.shape[0]
    k = top_k if 0 < top_k < V else V
    idx = np.argsort(-l, kind='stable')[:k]
    z = l[idx].astype(np.float64) / temperature
    p = np.exp(z - z.max())
    p /= p.sum()
    keep = np.ones(k, dtype=bool)
    if top_p < 1.0:
        keep &= (np.cumsum(p) - p) < top_p
    if min_p > 0:
        keep &= p >= min_p * p.max()
    q = np.where(keep, p, 0.0)
    q /= q.sum()
    out = np.zeros(V)
    out[idx] = q
    return out


def test_sampler_distribution():
    rng = np.random.default_rng(0)
    V = 300
    l = (rng.standard_normal(V) * 2.5).astype(np.float32)
    n = 4000
    for ops in backends():
        f32 = ops.dtype('f32')
        rows = ops.array(np.repeat(l[None], n, 0), f32)  # n independent draws from the same row
        for kw in (
                dict(temperature=1.0, top_k=10, top_p=0.9),
                dict(temperature=0.7, top_k=20, top_p=0.8),
                dict(temperature=1.0, top_k=8, min_p=0.1),
                dict(temperature=1.0, top_p=0.5),  # top_k=0: sorts the vocabulary
        ):
            s = Sampler(seed=1, **kw)
            s.bind(ops, V)
            got = ops.numpy(s.sample(rows)).astype(np.int64)
            exp = expected_dist(l, kw['temperature'], kw.get('top_k', 0), kw.get('top_p', 1.0), kw.get('min_p', 0.0))
            assert np.all(exp[got] > 0), (ops.name, kw, 'drew outside the support')
            emp = np.bincount(got, minlength=V) / n
            err = np.abs(emp - exp).max()
            assert err < 0.04, (ops.name, kw, err)
        # greedy is an argmax
        s = Sampler()
        s.bind(ops, V)
        assert ops.numpy(s.sample(rows[:3])).tolist() == [int(np.argmax(l))] * 3
        # presence penalty: after observing the argmax token, a heavy penalty removes it from the draws
        s = Sampler(temperature=1.0, top_k=5, presence_penalty=100.0, seed=2)
        s.bind(ops, V)
        top = int(np.argmax(l))
        s.observe(ops.array(np.asarray([top], dtype=np.int32)))
        got = ops.numpy(s.sample(rows[:500])).tolist()
        assert top not in got, ops.name
        print(f'{ops.name}: sampler distributions OK')


def test_probs_and_rejection_sampling():
    """`Sampler.probs` equals the exact warped distribution, and the speculative accept/correct step reproduces
    the target distribution whatever the draft distribution is (the speculative-sampling theorem), with an
    acceptance rate of sum(min(p, q))."""

    from ..model import speculative_accept

    rng = np.random.default_rng(1)
    V = 200
    l = (rng.standard_normal(V) * 2.5).astype(np.float32)
    for ops in backends():
        f32 = ops.dtype('f32')
        for kw in (
                dict(temperature=1.0, top_k=10, top_p=0.9),
                dict(temperature=0.7, top_k=20, top_p=0.8),
                dict(temperature=1.0, top_k=8, min_p=0.1),
                dict(temperature=1.0, top_p=0.5),
                dict(),  # greedy: one-hot
        ):
            s = Sampler(seed=1, **kw)
            s.bind(ops, V)
            got = ops.numpy(s.probs(ops.array(np.stack([l, l]), f32)))
            if kw:
                exp = expected_dist(l, kw['temperature'], kw.get('top_k', 0), kw.get('top_p', 1.0), kw.get('min_p', 0.0))
            else:
                exp = np.zeros(V)
                exp[int(np.argmax(l))] = 1.0
            assert np.abs(got[0] - exp).max() < 1e-5 and np.abs(got[1] - exp).max() < 1e-5, (ops.name, kw)

        # rejection sampling: N independent trials batched along the draft axis
        n = 4000
        s = Sampler(temperature=1.0, top_k=12, top_p=0.9, seed=2)
        s.bind(ops, V)
        lp = (rng.standard_normal(V) * 2.5).astype(np.float32)
        lq = (lp + rng.standard_normal(V) * 1.5).astype(np.float32)  # a draft head that is related but wrong
        p1 = s.probs(ops.array(lp[None], f32))  # [1, V]
        q1 = s.probs(ops.array(lq[None], f32))
        p_rows = ops.concat([p1] * (n + 1), 0)
        q_rows = ops.concat([q1] * n, 0)
        drafts = ops.cast(s.draw(q_rows), ops.dtype('i32'))
        q_d = Sampler.gather(ops, q_rows, drafts)
        accept, corr = speculative_accept(ops, s, p_rows, q_rows, drafts, q_d)
        dr = ops.numpy(drafts).astype(np.int64)
        ac = ops.numpy(accept).astype(bool)
        co = ops.numpy(corr).astype(np.int64)[:n]
        committed = np.where(ac, dr, co)
        p_np = ops.numpy(p1)[0]
        q_np = ops.numpy(q1)[0]
        emp = np.bincount(committed, minlength=V) / n
        err = np.abs(emp - p_np).max()
        assert err < 0.03, (ops.name, err)
        rate, expected_rate = ac.mean(), np.minimum(p_np, q_np).sum()
        assert abs(rate - expected_rate) < 0.04, (ops.name, rate, expected_rate)
        # the naive scheme's rate for comparison: p(argmax q)
        naive = p_np[int(np.argmax(q_np))]
        print(f'{ops.name}: probs exact; rejection sampling reproduces p (max err {err:.3f}); acceptance '
              f'{rate:.2f} vs sum(min(p,q)) {expected_rate:.2f} (accept-if-equal would be {naive:.2f})')


def test_sampled_spec_runs():
    """Speculative decoding with a sampling sampler runs end to end and honours the token budget."""

    from ..model import Qwen35
    from .test_parity import synthetic_source

    cfg, hf, src = synthetic_source()
    prompt = np.random.default_rng(7).integers(0, 256, 5).tolist()
    for ops in backends():
        if getattr(ops, 'capture_mode', None) == 'auto' and ops.name.endswith('cpu'):
            ops.capture_mode = 'static'
        model = Qwen35.from_source(src, ops, dtype='f32', verbose=False, mtp=True)
        s = Sampler(temperature=1.0, top_k=20, top_p=0.95, presence_penalty=1.5, seed=3)
        out = model.generate(prompt, max_new_tokens=17, spec=3, sampler=s)
        assert len(out) == 17 and all(0 <= t < cfg.vocab_size for t in out), (ops.name, out)
        out2 = model.generate(prompt, max_new_tokens=17, sampler=Sampler(temperature=1.0, top_k=20, seed=3))
        assert len(out2) == 17
        if hasattr(ops, 'capture_mode'):
            ops.capture_mode = 'auto'
        print(f'{ops.name}: sampled spec decode OK ({model.last_spec.rounds} rounds)')


if __name__ == '__main__':
    test_sampler_distribution()
    test_probs_and_rejection_sampling()
    test_sampled_spec_runs()
