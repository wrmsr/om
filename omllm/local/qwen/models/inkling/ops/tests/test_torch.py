# ruff: noqa: N806
"""
The Triton kernels for Inkling 2's operations (torchkernels.py) against the composed definitions they override
(base.py), in both Triton modes: interpreted on the CPU in float32, compiled on CUDA in bf16 and float32.
"""
import numpy as np

from .....tests.tritonmodes import triton_modes
from .. import torchkernels
from ..backends import inkling2_ops
from ..base import Inkling2Ops


##


def _env():
    import torch

    from .....backends.torch import TorchOps

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    dtypes = [torch.float32, torch.bfloat16] if device == 'cuda' else [torch.float32]
    ops = TorchOps(device, triton=True)
    inkling2_ops(ops)  # (jits the kernels)
    return torch, ops, device, dtypes


def _close(got, want, tol: float) -> float:
    err = float((got.float() - want.float()).abs().max() / max(1e-6, float(want.float().abs().max())))
    assert err < tol, err
    return err


@triton_modes('interpret', 'compiled')
def test_bottleneck_blend():
    torch, ops, device, dtypes = _env()

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

            want = Inkling2Ops(ops).bottleneck_blend(x, m, down, forget, gain, eps=1e-6, dtype=dtype)
            got = torchkernels.bottleneck_blend(x, m, down, forget, gain, 1e-6)
            assert got.shape == want.shape and got.dtype == torch.float32
            _close(got, want, 2e-5 if dtype == torch.float32 else 2e-2)

            if device == 'cuda':
                through = inkling2_ops(ops).bottleneck_blend(x, m, down, forget, gain, eps=1e-6, dtype=dtype)
                assert torch.equal(through, got)


@triton_modes('interpret', 'compiled')
def test_l2_clip():
    torch, ops, device, dtypes = _env()

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
                want = Inkling2Ops(ops).l2_clip(x, 9.0, scale=sc, after=af)
                got = torchkernels.l2_clip(x, 9.0, sc, af)
                assert got.shape == want.shape and got.dtype == x.dtype
                _close(got, want, 2e-5 if dtype == torch.float32 else 1e-2)
                if device == 'cuda':
                    assert torch.equal(inkling2_ops(ops).l2_clip(x, 9.0, scale=sc, after=af), got)
            assert float(torch.linalg.vector_norm(got.float(), dim=-1).max()) <= 9.0 * 1.4 * 1.01


@triton_modes('interpret', 'compiled')
def test_depth_mix():
    torch, ops, device, dtypes = _env()

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

            want = Inkling2Ops(ops).depth_mix(queries, sources, raw=raw, eps=1e-6)
            got = torchkernels.depth_mix(queries, sources, raw, 1e-6)
            assert got.shape == want.shape == (1, T, Q, H) and got.dtype == torch.float32
            _close(got, want, 5e-5)
            if device == 'cuda':
                assert torch.equal(inkling2_ops(ops).depth_mix(queries, sources, raw=raw, eps=1e-6), got)


@triton_modes('interpret', 'compiled')
def test_sum_to():
    torch, ops, device, dtypes = _env()

    rng = np.random.default_rng(12)
    for dtype in dtypes:
        for shape in ((1, 1, 64), (1, 3, 300), (1, 5, 2304)):
            a = torch.from_numpy(rng.standard_normal(shape).astype(np.float32)).to(device)
            b = torch.from_numpy(rng.standard_normal(shape).astype(np.float32)).to(device).to(dtype)
            for out in (torch.float32, dtype):
                want = Inkling2Ops(ops).sum_to(a, b, out)
                got = torchkernels.sum_to(a, b, out)
                assert got.dtype == out and torch.equal(got, want), (dtype, shape, out)
                if device == 'cuda':
                    assert torch.equal(inkling2_ops(ops).sum_to(a, b, out), want)

                want = Inkling2Ops(ops).sigmoid_gated(a, b, out)
                got = torchkernels.sigmoid_gated(a, b, out)
                assert got.dtype == out, (dtype, shape, out)
                _close(got, want, 2e-6 if out == torch.float32 else 2e-2)
                if device == 'cuda':
                    assert torch.equal(inkling2_ops(ops).sigmoid_gated(a, b, out), got)


@triton_modes('interpret', 'compiled')
def test_expert_small_work():
    """The router's pick, the capped gate, the weighted sum of the experts' outputs."""

    torch, ops, device, dtypes = _env()

    rng = np.random.default_rng(5)

    def t(a, dtype=torch.float32):
        return torch.from_numpy(np.asarray(a, dtype=np.float32)).to(device).to(dtype)

    for N, E, k in ((1, 128, 8), (5, 128, 8), (3, 40, 3), (2, 16, 16)):
        logits = t(rng.standard_normal((N, E)) * 2)
        bias = t(rng.standard_normal((E,)) * 0.3)
        want_i, want_w = Inkling2Ops(ops).sigmoid_route(logits, bias, k, total=8.0)
        got_i, got_w = torchkernels.sigmoid_route(logits, bias, k, 8.0)
        assert got_i.shape == (N, k) and torch.equal(got_i.long(), want_i.long()), (N, E, k)
        _close(got_w, want_w, 1e-5)
        assert float((got_w.sum(-1) - 8.0).abs().max()) < 1e-4

    # equal scores: the first of them, and each expert once
    flat = torch.zeros((1, 16), device=device)
    got_i, got_w = torchkernels.sigmoid_route(flat, flat[0], 4, 1.0)
    assert got_i.tolist() == [[0, 1, 2, 3]] and float((got_w - 0.25).abs().max()) < 1e-6

    for dtype in dtypes:
        for R, I in ((1, 96), (8, 1152), (24, 40)):  # noqa: E741
            h = t(rng.standard_normal((R, 2 * I)) * 20, dtype)  # (past both caps)
            want = Inkling2Ops(ops).capped_gate(h, gate_cap=4.0, up_cap=25.0)
            got = torchkernels.capped_gate(h, 4.0, 25.0)
            assert got.shape == (R, I) and got.dtype == h.dtype
            _close(got, want, 2e-5 if dtype == torch.float32 else 1e-2)

        for N, K, H in ((1, 8, 2304), (3, 8, 300), (2, 1, 64)):
            y = t(rng.standard_normal((N, K, H)), dtype)
            w = t(rng.uniform(0.0, 2.0, (N, K)))
            want = Inkling2Ops(ops).weighted_rows(y, w, dtype)
            got = torchkernels.weighted_rows(y, w, dtype)
            assert got.shape == (N, H) and got.dtype == dtype
            _close(got, want, 2e-5 if dtype == torch.float32 else 1e-2)


@triton_modes('interpret', 'compiled')
def test_rms_norm_to():
    torch, ops, device, dtypes = _env()

    rng = np.random.default_rng(6)

    def t(a, dtype=torch.float32):
        return torch.from_numpy(np.asarray(a, dtype=np.float32)).to(device).to(dtype)

    for dtype in dtypes:
        for H, T in ((96, 1), (2304, 1), (2304, 5), (300, 2)):
            mix = t(rng.standard_normal((1, T, 3, H)) * 5)
            x = mix[:, :, 2]  # (a read's: one query's rows of a mix)
            w = t(rng.standard_normal((H,)) * 0.2 + 1.0)
            want = Inkling2Ops(ops).rms_norm_to(x, w, 1e-6, dtype)
            got = torchkernels.rms_norm_to(x, w, 1e-6, dtype)
            assert got.shape == want.shape == (1, T, H) and got.dtype == dtype
            _close(got, want, 2e-5 if dtype == torch.float32 else 1e-2)
