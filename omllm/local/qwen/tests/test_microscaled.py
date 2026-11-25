# ruff: noqa: N803 N806
"""
Microscaled float weights (ops/microscaled.py: NVFP4, MXFP8): the code tables against the encodings' definitions and
torch's own float8 type, the reference decode against the scalar formula, the torch container's composed decode, and
the Triton kernels that read the packed experts -- the per-row GEMV and the dense decode -- against it; the
tinygrad container, which decodes by arithmetic on the bits, where that backend is enabled (test_parity.py); and the
MLX container, with numpy's arrays in MLX's place anywhere, and on MLX where it is installed.
"""
import typing as ta

import numpy as np
import pytest

from ..ops.microscaled import MicroscaledWeight
from ..ops.microscaled import e2m1_pair_values
from ..ops.microscaled import e2m1_values
from ..ops.microscaled import e4m3_values
from ..ops.microscaled import pow2_scale_values
from ..ops.reference import NumpyOps
from .tritonmodes import triton_modes


##


def random_microscaled(rng: np.random.Generator, fmt: str, E: int, N: int, K: int) -> MicroscaledWeight:
    """Random experts in a format: every code, scales of moderate size (inkling2checkpoints.py writes the same)."""

    if fmt == 'nvfp4':
        return MicroscaledWeight(
            fmt,
            rng.integers(0, 256, (E, N, K // 2), dtype=np.uint8),
            ((rng.integers(5, 9, (E, N, K // 16)) << 3) | rng.integers(0, 8, (E, N, K // 16))).astype(np.uint8),
            rng.uniform(0.01, 0.05, E).astype(np.float32),
            (E, N, K),
        )

    codes = (rng.integers(0, 2, (E, N, K)) << 7) | (rng.integers(3, 9, (E, N, K)) << 3) | rng.integers(0, 8, (E, N, K))
    return MicroscaledWeight(
        fmt,
        codes.astype(np.uint8),
        rng.integers(122, 125, (E, N, K // 32), dtype=np.uint8),
        None,
        (E, N, K),
    )


def test_code_tables():
    # E2M1: sign, two exponent bits, one mantissa bit -- subnormal at exponent 0
    assert e2m1_values().tolist() == [0, .5, 1, 1.5, 2, 3, 4, 6, -0., -.5, -1, -1.5, -2, -3, -4, -6]
    assert e2m1_pair_values()[0x2F].tolist() == [-6., 1.]  # (the low nibble first)

    # E4M3: sign, four exponent bits biased by 7, three mantissa bits
    v = e4m3_values()
    assert v[0] == 0 and v[0x38] == 1.0 and v[0x39] == 1.125 and v[0x40] == 2.0 and v[0xB8] == -1.0
    assert v[0x01] == 2. ** -9 and v[0x07] == 7 * 2. ** -9 and v[0x08] == 2. ** -6  # subnormals, then a normal
    assert v[0x7E] == 448.0 and np.isnan(v[0x7F]) and np.isnan(v[0xFF])

    assert pow2_scale_values()[127] == 1.0 and pow2_scale_values()[120] == 2. ** -7 and pow2_scale_values()[130] == 8.0

    try:
        import torch
    except ImportError:
        return
    if not hasattr(torch, 'float8_e4m3fn'):
        return
    theirs = torch.arange(256, dtype=torch.uint8).view(torch.float8_e4m3fn).to(torch.float32).numpy()
    assert np.array_equal(theirs, v, equal_nan=True)


def test_reference_decode():
    rng = np.random.default_rng(0)

    for fmt in ('nvfp4', 'mxfp8'):
        mw = random_microscaled(rng, fmt, 3, 5, 64)
        w = mw.dequantize()
        assert w.shape == (3, 5, 64) and w.dtype == np.float32

        # the scalar formula, element by element
        for e, n, k in ((0, 0, 0), (1, 2, 17), (2, 4, 63), (0, 3, 32)):
            if fmt == 'nvfp4':
                byte = int(mw.codes[e, n, k // 2])
                code = (byte >> 4) if k % 2 else (byte & 0xF)
                scale = e4m3_values()[mw.scales[e, n, k // 16]]
                want = e2m1_values()[code] * scale * mw.outer[e]  # type: ignore[index]
            else:
                want = e4m3_values()[mw.codes[e, n, k]] * np.float32(2.) ** (int(mw.scales[e, n, k // 32]) - 127)
            assert abs(float(w[e, n, k]) - float(want)) <= 1e-6 * abs(float(want)), (fmt, e, n, k)

        assert np.array_equal(mw.dequantize(np.asarray([2, 0])), w[[2, 0]])

        # rows reordered are the same rows
        order = np.asarray([4, 0, 3, 1, 2])
        assert np.array_equal(mw.rows(order).dequantize(), w[:, order])

        # the default adoption is the dense weights; every row against its own expert
        ops = NumpyOps()
        dense = ops.microscaled(mw, ops.dtype('f32'))
        x = rng.standard_normal((4, 64))
        eids = np.asarray([2, 0, 0, 1, 2, 2, 1, 0])
        got = ops.expert_linear(x, dense, eids, 2)
        want_rows = np.stack([w[eids[r]].astype(np.float64) @ x[r // 2] for r in range(8)])
        assert np.allclose(got, want_rows)
        assert np.allclose(ops.expert_linear_grouped(np.repeat(x, 2, 0), dense, eids), want_rows)

    with pytest.raises(Exception):  # noqa: B017, PT011
        MicroscaledWeight('nvfp4', np.zeros((1, 2, 8), np.uint8), np.zeros((1, 2, 2), np.uint8), None, (1, 2, 16))


def test_tinygrad_container():
    from .test_parity import backends

    ops: ta.Any = next((o for o in backends() if o.name.startswith('tinygrad')), None)
    if ops is None:
        pytest.skip('tinygrad not installed, or disabled in test_parity.DISABLED_BACKENDS')

    import tinygrad as tg

    from ..backends.tinygrad import TinyMicroscaledExperts
    from ..backends.tinygrad import _tg_e2m1
    from ..backends.tinygrad import _tg_e4m3
    from ..backends.tinygrad import _tg_pow2

    # the bits' arithmetic against the tables, every code (E4M3's two NaN codes aside: no stored value is one)
    codes = tg.Tensor(np.arange(256, dtype=np.uint8), device=ops.device)
    assert np.array_equal(_tg_e2m1(codes[:16].cast(tg.dtypes.uint32)).numpy(), e2m1_values())
    real = ~np.isnan(e4m3_values())
    assert np.array_equal(_tg_e4m3(codes).numpy()[real], e4m3_values()[real])
    assert np.array_equal(_tg_pow2(codes).numpy(), pow2_scale_values())

    rng = np.random.default_rng(2)
    f32 = ops.dtype('f32')
    E, N, K = 6, 8, 64
    for fmt in ('nvfp4', 'mxfp8'):
        mw = random_microscaled(rng, fmt, E, N, K)
        want = mw.dequantize()

        w = ops.microscaled(mw, f32, name=f'layers.0.{fmt}')
        assert isinstance(w, TinyMicroscaledExperts) and ops.nbytes(w) == mw.nbytes()

        # the decode is exact: a slice of the stack, a gather of rows' experts, one expert
        eids = np.asarray([3, 0, 5, 3], dtype=np.int32)
        assert np.array_equal(ops.numpy(w.dequant(f32, slice(0, E))), want)
        assert np.array_equal(ops.numpy(w.dequant(f32, tg.Tensor(eids, device=ops.device))), want[eids])
        assert np.array_equal(ops.numpy(ops.expert_dense(w, 4, f32)), want[4])

        # every row against its own expert, two slots a token
        x = rng.standard_normal((2, K)).astype(np.float32)
        got = ops.numpy(ops.expert_linear(ops.array(x, f32), w, tg.Tensor(eids, device=ops.device), 2))
        ref = np.einsum('rnk,rk->rn', want[eids].astype(np.float64), np.repeat(x, 2, 0).astype(np.float64))
        assert np.abs(got - ref).max() < 1e-5 * np.abs(ref).max(), fmt


def test_mlx_container_on_numpy():
    """
    The MLX container's decode and its products name no MLX function (backends/mlx_microscaled.py), so numpy's arrays
    stand in for MLX's: which table decodes which bytes, the nibbles' order, the block scales, the pieces and their
    order, against the reference decode -- wherever numpy runs. On MLX itself: test_mlx_container.
    """

    from ..backends.mlx_microscaled import mlx_microscaled_experts

    rng = np.random.default_rng(3)
    E, N, K = 6, 8, 64
    for fmt in ('nvfp4', 'mxfp8'):
        mw = random_microscaled(rng, fmt, E, N, K)
        want = mw.dequantize()

        w = mlx_microscaled_experts(mw, np.asarray)
        assert w.nbytes() == mw.nbytes()

        eids = np.asarray([3, 0, 5, 3, 1, 1, 4], dtype=np.int32)
        assert np.array_equal(w.dequant(np.float32, slice(0, E)), want)
        assert np.array_equal(w.dequant(np.float32, eids), want[eids])  # type: ignore[arg-type,unused-ignore]
        assert np.array_equal(w.dequant(np.float32, slice(4, 5))[0], want[4])

        # every row against its own expert, in pieces of every size up to all the rows at once
        x = rng.standard_normal((len(eids), K)).astype(np.float32)
        ref = np.einsum('rnk,rk->rn', want[eids].astype(np.float64), x.astype(np.float64))
        for step in (1, 2, 3, len(eids), 16):
            parts = w.products(x, eids, step)  # type: ignore[arg-type,unused-ignore]
            assert len(parts) == -(-len(eids) // step) and all(p.dtype == np.float32 for p in parts), (fmt, step)
            assert np.abs(np.concatenate(parts, 0) - ref).max() < 1e-5 * np.abs(ref).max(), (fmt, step)


def test_mlx_container():
    """
    The same on MLX, where it is installed: the bytes stay packed, the decode is exact, and every row meets its own
    expert -- at once, a few rows at a time, expert by expert, and inside a compiled step, in float32 and bfloat16.
    """

    try:
        import mlx.core as mx
    except ImportError:
        print('mlx not installed; skipping')
        return

    from ..backends.mlx import MlxOps
    from ..backends.mlx_microscaled import MlxMicroscaledExperts

    ops = MlxOps()
    rng = np.random.default_rng(2)
    f32 = ops.dtype('f32')
    E, N, K = 6, 8, 64
    for fmt in ('nvfp4', 'mxfp8'):
        mw = random_microscaled(rng, fmt, E, N, K)
        want = mw.dequantize()

        w = ops.microscaled(mw, f32)
        assert isinstance(w, MlxMicroscaledExperts) and ops.nbytes(w) == mw.nbytes()
        assert w.codes.dtype == mx.uint8 and w.scales.dtype == mx.uint8

        eids = np.asarray([3, 0, 5, 3], dtype=np.int32)
        assert np.array_equal(ops.numpy(w.dequant(f32, slice(0, E))), want)
        assert np.array_equal(ops.numpy(w.dequant(f32, ops.array(eids))), want[eids])
        assert np.array_equal(ops.numpy(ops.expert_dense(w, 4, f32)), want[4])

        # every row against its own expert, two slots a token
        x = rng.standard_normal((2, K)).astype(np.float32)
        rows = np.repeat(x, 2, 0)
        ref = np.einsum('rnk,rk->rn', want[eids].astype(np.float64), rows.astype(np.float64))
        scale = np.abs(ref).max()

        for step in (8, 3, 1):
            ops.microscaled_rows = step
            got = ops.numpy(ops.expert_linear(ops.array(x, f32), w, ops.array(eids), 2))
            assert np.abs(got - ref).max() < 1e-5 * scale, (fmt, step)

        got = ops.numpy(ops.expert_linear_grouped(ops.array(rows, f32), w, ops.array(eids)))
        assert np.abs(got - ref).max() < 1e-5 * scale, fmt

        # compiled, as a decode step has it: the experts are an input, and another step's are other experts
        compiled = ops.capture(lambda x_, eids_, w=w: (ops.expert_linear(x_, w, eids_, 2),))
        for picked in (eids, eids[::-1].copy()):
            got = ops.numpy(compiled(ops.array(x, f32), ops.array(picked))[0])
            ref_p = np.einsum('rnk,rk->rn', want[picked].astype(np.float64), rows.astype(np.float64))
            assert np.abs(got - ref_p).max() < 1e-5 * scale, fmt

        # the model's dtype on an accelerator: the weights rounded to bfloat16, the product in it
        bf16 = ops.dtype('bf16')
        got = ops.numpy(ops.expert_linear(ops.array(x, bf16), w, ops.array(eids), 2))
        assert np.abs(got - ref).max() < 3e-2 * scale, fmt


def _skip() -> bool:
    try:
        import torch  # noqa
    except ImportError:
        print('torch not installed; skipping')
        return True
    return False


@triton_modes('interpret', 'compiled')
def test_microscaled_kernels():
    """
    The expert GEMV and the dense decode for both formats, N off the row block and K at each tile width, against the
    container's composed decode (which is the numpy reference's, exactly); and TorchOps.expert_linear on the packed
    stack -- by the kernel on CUDA, row by row or expert by expert elsewhere -- against the dense stack.
    """

    if _skip():
        return

    import torch

    from ..backends.torch import TorchMicroscaledExperts
    from ..backends.torch import TorchOps
    from ..backends.torch_triton import mdequantize
    from ..backends.torch_triton import mgemv_experts

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    ops = TorchOps(device)
    rng = np.random.default_rng(1)
    E = 6

    for fmt in ('nvfp4', 'mxfp8'):
        for n, k in ((96, 256), (40, 192), (70, 32)):  # K tiles of 128, 64 and 32
            mw = random_microscaled(rng, fmt, E, n, k)
            w = ops.microscaled(mw, torch.float32)
            assert isinstance(w, TorchMicroscaledExperts)

            dense = torch.from_numpy(mw.dequantize()).to(device)
            assert torch.equal(w.dequant(torch.float32, torch.arange(E, device=device)), dense), (fmt, n, k)

            for e in (0, E - 1):
                got = mdequantize(
                    w.codes[e],
                    w.scales[e],
                    w.outer[e:e + 1] if w.outer is not None else None,
                    w.code_table,
                    w.scale_table,
                    w.block,
                    w.shape,
                    torch.float32,
                )
                assert ((got - dense[e]).abs().max() / dense[e].abs().max()).item() < 1e-6, (fmt, n, k, e)
                assert torch.allclose(ops.expert_dense(w, e, torch.float32), dense[e], rtol=1e-6, atol=0)

            for x_div in (1, 3):
                rows = 7 * x_div
                x = torch.from_numpy(rng.standard_normal((rows // x_div, k)).astype(np.float32)).to(device)
                eids = torch.from_numpy(rng.integers(0, E, rows)).to(device)
                ref = torch.stack([x[r // x_div] @ dense[int(eids[r])].T for r in range(rows)])

                y = mgemv_experts(
                    x,
                    eids.to(torch.int32),
                    w.codes,
                    w.scales,
                    w.outer,
                    w.code_table,
                    w.scale_table,
                    w.block,
                    w.shape,
                    x_div=x_div,
                )
                assert ((y - ref).abs().max() / ref.abs().max()).item() < 1e-5, (fmt, n, k, x_div)

                via_ops = ops.expert_linear(x, w, eids, x_div)
                assert ((via_ops - ref).abs().max() / ref.abs().max()).item() < 1e-5, (fmt, n, k, x_div)

            # many rows: expert by expert, each decoded once
            x = torch.from_numpy(rng.standard_normal((300, k)).astype(np.float32)).to(device)
            eids = torch.from_numpy(rng.integers(0, E, 300)).to(device)
            ref = torch.stack([x[r] @ dense[int(eids[r])].T for r in range(300)])
            for got in (ops.expert_linear(x, w, eids), ops.expert_linear_grouped(x, w, eids)):
                assert ((got - ref).abs().max() / ref.abs().max()).item() < 1e-5, (fmt, n, k, 'grouped')

    print(f'microscaled expert GEMV and dense decode == the reference decode on {device}')
