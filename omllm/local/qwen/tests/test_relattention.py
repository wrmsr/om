# ruff: noqa: N806
"""
Attention with a relative term and a sink (Ops.sdpa_sink, Ops.rel_bias, Ops.sdpa_static_rel: what Inkling 2's layers
attend with): the composed references against the definition written out per query, at the distances and sink values
where an off-by-one or a dropped term would show; and the torch backend's length-aware form -- the far keys through
the decode attention kernel, the near ones gathered -- against the reference, in both KV formats.
"""
import numpy as np

from ..ops.reference import NumpyOps
from .tritonmodes import triton_modes


##


def _by_hand(q, k, v, scale, rel, sink, qpos, kpos, window=None):
    """The definition, a query at a time, in float64: [H, T, D]."""

    H, T, D = q.shape
    KV = k.shape[0]
    E = rel.shape[-1]
    out = np.zeros((H, T, D))
    for h in range(H):
        kh = h // (H // KV)
        for t in range(T):
            logits = []
            vals = []
            for j, p in enumerate(kpos):
                d = qpos[t] - p
                if d < 0 or p < 0 or (window is not None and d >= window):
                    continue
                logits.append(float(q[h, t] @ k[kh, j]) * scale + (float(rel[t, h, d]) if d < E else 0.0))
                vals.append(v[kh, j])
            logits.append(float(sink[h, t]))  # the sink: a logit with no value behind it
            w = np.exp(np.asarray(logits) - max(logits))
            w = w / w.sum()
            out[h, t] = (w[:-1, None] * np.asarray(vals)).sum(0)
    return out


def test_composed_references():
    ops = NumpyOps()
    rng = np.random.default_rng(0)
    H, KV, D, E, L = 4, 2, 8, 5, 24

    k = rng.standard_normal((1, KV, L, D))
    v = rng.standard_normal((1, KV, L, D))

    for T, pos in ((1, 0), (1, 4), (1, 5), (1, 6), (3, 3), (4, L - 4)):  # distances below, at and past the extent
        q = rng.standard_normal((1, H, T, D))
        rel = rng.standard_normal((T, H, E))
        qpos = np.arange(pos, pos + T)
        kpos = np.arange(L)

        # the relative term alone: by distance, nothing at or past the extent, nothing for a key ahead
        got = ops.rel_bias(rel, qpos.astype(np.int32), kpos.astype(np.int32))
        for t in range(T):
            for j in range(L):
                d = qpos[t] - j
                want = rel[t, :, d] if 0 <= d < E else np.zeros(H)
                assert np.array_equal(got[t, j], want), (T, pos, t, j)

        for sink_value in (0.0, 30.0, -30.0):  # an ordinary sink, one that takes nearly everything, one that takes none
            sink = rng.standard_normal((1, H, T)) + sink_value
            got = ops.sdpa_static_rel(q, (k, v), np.asarray(pos, dtype=np.int32), np.arange(L), 0.3, rel, sink)
            want = _by_hand(q[0], k[0], v[0], 0.3, rel, sink[0], qpos, kpos)
            assert np.abs(got[0] - want).max() < 1e-9, (T, pos, sink_value)

            if sink_value == 30.0:
                assert np.abs(got).max() < 1e-6  # (its share is not handed back to the keys)
            if sink_value == -30.0:
                p = np.asarray(pos, dtype=np.int32)
                gone = ops.sdpa_static_rel(q, (k, v), p, np.arange(L), 0.3, rel, sink - 30)
                assert np.abs(got - gone).max() < 1e-9


def test_partials_merge_to_one_softmax():
    """
    `sdpa_partials` over two sets of keys -- one scored plainly, one with a bias -- merged with the sink
    (`sdpa_merge`) is `sdpa_sink` over all of them: what a prefill's attention is computed as, against its definition.
    """

    rng = np.random.default_rng(1)
    H, KV, D, T = 6, 2, 8, 5

    backends: list = [NumpyOps()]
    try:
        from ..backends.torch import TorchOps

        backends.append(TorchOps('cpu', triton=False))
    except ImportError:
        pass

    for ops in backends:
        f32 = ops.dtype('f32')
        tol = 1e-9 if isinstance(ops, NumpyOps) else 2e-5

        def arr(a: np.ndarray, ops=ops, f32=f32):
            return a if isinstance(ops, NumpyOps) else ops.array(a.astype(np.float32), f32)

        for far, near in ((0, 7), (1, 6), (30, 9), (200, 5)):
            L = far + near
            q = arr(rng.standard_normal((1, H, T, D)))
            k = arr(rng.standard_normal((1, KV, L, D)))
            v = arr(rng.standard_normal((1, KV, L, D)))
            bias_near = rng.standard_normal((1, H, T, near))
            bias_near[..., -2:] = -1e30  # (keys some queries do not see)
            bias_near[:, :, 0, :-1] = -1e30
            bias_near[:, :, 0, -1] = 0.5
            sink = arr(rng.standard_normal((1, H, T)) * 2)

            full = np.concatenate([np.zeros((1, H, T, far)), bias_near], -1)
            want = ops.numpy(ops.sdpa_sink(q, k, v, 0.3, arr(full), sink))

            parts = []
            if far:
                parts.append(ops.sdpa_partials(q, k[:, :, :far], v[:, :, :far], 0.3))
            parts.append(ops.sdpa_partials(q, k[:, :, far:], v[:, :, far:], 0.3, arr(bias_near)))
            got = ops.numpy(ops.sdpa_merge(parts, sink, f32))
            assert np.abs(got - want).max() < tol * max(1., np.abs(want).max()), (ops.name, far, near)

            # ... and with no sink it is a plain softmax over the keys
            got = ops.numpy(ops.sdpa_merge(parts, None, f32))
            want = ops.numpy(ops.sdpa_sink(q, k, v, 0.3, arr(full), arr(np.full((1, H, T), -1e30))))
            assert np.abs(got - want).max() < tol * max(1., np.abs(want).max()), (ops.name, far, near)


def _skip() -> bool:
    try:
        import torch  # noqa
    except ImportError:
        print('torch not installed; skipping')
        return True

    from ..backends.torch_triton import HAVE_TRITON

    if not HAVE_TRITON:
        print('triton not installed; skipping')
        return True

    return False


@triton_modes('interpret', 'compiled')
def test_length_aware_relative_attention():
    if _skip():
        return

    import torch

    from ..backends.torch import TorchOps
    from ..ops.base import Ops

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    rng = np.random.default_rng(3)
    H, KV, D, E, L = 4, 2, 16, 8, 64

    def t(a: np.ndarray, dtype: torch.dtype = torch.float32) -> torch.Tensor:
        return torch.from_numpy(a.astype(np.float32)).to(device).to(dtype)

    for kv_dtype in ('bf16', 'fp8'):
        ops = TorchOps(device, kv_dtype=kv_dtype, triton=True)
        ar = torch.arange(L, dtype=torch.int32, device=device)

        # (fewer cases under the interpreter, which takes seconds a launch)
        for T in ((1, 3, 6) if device == 'cuda' else (1, 3)):
            # (no far keys, the first far key, many)
            for pos in ((0, 1, 5, 7, 8, 9, 20, 40, L - T) if device == 'cuda' else (0, 7, 8, 40)):
                state = ops.kv_new(t(rng.standard_normal((1, KV, L, D))), t(rng.standard_normal((1, KV, L, D))))
                q = t(rng.standard_normal((1, H, T, D)))
                rel = t(rng.standard_normal((T, H, E)))
                sink = t(rng.standard_normal((1, H, T)) * 3)
                p = torch.full((), pos, dtype=torch.int32, device=device)

                want = Ops.sdpa_static_rel(ops, q, state, p, ar, 0.25, rel, sink)

                # (the two-part form itself: what `sdpa_static_rel` is on CUDA, run here on any device)
                got = ops.sdpa_static_rel_split(q, state, p, 0.25, rel, sink)
                err = ((got - want).abs().max() / want.abs().max()).item()
                assert err < 2e-5, (kv_dtype, T, pos, err)

                if device == 'cuda':
                    assert torch.equal(ops.sdpa_static_rel(q, state, p, ar, 0.25, rel, sink), got)

    # a prefill's far keys: the causal partials through the same kernel, every row at once on one split of the keys,
    # against the composed form -- whose rows with no key weigh nothing, as the kernel's must
    ops = TorchOps(device, triton=True)
    for T, last in ((20, -30), (20, -7), (24, 0), (40, 17)) if device == 'cuda' else ((20, -7),):
        L = max(1, last + T)
        q = t(rng.standard_normal((1, H, T, D)))
        k = t(rng.standard_normal((1, KV, L, D)))
        v = t(rng.standard_normal((1, KV, L, D)))
        sink = t(rng.standard_normal((1, H, T)))

        want = Ops.sdpa_causal_partials(ops, q, k, v, last, 0.25)
        got = ops.sdpa_causal_partials(q, k, v, last, 0.25)
        # (the partials themselves are relative to a maximum; what they merge to is what is compared)
        a = ops.sdpa_merge([want], sink, torch.float32)
        b = ops.sdpa_merge([got], sink, torch.float32)
        assert torch.isfinite(b).all() and (a - b).abs().max().item() < 2e-5 * max(1., a.abs().max().item()), (T, last)
        empty = max(0, min(T, -last))  # the rows that see no key: all sink
        assert b[:, :, :empty].abs().max().item() == 0 if empty else True

    print(f'length-aware relative attention == the composed reference on {device}')
