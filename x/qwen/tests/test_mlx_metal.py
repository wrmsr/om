"""
The MLX Metal kernels (backends/mlx_metal.py, and MlxOps.sdpa_static on mx.fast) against the composed references.
Runs only where Metal is available (Apple silicon); skipped elsewhere, where MlxOps uses the references anyway.

Run:  python -m pytest x/qwen/tests/test_mlx_metal.py -q      or      python -m x.qwen.tests.test_mlx_metal
"""
import numpy as np

try:
    import mlx.core as mx
except ImportError:  # pragma: no cover
    mx = None  # type: ignore[assignment]


##


def _skip() -> bool:
    if mx is None:
        print('mlx not installed; skipping')
        return True
    if not mx.metal.is_available():
        print('Metal not available; skipping')
        return True
    return False


def rel_err(a, b) -> float:
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    return float(np.abs(a - b).max() / (np.abs(b).max() + 1e-12))


def test_gdn_step_metal():
    if _skip():
        return
    from ..backends.mlx import MlxOps
    from ..backends.mlx_metal import gdn_step_metal

    ref = MlxOps(metal=False)  # composed reference
    rng = np.random.default_rng(0)
    for (Hk, Hv, dk, dv) in ((2, 6, 16, 32), (16, 48, 128, 128)):
        B = 2 if dk == 16 else 1
        A = mx.array((-rng.random(Hv) * 4 - 0.1).astype(np.float32))
        dt = mx.array(rng.standard_normal(Hv).astype(np.float32))
        for T in (1, 4):
            q = mx.array(rng.standard_normal((B, T, Hk, dk)).astype(np.float32))
            k = mx.array(rng.standard_normal((B, T, Hk, dk)).astype(np.float32))
            v = mx.array(rng.standard_normal((B, T, Hv, dv)).astype(np.float32))
            a = mx.array(rng.standard_normal((B, T, Hv)).astype(np.float32))
            b = mx.array(rng.standard_normal((B, T, Hv)).astype(np.float32))
            s0 = mx.array((rng.standard_normal((B, Hv, dk, dv)) * 0.3).astype(np.float32))
            for all_states in (False, True):
                ro, rs = ref.gdn_step(q, k, v, a, b, A, dt, s0, all_states)
                for variant, kw in (('tg', {}), ('simd', {'ks': 4}), ('simd', {'ks': 8, 'tgv': 16})):
                    fo, fs = gdn_step_metal(q, k, v, a, b, A, dt, s0, all_states, variant=variant, **kw)
                    mx.eval(ro, rs, fo, fs)
                    eo, es = rel_err(fo, ro), rel_err(fs, rs)
                    assert eo < 1e-4 and es < 1e-4, ((Hk, Hv, dk, dv), T, all_states, variant, kw, eo, es)
                    assert fs.shape == rs.shape
    print('Metal DeltaNet step (tg and simd variants) matches the composed reference (small and 27B-like '
          'geometries, T=1/4, all states)')


def test_sdpa_static_metal():
    if _skip():
        return
    from ..backends.mlx import MlxOps

    ops = MlxOps()
    ref = MlxOps(metal=False)
    rng = np.random.default_rng(1)
    B, H, KV, D, L = 1, 24, 4, 256, 512
    for T in (1, 4):
        q = mx.array(rng.standard_normal((B, H, T, D)).astype(np.float32)).astype(mx.bfloat16)
        kb = mx.array(rng.standard_normal((B, KV, L, D)).astype(np.float32)).astype(mx.bfloat16)
        vb = mx.array(rng.standard_normal((B, KV, L, D)).astype(np.float32)).astype(mx.bfloat16)
        pos = ops.scalar(37)
        ar = ops.arange(L)
        o = ops.numpy(ops.sdpa_static(q, kb, vb, pos, ar, D ** -0.5))
        r = ref.numpy(ref.sdpa_static(q, kb, vb, pos, ar, D ** -0.5))
        e = rel_err(o, r)
        assert e < 2e-2, (T, e)  # bf16 inputs; both paths round differently
    print('mx.fast SDPA over the static buffer matches the folded-matmul reference')


if __name__ == '__main__':
    test_gdn_step_metal()
    test_sdpa_static_metal()
