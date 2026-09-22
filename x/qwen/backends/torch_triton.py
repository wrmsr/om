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
planes, which avoids interleaving in registers. Scales are loaded once per group ([BLOCK_N, groups per block])
and broadcast over the group through a reshape, never gathered per element. Larger M (prefill) is compute-bound
and should keep using dequant + cuBLAS; `TorchOps.linear` switches at `triton_max_m`.

Shared memory: the software pipeline stages every load that feeds a `tl.dot`, so the per-stage footprint is the
x tiles plus the dequantized weight tiles in the activation dtype. At BLOCK_N=32, BLOCK_K=128 that is ~14 KB (bf16)
or ~26 KB (f32) per stage; consumer Blackwell (sm_120) allows ~99 KB per block, so BLOCK_K=256 with 3 stages in
f32 does not fit -- keep BLOCK_K at 128 and let f32 use 2 stages.

With `TRITON_INTERPRET=1` the kernel runs on CPU through Triton's numpy interpreter (slow, f32 only), which is
how `tests/test_triton.py` checks it without a GPU.
"""
import dataclasses as dc
import json
import pathlib
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

# (dtype, bits) -> (block_k, num_stages) that compiled; filled in by `qlinear` when a launch runs out of shared
# memory and a smaller configuration is tried instead
_RESOLVED: dict[tuple[ta.Any, int], tuple[int, int]] = {}


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
            SPLIT_K: tl.constexpr,
            IEEE: tl.constexpr,
    ):
        pid_n = tl.program_id(0)
        pid_m = tl.program_id(1)
        pid_s = tl.program_id(2)  # split-K slice; partial sums land in y[pid_s]
        rm = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)
        rn = pid_n * BLOCK_N + tl.arange(0, BLOCK_N)
        m_mask = rm < M
        n_mask = rn < N
        n_groups = K // GROUP
        k_lo = pid_s * (K // SPLIT_K)
        k_hi = k_lo + K // SPLIT_K
        acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)

        G: tl.constexpr = BLOCK_K // GROUP  # groups per K block
        rg = tl.arange(0, G)

        if BITS == 4:
            KB: tl.constexpr = BLOCK_K // 2  # packed bytes per row per block
            GB: tl.constexpr = GROUP // 2  # packed bytes per group
            rb = tl.arange(0, KB)
            for k0 in range(k_lo, k_hi, BLOCK_K):
                kb = k0 // 2 + rb  # byte columns
                ke = k0 + 2 * rb  # even element columns; odd = ke + 1
                gcol = k0 // GROUP + rg  # [G] group columns of the scale plane
                q = tl.load(q_ptr + rn[:, None] * (K // 2) + kb[None, :], mask=n_mask[:, None], other=0)
                s = tl.load(s_ptr + rn[:, None] * n_groups + gcol[None, :], mask=n_mask[:, None], other=0.0)
                b = tl.load(b_ptr + rn[:, None] * n_groups + gcol[None, :], mask=n_mask[:, None], other=0.0)
                s = s.to(tl.float32)[:, :, None]  # [BLOCK_N, G, 1]
                b = b.to(tl.float32)[:, :, None]
                lo = tl.reshape((q & 0xF).to(tl.float32), (BLOCK_N, G, GB)) * s + b
                hi = tl.reshape((q >> 4).to(tl.float32), (BLOCK_N, G, GB)) * s + b
                lo = tl.reshape(lo, (BLOCK_N, KB))  # w[:, even]
                hi = tl.reshape(hi, (BLOCK_N, KB))  # w[:, odd]
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
            for k0 in range(k_lo, k_hi, BLOCK_K):
                rk = k0 + rk0
                gcol = k0 // GROUP + rg
                q = tl.load(q_ptr + rn[:, None] * K + rk[None, :], mask=n_mask[:, None], other=0)
                s = tl.load(s_ptr + rn[:, None] * n_groups + gcol[None, :], mask=n_mask[:, None], other=0.0)
                b = tl.load(b_ptr + rn[:, None] * n_groups + gcol[None, :], mask=n_mask[:, None], other=0.0)
                s = s.to(tl.float32)[:, :, None]
                b = b.to(tl.float32)[:, :, None]
                w = tl.reshape(q.to(tl.float32), (BLOCK_N, G, GROUP)) * s + b
                w = tl.reshape(w, (BLOCK_N, BLOCK_K))
                xt = tl.load(x_ptr + rm[:, None] * stride_xm + rk[None, :], mask=m_mask[:, None], other=0.0)
                if IEEE:
                    acc = tl.dot(xt, tl.trans(w.to(xt.dtype)), acc, input_precision='ieee')
                else:
                    acc = tl.dot(xt, tl.trans(w.to(xt.dtype)), acc)

        y = acc.to(y_ptr.dtype.element_ty)
        y_base = y_ptr + pid_s * M * stride_ym
        tl.store(y_base + rm[:, None] * stride_ym + rn[None, :], y, mask=m_mask[:, None] & n_mask[None, :])


def _block_k(k: int, cap: int = 128) -> int:
    for bk in (256, 128, 64):
        if bk <= cap and k % bk == 0:
            return bk
    raise ValueError(f'K={k} is not a multiple of 64')


@dc.dataclass(frozen=True)
class GemvConfig:
    block_n: int = 32
    block_k: int = 128
    num_warps: int = 4
    num_stages: int = 3
    split_k: int = 1


# (N, K, bits) -> config, filled by `tune` / `load_tuned`; consulted before the heuristics
TUNED: dict[tuple[int, int, int], GemvConfig] = {}


def default_config(n: int, k: int, bits: int, dtype: torch.dtype) -> GemvConfig:
    """Heuristic when nothing is tuned: enough programs to fill the GPU. Narrow outputs (N=5120 at
    block_n=32 is 160 programs) get split-K so the K loop is shared across several programs."""

    block_n = 32 if n <= 8192 else 64
    programs = triton.cdiv(n, block_n)
    split = 1
    while programs * split < 512 and split < 8 and k % (_block_k(k) * split * 2) == 0:
        split *= 2
    return GemvConfig(block_n, _block_k(k), 4, 2 if dtype == torch.float32 else 3, split)


def load_tuned(path: str | pathlib.Path) -> int:
    """Read a JSON written by `tune` into TUNED; returns the number of entries."""

    p = pathlib.Path(path).expanduser()
    if not p.exists():
        return 0
    for e in json.loads(p.read_text()):
        TUNED[(e['n'], e['k'], e['bits'])] = GemvConfig(**e['config'])
    return len(TUNED)


def save_tuned(path: str | pathlib.Path) -> None:
    p = pathlib.Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(
        [{'n': n, 'k': k, 'bits': b, 'config': dc.asdict(c)} for (n, k, b), c in sorted(TUNED.items())],
        indent=1,
    ))


def qlinear(
        x: torch.Tensor,
        q: torch.Tensor,
        scale: torch.Tensor,
        bias: torch.Tensor,
        bits: int,
        group: int,
        shape: tuple[int, int],
        config: GemvConfig | None = None,
        block_n: int | None = None,
) -> torch.Tensor:
    """
    x [..., K] @ w.T -> [..., N] in x's dtype, w given as packed codes + per-group scale/bias.

    The launch configuration comes from `config`, else `TUNED[(N, K, bits)]` (see `tune`), else
    `default_config`. split_k > 1 runs the K loop on several programs and sums float32 partials (one extra
    tiny kernel); it is what makes the narrow projections (o_proj, down_proj, out_proj: N=5120) fill the GPU.
    `block_n` overrides that one field of the config (kept for TorchOps.triton_block_n).
    """

    if not HAVE_TRITON:
        raise RuntimeError('triton is not installed')
    n, k = shape
    cfg = config or TUNED.get((n, k, bits)) or default_config(n, k, bits, x.dtype)
    if block_n is not None:
        cfg = dc.replace(cfg, block_n=block_n)
    x2 = x.reshape(-1, k)
    if x2.stride(1) != 1:
        x2 = x2.contiguous()
    m = x2.shape[0]
    bk = _block_k(k, cfg.block_k)
    split = cfg.split_k
    while split > 1 and k % (bk * split):
        split //= 2
    num_stages = cfg.num_stages
    while True:
        y = torch.empty((split, m, n), dtype=torch.float32 if split > 1 else x.dtype, device=x.device)
        grid = (triton.cdiv(n, cfg.block_n), triton.cdiv(m, 16), split)
        try:
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
                y.stride(1),
                BITS=bits,
                GROUP=group,
                BLOCK_M=16,
                BLOCK_N=cfg.block_n,
                BLOCK_K=bk,
                SPLIT_K=split,
                IEEE=(x.dtype == torch.float32),
                num_warps=cfg.num_warps,
                num_stages=num_stages,
            )
        except triton.runtime.errors.OutOfResources:
            # shared memory: shrink the stage first, then the pipeline depth
            if bk > 64 and k % (bk // 2) == 0:
                bk //= 2
            elif num_stages > 1:
                num_stages -= 1
            else:
                raise
            continue
        out = y.sum(0).to(x.dtype) if split > 1 else y[0]
        return out.reshape(*x.shape[:-1], n)


def tune(
        shapes: ta.Iterable[tuple[int, int]],
        bits: int,
        dtype: torch.dtype = torch.bfloat16,
        m: int = 1,
        group: int = 64,
        device: str = 'cuda',
        log: ta.Callable[[str], None] | None = print,
) -> dict[tuple[int, int, int], GemvConfig]:
    """
    Sweep launch configurations per (N, K) on the current GPU, keep the fastest in TUNED and return them.
    Prints achieved GB/s of packed-weight traffic per shape (the number to compare against the card's
    bandwidth). Each configuration is a Triton compile (~1 s), so the sweep is kept to ~16-64 per shape: a few
    minutes for the ~9 distinct shapes of a model.
    """

    import itertools
    import time

    out: dict[tuple[int, int, int], GemvConfig] = {}
    for n, k in shapes:
        w = torch.randn(n, k, device=device) * 0.05
        from .torch import TorchOps

        ops = TorchOps(device)
        qw = ops.quantize(w.cpu().numpy(), bits, group, dtype)
        x = torch.randn(m, k, device=device, dtype=dtype)
        ref = None
        best: tuple[float, GemvConfig] | None = None
        nbytes = qw.q.numel() + qw.scale.numel() * qw.scale.element_size() * 2
        bns = (16, 32) if n <= 2048 else (32, 64) if n <= 8192 else (64, 128)
        bks = tuple(b for b in (128, 256) if k % b == 0) or (64,)
        sks = (1, 2, 4, 8) if n <= 8192 else (1,)
        for bn, bk, nw, ns, sk in itertools.product(bns, bks, (4, 8), (2, 3), sks):
            if k % (bk * sk):
                continue
            cfg = GemvConfig(bn, bk, nw, ns, sk)
            try:
                y = qlinear(x, qw.q, qw.scale, qw.bias, bits, group, (n, k), config=cfg)
                torch.cuda.synchronize()
                if ref is None:
                    ref = (x.float() @ qw.dequant(torch.float32).T)
                if ((y.float() - ref).abs().max() / ref.abs().max()).item() > 3e-2:
                    continue  # a config that compiles but computes wrong is a bug; skip it loudly below
                for _ in range(2):
                    qlinear(x, qw.q, qw.scale, qw.bias, bits, group, (n, k), config=cfg)
                torch.cuda.synchronize()
                t0 = time.perf_counter()
                for _ in range(10):
                    qlinear(x, qw.q, qw.scale, qw.bias, bits, group, (n, k), config=cfg)
                torch.cuda.synchronize()
                dt = (time.perf_counter() - t0) / 10
            except triton.runtime.errors.OutOfResources:
                continue
            if best is None or dt < best[0]:
                best = (dt, cfg)
        if best is None:
            raise RuntimeError(f'no working configuration for N={n} K={k}')
        dt, cfg = best
        out[(n, k, bits)] = cfg
        TUNED[(n, k, bits)] = cfg
        if log:
            log(f'N={n:7d} K={k:6d} int{bits}: {dt * 1e6:7.1f} us  {nbytes / dt / 1e9:7.0f} GB/s  {cfg}')
    return out
