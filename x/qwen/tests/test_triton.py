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
        print('torch not installed; skipping')
        return True
    from ..backends.torch_triton import HAVE_TRITON

    if not HAVE_TRITON:
        print('triton not installed; skipping')
        return True
    return False


def test_qlinear_kernel():
    if _skip():
        return
    from ..backends.torch import TorchOps
    from ..backends.torch_triton import qlinear

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
    # split-K: partial sums over K slices, then a reduction; must match the single-program result
    from ..backends.torch_triton import GemvConfig

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
    test_model_decode_with_kernel()
