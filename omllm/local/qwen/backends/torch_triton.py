# ruff: noqa: N803 N806 N812
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
import json
import pathlib
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang


if ta.TYPE_CHECKING:
    import torch  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import triton  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import triton.language as tl  # type: ignore[import-not-found,import-untyped,unused-ignore]
else:
    torch = lang.proxy_import('torch')
    triton = lang.proxy_import('triton')
    tl = lang.proxy_import('triton.language')


##


HAVE_TRITON = lang.can_import('triton')  # found, not imported: the kernels are jitted on first use

# (N, K, bits, dtype, config) -> (block_k, num_stages, split_k) that launched successfully; filled by `_resolve`, which
# is the only place a launch may fail and be retried smaller (keeps try/except out of the traced hot path)
_RESOLVED: dict[tuple[ta.Any, ...], tuple[int, int, int]] = {}


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
        T: tl.constexpr,
        DK: tl.constexpr,
        DV: tl.constexpr,
        BLOCK_DV: tl.constexpr,
        ALL_STATES: tl.constexpr,
        EPS: tl.constexpr,
        QSCALE: tl.constexpr,
):
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
    for t in tl.static_range(T):
        qv = tl.load(q_ptr + bidx * sq_b + t * sq_t + kh * sq_h + rk).to(tl.float32)
        kv = tl.load(k_ptr + bidx * sq_b + t * sq_t + kh * sq_h + rk).to(tl.float32)
        qn = qv * tl.rsqrt(tl.sum(qv * qv, 0) + EPS) * QSCALE
        kn = kv * tl.rsqrt(tl.sum(kv * kv, 0) + EPS)
        vt = tl.load(v_ptr + bidx * sv_b + t * sv_t + h * sv_h + rv).to(tl.float32)
        a_t = tl.load(a_ptr + bidx * sa_b + t * sa_t + h).to(tl.float32)
        b_t = tl.load(b_ptr + bidx * sa_b + t * sa_t + h).to(tl.float32)
        beta = tl.sigmoid(b_t)
        xg = a_t + dt_h
        sp = tl.where(xg > 20.0, xg, tl.log(1.0 + tl.exp(tl.minimum(xg, 20.0))))
        S = S * tl.exp(A_h * sp)  # decay
        mem = tl.sum(S * kn[:, None], 0)  # k^T S -> [BLOCK_DV]
        delta = (vt - mem) * beta
        S = S + kn[:, None] * delta[None, :]  # rank-1 update
        o = tl.sum(S * qn[:, None], 0)  # q^T S
        tl.store(out_ptr + bidx * so_b + t * so_t + h * so_h + rv, o)
        if ALL_STATES:
            tl.store(s_out_ptr + t * ss_out_t + s_off, S)
    if not ALL_STATES:
        tl.store(s_out_ptr + s_off, S)


def _attn_decode_kernel(
        q_ptr,
        k_ptr,
        v_ptr,
        ks_ptr,
        vs_ptr,
        pos_ptr,
        m_ptr,
        l_ptr,
        o_ptr,
        stride_qb,
        stride_qh,
        stride_qt,
        stride_kb,
        stride_kh,
        stride_kl,
        stride_ob,
        stride_oh,
        stride_os,
        stride_om,
        stride_mb,
        stride_mh,
        stride_ms,
        stride_sb,
        stride_sh,
        scale,
        T,
        G,
        KV,
        BLOCK_M: tl.constexpr,
        BLOCK_N: tl.constexpr,
        D: tl.constexpr,
        SPLITS: tl.constexpr,
        IEEE: tl.constexpr,
        FP8: tl.constexpr,
):
    """
    Decode attention over the static KV buffer that reads only the positions in use: the number of key blocks comes from
    `pos` (a device scalar) at run time, so one fixed CUDA graph serves every sequence length and the work grows with
    the sequence, not the capacity. One program per (batch, kv head, split): its rows are that kv head's G query heads x
    T tokens (row g*T + t), it walks its share of the key blocks up to pos + T with an online softmax, and writes
    partial (max, sum, acc); the wrapper merges the SPLITS partials (flash-decoding). Query row (g, t) may see keys <=
    pos + t. With FP8 the buffers hold e4m3 codes and ks / vs the per-position scales: a key's score is the dot with
    its codes times its scale, a value is its codes times its scale.
    """

    pid = tl.program_id(0)
    s = tl.program_id(1)
    b = pid // KV
    kvh = pid % KV
    rm = tl.arange(0, BLOCK_M)
    rd = tl.arange(0, D)
    g_of = rm // T
    t_of = rm % T
    row_ok = rm < G * T
    q_off = b * stride_qb + (kvh * G + g_of)[:, None] * stride_qh + t_of[:, None] * stride_qt + rd[None, :]
    q = tl.load(q_ptr + q_off, mask=row_ok[:, None], other=0.0)  # [BLOCK_M, D]
    pos = tl.load(pos_ptr)
    n_valid = pos + T
    n_blocks = (n_valid + BLOCK_N - 1) // BLOCK_N
    per = (n_blocks + SPLITS - 1) // SPLITS
    blk_lo = s * per
    blk_hi = tl.minimum(blk_lo + per, n_blocks)
    m_i = tl.full([BLOCK_M], float('-inf'), tl.float32)
    l_i = tl.zeros([BLOCK_M], tl.float32)
    acc = tl.zeros([BLOCK_M, D], tl.float32)
    kv_base = b * stride_kb + kvh * stride_kh
    for blk in range(blk_lo, blk_hi):
        j = blk * BLOCK_N + tl.arange(0, BLOCK_N)
        kmask = j < n_valid
        kv_off = kv_base + j[:, None] * stride_kl + rd[None, :]
        k = tl.load(k_ptr + kv_off, mask=kmask[:, None], other=0.0)  # [BLOCK_N, D]
        if FP8:
            k = k.to(q.dtype)
        if IEEE:
            sc = tl.dot(q, tl.trans(k), input_precision='ieee') * scale
        else:
            sc = tl.dot(q, tl.trans(k)) * scale
        if FP8:
            ksc = tl.load(ks_ptr + b * stride_sb + kvh * stride_sh + j, mask=kmask, other=0.0)
            sc = sc * ksc[None, :]
        allowed = (j[None, :] <= (pos + t_of)[:, None]) & kmask[None, :]
        sc = tl.where(allowed, sc, float('-inf'))
        m_new = tl.maximum(m_i, tl.max(sc, 1))
        m_safe = tl.where(m_new == float('-inf'), 0.0, m_new)  # rows with no key yet: keep p = 0, alpha = 0
        alpha = tl.exp(m_i - m_safe)
        p = tl.exp(sc - m_safe[:, None])
        l_i = l_i * alpha + tl.sum(p, 1)
        v = tl.load(v_ptr + kv_off, mask=kmask[:, None], other=0.0)
        if FP8:
            vsc = tl.load(vs_ptr + b * stride_sb + kvh * stride_sh + j, mask=kmask, other=0.0)
            v = (v.to(tl.float32) * vsc[:, None]).to(q.dtype)
        if IEEE:
            acc = acc * alpha[:, None] + tl.dot(p.to(v.dtype), v, input_precision='ieee')
        else:
            acc = acc * alpha[:, None] + tl.dot(p.to(v.dtype), v)
        m_i = m_new
    mo = b * stride_mb + kvh * stride_mh + s * stride_ms + rm
    tl.store(m_ptr + mo, m_i)
    tl.store(l_ptr + mo, l_i)
    oo = b * stride_ob + kvh * stride_oh + s * stride_os + rm[:, None] * stride_om + rd[None, :]
    tl.store(o_ptr + oo, acc)


def attn_decode(
        q: torch.Tensor,
        kbuf: torch.Tensor,
        vbuf: torch.Tensor,
        pos: torch.Tensor,
        scale: float,
        splits: int = 32,
        num_warps: int = 4,
        ks: torch.Tensor | None = None,
        vs: torch.Tensor | None = None,
) -> torch.Tensor:
    """
    Ops.sdpa_static on the length-aware kernel: q [B, H, T, D] for positions pos..pos+T-1, kbuf / vbuf [B, KV, L, D]
    (positions 0..pos+T-1 valid), pos a 0-d int device tensor -> [B, H, T, D] in q's dtype. G*T query rows must fit
    BLOCK_M = 32 (24 heads / 4 = 6 per kv head, so T <= 5). The partials of the `splits` programs per head are merged
    here with a few torch ops (graph-capturable). With ks / vs ([B, KV, L] float32 scales) the buffers are fp8 e4m3
    codes.
    """

    B, H, T, D = q.shape
    KV = kbuf.shape[1]
    G = H // KV
    block_m = 32
    if G * T > block_m:
        raise ValueError(f'{G} query heads x {T} tokens exceed the {block_m} rows the decode attention kernel holds')
    if D & (D - 1):
        raise ValueError(f'head_dim {D} must be a power of two')
    q = q.contiguous()
    if kbuf.stride(-1) != 1 or vbuf.stride(-1) != 1:
        raise ValueError('KV buffers must be contiguous along head_dim')
    m = torch.empty((B, KV, splits, block_m), dtype=torch.float32, device=q.device)
    l = torch.empty_like(m)
    o = torch.empty((B, KV, splits, block_m, D), dtype=torch.float32, device=q.device)
    fp8 = ks is not None
    if fp8:
        ks = check.not_none(ks).contiguous()
        vs = check.not_none(vs).contiguous()
    else:
        ks = vs = m  # unread
    ensure_kernels()

    def launch(block_m_: int, block_n_: int, num_stages: int) -> None:
        _attn_jit[(B * KV, splits)](
            q,
            kbuf,
            vbuf,
            ks,
            vs,
            pos,
            m,
            l,
            o,
            q.stride(0),
            q.stride(1),
            q.stride(2),
            kbuf.stride(0),
            kbuf.stride(1),
            kbuf.stride(2),
            o.stride(0),
            o.stride(1),
            o.stride(2),
            o.stride(3),
            m.stride(0),
            m.stride(1),
            m.stride(2),
            ks.stride(0) if fp8 else 0,
            ks.stride(1) if fp8 else 0,
            scale,
            T,
            G,
            KV,
            BLOCK_M=block_m_,
            BLOCK_N=block_n_,
            D=D,
            SPLITS=splits,
            IEEE=(q.dtype == torch.float32),
            FP8=fp8,
            num_warps=num_warps,
            num_stages=num_stages,
        )

    cfg = _ATTN_CFG.get(('decode', D, q.dtype, fp8))
    if cfg is None:
        _resolve_attn('decode', (D, q.dtype, fp8), launch)
    else:
        launch(*cfg)
    # merge the splits: softmax over all keys = weighted combination of the per-split partials
    mx = m.amax(2, keepdim=True)  # [B, KV, 1, BM]
    w = torch.exp(m - mx)  # [B, KV, S, BM]; a split with no keys has m = -inf -> weight 0
    lsum = (w * l).sum(2)  # [B, KV, BM]
    out = (w[..., None] * o).sum(2) / lsum[..., None]  # [B, KV, BM, D]
    out = out[:, :, :G * T].reshape(B, KV, G, T, D).reshape(B, H, T, D)
    return out.to(q.dtype)


def _attn_prefill_kernel(
        q_ptr,
        k_ptr,
        v_ptr,
        ks_ptr,
        vs_ptr,
        o_ptr,
        stride_qh,
        stride_qt,
        stride_kh,
        stride_kl,
        stride_oh,
        stride_ot,
        stride_sh,
        scale,
        T,
        past,
        G,
        BLOCK_M: tl.constexpr,
        BLOCK_N: tl.constexpr,
        D: tl.constexpr,
        IEEE: tl.constexpr,
        FP8: tl.constexpr,
):
    """
    Prefill attention (flash-attention forward) for T new queries against past + T keys, causal with the offset: query i
    sees keys j <= past + i. One program per (batch*head, block of BLOCK_M queries); it walks the key blocks up to its
    diagonal with an online softmax and never touches the blocks above it, so a chunk of a long prompt costs O(T * (past
    + T)) reads and no [T, L] mask is ever materialised. Batch and head are one folded axis (the wrapper passes
    strides); head h reads kv head h // G.
    """

    pid_m = tl.program_id(0)
    bh = tl.program_id(1)
    bkv = bh // G  # kv row of this head: (b*H + h) // G == b*KV + h // G when heads are folded as b*H + h
    rm = pid_m * BLOCK_M + tl.arange(0, BLOCK_M)
    rd = tl.arange(0, D)
    q_ok = rm < T
    q = tl.load(q_ptr + bh * stride_qh + rm[:, None] * stride_qt + rd[None, :], mask=q_ok[:, None], other=0.0)
    m_i = tl.full([BLOCK_M], float('-inf'), tl.float32)
    l_i = tl.zeros([BLOCK_M], tl.float32)
    acc = tl.zeros([BLOCK_M, D], tl.float32)
    n_keys = past + tl.minimum((pid_m + 1) * BLOCK_M, T)  # the last query of this block sees keys < n_keys
    for start in range(0, n_keys, BLOCK_N):
        j = start + tl.arange(0, BLOCK_N)
        kmask = j < n_keys
        kv_off = bkv * stride_kh + j[:, None] * stride_kl + rd[None, :]
        k = tl.load(k_ptr + kv_off, mask=kmask[:, None], other=0.0)
        if FP8:
            k = k.to(q.dtype)
        if IEEE:
            sc = tl.dot(q, tl.trans(k), input_precision='ieee') * scale
        else:
            sc = tl.dot(q, tl.trans(k)) * scale
        if FP8:
            ksc = tl.load(ks_ptr + bkv * stride_sh + j, mask=kmask, other=0.0)
            sc = sc * ksc[None, :]
        allowed = (j[None, :] <= (past + rm)[:, None]) & kmask[None, :]
        sc = tl.where(allowed, sc, float('-inf'))
        m_new = tl.maximum(m_i, tl.max(sc, 1))
        m_safe = tl.where(m_new == float('-inf'), 0.0, m_new)
        alpha = tl.exp(m_i - m_safe)
        p = tl.exp(sc - m_safe[:, None])
        l_i = l_i * alpha + tl.sum(p, 1)
        v = tl.load(v_ptr + kv_off, mask=kmask[:, None], other=0.0)
        if FP8:
            vsc = tl.load(vs_ptr + bkv * stride_sh + j, mask=kmask, other=0.0)
            v = (v.to(tl.float32) * vsc[:, None]).to(q.dtype)
        if IEEE:
            acc = acc * alpha[:, None] + tl.dot(p.to(v.dtype), v, input_precision='ieee')
        else:
            acc = acc * alpha[:, None] + tl.dot(p.to(v.dtype), v)
        m_i = m_new
    out = acc / l_i[:, None]
    o_off = bh * stride_oh + rm[:, None] * stride_ot + rd[None, :]
    tl.store(o_ptr + o_off, out.to(o_ptr.dtype.element_ty), mask=q_ok[:, None])


def attn_prefill(
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        scale: float,
        past: int,
        num_warps: int = 4,
        ks: torch.Tensor | None = None,
        vs: torch.Tensor | None = None,
) -> torch.Tensor:
    """
    Ops.sdpa for prefill on the flash-attention kernel: q [B, H, T, D], k / v [B, KV, past + T, D] -> [B, H, T, D],
    query i attending keys <= past + i. Requires D a power of two (<= 256) and the tensors contiguous along D. With
    ks / vs ([B, KV, past + T] float32) k / v are fp8 e4m3 codes with per-position scales.
    """

    B, H, T, D = q.shape
    KV = k.shape[1]
    G = H // KV
    if D & (D - 1):
        raise ValueError(f'head_dim {D} must be a power of two')
    q = q.contiguous()
    k = k.contiguous()
    v = v.contiguous()
    out = torch.empty_like(q)
    fp8 = ks is not None
    if fp8:
        ks = check.not_none(ks).contiguous()
        vs = check.not_none(vs).contiguous()
    else:
        ks = vs = out  # unread
    # batch and head folded: q / out [B*H, T, D]; k / v [B*KV, L, D]; kv row of head bh is bh // G because
    # (b*H + h) // G == b*KV + h // G when H == KV*G
    ensure_kernels()

    def launch(block_m_: int, block_n_: int, num_stages: int) -> None:
        _attn_prefill_jit[(triton.cdiv(T, block_m_), B * H)](
            q,
            k,
            v,
            ks,
            vs,
            out,
            q.stride(1),
            q.stride(2),
            k.stride(1),
            k.stride(2),
            out.stride(1),
            out.stride(2),
            ks.stride(1) if fp8 else 0,
            scale,
            T,
            past,
            G,
            BLOCK_M=block_m_,
            BLOCK_N=block_n_,
            D=D,
            IEEE=(q.dtype == torch.float32),
            FP8=fp8,
            num_warps=num_warps,
            num_stages=num_stages,
        )

    cfg = _ATTN_CFG.get(('prefill', D, q.dtype, fp8))
    if cfg is None:
        _resolve_attn('prefill', (D, q.dtype, fp8), launch)
    else:
        launch(*cfg)
    return out


# The jitted kernels, module globals so that torch.compile sees plain `JITFunction` objects when it traces the wrappers
# below (it then lowers `kernel[grid](...)` as a user-defined Triton kernel; anything less direct -- a factory call, an
# attribute of a namespace -- it traces as Python and recompiles per shape). None until `ensure_kernels`, which TorchOps
# calls when it is constructed with Triton on, so importing this module still imports neither triton nor torch.
_qlinear_jit: ta.Any = None
_fma_jit: ta.Any = None
_gdn_jit: ta.Any = None
_attn_jit: ta.Any = None
_attn_prefill_jit: ta.Any = None


def ensure_kernels() -> None:
    """
    Jit the kernels (once). `triton.jit` is applied here rather than as decorators so the kernel bodies above are plain
    functions until this runs. Triton resolves `tl` through the kernel function's globals and wants the real
    `triton.language` module there (the interpreter checks identity), so the proxies are replaced by the modules at this
    point.
    """

    global _qlinear_jit, _fma_jit, _gdn_jit, _attn_jit, _attn_prefill_jit

    if _qlinear_jit is not None:
        return
    import importlib

    g = globals()
    g['triton'] = importlib.import_module('triton')
    g['tl'] = importlib.import_module('triton.language')
    _fma_jit = triton.jit(_qgemv_fma_kernel)
    _gdn_jit = triton.jit(_gdn_step_kernel)
    _attn_jit = triton.jit(_attn_decode_kernel)
    _attn_prefill_jit = triton.jit(_attn_prefill_kernel)
    _qlinear_jit = triton.jit(_qlinear_kernel)  # last: it is the "built" flag


# attention launch configurations that fit the GPU's shared memory, resolved per (kind, head_dim, dtype) on first use:
# the tiles are [BLOCK, D] and D = 256 is big, so the first choice can exceed consumer Blackwell's 99 KB
_ATTN_CFG: dict[tuple[ta.Any, ...], tuple[int, int, int]] = {}
_ATTN_LADDER: dict[str, tuple[tuple[int, int, int], ...]] = {
    # (block_m, block_n, num_stages), largest first
    'decode': ((32, 64, 2), (32, 32, 2), (32, 32, 1), (32, 16, 1)),
    'prefill': ((64, 64, 2), (64, 32, 2), (32, 32, 2), (32, 32, 1), (32, 16, 1)),
}


def _resolve_attn(
        kind: str,
        key: tuple[ta.Any, ...],
        launch: ta.Callable[[int, int, int], None],
) -> tuple[int, int, int]:
    """
    First use of an attention kernel for (head_dim, dtype): walk the ladder until a configuration launches (the
    successful attempt does the work), remember it. try/except lives here, off the hot path torch.compile traces (by
    then the entry exists: TorchOps.compile_fn runs every step once eagerly before compiling).
    """

    for cfg in _ATTN_LADDER[kind]:
        try:
            launch(*cfg)
        except triton.runtime.errors.OutOfResources:
            continue
        _ATTN_CFG[(kind, *key)] = cfg
        return cfg
    raise RuntimeError(f'no {kind} attention configuration fits this GPU for head_dim {key[0]}')


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
        block_dv: int = 32,
        num_warps: int = 8,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    Fused DeltaNet token step (the whole of Ops.gdn_step) in one launch per layer: each program owns a [dk, block_dv]
    slice of one head's state in registers, runs the T-token recurrence on it -- l2-norm of q/k, beta and the decay
    computed in-kernel, key heads broadcast by index -- and writes the outputs and either the final state or the state
    after every token. Replaces ~25 small kernels (and ~24 MB of state traffic per layer at T=1) with one kernel that
    reads and writes the 3 MB state once.

    q, k: [B, T, Hk, dk]; v: [B, T, Hv, dv]; a, b: [B, T, Hv]; A, dt_bias: [Hv]; state: [B, Hv, dk, dv] float32.
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
    ensure_kernels()
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
        T=T,
        DK=dk,
        DV=dv,
        BLOCK_DV=block_dv,
        ALL_STATES=all_states,
        EPS=eps,
        QSCALE=dk**-0.5,
        num_warps=num_warps,
    )
    return out, s_out


def _qgemv_fma_kernel(
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
):
    """
    The same GEMV as _qlinear_kernel without tensor cores: for M <= BLOCK_M (<= 8) rows the products are plain FMAs
    reduced along K in registers, so the dequantized weight tile never goes through shared memory -- what every int4
    GEMV in llama.cpp / exllama does for small M. Which formulation streams faster on a given GPU is for the tuner to
    decide (GemvConfig.fma). Rows are accumulated into a [BLOCK_M, BLOCK_N] tile with a masked add per row (Triton has
    no row assignment; a per-row list does not survive its loops).
    """

    pid_n = tl.program_id(0)
    pid_s = tl.program_id(1)
    rm = tl.arange(0, BLOCK_M)
    rn = pid_n * BLOCK_N + tl.arange(0, BLOCK_N)
    n_mask = rn < N
    n_groups = K // GROUP
    k_lo = pid_s * (K // SPLIT_K)
    k_hi = k_lo + K // SPLIT_K
    G: tl.constexpr = BLOCK_K // GROUP
    rg = tl.arange(0, G)
    acc = tl.zeros((BLOCK_M, BLOCK_N), dtype=tl.float32)
    if BITS == 4:
        KB: tl.constexpr = BLOCK_K // 2
        GB: tl.constexpr = GROUP // 2
        rb = tl.arange(0, KB)
        for k0 in range(k_lo, k_hi, BLOCK_K):
            kb = k0 // 2 + rb
            ke = k0 + 2 * rb
            gcol = k0 // GROUP + rg
            q = tl.load(q_ptr + rn[:, None] * (K // 2) + kb[None, :], mask=n_mask[:, None], other=0)
            s = tl.load(s_ptr + rn[:, None] * n_groups + gcol[None, :], mask=n_mask[:, None], other=0.0)
            b = tl.load(b_ptr + rn[:, None] * n_groups + gcol[None, :], mask=n_mask[:, None], other=0.0)
            s = s.to(tl.float32)[:, :, None]
            b = b.to(tl.float32)[:, :, None]
            lo = tl.reshape(tl.reshape((q & 0xF).to(tl.float32), (BLOCK_N, G, GB)) * s + b, (BLOCK_N, KB))
            hi = tl.reshape(tl.reshape((q >> 4).to(tl.float32), (BLOCK_N, G, GB)) * s + b, (BLOCK_N, KB))
            for mi in tl.static_range(BLOCK_M):
                xm = (ke < K) & (mi < M)
                xe = tl.load(x_ptr + mi * stride_xm + ke, mask=xm, other=0.0).to(tl.float32)
                xo = tl.load(x_ptr + mi * stride_xm + ke + 1, mask=xm, other=0.0).to(tl.float32)
                row = tl.sum(lo * xe[None, :], 1) + tl.sum(hi * xo[None, :], 1)  # [BLOCK_N]
                acc += tl.where(rm[:, None] == mi, row[None, :], 0.0)
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
            w = tl.reshape(tl.reshape(q.to(tl.float32), (BLOCK_N, G, GROUP)) * s + b, (BLOCK_N, BLOCK_K))
            for mi in tl.static_range(BLOCK_M):
                xm = (rk < K) & (mi < M)
                xt = tl.load(x_ptr + mi * stride_xm + rk, mask=xm, other=0.0).to(tl.float32)
                row = tl.sum(w * xt[None, :], 1)
                acc += tl.where(rm[:, None] == mi, row[None, :], 0.0)
    y_base = y_ptr + pid_s * M * stride_ym
    y = acc.to(y_ptr.dtype.element_ty)
    tl.store(y_base + rm[:, None] * stride_ym + rn[None, :], y, mask=(rm[:, None] < M) & n_mask[None, :])


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
    fma: bool = False  # _qgemv_fma_kernel (registers, M <= 8) instead of the tensor-core _qlinear_kernel


# (N, K, bits) -> config, filled by `tune` / `load_tuned`; consulted before the heuristics
TUNED: dict[tuple[int, int, int], GemvConfig] = {}


def default_config(n: int, k: int, bits: int, dtype: torch.dtype) -> GemvConfig:
    """
    Heuristic when nothing is tuned: enough programs to fill the GPU. Narrow outputs (N=5120 at block_n=32 is 160
    programs) get split-K so the K loop is shared across several programs.
    """

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

    The launch configuration comes from `config`, else `TUNED[(N, K, bits)]` (see `tune`), else `default_config`.
    split_k > 1 runs the K loop on several programs and sums float32 partials (one extra tiny kernel); it is what makes
    the narrow projections (o_proj, down_proj, out_proj: N=5120) fill the GPU. `block_n` overrides that one field of the
    config (kept for TorchOps.triton_block_n).
    """

    if not HAVE_TRITON:
        raise RuntimeError('triton is not installed')
    ensure_kernels()
    n, k = shape
    cfg = config or TUNED.get((n, k, bits)) or default_config(n, k, bits, x.dtype)
    if block_n is not None:
        cfg = dc.replace(cfg, block_n=block_n)
    x2 = x.reshape(-1, k)
    if x2.stride(1) != 1:
        x2 = x2.contiguous()
    m = x2.shape[0]
    key = (n, k, bits, x.dtype, cfg)
    resolved = _RESOLVED.get(key)
    if resolved is None:
        resolved = _resolve(
            x2,
            q,
            scale,
            bias,
            bits,
            group,
            n,
            k,
            cfg,
        )
        _RESOLVED[key] = resolved
    bk, num_stages, split = resolved
    y = torch.empty((split, m, n), dtype=torch.float32 if split > 1 else x.dtype, device=x.device)
    if cfg.fma and m <= 8:
        grid = (triton.cdiv(n, cfg.block_n), split)
        _fma_jit[grid](
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
            BLOCK_M=8,
            BLOCK_N=cfg.block_n,
            BLOCK_K=bk,
            SPLIT_K=split,
            num_warps=cfg.num_warps,
            num_stages=num_stages,
        )
        out = y.sum(0).to(x.dtype) if split > 1 else y[0]
        return out.reshape(*x.shape[:-1], n)
    grid = (  # type: ignore[assignment]
        triton.cdiv(n, cfg.block_n),
        triton.cdiv(m, 16),
        split,
    )
    _qlinear_jit[grid](
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
    out = y.sum(0).to(x.dtype) if split > 1 else y[0]
    return out.reshape(*x.shape[:-1], n)


def _resolve(
        x2,
        q,
        scale,
        bias,
        bits,
        group,
        n,
        k,
        cfg: GemvConfig,
) -> tuple[int, int, int]:
    """
    Find (block_k, num_stages, split_k) for `cfg` that fits the GPU's shared memory: try as configured, shrink the K
    block, then the pipeline depth. Runs once per (shape, dtype, config).
    """

    m = x2.shape[0]
    bk = _block_k(k, cfg.block_k)
    split = cfg.split_k
    while split > 1 and k % (bk * split):
        split //= 2
    num_stages = cfg.num_stages
    while True:
        y = torch.empty((split, m, n), dtype=torch.float32 if split > 1 else x2.dtype, device=x2.device)
        grid = (triton.cdiv(n, cfg.block_n), triton.cdiv(m, 16), split)
        try:
            if cfg.fma and m <= 8:
                _fma_jit[(triton.cdiv(n, cfg.block_n), split)](
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
                    BLOCK_M=8,
                    BLOCK_N=cfg.block_n,
                    BLOCK_K=bk,
                    SPLIT_K=split,
                    num_warps=cfg.num_warps,
                    num_stages=num_stages,
                )
                return bk, num_stages, split
            _qlinear_jit[grid](
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
                IEEE=(x2.dtype == torch.float32),
                num_warps=cfg.num_warps,
                num_stages=num_stages,
            )
            return bk, num_stages, split
        except triton.runtime.errors.OutOfResources:
            if bk > 64 and k % (bk // 2) == 0:
                bk //= 2
            elif num_stages > 1:
                num_stages -= 1
            else:
                raise


def time_graphed(fn: ta.Callable[[int], ta.Any], reps: int = 10, iters: int = 5) -> float:
    """
    Seconds per call of `fn(i)`, measured as CUDA-graph replays: `reps` calls are captured into one graph and the graph
    is replayed `iters` times between CUDA events. An eager Triton launch costs ~40-50 us of Python and launcher
    overhead, which is more than most of these kernels take -- timing eagerly makes every small shape look identical
    (and penalises split-K for its extra reduction launch). Inside a graph only the GPU time is left, which is also how
    the kernels run in the decode step. `fn` gets the rep index so the caller can rotate through several copies of the
    weight: a weight smaller than the L2 cache (96 MB on a 5090) that is timed on its own is served from L2 after the
    first pass and reports bandwidth the decode step, which streams every weight once from DRAM, will never see.
    """

    fn(0)
    fn(1 % reps)
    torch.cuda.synchronize()
    s = torch.cuda.Stream()
    s.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(s):
        fn(0)
    torch.cuda.current_stream().wait_stream(s)
    g = torch.cuda.CUDAGraph()
    with torch.cuda.graph(g):
        for i in range(reps):
            fn(i)
    g.replay()
    torch.cuda.synchronize()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)
    start.record()
    for _ in range(iters):
        g.replay()
    end.record()
    torch.cuda.synchronize()
    return start.elapsed_time(end) / 1000.0 / (reps * iters)


def tune(
        shapes: ta.Iterable[tuple[int, int]],
        bits: int,
        dtype: ta.Any = None,
        m: int = 1,
        group: int = 64,
        device: str = 'cuda',
        log: ta.Callable[[str], None] | None = print,
) -> dict[tuple[int, int, int], GemvConfig]:
    """
    Sweep launch configurations per (N, K) on the current GPU, keep the fastest in TUNED and return them. Prints
    achieved GB/s of packed-weight traffic per shape (the number to compare against the card's bandwidth). Timing is by
    CUDA-graph replay (see `time_graphed`), so it reflects what the decode graph sees. Each configuration is a Triton
    compile (~1 s), so the sweep is kept to ~16-64 per shape: a few minutes for the ~9 distinct shapes of a model.
    """

    if dtype is None:
        dtype = torch.bfloat16
    import itertools

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
        # enough distinct copies of the weight to exceed L2 across the captured reps (see time_graphed)
        n_copies = max(1, min(16, -(-256 * 2**20 // nbytes)))
        copies = [qw] + [
            dc.replace(
                qw,
                q=qw.q.clone(),
                scale=qw.scale.clone(),
                bias=qw.bias.clone(),
            )
            for _ in range(n_copies - 1)
        ]
        reps = max(10, n_copies)
        bns = (16, 32) if n <= 2048 else (32, 64) if n <= 8192 else (64, 128)
        bks = tuple(b for b in (128, 256) if k % b == 0) or (64,)
        sks = (1, 2, 4, 8) if n <= 16384 else (1,)
        for (
                fma,
                bn,
                bk,
                nw,
                ns,
                sk,
        ) in itertools.product(
            (False, True),
            bns,
            bks,
            (4, 8),
            (2, 3),
            sks,
        ):
            if k % (bk * sk):
                continue
            if fma and (bn > 64 or bk > 128 or m > 8):
                continue  # the FMA tile lives in registers: [bn, bk] f32 per plane
            cfg = GemvConfig(bn, bk, nw, ns, sk, fma)
            try:
                y = qlinear(
                    x,
                    qw.q,
                    qw.scale,
                    qw.bias,
                    bits,
                    group,
                    (n, k),
                    config=cfg,
                )
                torch.cuda.synchronize()
                if ref is None:
                    ref = (x.float() @ qw.dequant(torch.float32).T)
                if ((y.float() - ref).abs().max() / ref.abs().max()).item() > 3e-2:
                    if log:
                        log(f'  !! N={n} K={k} {cfg} computes wrong results; skipped')
                    continue
                dt = time_graphed(
                    lambda i: qlinear(
                        x,
                        copies[i % n_copies].q,
                        copies[i % n_copies].scale,
                        copies[i % n_copies].bias,
                        bits,
                        group,
                        (n, k),
                        config=cfg,
                    ),
                    reps=reps,
                )
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
