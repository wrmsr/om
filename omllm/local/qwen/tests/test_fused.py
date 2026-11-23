# ruff: noqa: N806
"""
The fused kernels (backends/torch_fused.py) against the composed operations they override (ops/base.py), in both
Triton modes: interpreted on the CPU in float32, compiled on CUDA in bf16 and float32.
"""
import numpy as np

from .tritonmodes import triton_modes


##


def _env():
    import torch

    from ..backends.torch import TorchOps

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    dtypes = [torch.float32, torch.bfloat16] if device == 'cuda' else [torch.float32]
    return torch, TorchOps(device, triton=True), device, dtypes


def _close(got, want, tol: float) -> float:
    err = float((got.float() - want.float()).abs().max() / max(1e-6, float(want.float().abs().max())))
    assert err < tol, err
    return err


@triton_modes('interpret', 'compiled')
def test_bottleneck_blend():
    torch, ops, device, dtypes = _env()

    from ..backends import torch_fused
    from ..ops.base import Ops

    rng = np.random.default_rng(0)

    def t(a, dtype=torch.float32):
        return torch.from_numpy(np.asarray(a, dtype=np.float32)).to(device).to(dtype)

    for dtype in dtypes:
        cases = ((96, 16, 1), (300, 32, 3), (2304, 64, 1), (2304, 64, 5))
        for H, R, T in cases[:(4 if device == 'cuda' else 2)]:
            x = t(rng.standard_normal((1, T, H)) * 3)
            m4 = t(rng.standard_normal((1, T, 3, H)))
            m = m4[:, :, 1]  # (a view with a stride between its rows, as a message read hands one over)
            down = t(rng.standard_normal((R, 2 * H)) / np.sqrt(H), dtype)
            forget = t(rng.standard_normal((H, R)) / np.sqrt(R))
            gain = t(rng.standard_normal((H, R)) / np.sqrt(R))

            want = Ops.bottleneck_blend(ops, x, m, down, forget, gain, eps=1e-6, dtype=dtype)
            got = torch_fused.bottleneck_blend(x, m, down, forget, gain, 1e-6)
            assert got.shape == want.shape and got.dtype == torch.float32
            _close(got, want, 2e-5 if dtype == torch.float32 else 2e-2)

            if device == 'cuda':
                assert torch.equal(ops.bottleneck_blend(x, m, down, forget, gain, eps=1e-6, dtype=dtype), got)


@triton_modes('interpret', 'compiled')
def test_short_conv():
    torch, ops, device, dtypes = _env()

    from ..backends import torch_fused
    from ..ops.base import Ops

    rng = np.random.default_rng(1)

    def t(a, dtype=torch.float32):
        return torch.from_numpy(np.asarray(a, dtype=np.float32)).to(device).to(dtype)

    for dtype in dtypes:
        for C, K, T in ((40, 4, 1), (40, 4, 2), (300, 4, 3), (64, 3, 5), (2304, 4, 1), (1024, 4, 7)):
            w = t(rng.standard_normal((C, K)) * 0.3)
            hist = None
            # a run of steps, each from the history the one before left: fused and composed side by side
            for step in range(3):
                x = t(rng.standard_normal((1, T, C)), dtype)
                for all_states in (False, True):
                    want_y, want_h = Ops.short_conv(ops, x, hist, w, scale=0.4, all_states=all_states)
                    got_y, got_h = torch_fused.short_conv(x, hist, w, 0.4, all_states)
                    assert got_y.shape == want_y.shape and got_y.dtype == x.dtype, (C, K, T)
                    assert got_h.shape == want_h.shape and got_h.dtype == torch.float32, (C, K, T, all_states)
                    # (a state that holds its own storage and no more: not a view into every row's history)
                    assert got_h.untyped_storage().nbytes() == got_h.numel() * 4, (C, K, T, all_states)
                    _close(got_y, want_y, 2e-5 if dtype == torch.float32 else 1e-2)
                    assert torch.equal(got_h, want_h), (C, K, T, step, all_states)  # (the inputs themselves)
                hist = want_h[-1] if step == 0 else got_h[-1]  # (the last token's, as a commit of all T keeps)


@triton_modes('interpret', 'compiled')
def test_l2_clip():
    torch, ops, device, dtypes = _env()

    from ..backends import torch_fused
    from ..ops.base import Ops

    rng = np.random.default_rng(2)

    def t(a, dtype=torch.float32):
        return torch.from_numpy(np.asarray(a, dtype=np.float32)).to(device).to(dtype)

    for dtype in dtypes:
        for T, G, D in ((1, 24, 128), (3, 24, 16), (2, 8, 128), (5, 5, 32)):
            # (norms on both sides of the threshold)
            x = t(rng.standard_normal((1, T, G, D)) * rng.uniform(0.2, 4.0, (1, T, G, 1)), dtype)
            scale = t(rng.standard_normal((G, D)) * 0.5 + 1.0, dtype)
            after = t(rng.uniform(1.0, 1.4, (T,)))
            for sc, af in ((None, None), (scale, None), (scale, after), (None, after)):
                want = Ops.l2_clip(ops, x, 9.0, scale=sc, after=af)
                got = torch_fused.l2_clip(x, 9.0, sc, af)
                assert got.shape == want.shape and got.dtype == x.dtype
                _close(got, want, 2e-5 if dtype == torch.float32 else 1e-2)
                if device == 'cuda':
                    assert torch.equal(ops.l2_clip(x, 9.0, scale=sc, after=af), got)
            assert float(torch.linalg.vector_norm(got.float(), dim=-1).max()) <= 9.0 * 1.4 * 1.01


@triton_modes('interpret', 'compiled')
def test_depth_mix():
    torch, ops, device, dtypes = _env()

    from ..backends import torch_fused
    from ..ops.base import Ops

    rng = np.random.default_rng(3)

    def t(a, dtype=torch.float32):
        return torch.from_numpy(np.asarray(a, dtype=np.float32)).to(device).to(dtype)

    for dtype in dtypes:
        cases = ((96, 1, 1, 1, 1), (96, 2, 3, 2, 0), (300, 3, 1, 5, 1), (2304, 1, 3, 5, 1), (2304, 4, 1, 6, 2))
        for H, T, Q, S, raw in cases:
            queries = t(rng.standard_normal((Q, H)))
            sources = [t(rng.standard_normal((1, T, H))) for _ in range(S - raw)]
            # (the raw ones as a stream's running sum is: any scale, the model's dtype)
            sources += [t(rng.standard_normal((1, T, H)) * 7.0, dtype) for _ in range(raw)]

            want = Ops.depth_mix(ops, queries, sources, raw=raw, eps=1e-6)
            got = torch_fused.depth_mix(queries, sources, raw, 1e-6)
            assert got.shape == want.shape == (1, T, Q, H) and got.dtype == torch.float32
            _close(got, want, 5e-5)
            if device == 'cuda':
                assert torch.equal(ops.depth_mix(queries, sources, raw=raw, eps=1e-6), got)


@triton_modes('interpret', 'compiled')
def test_sdpa_window_rel():
    torch, ops, device, dtypes = _env()

    from ..backends import torch_fused
    from ..ops.base import Ops

    rng = np.random.default_rng(4)

    def t(a, dtype=torch.float32):
        return torch.from_numpy(np.asarray(a, dtype=np.float32)).to(device).to(dtype)

    # (H, KV, D, R, window, extent, T, pos): a window not yet full, just full, long full; a term shorter than it
    cases = (
        (4, 2, 16, 4, 12, 12, 1, 3),
        (4, 2, 16, 4, 12, 12, 3, 0),
        (4, 2, 16, 4, 12, 12, 1, 11),
        (6, 2, 16, 4, 12, 7, 4, 40),
        (24, 8, 128, 16, 1024, 1024, 1, 5000),
        (24, 8, 128, 16, 1024, 1024, 8, 700),
    )
    for dtype in dtypes:
        for H, KV, D, R, window, E, T, pos in cases[:(6 if device == 'cuda' else 4)]:
            N = window - 1 + T
            q = t(rng.standard_normal((1, T, H, D)), dtype).transpose(1, 2)  # (as the model makes it: a transpose)
            k = t(rng.standard_normal((1, KV, N, D)), dtype)
            v = t(rng.standard_normal((1, KV, N, D)), dtype)
            rel = t(rng.standard_normal((T, H, R)), dtype)
            rel_proj = t(rng.standard_normal((E, R)) * 0.5, dtype)
            sink = t(rng.standard_normal((1, T, H)) * 2).transpose(1, 2)
            p = torch.full((), pos, dtype=torch.int32, device=device)

            kw = dict(scale=D ** -0.5, rel=rel, rel_proj=rel_proj, sink=sink, window=window)
            want = Ops.sdpa_window_rel(ops, q, k, v, p, **kw)
            bn = 8 if D < 64 else 64
            got = torch_fused.sdpa_window_rel(q, k, v, p, D ** -0.5, rel, rel_proj, sink, window, block_n=bn)
            assert got.shape == want.shape == (1, H, T, D) and got.dtype == q.dtype
            _close(got, want, 5e-5 if dtype == torch.float32 else 3e-2)
            if device == 'cuda':
                assert torch.equal(ops.sdpa_window_rel(q, k, v, p, **kw), got) or D < 64

            # another set of keys under the same softmax, as its partials
            far = (
                t(rng.standard_normal((1, T, H)) * 3).transpose(1, 2).contiguous(),
                t(np.abs(rng.standard_normal((1, T, H))) + 0.5).transpose(1, 2).contiguous(),
                t(rng.standard_normal((1, T, H, D))).transpose(1, 2).contiguous(),
            )
            want = Ops.sdpa_window_rel(ops, q, k, v, p, more=[far], **kw)
            got = torch_fused.sdpa_window_rel(q, k, v, p, D ** -0.5, rel, rel_proj, sink, window, [far], block_n=bn)
            _close(got, want, 5e-5 if dtype == torch.float32 else 3e-2)

    # a prefill's queries: more of them than the backend hands the kernel at a time, over keys that start short of a
    # window, with and without the far set
    if device == 'cuda':
        H, KV, D, R, window, E = 6, 2, 16, 4, 40, 40
        for T, before in ((300, 0), (300, 17), (700, 39)):
            N = before + T
            q = t(rng.standard_normal((1, T, H, D))).transpose(1, 2)
            k = t(rng.standard_normal((1, KV, N + 5, D)))[:, :, 5:]  # (a slice, as a prefill's are)
            v = t(rng.standard_normal((1, KV, N + 5, D)))[:, :, 5:]
            rel = t(rng.standard_normal((T, H, R)))
            rel_proj = t(rng.standard_normal((E, R)) * 0.5)
            sink = t(rng.standard_normal((1, T, H)) * 2).transpose(1, 2)
            p = torch.full((), 1000 + before, dtype=torch.int32, device=device)
            far = (
                t(rng.standard_normal((1, T, H)) * 3).transpose(1, 2).contiguous(),
                t(np.abs(rng.standard_normal((1, T, H))) + 0.5).transpose(1, 2).contiguous(),
                t(rng.standard_normal((1, T, H, D))).transpose(1, 2).contiguous(),
            )
            kw = dict(scale=D ** -0.5, rel=rel, rel_proj=rel_proj, sink=sink, window=window)
            for more in ((), [far]):
                want = Ops.sdpa_window_rel(ops, q, k, v, p, more=more, **kw)
                got = ops.sdpa_window_rel(q, k, v, p, more=more, **kw)
                assert got.shape == want.shape == (1, H, T, D)
                _close(got, want, 5e-5)


@triton_modes('interpret', 'compiled')
def test_sum_to():
    torch, ops, device, dtypes = _env()

    from ..backends import torch_fused
    from ..ops.base import Ops

    rng = np.random.default_rng(12)
    for dtype in dtypes:
        for shape in ((1, 1, 64), (1, 3, 300), (1, 5, 2304)):
            a = torch.from_numpy(rng.standard_normal(shape).astype(np.float32)).to(device)
            b = torch.from_numpy(rng.standard_normal(shape).astype(np.float32)).to(device).to(dtype)
            for out in (torch.float32, dtype):
                want = Ops.sum_to(ops, a, b, out)
                got = torch_fused.sum_to(a, b, out)
                assert got.dtype == out and torch.equal(got, want), (dtype, shape, out)
                if device == 'cuda':
                    assert torch.equal(ops.sum_to(a, b, out), want)

                want = Ops.sigmoid_gated(ops, a, b, out)
                got = torch_fused.sigmoid_gated(a, b, out)
                assert got.dtype == out, (dtype, shape, out)
                _close(got, want, 2e-6 if out == torch.float32 else 2e-2)
                if device == 'cuda':
                    assert torch.equal(ops.sigmoid_gated(a, b, out), got)


@triton_modes('interpret', 'compiled')
def test_kv_append():
    """A step's keys and values into their buffers at a position on the device, as the indexed write puts them."""

    torch, ops, device, dtypes = _env()

    from ..backends import torch_fused

    rng = np.random.default_rng(11)

    def t(a, dtype=torch.float32):
        return torch.from_numpy(np.asarray(a, dtype=np.float32)).to(device).to(dtype)

    for dtype in dtypes:
        for KV, D, L, T, pos in ((2, 16, 40, 1, 0), (2, 16, 40, 3, 37), (8, 128, 300, 5, 123)):
            kbuf, vbuf = t(rng.standard_normal((1, KV, L, D)), dtype), t(rng.standard_normal((1, KV, L, D)), dtype)
            # (as a model makes them: [1, T, KV, D] transposed, and in float32 while the buffers are the model's)
            k = t(rng.standard_normal((1, T, KV, D))).transpose(1, 2)
            v = t(rng.standard_normal((1, T, KV, D))).transpose(1, 2)
            p = torch.full((), pos, dtype=torch.int32, device=device)

            want_k, want_v = kbuf.clone(), vbuf.clone()
            want_k[:, :, pos:pos + T] = k.to(dtype)
            want_v[:, :, pos:pos + T] = v.to(dtype)

            got_k, got_v = kbuf.clone(), vbuf.clone()
            torch_fused.kv_append(got_k, got_v, p, k, v)
            assert torch.equal(got_k, want_k) and torch.equal(got_v, want_v), (dtype, KV, D, T)

            if device == 'cuda':
                st = ops.kv_write_tokens((kbuf.clone(), vbuf.clone()), p, k, v)
                assert torch.equal(st[0], want_k) and torch.equal(st[1], want_v)


@triton_modes('interpret', 'compiled')
def test_expert_small_work():
    """The router's pick, the capped gate, the weighted sum of the experts' outputs."""

    torch, ops, device, dtypes = _env()

    from ..backends import torch_fused
    from ..ops.base import Ops

    rng = np.random.default_rng(5)

    def t(a, dtype=torch.float32):
        return torch.from_numpy(np.asarray(a, dtype=np.float32)).to(device).to(dtype)

    for N, E, k in ((1, 128, 8), (5, 128, 8), (3, 40, 3), (2, 16, 16)):
        logits = t(rng.standard_normal((N, E)) * 2)
        bias = t(rng.standard_normal((E,)) * 0.3)
        want_i, want_w = Ops.sigmoid_route(ops, logits, bias, k, total=8.0)
        got_i, got_w = torch_fused.sigmoid_route(logits, bias, k, 8.0)
        assert got_i.shape == (N, k) and torch.equal(got_i.long(), want_i.long()), (N, E, k)
        _close(got_w, want_w, 1e-5)
        assert float((got_w.sum(-1) - 8.0).abs().max()) < 1e-4

    # equal scores: the first of them, and each expert once
    flat = torch.zeros((1, 16), device=device)
    got_i, got_w = torch_fused.sigmoid_route(flat, flat[0], 4, 1.0)
    assert got_i.tolist() == [[0, 1, 2, 3]] and float((got_w - 0.25).abs().max()) < 1e-6

    for dtype in dtypes:
        for R, I in ((1, 96), (8, 1152), (24, 40)):  # noqa: E741
            h = t(rng.standard_normal((R, 2 * I)) * 20, dtype)  # (past both caps)
            want = Ops.capped_gate(ops, h, gate_cap=4.0, up_cap=25.0)
            got = torch_fused.capped_gate(h, 4.0, 25.0)
            assert got.shape == (R, I) and got.dtype == h.dtype
            _close(got, want, 2e-5 if dtype == torch.float32 else 1e-2)

        for N, K, H in ((1, 8, 2304), (3, 8, 300), (2, 1, 64)):
            y = t(rng.standard_normal((N, K, H)), dtype)
            w = t(rng.uniform(0.0, 2.0, (N, K)))
            want = Ops.weighted_rows(ops, y, w, dtype)
            got = torch_fused.weighted_rows(y, w, dtype)
            assert got.shape == (N, H) and got.dtype == dtype
            _close(got, want, 2e-5 if dtype == torch.float32 else 1e-2)


@triton_modes('interpret', 'compiled')
def test_short_conv_dynamic_and_rms_norm_to():
    torch, ops, device, dtypes = _env()

    from ..backends import torch_fused
    from ..ops.base import Ops

    rng = np.random.default_rng(6)

    def t(a, dtype=torch.float32):
        return torch.from_numpy(np.asarray(a, dtype=np.float32)).to(device).to(dtype)

    for dtype in dtypes:
        for C, K, G, T in ((48, 4, 4, 1), (48, 4, 4, 3), (1024, 4, 8, 1), (1024, 4, 8, 6), (60, 3, 5, 2)):
            w = t(rng.standard_normal((K, C)) * 0.3)
            hist = None
            for step in range(3):
                x = t(rng.standard_normal((1, T, C)), dtype)
                dyn = t(rng.standard_normal((1, T, G, K)) * 0.3)
                for all_states in (False, True):
                    want_y, want_h = Ops.short_conv_dynamic(ops, x, hist, w, dyn, scale=1 / 3, all_states=all_states)
                    got_y, got_h = torch_fused.short_conv(x, hist, w, 1 / 3, all_states, dyn=dyn)
                    assert got_y.shape == want_y.shape and got_y.dtype == x.dtype
                    assert got_h.shape == want_h.shape and torch.equal(got_h, want_h), (C, K, G, T, step, all_states)
                    _close(got_y, want_y, 2e-5 if dtype == torch.float32 else 1e-2)
                hist = got_h[-1]

        for H, T in ((96, 1), (2304, 1), (2304, 5), (300, 2)):
            mix = t(rng.standard_normal((1, T, 3, H)) * 5)
            x = mix[:, :, 2]  # (a read's: one query's rows of a mix)
            w = t(rng.standard_normal((H,)) * 0.2 + 1.0)
            want = Ops.rms_norm_to(ops, x, w, 1e-6, dtype)
            got = torch_fused.rms_norm_to(x, w, 1e-6, dtype)
            assert got.shape == want.shape == (1, T, H) and got.dtype == dtype
            _close(got, want, 2e-5 if dtype == torch.float32 else 1e-2)


@triton_modes('interpret', 'compiled')
def test_dense_gemv():
    torch, ops, device, dtypes = _env()

    from ..backends import torch_fused

    rng = np.random.default_rng(7)

    def t(a, dtype=torch.float32):
        return torch.from_numpy(np.asarray(a, dtype=np.float32)).to(device).to(dtype)

    for dtype in dtypes:
        for N, K in ((24, 300), (128, 2304), (3072, 2304), (40, 5000))[:(4 if device == 'cuda' else 2)]:
            w = t(rng.standard_normal((N, K)) / np.sqrt(K), dtype)
            x = t(rng.standard_normal((1, 1, K)), dtype)
            want = torch.nn.functional.linear(x.float(), w.float())
            got = torch_fused.dense_gemv(x, w)
            assert got.shape == (1, 1, N) and got.dtype == dtype
            _close(got, want, 2e-5 if dtype == torch.float32 else 2e-2)
            if device == 'cuda':
                assert torch.equal(ops.linear(x, w), got)

            # a few rows: every row of x against each row of w, loaded once
            if K <= torch_fused.DENSE_ROWS_MAX_K:
                for T in (2, 5, 8):
                    xs = t(rng.standard_normal((T, K)), dtype)
                    want = torch.nn.functional.linear(xs.float(), w.float())
                    got = torch_fused.dense_rows(xs, w)
                    assert got.shape == (T, N) and got.dtype == dtype
                    _close(got, want, 2e-5 if dtype == torch.float32 else 2e-2)
                    if device == 'cuda' and torch_fused.dense_rows_pays(T, N):
                        assert torch.equal(ops.linear(xs.reshape(1, T, K), w), got.reshape(1, T, N))
