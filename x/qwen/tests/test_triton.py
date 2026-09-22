"""
The Triton int4/int8 GEMV (backends/torch_triton.py) against `TorchQWeight.dequant` + matmul.

Without a GPU this runs through Triton's numpy interpreter (`TRITON_INTERPRET=1`, set below before triton is
imported), f32 only and slowly, so the shapes are small. On a GPU it also runs the bf16 path.

Run:  python -m pytest x/qwen/tests/test_triton.py -q      or      python -m x.qwen.tests.test_triton
"""
import os

import numpy as np


try:
    import torch
except ImportError:  # pragma: no cover
    torch = None  # type: ignore[assignment]

if torch is not None and not torch.cuda.is_available():
    os.environ.setdefault('TRITON_INTERPRET', '1')

from ..quant import quantize as quantize_np


##


def _skip() -> bool:
    if torch is None:
        print('torch not installed; skipping')  # type: ignore
        return True

    from ..backends.triton import HAVE_TRITON

    if not HAVE_TRITON:
        print('triton not installed; skipping')
        return True

    return False


def test_qlinear_kernel():
    if _skip():
        return

    from ..backends.torch import TorchOps
    from ..backends.triton import qlinear

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    ops = TorchOps(device)
    rng = np.random.default_rng(0)
    dtypes = [torch.float32] + ([torch.bfloat16] if device == 'cuda' else [])
    for bits in (8, 4):
        for n, k in ((64, 256), (100, 320), (48, 512)):  # N not a multiple of the block; K forcing BLOCK_K 64
            w = (rng.standard_normal((n, k)) * 0.05).astype(np.float32)
            qw = ops.qweight(quantize_np(w, bits, 64), torch.float32)
            for m in (1, 5, 16, 33):
                for dt in dtypes:
                    x = torch.from_numpy(rng.standard_normal((m, k)).astype(np.float32)).to(device=device, dtype=dt)
                    s, b = qw.scale.to(dt), qw.bias.to(dt)
                    y = qlinear(x, qw.q, s, b, bits, 64, qw.shape)
                    ref = x.float() @ qw.dequant(torch.float32).T
                    tol = 1e-4 if dt == torch.float32 else 2e-2
                    err = ((y.float() - ref).abs().max() / ref.abs().max()).item()
                    assert err < tol, (bits, n, k, m, dt, err)
        print(f'int{bits}: kernel matches dequant reference for M in (1, 5, 16, 33)')

    # the FMA formulation (registers, M <= 8) must match too, for both widths and with split-K
    from ..backends.triton import GemvConfig

    for bits in (8, 4):
        w = (rng.standard_normal((72, 512)) * 0.05).astype(np.float32)
        qw = ops.qweight(quantize_np(w, bits, 64), torch.float32)
        for mm in (1, 3, 8):
            x = torch.from_numpy(rng.standard_normal((mm, 512)).astype(np.float32)).to(device)
            ref = x @ qw.dequant(torch.float32).T
            for sk in (1, 2):
                y = qlinear(x, qw.q, qw.scale, qw.bias, bits, 64, qw.shape, config=GemvConfig(32, 128, 4, 2, sk, True))
                assert ((y - ref).abs().max() / ref.abs().max()).item() < 1e-4, ('fma', bits, mm, sk)
    print('FMA GEMV int8/int4, M in (1, 3, 8), split-K 1/2 OK')

    # split-K: partial sums over K slices, then a reduction; must match the single-program result
    w = (rng.standard_normal((40, 1024)) * 0.05).astype(np.float32)
    qw = ops.qweight(quantize_np(w, 4, 64), torch.float32)
    x = torch.from_numpy(rng.standard_normal((3, 1024)).astype(np.float32)).to(device)
    ref = x @ qw.dequant(torch.float32).T
    for sk in (1, 2, 4, 8):
        y = qlinear(x, qw.q, qw.scale, qw.bias, 4, 64, qw.shape, config=GemvConfig(32, 128, 4, 2, sk))
        assert ((y - ref).abs().max() / ref.abs().max()).item() < 1e-4, sk
    print('split-K 1/2/4/8 OK')

    # 3-D activations (B, T, K) and the TorchOps.linear switch
    w = (rng.standard_normal((96, 256)) * 0.05).astype(np.float32)
    qw = ops.qweight(quantize_np(w, 4, 64), torch.float32)
    x = torch.from_numpy(rng.standard_normal((2, 3, 256)).astype(np.float32)).to(device)
    ops.triton = True
    y = ops.linear(x, qw)
    ops.triton = False
    ref = ops.linear(x, qw)
    assert y.shape == (2, 3, 96) and (y - ref).abs().max().item() < 1e-4
    print('TorchOps.linear switch OK')


def test_gdn_step_kernel():
    """
    The fused DeltaNet step against the composed Ops.gdn_step reference: T in (1, 4), 3 value heads per key
    head, final state and all-states variants.
    """

    if _skip():
        return

    from ..backends.torch import TorchOps
    from ..backends.triton import gdn_step

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    ops = TorchOps(device, triton=False)  # reference path
    torch.manual_seed(0)
    B, Hk, Hv, dk, dv = 2, 2, 6, 16, 32
    A = -torch.rand(Hv, device=device) * 4 - 0.1
    dt = torch.randn(Hv, device=device)
    for T in (1, 4):
        q = torch.randn(B, T, Hk, dk, device=device)
        k = torch.randn(B, T, Hk, dk, device=device)
        v = torch.randn(B, T, Hv, dv, device=device)
        a = torch.randn(B, T, Hv, device=device)
        b = torch.randn(B, T, Hv, device=device)
        S0 = torch.randn(B, Hv, dk, dv, device=device) * 0.3
        for all_states in (False, True):
            ro, rs = ops.gdn_step(q, k, v, a, b, A, dt, S0, all_states)
            for block_dv in (16, 32):
                fo, fs = gdn_step(q, k, v, a, b, A, dt, S0, all_states, block_dv=block_dv, num_warps=4)
                eo = ((fo - ro).abs().max() / ro.abs().max()).item()
                es = ((fs - rs).abs().max() / rs.abs().max()).item()
                assert eo < 1e-4 and es < 1e-4, (T, all_states, block_dv, eo, es)
                assert fs.shape == rs.shape
        # non-contiguous inputs (as produced by split + reshape in the model)
        big = torch.randn(B, T, 2 * Hk * dk + Hv * dv, device=device)
        qq, kk, vv = torch.split(big, [Hk * dk, Hk * dk, Hv * dv], -1)
        ro, rs = ops.gdn_step(qq.reshape(B, T, Hk, dk), kk.reshape(B, T, Hk, dk), vv.reshape(B, T, Hv, dv), a, b, A, dt, S0, False)  # noqa
        fo, fs = gdn_step(qq.reshape(B, T, Hk, dk), kk.reshape(B, T, Hk, dk), vv.reshape(B, T, Hv, dv), a, b, A, dt, S0, False)  # noqa
        assert ((fo - ro).abs().max() / ro.abs().max()).item() < 1e-4
    print('fused DeltaNet step matches the reference (T=1, 4; final and all states)')


def test_model_decode_with_kernel():
    """A quantized model's static decode step gives the same logits with and without the kernel."""

    if _skip():
        return
    from ..backends.torch import TorchOps
    from ..model import Cache
    from ..model import Decoder
    from ..model import Qwen35
    from .test_parity import rel_err
    from .test_parity import synthetic_source

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    cfg, hf, src = synthetic_source()
    ids = np.random.default_rng(5).integers(0, 256, (1, 8))
    outs = []
    for use in (False, True):
        ops = TorchOps(device, triton=use)
        m = Qwen35.from_source(src, ops, dtype='f32', quant='int4', verbose=False)
        cache = Cache(cfg)
        m.forward(ids[:, :5], cache)
        dec = Decoder(m, cache, capacity=16)
        outs.append(np.concatenate([ops.numpy(dec.step(int(t))) for t in ids[0, 5:]], 0))
    e = rel_err(outs[1], outs[0])
    assert e < 1e-4, e
    print(f'int4 model decode: kernel vs dequant path rel err {e:.1e}')


if __name__ == '__main__':
    test_qlinear_kernel()
    test_gdn_step_kernel()
    test_model_decode_with_kernel()
