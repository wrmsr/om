# ruff: noqa: N803 N806
"""
The Triton kernel for the Qwen families' fused DeltaNet step (base.py's `QwenOps.gdn_step`, its definition and what
tests/test_torch.py holds the kernel to).

Conventions are backends/torch_triton.py's: the kernel body is a plain function, jitted into a module global by
`ensure_qwen_kernels` (so a torch.compile trace of the wrapper finds a `JITFunction` and lowers the launch as a
user-defined kernel), and the integer arguments that follow a prompt's length are kept out of its specializations.
"""
import importlib
import typing as ta

from omcore import lang

from ....backends.torch_triton import HAVE_TRITON


if ta.TYPE_CHECKING:
    import torch  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import triton  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import triton.language as tl  # type: ignore[import-not-found,import-untyped,unused-ignore]
else:
    torch = lang.proxy_import('torch')
    triton = lang.proxy_import('triton')
    tl = lang.proxy_import('triton.language')


##


def _gdn_step_kernel(
        q_ptr,
        k_ptr,
        v_ptr,
        a_ptr,
        b_ptr,
        A_ptr,
        dt_ptr,
        s_in_ptr,
        out_ptr,
        s_out_ptr,
        sq_b,
        sq_t,
        sq_h,
        sv_b,
        sv_t,
        sv_h,
        sa_b,
        sa_t,
        ss_b,
        ss_h,
        so_b,
        so_t,
        so_h,
        ss_out_t,
        Hv,
        R,
        T,
        DK: tl.constexpr,
        DV: tl.constexpr,
        BLOCK_DV: tl.constexpr,
        ALL_STATES: tl.constexpr,
        EPS: tl.constexpr,
        QSCALE: tl.constexpr,
):
    """
    The Gated DeltaNet recurrence over T tokens, any T: a decode step (1), a speculative verify (k + 1, with the state
    after every token), a prefill chunk (thousands). A program owns a [DK, BLOCK_DV] slice of one head's state in
    registers for the whole run, so the serial chain per token is two reductions and a rank-1 update: ~1 us a token on
    a 5090 however many heads there are. Each token's inputs are read through pointers advanced a token at a time, so
    no offset is ever T times a stride (a long chunk cannot overflow 32 bits, and the interpreter's plain-int loop
    variable needs no cast).
    """

    pid = tl.program_id(0)  # b * Hv + h
    pid_v = tl.program_id(1)  # slice of the value dim
    bidx = pid // Hv
    h = pid % Hv
    kh = h // R  # the key head this value head reads
    rk = tl.arange(0, DK)
    rv = pid_v * BLOCK_DV + tl.arange(0, BLOCK_DV)
    s_off = bidx * ss_b + h * ss_h + rk[:, None] * DV + rv[None, :]
    S = tl.load(s_in_ptr + s_off)  # [DK, BLOCK_DV] float32, held in registers for all T tokens
    A_h = tl.load(A_ptr + h)
    dt_h = tl.load(dt_ptr + h)
    q_p = q_ptr + bidx * sq_b + kh * sq_h + rk
    k_p = k_ptr + bidx * sq_b + kh * sq_h + rk
    v_p = v_ptr + bidx * sv_b + h * sv_h + rv
    a_p = a_ptr + bidx * sa_b + h
    b_p = b_ptr + bidx * sa_b + h
    o_p = out_ptr + bidx * so_b + h * so_h + rv
    st_p = s_out_ptr + s_off
    for _ in range(T):
        qv = tl.load(q_p).to(tl.float32)
        kv = tl.load(k_p).to(tl.float32)
        qn = qv * tl.rsqrt(tl.sum(qv * qv, 0) + EPS) * QSCALE
        kn = kv * tl.rsqrt(tl.sum(kv * kv, 0) + EPS)
        vt = tl.load(v_p).to(tl.float32)
        a_t = tl.load(a_p).to(tl.float32)
        b_t = tl.load(b_p).to(tl.float32)
        beta = tl.sigmoid(b_t)
        xg = a_t + dt_h
        sp = tl.where(xg > 20.0, xg, tl.log(1.0 + tl.exp(tl.minimum(xg, 20.0))))
        S = S * tl.exp(A_h * sp)  # decay
        mem = tl.sum(S * kn[:, None], 0)  # k^T S -> [BLOCK_DV]
        delta = (vt - mem) * beta
        S = S + kn[:, None] * delta[None, :]  # rank-1 update
        o = tl.sum(S * qn[:, None], 0)  # q^T S
        tl.store(o_p, o)
        if ALL_STATES:
            tl.store(st_p, S)
            st_p += ss_out_t
        q_p += sq_t
        k_p += sq_t
        v_p += sv_t
        a_p += sa_t
        b_p += sa_t
        o_p += so_t
    if not ALL_STATES:
        tl.store(st_p, S)


def gdn_step(
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        a: torch.Tensor,
        b: torch.Tensor,
        A: torch.Tensor,
        dt_bias: torch.Tensor,
        state: torch.Tensor,
        all_states: bool,
        eps: float = 1e-6,
        block_dv: int = 16,
        num_warps: int = 1,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Fused DeltaNet step (the whole of `QwenOps.gdn_step`) for any number of tokens in one launch per layer: each program
    owns a [dk, block_dv] slice of one head's state in registers, runs the T-token recurrence on it -- l2-norm of q/k,
    beta and the decay computed in-kernel, key heads broadcast by index -- and writes the outputs and either the final
    state or the state after every token. At T = 1 it replaces ~25 small kernels (and ~24 MB of state traffic per layer)
    with one that reads and writes the 3 MB state once; over a prefill chunk it replaces the chunked form's ~1000
    launches per layer (4096 tokens of the 27B's geometry: 4 ms against 33).

    Numerically it is the recurrence itself, token by token in float32 -- exactly what decode computes, so a prefill
    leaves the state decoding the same tokens would have (a run split anywhere is bitwise the whole run). Its rounding
    accumulates with the run: against a float64 recurrence on the 27B's activations, ~3e-6 relative over 4096 tokens,
    where the chunked WY form (64x fewer state updates) is at ~2e-7 -- and with fast-decaying random inputs the order
    reverses (2e-7 against the WY form's cancellation, 3e-6). Either is three orders under the bf16 the model
    computes in: swapping one for the other moves the 27B's outputs no more than re-chunking the same prefill does.

    q, k: [B, T, Hk, dk]; v: [B, T, Hv, dv]; a, b: [B, T, Hv]; A, dt_bias: [Hv]; state: [B, Hv, dk, dv] float32.

    block_dv 16 with one warp is the fastest launch at every T on a 5090 and a 5080 (the chain is serial per program,
    so small tiles in one warp -- no cross-warp reductions -- beat more threads): 2.7 us at T = 1, ~0.9 us a token
    from there.
    """

    if not HAVE_TRITON:
        raise RuntimeError('triton is not installed')
    B, T, Hk, dk = q.shape
    Hv = v.shape[2]
    dv = v.shape[3]
    if q.stride(-1) != 1:
        q = q.contiguous()
    if k.stride(-1) != 1:
        k = k.contiguous()
    if v.stride(-1) != 1:
        v = v.contiguous()
    a = a.contiguous()
    b = b.contiguous()
    state = state.contiguous()
    out = torch.empty((B, T, Hv, dv), dtype=torch.float32, device=q.device)
    if all_states:
        s_out = torch.empty((T, B, Hv, dk, dv), dtype=torch.float32, device=q.device)
        ss_out_t = s_out.stride(0)
    else:
        s_out = torch.empty((B, Hv, dk, dv), dtype=torch.float32, device=q.device)
        ss_out_t = 0
    block_dv = min(block_dv, dv)
    if dv % block_dv:
        raise ValueError(f'dv={dv} is not a multiple of block_dv={block_dv}')
    grid = (B * Hv, dv // block_dv)
    ensure_qwen_kernels()
    _gdn_jit[grid](
        q,
        k,
        v,
        a,
        b,
        A,
        dt_bias,
        state,
        out,
        s_out,
        q.stride(0),
        q.stride(1),
        q.stride(2),
        v.stride(0),
        v.stride(1),
        v.stride(2),
        a.stride(0),
        a.stride(1),
        state.stride(0),
        state.stride(1),
        out.stride(0),
        out.stride(1),
        out.stride(2),
        ss_out_t,
        Hv,
        Hv // Hk,
        T,
        DK=dk,
        DV=dv,
        BLOCK_DV=block_dv,
        ALL_STATES=all_states,
        EPS=eps,
        QSCALE=dk**-0.5,
        num_warps=num_warps,
    )
    return out, s_out


##


# (a module global, as backends/torch_triton.py's are and for its reason: a traced wrapper must find a plain
# `JITFunction`)
_gdn_jit: ta.Any = None


def ensure_qwen_kernels() -> None:
    """Jit the kernel (once); until then nothing here has imported triton or torch."""

    global _gdn_jit

    if _gdn_jit is not None:
        return

    g = globals()
    g['triton'] = importlib.import_module('triton')
    g['tl'] = importlib.import_module('triton.language')

    # (no alignment variants for the arguments that follow a prompt's length: see backends/torch_triton.py's
    # `ensure_kernels`)
    _gdn_jit = triton.jit(
        _gdn_step_kernel,
        do_not_specialize_on_alignment=['sq_b', 'sv_b', 'sa_b', 'so_b', 'T'],
    )


def gdn_kernel_variants() -> int:
    """
    How many variants Triton has compiled of the kernel in this process: what a test counts to see that prompt
    lengths do not multiply them. 0 before it is first launched, and under the interpreter, which compiles nothing.
    """

    return sum(len(caches[0]) for caches in getattr(_gdn_jit, 'device_caches', {}).values())
