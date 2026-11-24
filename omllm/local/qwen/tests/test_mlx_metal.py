# ruff: noqa: N803 N806 N812
"""
MLX's fast attention for the static step (MlxOps.sdpa_static on mx.fast) against the composed reference. Runs
only where Metal is available (Apple silicon); skipped elsewhere, where MlxOps uses the references anyway.
"""
import numpy as np


try:
    import mlx.core as mx
except ImportError:
    mx = None  # type: ignore[assignment,unused-ignore]


##


def _skip() -> bool:
    if mx is None:
        print('mlx not installed; skipping')  # type: ignore[unreachable,unused-ignore]
        return True
    if not mx.metal.is_available():
        print('Metal not available; skipping')
        return True
    return False


def rel_err(a, b) -> float:
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    return float(np.abs(a - b).max() / (np.abs(b).max() + 1e-12))


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
