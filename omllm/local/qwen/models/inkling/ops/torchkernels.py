# ruff: noqa: N803 N806
"""
Triton kernels for Inkling 2's own operations (base.py's `Inkling2Ops`): each fuses one small, regular piece of a
step -- a chain of a dozen or more elementwise operations, reductions and little matmuls that read almost nothing,
whose cost on a GPU was their launches -- into one launch over every row (token) of the step. The composed form of
each is its definition, and what tests/test_torch.py holds the kernel to, compiled and under Triton's interpreter.

Conventions are backends/torch_fused.py's, whose helpers these use: the kernel bodies are plain functions, jitted
into module globals by `ensure_inkling2_kernels` (so a torch.compile trace of a wrapper finds a `JITFunction` and
lowers the launch as a user-defined kernel); no dataclass construction on a traced path; integer arguments that follow
a prompt's length are kept out of the kernels' specializations.
"""
import importlib
import typing as ta

from omcore import lang

from ....backends.torch_fused import fused_block


if ta.TYPE_CHECKING:
    import torch  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import triton  # type: ignore[import-not-found,import-untyped,unused-ignore]
    import triton.language as tl  # type: ignore[import-not-found,import-untyped,unused-ignore]
else:
    torch = lang.proxy_import('torch')
    triton = lang.proxy_import('triton')
    tl = lang.proxy_import('triton.language')


##


def _tanh(x):
    """
    tanh for a kernel, good to float32 at every size: 2 sigmoid(2x) - 1 is a difference of nearly equal numbers for
    a small x, and what it loses there showed in a model's logits (2e-4 of them, through 48 layers).
    """

    ax = tl.abs(x)
    x2 = x * x
    e = tl.exp(-2.0 * ax)
    small = ax * (1.0 - x2 * (1.0 / 3.0 - x2 * (2.0 / 15.0 - x2 * (17.0 / 315.0))))
    t = tl.where(ax < 0.1, small, (1.0 - e) / (1.0 + e))
    return tl.where(x < 0.0, -t, t)


##


def _bottleneck_z_kernel(
        x_ptr,
        m_ptr,
        d_ptr,
        z_ptr,
        stride_x,
        stride_m,
        eps,
        H: tl.constexpr,
        R: tl.constexpr,
        BH: tl.constexpr,
        BR: tl.constexpr,
):
    """
    The bottleneck of `Inkling2Ops.bottleneck_blend`: z [rows, R] = down [unit(x) | unit(m)], rounded to down's dtype.
    The grid is (rows, R / BR), and a program takes the whole hidden axis as one tile: it sums its row's squares for
    itself -- a few thousand loads -- so that none waits on another, and applies the two norms to its dot products
    (the unit vectors are not rounded to down's dtype on the way, as the composed form's cast rounds them).
    """

    t = tl.program_id(0)
    rr = tl.program_id(1) * BR + tl.arange(0, BR)
    rh = tl.arange(0, BH)
    hm = rh < H

    xv = tl.load(x_ptr + t * stride_x + rh, mask=hm, other=0.0).to(tl.float32)
    mv = tl.load(m_ptr + t * stride_m + rh, mask=hm, other=0.0).to(tl.float32)
    rx = 1.0 / tl.sqrt(tl.sum(xv * xv, 0) / H + eps)
    rm = 1.0 / tl.sqrt(tl.sum(mv * mv, 0) / H + eps)

    dx = tl.load(d_ptr + rr[:, None] * (2 * H) + rh[None, :], mask=hm[None, :], other=0.0).to(tl.float32)
    dm = tl.load(d_ptr + rr[:, None] * (2 * H) + H + rh[None, :], mask=hm[None, :], other=0.0).to(tl.float32)
    z = tl.sum(dx * xv[None, :], 1) * rx + tl.sum(dm * mv[None, :], 1) * rm

    tl.store(z_ptr + t * R + rr, z.to(d_ptr.dtype.element_ty).to(tl.float32))


def _bottleneck_out_kernel(
        x_ptr,
        m_ptr,
        z_ptr,
        f_ptr,
        g_ptr,
        y_ptr,
        stride_x,
        stride_m,
        H,
        R: tl.constexpr,
        BH: tl.constexpr,
):
    """
    The blend of `Inkling2Ops.bottleneck_blend` from its bottleneck: (1 - tanh(forget z)) x + tanh(gain z) m, a tile of
    the hidden axis a program. The grid is (rows, H / BH).
    """

    t = tl.program_id(0)
    rh = tl.program_id(1) * BH + tl.arange(0, BH)
    hm = rh < H
    rr = tl.arange(0, R)

    z = tl.load(z_ptr + t * R + rr)
    xv = tl.load(x_ptr + t * stride_x + rh, mask=hm, other=0.0).to(tl.float32)
    mv = tl.load(m_ptr + t * stride_m + rh, mask=hm, other=0.0).to(tl.float32)
    fw = tl.load(f_ptr + rh[:, None] * R + rr[None, :], mask=hm[:, None], other=0.0)
    gw = tl.load(g_ptr + rh[:, None] * R + rr[None, :], mask=hm[:, None], other=0.0)
    f = _tanh(tl.sum(fw * z[None, :], 1))
    g = _tanh(tl.sum(gw * z[None, :], 1))
    tl.store(y_ptr + t * H + rh, (1.0 - f) * xv + g * mv, mask=hm)


def bottleneck_blend(
        x: torch.Tensor,
        m: torch.Tensor,
        down: torch.Tensor,
        forget: torch.Tensor,
        gain: torch.Tensor,
        eps: float,
) -> torch.Tensor:
    """
    `Inkling2Ops.bottleneck_blend`: x, m [..., H] float32; down [R, 2H]; forget, gain [H, R] float32. R a power of two.
    Two launches: the bottleneck, then the blend.
    """

    H = x.shape[-1]
    R = down.shape[0]
    x2 = x.reshape(-1, H)
    m2 = m.reshape(-1, H)
    rows = x2.shape[0]
    z = torch.empty((rows, R), dtype=torch.float32, device=x.device)
    y = torch.empty((rows, H), dtype=torch.float32, device=x.device)
    br = min(R, 2)
    bh = 64
    _blend_z_jit[(rows, R // br)](
        x2,
        m2,
        down,
        z,
        x2.stride(0),
        m2.stride(0),
        eps,
        H=H,
        R=R,
        BH=fused_block(H, 1 << 16),
        BR=br,
        num_warps=4,
    )
    _blend_out_jit[(rows, triton.cdiv(H, bh))](
        x2,
        m2,
        z,
        forget,
        gain,
        y,
        x2.stride(0),
        m2.stride(0),
        H,
        R=R,
        BH=bh,
        num_warps=2,
    )
    return y.reshape(x.shape)


##


def _rms_norm_kernel(
        x_ptr,
        w_ptr,
        y_ptr,
        stride_x,
        eps,
        H,
        BH: tl.constexpr,
        BS: tl.constexpr,
):
    """
    `Inkling2Ops.rms_norm_to`: a tile of a row a program, x / sqrt(mean(x^2) + eps) * w in the output's dtype. Each
    program sums its row's squares for itself. The grid is (rows, H / BH).
    """

    r = tl.program_id(0)
    xr = x_ptr + r * stride_x

    rs = tl.arange(0, BS)
    ss = 0.0
    for h0 in range(0, H, BS):
        v = tl.load(xr + h0 + rs, mask=(h0 + rs) < H, other=0.0).to(tl.float32)
        ss += tl.sum(v * v, 0)

    rh = tl.program_id(1) * BH + tl.arange(0, BH)
    hm = rh < H
    v = tl.load(xr + rh, mask=hm, other=0.0).to(tl.float32)
    y = v * (1.0 / tl.sqrt(ss / H + eps)) * tl.load(w_ptr + rh, mask=hm, other=0.0).to(tl.float32)
    tl.store(y_ptr + r * H + rh, y.to(y_ptr.dtype.element_ty), mask=hm)


def rms_norm_to(x: torch.Tensor, w: torch.Tensor, eps: float, dtype: torch.dtype) -> torch.Tensor:
    """
    `Inkling2Ops.rms_norm_to`: x [..., H] (rows evenly strided), w [H] -> x's shape in `dtype`. A row is one program up
    to 4,096 wide, on eight warps from 2,048: 1.2 us for a row of 2,304 in a captured graph on the 5090, where tiles of
    128 on one warp, each summing the row for itself, were 3.1.
    """

    H = x.shape[-1]
    x2 = x.reshape(-1, H)
    y = torch.empty((x2.shape[0], H), dtype=dtype, device=x.device)
    bh = fused_block(H, 4096)
    _rms_norm_jit[(x2.shape[0], triton.cdiv(H, bh))](
        x2,
        w,
        y,
        x2.stride(0),
        eps,
        H,
        BH=bh,
        BS=bh,
        num_warps=8 if bh >= 2048 else (4 if bh >= 512 else 1),
    )
    return y.reshape(x.shape)


##


def _l2_clip_kernel(
        x_ptr,
        s_ptr,
        a_ptr,
        y_ptr,
        threshold,
        G,
        D: tl.constexpr,
        BG: tl.constexpr,
        SCALED: tl.constexpr,
        AFTER: tl.constexpr,
):
    """
    `Inkling2Ops.l2_clip` over x [T, G, D]: a tile of BG of a row's G vectors a program, each scaled (and rounded to x's
    dtype, as a separate multiply rounds it), clipped, and with AFTER multiplied by its row's factor. The grid is
    (T, G / BG).
    """

    t = tl.program_id(0)
    rg = tl.program_id(1) * BG + tl.arange(0, BG)
    gm = rg < G
    rd = tl.arange(0, D)
    xt = x_ptr.dtype.element_ty
    at = t * G * D + rg[:, None] * D + rd[None, :]

    v = tl.load(x_ptr + at, mask=gm[:, None], other=0.0)
    if SCALED:
        v = (v * tl.load(s_ptr + rg[:, None] * D + rd[None, :], mask=gm[:, None], other=0.0)).to(xt)
    v = v.to(tl.float32)
    norm = tl.sqrt(tl.sum(v * v, 1))
    y = (v * tl.minimum(threshold / (norm + 1e-6), 1.0)[:, None]).to(xt)
    if AFTER:
        y = (y.to(tl.float32) * tl.load(a_ptr + t)).to(xt)
    tl.store(y_ptr + at, y, mask=gm[:, None])


def l2_clip(
        x: torch.Tensor,
        threshold: float,
        scale: torch.Tensor | None,
        after: torch.Tensor | None,
) -> torch.Tensor:
    """
    `Inkling2Ops.l2_clip`: x [1, T, G, D] (contiguous), D a power of two; scale [G, D] in x's dtype; after [T]
    float32.
    """

    _, T, G, D = x.shape
    y = torch.empty_like(x)
    bg = max(1, min(fused_block(G, 1 << 16), 512 // D))
    _l2_clip_jit[(T, triton.cdiv(G, bg))](
        x,
        scale if scale is not None else x,
        after if after is not None else x,
        y,
        threshold,
        G,
        D=D,
        BG=bg,
        SCALED=scale is not None,
        AFTER=after is not None,
        num_warps=1,
    )
    return y


##


def _depth_mix_kernel(
        q_ptr,
        s0_ptr,
        s1_ptr,
        s2_ptr,
        s3_ptr,
        s4_ptr,
        s5_ptr,
        y_ptr,
        eps,
        H,
        Q,
        S: tl.constexpr,
        RAW: tl.constexpr,
        BH: tl.constexpr,
):
    """
    `Inkling2Ops.depth_mix`: for row t and query q, a tile of the hidden axis a program. Each program takes its own
    measure of every source first -- its dot product with the query and, for the last RAW ones, its mean square -- which
    is S passes over a few thousand floats and lets no program wait on another; then its tile of the weighted sum.
    Sources past S are not read. The grid is (T * Q, H / BH).
    """

    tq = tl.program_id(0)
    t = tq // Q
    q = tq % Q
    r0 = tl.arange(0, BH)
    qrow = q_ptr + q * H

    d0 = 0.0
    d1 = 0.0
    d2 = 0.0
    d3 = 0.0
    d4 = 0.0
    d5 = 0.0
    n0 = 0.0
    n1 = 0.0
    n2 = 0.0
    n3 = 0.0
    n4 = 0.0
    n5 = 0.0
    for h0 in range(0, H, BH):
        rh = h0 + r0
        hm = rh < H
        qv = tl.load(qrow + rh, mask=hm, other=0.0)
        v = tl.load(s0_ptr + t * H + rh, mask=hm, other=0.0).to(tl.float32)
        d0 += tl.sum(v * qv, 0)
        n0 += tl.sum(v * v, 0)
        if S > 1:
            v = tl.load(s1_ptr + t * H + rh, mask=hm, other=0.0).to(tl.float32)
            d1 += tl.sum(v * qv, 0)
            n1 += tl.sum(v * v, 0)
        if S > 2:
            v = tl.load(s2_ptr + t * H + rh, mask=hm, other=0.0).to(tl.float32)
            d2 += tl.sum(v * qv, 0)
            n2 += tl.sum(v * v, 0)
        if S > 3:
            v = tl.load(s3_ptr + t * H + rh, mask=hm, other=0.0).to(tl.float32)
            d3 += tl.sum(v * qv, 0)
            n3 += tl.sum(v * v, 0)
        if S > 4:
            v = tl.load(s4_ptr + t * H + rh, mask=hm, other=0.0).to(tl.float32)
            d4 += tl.sum(v * qv, 0)
            n4 += tl.sum(v * v, 0)
        if S > 5:
            v = tl.load(s5_ptr + t * H + rh, mask=hm, other=0.0).to(tl.float32)
            d5 += tl.sum(v * qv, 0)
            n5 += tl.sum(v * v, 0)

    # each source's scale (1 for one given at unit RMS) and logit
    c0 = 1.0
    c1 = 1.0
    c2 = 1.0
    c3 = 1.0
    c4 = 1.0
    c5 = 1.0
    if S - RAW <= 0:
        c0 = 1.0 / tl.sqrt(n0 / H + eps)
    if S - RAW <= 1:
        c1 = 1.0 / tl.sqrt(n1 / H + eps)
    if S - RAW <= 2:
        c2 = 1.0 / tl.sqrt(n2 / H + eps)
    if S - RAW <= 3:
        c3 = 1.0 / tl.sqrt(n3 / H + eps)
    if S - RAW <= 4:
        c4 = 1.0 / tl.sqrt(n4 / H + eps)
    if S - RAW <= 5:
        c5 = 1.0 / tl.sqrt(n5 / H + eps)

    k = 1.0 / tl.sqrt(H * 1.0)
    l0 = d0 * c0 * k
    top = l0
    l1 = l0
    l2 = l0
    l3 = l0
    l4 = l0
    l5 = l0
    if S > 1:
        l1 = d1 * c1 * k
        top = tl.maximum(top, l1)
    if S > 2:
        l2 = d2 * c2 * k
        top = tl.maximum(top, l2)
    if S > 3:
        l3 = d3 * c3 * k
        top = tl.maximum(top, l3)
    if S > 4:
        l4 = d4 * c4 * k
        top = tl.maximum(top, l4)
    if S > 5:
        l5 = d5 * c5 * k
        top = tl.maximum(top, l5)

    w0 = tl.exp(l0 - top)
    den = w0
    w1 = w0
    w2 = w0
    w3 = w0
    w4 = w0
    w5 = w0
    if S > 1:
        w1 = tl.exp(l1 - top)
        den += w1
    if S > 2:
        w2 = tl.exp(l2 - top)
        den += w2
    if S > 3:
        w3 = tl.exp(l3 - top)
        den += w3
    if S > 4:
        w4 = tl.exp(l4 - top)
        den += w4
    if S > 5:
        w5 = tl.exp(l5 - top)
        den += w5

    rh = tl.program_id(1) * BH + r0
    hm = rh < H
    y = tl.load(s0_ptr + t * H + rh, mask=hm, other=0.0).to(tl.float32) * (w0 * c0 / den)
    if S > 1:
        y += tl.load(s1_ptr + t * H + rh, mask=hm, other=0.0).to(tl.float32) * (w1 * c1 / den)
    if S > 2:
        y += tl.load(s2_ptr + t * H + rh, mask=hm, other=0.0).to(tl.float32) * (w2 * c2 / den)
    if S > 3:
        y += tl.load(s3_ptr + t * H + rh, mask=hm, other=0.0).to(tl.float32) * (w3 * c3 / den)
    if S > 4:
        y += tl.load(s4_ptr + t * H + rh, mask=hm, other=0.0).to(tl.float32) * (w4 * c4 / den)
    if S > 5:
        y += tl.load(s5_ptr + t * H + rh, mask=hm, other=0.0).to(tl.float32) * (w5 * c5 / den)
    tl.store(y_ptr + (t * Q + q) * H + rh, y, mask=hm)


DEPTH_MIX_MAX_SOURCES = 6


def depth_mix(
        queries: torch.Tensor,
        sources: ta.Sequence[torch.Tensor],
        raw: int,
        eps: float,
) -> torch.Tensor:
    """
    `Inkling2Ops.depth_mix`: queries [Q, H] float32; up to six sources [1, T, H] (each contiguous). [1, T, Q, H]
    float32.
    """

    Q, H = queries.shape
    T = sources[0].shape[1]
    S = len(sources)
    ptrs = [*sources, *([sources[0]] * (DEPTH_MIX_MAX_SOURCES - S))]
    y = torch.empty((1, T, Q, H), dtype=torch.float32, device=queries.device)
    bh = fused_block(H, 1 << 16)  # (the whole axis a tile on eight warps: 3.6 us where tiles of 256 on one took 5.5)
    _depth_mix_jit[(T * Q, triton.cdiv(H, bh))](
        queries,
        ptrs[0],
        ptrs[1],
        ptrs[2],
        ptrs[3],
        ptrs[4],
        ptrs[5],
        y,
        eps,
        H,
        Q,
        S=S,
        RAW=raw,
        BH=bh,
        num_warps=8,
    )
    return y


##


def _sigmoid_route_kernel(
        x_ptr,
        b_ptr,
        i_ptr,
        w_ptr,
        total,
        E,
        K: tl.constexpr,
        BE: tl.constexpr,
):
    """
    `Inkling2Ops.sigmoid_route` for one row: its E scores' sigmoids; the K largest of score + bias, picked one at a time
    (the first of equals), by index and by their own score; the weights those scores scaled to sum to `total`. The
    grid is the rows.
    """

    n = tl.program_id(0)
    re = tl.arange(0, BE)
    em = re < E

    sc = tl.sigmoid(tl.load(x_ptr + n * E + re, mask=em, other=0.0).to(tl.float32))
    rank = tl.where(em, sc + tl.load(b_ptr + re, mask=em, other=0.0), -1e30)

    picked = tl.zeros((BE,), dtype=tl.int32)  # the slot each expert was picked for, + 1
    ssum = 0.0
    for j in tl.static_range(K):
        top = tl.max(rank, 0)
        at = tl.min(tl.where(rank == top, re, BE), 0)
        hit = re == at
        picked = tl.where(hit, j + 1, picked)
        ssum += tl.sum(tl.where(hit, sc, 0.0), 0)
        rank = tl.where(hit, -1e30, rank)
        tl.store(i_ptr + n * K + j, at.to(tl.int32))

    for j in tl.static_range(K):
        own = tl.sum(tl.where(picked == j + 1, sc, 0.0), 0)
        tl.store(w_ptr + n * K + j, own * (total / (ssum + 1e-20)))


def sigmoid_route(
        logits: torch.Tensor,
        bias: torch.Tensor,
        k: int,
        total: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    `Inkling2Ops.sigmoid_route`: logits [N, E] (contiguous); bias [E] float32. (indices [N, k] int32, weights [N,
    k]).
    """

    N, E = logits.shape
    idx = torch.empty((N, k), dtype=torch.int32, device=logits.device)
    w = torch.empty((N, k), dtype=torch.float32, device=logits.device)
    _route_jit[(N,)](
        logits,
        bias,
        idx,
        w,
        total,
        E,
        K=k,
        BE=fused_block(E, 1 << 16),
        num_warps=1,
    )
    return idx, w


##


def _pair_to_kernel(
        a_ptr,
        b_ptr,
        y_ptr,
        N,
        GATED: tl.constexpr,
        BN: tl.constexpr,
):
    """
    Two arrays' elements combined in float32 and stored in y's dtype, a tile of N a program: a + b
    (`Inkling2Ops.sum_to`), or with GATED a * sigmoid(b) (`Inkling2Ops.sigmoid_gated`). The grid is N / BN.
    """

    rn = tl.program_id(0) * BN + tl.arange(0, BN)
    nm = rn < N
    a = tl.load(a_ptr + rn, mask=nm, other=0.0).to(tl.float32)
    b = tl.load(b_ptr + rn, mask=nm, other=0.0).to(tl.float32)
    if GATED:
        y = a * tl.sigmoid(b)
    else:
        y = a + b
    tl.store(y_ptr + rn, y.to(y_ptr.dtype.element_ty), mask=nm)


def _pair_to(a: torch.Tensor, b: torch.Tensor, dtype: torch.dtype, gated: bool) -> torch.Tensor:
    y = torch.empty(a.shape, dtype=dtype, device=a.device)
    n = a.numel()
    bn = fused_block(n, 256)
    _pair_to_jit[(triton.cdiv(n, bn),)](
        a,
        b,
        y,
        n,
        GATED=gated,
        BN=bn,
        num_warps=1,
    )
    return y


def sum_to(a: torch.Tensor, b: torch.Tensor, dtype: torch.dtype) -> torch.Tensor:
    """
    `Inkling2Ops.sum_to` for contiguous a, b of one shape: one launch where the composed form is two casts, an add and a
    cast -- a stream's write, twice a layer.
    """

    return _pair_to(a, b, dtype, False)


def sigmoid_gated(x: torch.Tensor, g: torch.Tensor, dtype: torch.dtype) -> torch.Tensor:
    """`Inkling2Ops.sigmoid_gated` for contiguous x, g of one shape: one launch for the composed form's five."""

    return _pair_to(x, g, dtype, True)


##


def _capped_gate_kernel(
        h_ptr,
        y_ptr,
        gate_cap,
        up_cap,
        I,  # noqa: E741
        BI: tl.constexpr,
):
    """
    `Inkling2Ops.capped_gate`: a tile of a row's I outputs a program -- from the row's two halves g | u, (gate_cap
    tanh(g / gate_cap)) sigmoid(g) (up_cap tanh(u / up_cap)), in the row's dtype. The grid is (rows, I / BI).
    """

    r = tl.program_id(0)
    ri = tl.program_id(1) * BI + tl.arange(0, BI)
    im = ri < I

    g = tl.load(h_ptr + r * 2 * I + ri, mask=im, other=0.0).to(tl.float32)
    u = tl.load(h_ptr + r * 2 * I + I + ri, mask=im, other=0.0).to(tl.float32)
    gc = _tanh(g / gate_cap) * gate_cap
    uc = _tanh(u / up_cap) * up_cap
    tl.store(y_ptr + r * I + ri, (gc * tl.sigmoid(g) * uc).to(y_ptr.dtype.element_ty), mask=im)


def capped_gate(h: torch.Tensor, gate_cap: float, up_cap: float) -> torch.Tensor:
    """`Inkling2Ops.capped_gate`: h [R, 2 I] (contiguous) -> [R, I] in h's dtype."""

    R, I2 = h.shape
    I = I2 // 2  # noqa: E741
    y = torch.empty((R, I), dtype=h.dtype, device=h.device)
    bi = fused_block(I, 128)
    _capped_gate_jit[(R, triton.cdiv(I, bi))](
        h,
        y,
        gate_cap,
        up_cap,
        I,
        BI=bi,
        num_warps=1,
    )
    return y


##


def _weighted_rows_kernel(
        y_ptr,
        w_ptr,
        o_ptr,
        H,
        K: tl.constexpr,
        BH: tl.constexpr,
):
    """
    `Inkling2Ops.weighted_rows`: a tile of the hidden axis a program -- its K rows, each times its weight, summed in
    float32 and stored in the output's dtype. The grid is (N, H / BH); y [N, K, H], w [N, K].
    """

    n = tl.program_id(0)
    rh = tl.program_id(1) * BH + tl.arange(0, BH)
    hm = rh < H

    acc = tl.zeros((BH,), dtype=tl.float32)
    for j in tl.static_range(K):
        acc += tl.load(y_ptr + (n * K + j) * H + rh, mask=hm, other=0.0).to(tl.float32) * tl.load(w_ptr + n * K + j)
    tl.store(o_ptr + n * H + rh, acc.to(o_ptr.dtype.element_ty), mask=hm)


def weighted_rows(y: torch.Tensor, w: torch.Tensor, dtype: torch.dtype) -> torch.Tensor:
    """`Inkling2Ops.weighted_rows`: y [N, K, H] (contiguous), w [N, K] float32 -> [N, H] in `dtype`."""

    N, K, H = y.shape
    out = torch.empty((N, H), dtype=dtype, device=y.device)
    bh = fused_block(H, 128)
    _weighted_rows_jit[(N, triton.cdiv(H, bh))](
        y,
        w,
        out,
        H,
        K=K,
        BH=bh,
        num_warps=1,
    )
    return out


##


# (module globals, as backends/torch_triton.py's are and for its reason: a traced wrapper must find plain
# `JITFunction`s)
_pair_to_jit: ta.Any = None
_blend_z_jit: ta.Any = None
_blend_out_jit: ta.Any = None
_rms_norm_jit: ta.Any = None
_l2_clip_jit: ta.Any = None
_depth_mix_jit: ta.Any = None
_route_jit: ta.Any = None
_capped_gate_jit: ta.Any = None
_weighted_rows_jit: ta.Any = None


def ensure_inkling2_kernels() -> None:
    """Jit the kernels (once); until then nothing here has imported triton or torch."""

    global _pair_to_jit, _blend_z_jit, _blend_out_jit, _rms_norm_jit, _l2_clip_jit, _depth_mix_jit
    global _route_jit, _capped_gate_jit, _weighted_rows_jit

    if _blend_z_jit is not None:
        return

    g = globals()
    g['triton'] = importlib.import_module('triton')
    g['tl'] = importlib.import_module('triton.language')
    g['_tanh'] = triton.jit(_tanh)  # (a kernel calls it by this name)

    _blend_z_jit = triton.jit(_bottleneck_z_kernel)
    _blend_out_jit = triton.jit(_bottleneck_out_kernel, do_not_specialize=['H'])
    _rms_norm_jit = triton.jit(_rms_norm_kernel, do_not_specialize=['H', 'stride_x'])
    _l2_clip_jit = triton.jit(_l2_clip_kernel, do_not_specialize=['G'])
    _depth_mix_jit = triton.jit(_depth_mix_kernel, do_not_specialize=['H', 'Q'])
    _pair_to_jit = triton.jit(_pair_to_kernel, do_not_specialize=['N'])
    _route_jit = triton.jit(_sigmoid_route_kernel, do_not_specialize=['E'])
    _capped_gate_jit = triton.jit(_capped_gate_kernel, do_not_specialize=['I'])
    _weighted_rows_jit = triton.jit(_weighted_rows_kernel, do_not_specialize=['H'])
