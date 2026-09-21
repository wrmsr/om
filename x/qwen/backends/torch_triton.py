"""
Triton kernel for `TorchQWeight`: y = x @ dequant(w).T without materialising dequant(w).

Decode is memory-bound, and `TorchQWeight.linear` expands the weight to bf16 before every matmul, so a step reads
~2.5 bytes per parameter instead of 0.5 (int4) or 1 (int8). This kernel reads the packed codes once, dequantizes in
registers and feeds the tensor cores directly, so the traffic is the packed weight plus a few scales.

Layout is quant.QWeight's: q uint8 [N, K] (int8) or [N, K // 2] (int4, low nibble = even k, high nibble = odd k);
scale, bias [N, K // GROUP] in the compute dtype; w = q * scale + bias.

Each program computes a [BLOCK_M, BLOCK_N] output tile over the whole K axis. BLOCK_M is 16 (the tensor-core
minimum); rows beyond M are masked to zero, so M == 1 runs the same code and simply wastes lanes it was not going
to use anyway. For int4 the even and odd elements are two separate `tl.dot`s against the low- and high-nibble
planes, which avoids interleaving in registers. Larger M (prefill) is compute-bound and should keep using
dequant + cuBLAS; `TorchOps.linear` switches at `triton_max_m`.

With `TRITON_INTERPRET=1` the kernel runs on CPU through Triton's numpy interpreter (slow, f32 only), which is
how `tests/test_triton.py` checks it without a GPU.
"""
import typing as ta

import torch

try:
    import triton
    import triton.language as tl
except ImportError:  # pragma: no cover
    triton = None  # type: ignore[assignment]
    tl = None  # type: ignore[assignment]


##


HAVE_TRITON = triton is not None


if HAVE_TRITON:

    @triton.jit
    def _qlinear_kernel(
            x_ptr,
            q_ptr,
            s_ptr,
            b_ptr,
            y_ptr,
            M,
            N,
            K,
            stride_xm,
            stride_ym,
            BITS: tl.constexpr,
            GROUP: tl.constexpr,
            BLOCK_M: tl.constexpr,
            BLOCK_N: tl.constexpr,
            BLOCK_K: tl.constexpr,
            IEEE: tl.constexpr,
    ):
        pid_n = tl.program_id(0)
        pid_m = tl.program_id(1)
        rm = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)
        rn = pid_n * BLOCK_N + tl.arange(0, BLOCK_N)
        m_mask = rm < M
        n_mask = rn < N
        n_groups = K // GROUP
        acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)

        if BITS == 4:
            KB: tl.constexpr = BLOCK_K // 2  # packed bytes per row per block
            rb = tl.arange(0, KB)
            for k0 in range(0, K, BLOCK_K):
                kb = k0 // 2 + rb  # byte columns
                ke = k0 + 2 * rb  # even element columns; odd = ke + 1
                g = ke // GROUP
                q = tl.load(q_ptr + rn[:, None] * (K // 2) + kb[None, :], mask=n_mask[:, None], other=0)
                s = tl.load(s_ptr + rn[:, None] * n_groups + g[None, :], mask=n_mask[:, None], other=0.0)
                b = tl.load(b_ptr + rn[:, None] * n_groups + g[None, :], mask=n_mask[:, None], other=0.0)
                s = s.to(tl.float32)
                b = b.to(tl.float32)
                lo = (q & 0xF).to(tl.float32) * s + b  # [BLOCK_N, KB]  w[:, even]
                hi = (q >> 4).to(tl.float32) * s + b  # [BLOCK_N, KB]  w[:, odd]
                xe = tl.load(x_ptr + rm[:, None] * stride_xm + ke[None, :], mask=m_mask[:, None], other=0.0)
                xo = tl.load(x_ptr + rm[:, None] * stride_xm + (ke + 1)[None, :], mask=m_mask[:, None], other=0.0)
                if IEEE:
                    acc = tl.dot(xe, tl.trans(lo.to(xe.dtype)), acc, input_precision='ieee')
                    acc = tl.dot(xo, tl.trans(hi.to(xo.dtype)), acc, input_precision='ieee')
                else:
                    acc = tl.dot(xe, tl.trans(lo.to(xe.dtype)), acc)
                    acc = tl.dot(xo, tl.trans(hi.to(xo.dtype)), acc)
        else:
            rk0 = tl.arange(0, BLOCK_K)
            for k0 in range(0, K, BLOCK_K):
                rk = k0 + rk0
                g = rk // GROUP
                q = tl.load(q_ptr + rn[:, None] * K + rk[None, :], mask=n_mask[:, None], other=0)
                s = tl.load(s_ptr + rn[:, None] * n_groups + g[None, :], mask=n_mask[:, None], other=0.0)
                b = tl.load(b_ptr + rn[:, None] * n_groups + g[None, :], mask=n_mask[:, None], other=0.0)
                w = q.to(tl.float32) * s.to(tl.float32) + b.to(tl.float32)  # [BLOCK_N, BLOCK_K]
                xt = tl.load(x_ptr + rm[:, None] * stride_xm + rk[None, :], mask=m_mask[:, None], other=0.0)
                if IEEE:
                    acc = tl.dot(xt, tl.trans(w.to(xt.dtype)), acc, input_precision='ieee')
                else:
                    acc = tl.dot(xt, tl.trans(w.to(xt.dtype)), acc)

        y = acc.to(y_ptr.dtype.element_ty)
        tl.store(y_ptr + rm[:, None] * stride_ym + rn[None, :], y, mask=m_mask[:, None] & n_mask[None, :])


def _block_k(k: int) -> int:
    for bk in (256, 128, 64):
        if k % bk == 0:
            return bk
    raise ValueError(f'K={k} is not a multiple of 64')


def qlinear(
        x: torch.Tensor,
        q: torch.Tensor,
        scale: torch.Tensor,
        bias: torch.Tensor,
        bits: int,
        group: int,
        shape: tuple[int, int],
        block_n: int | None = None,
        num_warps: int = 4,
) -> torch.Tensor:
    """
    x [..., K] @ w.T -> [..., N] in x's dtype, w given as packed codes + per-group scale/bias.

    block_n defaults to 32 for narrow outputs (a 5120-wide projection is only 160 programs even then; a split-K
    variant is the next step for those) and 64 otherwise. These two knobs and `num_warps` are untuned guesses --
    sweep them on the target GPU.
    """

    if not HAVE_TRITON:
        raise RuntimeError('triton is not installed')
    n, k = shape
    if block_n is None:
        block_n = 32 if n <= 8192 else 64
    x2 = x.reshape(-1, k)
    if x2.stride(1) != 1:
        x2 = x2.contiguous()
    m = x2.shape[0]
    y = torch.empty((m, n), dtype=x.dtype, device=x.device)
    grid = (triton.cdiv(n, block_n), triton.cdiv(m, 16))
    _qlinear_kernel[grid](
        x2,
        q,
        scale,
        bias,
        y,
        m,
        n,
        k,
        x2.stride(0),
        y.stride(0),
        BITS=bits,
        GROUP=group,
        BLOCK_M=16,
        BLOCK_N=block_n,
        BLOCK_K=_block_k(k),
        IEEE=(x.dtype == torch.float32),
        num_warps=num_warps,
    )
    return y.reshape(*x.shape[:-1], n)
