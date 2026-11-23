# ruff: noqa: N803 N806
"""
Triton kernels that fuse small, regular pieces of a step: each replaces a chain of a dozen or more elementwise
operations, reductions and little matmuls that read almost nothing -- so that on a GPU their cost was their launches,
one or two microseconds apiece, and a model made of such pieces (Inkling 2: 12,600 launches a token) was bound by
them. A kernel here is one launch for the whole piece, over every row (token) of a step at once.

Each is the override of an `Ops` operation whose composed form (ops/base.py) is its definition and what its parity
test holds it to (tests/test_fused.py); none knows the model it is used in.

Conventions are torch_triton.py's: the kernel bodies are plain functions, jitted into module globals by
`ensure_fused_kernels` (so a torch.compile trace of a wrapper finds a `JITFunction` and lowers the launch as a
user-defined kernel); no dataclass construction on a traced path; integer arguments that follow a prompt's length are
kept out of the kernels' specializations.
"""
import importlib
import typing as ta

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


def fused_block(n: int, cap: int = 256) -> int:
    """The power-of-two tile a kernel walks an axis of n elements in: `cap`, or the least one that covers n."""

    b = 16
    while b < min(n, cap):
        b *= 2
    return b


def is_pow2(n: int) -> bool:
    return n > 0 and not (n & (n - 1))


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


def _dense_gemv_kernel(
        x_ptr,
        w_ptr,
        y_ptr,
        N,
        K,
        BN: tl.constexpr,
        BK: tl.constexpr,
):
    """
    y [N] = w [N, K] x [K] for a plain (unquantized) weight: BN rows a program, the input axis in tiles of BK --
    one tile, for the widths here. Accumulated in float32, stored in y's dtype. The grid is N / BN.
    """

    rn = tl.program_id(0) * BN + tl.arange(0, BN)
    nm = rn < N
    rk0 = tl.arange(0, BK)

    acc = tl.zeros((BN,), dtype=tl.float32)
    for k0 in range(0, K, BK):
        rk = k0 + rk0
        km = rk < K
        w = tl.load(w_ptr + rn[:, None] * K + rk[None, :], mask=nm[:, None] & km[None, :], other=0.0).to(tl.float32)
        xv = tl.load(x_ptr + rk, mask=km, other=0.0).to(tl.float32)
        acc += tl.sum(w * xv[None, :], 1)
    tl.store(y_ptr + rn, acc.to(y_ptr.dtype.element_ty), mask=nm)


def dense_gemv(x: torch.Tensor, w: torch.Tensor) -> torch.Tensor:
    """
    `F.linear(x, w)` for one row of x ([..., K], K elements in all) and a plain contiguous w [N, K] of x's dtype:
    [..., N]. A row of w a program over the whole input axis: 1.4 to 9.6 us on the 5090 for 24 to 3,072 rows of
    2,304, weights cold, where cuBLAS takes 2.4 to 11.7 -- the large ones are the card's memory bandwidth either way.
    """

    N, K = w.shape
    y = torch.empty((*x.shape[:-1], N), dtype=x.dtype, device=x.device)
    _dense_gemv_jit[(N,)](
        x,
        w,
        y,
        N,
        K,
        BN=1,
        BK=min(fused_block(K, 1 << 16), 4096),
        num_warps=2,
    )
    return y


def _dense_rows_kernel(
        x_ptr,
        w_ptr,
        y_ptr,
        N,
        K,
        stride_x,
        stride_y,
        T: tl.constexpr,
        TILE: tl.constexpr,
        BT: tl.constexpr,
        BN: tl.constexpr,
        BK: tl.constexpr,
):
    """
    y [T, N] = x [T, K] w [N, K]^T for a plain weight and a few rows of x: BN rows of w a program, loaded once over
    the whole input axis (K <= BK) and multiplied into every row of x -- all of them as one tile (TILE; BT the power
    of two that covers T), or a row at a time. Accumulated in float32, stored in y's dtype. The grid is N / BN.
    """

    rn = tl.program_id(0) * BN + tl.arange(0, BN)
    nm = rn < N
    rk = tl.arange(0, BK)
    km = rk < K

    w = tl.load(w_ptr + rn[:, None] * K + rk[None, :], mask=nm[:, None] & km[None, :], other=0.0).to(tl.float32)
    if TILE:
        rt = tl.arange(0, BT)
        tm = rt < T
        xv = tl.load(x_ptr + rt[:, None] * stride_x + rk[None, :], mask=tm[:, None] & km[None, :], other=0.0)
        acc = tl.sum(w[:, None, :] * xv.to(tl.float32)[None, :, :], 2)  # [BN, BT]
        tl.store(
            y_ptr + rt[None, :] * stride_y + rn[:, None],
            acc.to(y_ptr.dtype.element_ty),
            mask=nm[:, None] & tm[None, :],
        )
    else:
        for t in tl.static_range(T):
            xt = tl.load(x_ptr + t * stride_x + rk, mask=km, other=0.0).to(tl.float32)
            tl.store(y_ptr + t * stride_y + rn, tl.sum(w * xt[None, :], 1).to(y_ptr.dtype.element_ty), mask=nm)


# What `dense_rows` is for: up to 8 rows of x, and rows of x times rows of w up to 12,288. Alone and cold in a
# captured graph (the 5090, K = 2,304, bfloat16) it takes 1.5 / 1.9 / 2.6 us for 2 / 4 / 8 rows against a w of 24,
# 4.5 / 5.6 / 8.3 against one of 1,024 and 9.9 / 12.4 against one of 3,072, where cuBLAS takes 11 to 15 for most
# of those shapes and under 4 for a few. What settled the limits is a whole verify step of Inkling 2 Mini, which
# went from 13.8 to 10.8 ms at 2 rows, 17.1 to 14.7 at 4 and 22.9 to 21.0 at 8 -- and at 16 rows was 2 ms slower
# with any of its products here, the small ones included.
DENSE_ROWS_MAX_T = 8
DENSE_ROWS_MAX_PRODUCTS = 12288
DENSE_ROWS_MAX_K = 4096


def dense_rows_pays(rows: int, n: int) -> bool:
    """Whether `dense_rows` is the way to multiply `rows` rows of x by a w of `n` rows (the limits above)."""

    return 1 < rows <= DENSE_ROWS_MAX_T and rows * n <= DENSE_ROWS_MAX_PRODUCTS


def dense_rows(x: torch.Tensor, w: torch.Tensor) -> torch.Tensor:
    """
    `F.linear(x, w)` for a few rows of x [T, K] and a plain contiguous w [N, K] of x's dtype, K and T within the
    limits above: [T, N]. A speculative round's verify step is such rows, and most of its projections were each a
    cuBLAS launch that cost what the product of one row does not.
    """

    T, K = x.shape
    N = w.shape[0]
    x = x if x.is_contiguous() else x.contiguous()
    y = torch.empty((T, N), dtype=x.dtype, device=x.device)
    small = N <= 256
    bn = 1 if small else 2
    _dense_rows_jit[(triton.cdiv(N, bn),)](
        x,
        w,
        y,
        N,
        K,
        x.stride(0),
        y.stride(0),
        T=T,
        TILE=small,
        BT=triton.next_power_of_2(T),
        BN=bn,
        BK=fused_block(K, DENSE_ROWS_MAX_K),
        num_warps=4,
    )
    return y


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
    The bottleneck of `Ops.bottleneck_blend`: z [rows, R] = down [unit(x) | unit(m)], rounded to down's dtype. The
    grid is (rows, R / BR), and a program takes the whole hidden axis as one tile: it sums its row's squares for
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
    The blend of `Ops.bottleneck_blend` from its bottleneck: (1 - tanh(forget z)) x + tanh(gain z) m, a tile of the
    hidden axis a program. The grid is (rows, H / BH).
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
    `Ops.bottleneck_blend`: x, m [..., H] float32; down [R, 2H]; forget, gain [H, R] float32. R a power of two. Two
    launches: the bottleneck, then the blend.
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


def _short_conv_kernel(
        x_ptr,
        h_ptr,
        w_ptr,
        d_ptr,
        y_ptr,
        o_ptr,
        stride_x,
        scale,
        C,
        G,
        K: tl.constexpr,
        BC: tl.constexpr,
        DYN: tl.constexpr,
):
    """
    `Ops.short_conv` and, with DYN, `Ops.short_conv_dynamic`: row t of y, a tile of channels a program, and beside it
    the history as it stands after that row -- the K - 1 inputs up to it -- which is what the row's last K - 1 taps
    read. Input j of [history | x] is a history column while j < K - 1 and a row of x after. The static taps are w
    [C, K], oldest first; with DYN they are w [K, C] by backward lag, and each position adds its own, d [T, G, K] by
    lag, a group's shared by its C / G channels. The grid is (T, C / BC).
    """

    t = tl.program_id(0)
    rc = tl.program_id(1) * BC + tl.arange(0, BC)
    cm = rc < C

    acc = tl.zeros((BC,), dtype=tl.float32)
    cur = tl.zeros((BC,), dtype=tl.float32)
    for a in tl.static_range(K):
        j = t + a
        old = (rc * 0 + j) < (K - 1)  # (a tile-shaped mask: the interpreter takes no scalar one)
        hv = tl.load(h_ptr + rc * (K - 1) + j, mask=cm & old, other=0.0)
        xv = tl.load(x_ptr + (j - (K - 1)) * stride_x + rc, mask=cm & (~old), other=0.0).to(tl.float32)
        src = hv + xv
        if DYN:
            lag = K - 1 - a
            tap = tl.load(w_ptr + lag * C + rc, mask=cm, other=0.0)
            tap += tl.load(d_ptr + (t * G + rc // (C // G)) * K + lag, mask=cm, other=0.0).to(tl.float32)
        else:
            tap = tl.load(w_ptr + rc * K + a, mask=cm, other=0.0)
        acc += tap * src
        if a > 0:
            tl.store(o_ptr + (t * C + rc) * (K - 1) + (a - 1), src, mask=cm)
        cur = src

    tl.store(y_ptr + t * C + rc, ((cur + acc) * scale).to(y_ptr.dtype.element_ty), mask=cm)


def short_conv(
        x: torch.Tensor,
        hist: torch.Tensor | None,
        weight: torch.Tensor,
        scale: float,
        all_states: bool,
        dyn: torch.Tensor | None = None,
        bc_cap: int = 128,
        num_warps: int = 1,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    `Ops.short_conv`: x [1, T, C]; hist [1, C, K - 1] float32 or None; weight [C, K] float32. With `dyn` [1, T, G, K]
    (contiguous), `Ops.short_conv_dynamic`, whose weight is [K, C]. (Tiles of 128 channels on one warp: 1.2 us on the
    5090 where one tile of the whole axis on four took 80.)
    """

    _, T, C = x.shape
    K = weight.shape[0] if dyn is not None else weight.shape[-1]
    x2 = x.reshape(T, C)
    if hist is None:
        hist = torch.zeros((1, C, K - 1), dtype=torch.float32, device=x.device)
    y = torch.empty((T, C), dtype=x.dtype, device=x.device)
    after = torch.empty((T, C, K - 1), dtype=torch.float32, device=x.device)
    bc = fused_block(C, bc_cap)
    _short_conv_jit[(T, triton.cdiv(C, bc))](
        x2,
        hist,
        weight,
        dyn if dyn is not None else weight,
        y,
        after,
        x2.stride(0),
        scale,
        C,
        dyn.shape[2] if dyn is not None else 1,
        K=K,
        BC=bc,
        DYN=dyn is not None,
        num_warps=num_warps,
    )
    if all_states:
        return y.reshape(1, T, C), after.reshape(T, 1, C, K - 1)
    # (the last row's alone, as a tensor of its own: a view would keep every row's alive in the layer's state -- 15 GB
    # of them over a 4,096-token prefill chunk's 192 convolutions)
    return y.reshape(1, T, C), (after if T == 1 else after[T - 1:].clone())


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
    `Ops.rms_norm_to`: a tile of a row a program, x / sqrt(mean(x^2) + eps) * w in the output's dtype. Each program
    sums its row's squares for itself. The grid is (rows, H / BH).
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
    `Ops.rms_norm_to`: x [..., H] (rows evenly strided), w [H] -> x's shape in `dtype`. A row is one program up to
    4,096 wide, on eight warps from 2,048: 1.2 us for a row of 2,304 in a captured graph on the 5090, where tiles of
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
    `Ops.l2_clip` over x [T, G, D]: a tile of BG of a row's G vectors a program, each scaled (and rounded to x's
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
    """`Ops.l2_clip`: x [1, T, G, D] (contiguous), D a power of two; scale [G, D] in x's dtype; after [T] float32."""

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
    `Ops.depth_mix`: for row t and query q, a tile of the hidden axis a program. Each program takes its own measure
    of every source first -- its dot product with the query and, for the last RAW ones, its mean square -- which is
    S passes over a few thousand floats and lets no program wait on another; then its tile of the weighted sum.
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
    """`Ops.depth_mix`: queries [Q, H] float32; up to six sources [1, T, H] (each contiguous). [1, T, Q, H] float32."""

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


def _window_partials_kernel(
        q_ptr,
        k_ptr,
        v_ptr,
        r_ptr,
        p_ptr,
        pos_ptr,
        b_ptr,
        m_ptr,
        l_ptr,
        o_ptr,
        scale,
        T,
        H,
        N,
        L,
        E,
        window,
        G: tl.constexpr,
        D: tl.constexpr,
        R: tl.constexpr,
        BN: tl.constexpr,
        P: tl.constexpr,
):
    """
    `Ops.sdpa_window_rel` short of its softmax's normalization: for query (t, h) and a tile of BN of the window's N
    slots, the largest score m, and relative to it the scores' exponentials' sum l and the values weighted by them o
    [D]. Slot j stands for position pos + T - N + j; query t sees the ones 0 <= d < window back that are positions at
    all, and a score has rel[t, h] . rel_proj[d] added for d < E. A tile with nothing in it for its query has m =
    -1e30, l = 0, o = 0. The grid is (T * H, N / BN); q [T, H, D], rel [T, H, R], rel_proj [E, R]; k, v [KV, L, D],
    of which the window is the N slots from the one at b_ptr on (L = N and 0 for a window that is all of them).
    """

    th = tl.program_id(0)
    part = tl.program_id(1)
    t = th // H
    h = th % H
    kh = h // G
    rj = part * BN + tl.arange(0, BN)
    rd = tl.arange(0, D)
    rr = tl.arange(0, R)

    pos = tl.load(pos_ptr)
    d = (N - T + t) - rj  # how far back slot j is from the query
    seen = (rj < N) & (d >= 0) & (d < window) & ((pos + T - N + rj) >= 0)
    at = (kh * L + tl.load(b_ptr) + rj[:, None]) * D + rd[None, :]  # where the tile's slots lie in k and v

    qv = tl.load(q_ptr + th * D + rd).to(tl.float32)
    kt = tl.load(k_ptr + at, mask=seen[:, None], other=0.0).to(tl.float32)
    sc = tl.sum(kt * qv[None, :], 1) * scale

    near = seen & (d < E)
    rv = tl.load(r_ptr + th * R + rr).to(tl.float32)
    pt = tl.load(p_ptr + d[:, None] * R + rr[None, :], mask=near[:, None], other=0.0).to(tl.float32)
    sc = tl.where(seen, sc + tl.sum(pt * rv[None, :], 1), -1e30)

    m = tl.max(sc, 0)
    w = tl.where(seen, tl.exp(sc - m), 0.0)
    vt = tl.load(v_ptr + at, mask=seen[:, None], other=0.0).to(tl.float32)

    tl.store(m_ptr + th * P + part, m)
    tl.store(l_ptr + th * P + part, tl.sum(w, 0))
    tl.store(o_ptr + (th * P + part) * D + rd, tl.sum(vt * w[:, None], 0))


def _partials_merge_kernel(
        m_ptr,
        l_ptr,
        o_ptr,
        s_ptr,
        y_ptr,
        D: tl.constexpr,
        P: tl.constexpr,
        BP: tl.constexpr,
        SINK: tl.constexpr,
):
    """
    One softmax of P sets of partials a row -- m, l [rows, P] and o [rows, P, D] float32, as `Ops.sdpa_partials`
    gives them -- and, with SINK, one more logit a row with nothing behind it: (sum_p w_p o_p) / (sum_p w_p l_p +
    exp(sink - top)), w_p = exp(m_p - top), top the largest of them. The grid is the rows.
    """

    row = tl.program_id(0)
    rp = tl.arange(0, BP)
    pm = rp < P
    rd = tl.arange(0, D)

    m = tl.load(m_ptr + row * P + rp, mask=pm, other=-1e30)
    ls = tl.load(l_ptr + row * P + rp, mask=pm, other=0.0)
    top = tl.max(m, 0)
    den = 0.0
    if SINK:
        z = tl.load(s_ptr + row).to(tl.float32)
        top = tl.maximum(top, z)
        den = tl.exp(z - top)
    w = tl.where(pm, tl.exp(m - top), 0.0)
    den += tl.sum(w * ls, 0)

    o = tl.load(o_ptr + (row * P + rp[:, None]) * D + rd[None, :], mask=pm[:, None], other=0.0)
    y = tl.sum(o * w[:, None], 0) / den
    tl.store(y_ptr + row * D + rd, y.to(y_ptr.dtype.element_ty))


def _kv_append_kernel(
        k_ptr,
        v_ptr,
        kb_ptr,
        vb_ptr,
        p_ptr,
        T,
        L,
        stride_kh,
        stride_kt,
        stride_vh,
        stride_vt,
        D: tl.constexpr,
):
    """
    A step's keys and values written into their buffers: k, v [KV, T, D] (any strides over the first two axes) into
    kb, vb [KV, L, D] at the positions from the one at p_ptr on, cast to the buffers' dtype. The grid is KV * T.
    """

    i = tl.program_id(0)
    kh = i // T
    t = i % T
    rd = tl.arange(0, D)
    at = (kh * L + tl.load(p_ptr) + t) * D + rd
    tl.store(kb_ptr + at, tl.load(k_ptr + kh * stride_kh + t * stride_kt + rd).to(kb_ptr.dtype.element_ty))
    tl.store(vb_ptr + at, tl.load(v_ptr + kh * stride_vh + t * stride_vt + rd).to(vb_ptr.dtype.element_ty))


def kv_append(
        kbuf: torch.Tensor,
        vbuf: torch.Tensor,
        pos: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
) -> None:
    """
    k, v [1, KV, T, D] written into the plain buffers kbuf, vbuf [1, KV, L, D] at positions pos .. pos + T - 1 (`pos`
    a 0-d int tensor), in place: `Ops.kv_write_tokens` as one launch, where the indexed write is five -- the index
    made of three, a copy for each buffer -- for every attention layer of a step. D a power of two; the buffers
    contiguous, k and v contiguous along their last axis.
    """

    _, KV, T, D = k.shape
    _kv_append_jit[(KV * T,)](
        k,
        v,
        kbuf,
        vbuf,
        pos,
        T,
        kbuf.shape[2],
        k.stride(1),
        k.stride(2),
        v.stride(1),
        v.stride(2),
        D=D,
        num_warps=1,
    )


_FUSED_ZEROS: dict[ta.Any, ta.Any] = {}


def _fused_zero(device: ta.Any) -> torch.Tensor:
    """A 0-d int32 zero on `device`, made once: what a kernel that takes an offset is handed for none."""

    try:
        return _FUSED_ZEROS[device]
    except KeyError:
        z = _FUSED_ZEROS[device] = torch.zeros((), dtype=torch.int32, device=device)
        return z


def window_partials(
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        pos: torch.Tensor,
        scale: float,
        rel: torch.Tensor,
        rel_proj: torch.Tensor,
        window: int,
        extra: int = 0,
        block_n: int = 64,
        base: torch.Tensor | None = None,
        slots: int | None = None,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    The window's partials for `merge_partials`, a set a tile of block_n slots: m, l [T * H, P + extra] and o [T * H,
    P + extra, D] float32, rows (t, h). The last `extra` sets are left for the caller to fill (keys scored some other
    way). q [1, H, T, D]; k, v [1, KV, N, D] dense and contiguous -- or, with `base` (a 0-d int32 tensor) and
    `slots`, buffers [1, KV, L, D] of which the window is the `slots` positions from `base` on; pos a 0-d int
    tensor; rel [T, H, R]; rel_proj [E, R]. D and R powers of two.
    """

    _, H, T, D = q.shape
    KV, L = k.shape[1], k.shape[2]
    N = L if slots is None else slots
    if base is None:
        base = _fused_zero(q.device)
    E, R = rel_proj.shape
    qt = q.transpose(1, 2).contiguous()  # [1, T, H, D]: rows (t, h) (a view of what was transposed to make q)
    P = triton.cdiv(N, block_n)
    rows = T * H
    m = torch.empty((rows, P + extra), dtype=torch.float32, device=q.device)
    ls = torch.empty((rows, P + extra), dtype=torch.float32, device=q.device)
    o = torch.empty((rows, P + extra, D), dtype=torch.float32, device=q.device)
    _window_partials_jit[(rows, P)](
        qt,
        k,
        v,
        rel,
        rel_proj,
        pos,
        base,
        m,
        ls,
        o,
        scale,
        T,
        H,
        N,
        L,
        E,
        window,
        G=H // KV,
        D=D,
        R=R,
        BN=block_n,
        P=P + extra,
        num_warps=4,
    )
    return m, ls, o


def merge_partials(
        m: torch.Tensor,
        ls: torch.Tensor,
        o: torch.Tensor,
        sink: torch.Tensor,
        dtype: torch.dtype,
) -> torch.Tensor:
    """
    One softmax of each row's sets of partials (m, l [T * H, P], o [T * H, P, D], rows (t, h)) and its sink (`sink`
    [1, H, T]): the attention output [1, H, T, D] in `dtype`.
    """

    _, H, T = sink.shape
    rows, P, D = o.shape
    st = sink.transpose(1, 2).contiguous()
    y = torch.empty((1, T, H, D), dtype=dtype, device=o.device)
    _partials_merge_jit[(rows,)](
        m,
        ls,
        o,
        st,
        y,
        D=D,
        P=P,
        BP=fused_block(P, 1 << 16),
        SINK=True,
        num_warps=2,
    )
    return y.transpose(1, 2)


def sdpa_window_rel(
        q: torch.Tensor,
        k: torch.Tensor,
        v: torch.Tensor,
        pos: torch.Tensor,
        scale: float,
        rel: torch.Tensor,
        rel_proj: torch.Tensor,
        sink: torch.Tensor,
        window: int,
        more: ta.Sequence[tuple[torch.Tensor, torch.Tensor, torch.Tensor]] = (),
        block_n: int = 64,
        base: torch.Tensor | None = None,
        slots: int | None = None,
) -> torch.Tensor:
    """
    `Ops.sdpa_window_rel`. Two launches: every tile of the window's partials, then their softmax with the sink --
    and with `more`'s sets ([1, H, T], [1, H, T], [1, H, T, D]: `Ops.sdpa_partials`), laid beside the window's.
    With `base` and `slots`, `Ops.sdpa_window_rel_at`: the window read where it lies in k and v.
    """

    m, ls, o = window_partials(
        q,
        k,
        v,
        pos,
        scale,
        rel,
        rel_proj,
        window,
        extra=len(more),
        block_n=block_n,
        base=base,
        slots=slots,
    )
    for i, (mm, ll, oo) in enumerate(more):
        j = m.shape[1] - len(more) + i
        m[:, j] = mm[0].transpose(0, 1).reshape(-1)  # (rows (h, t) -> (t, h))
        ls[:, j] = ll[0].transpose(0, 1).reshape(-1)
        o[:, j] = oo[0].transpose(0, 1).reshape(-1, oo.shape[-1])
    return merge_partials(m, ls, o, sink, q.dtype)


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
    `Ops.sigmoid_route` for one row: its E scores' sigmoids; the K largest of score + bias, picked one at a time
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
    """`Ops.sigmoid_route`: logits [N, E] (contiguous); bias [E] float32. (indices [N, k] int32, weights [N, k])."""

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


def _pair_to_kernel(
        a_ptr,
        b_ptr,
        y_ptr,
        N,
        GATED: tl.constexpr,
        BN: tl.constexpr,
):
    """
    Two arrays' elements combined in float32 and stored in y's dtype, a tile of N a program: a + b (`Ops.sum_to`),
    or with GATED a * sigmoid(b) (`Ops.sigmoid_gated`). The grid is N / BN.
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
    `Ops.sum_to` for contiguous a, b of one shape: one launch where the composed form is two casts, an add and a
    cast -- a stream's write, twice a layer.
    """

    return _pair_to(a, b, dtype, False)


def sigmoid_gated(x: torch.Tensor, g: torch.Tensor, dtype: torch.dtype) -> torch.Tensor:
    """`Ops.sigmoid_gated` for contiguous x, g of one shape: one launch for the composed form's five."""

    return _pair_to(x, g, dtype, True)


def _capped_gate_kernel(
        h_ptr,
        y_ptr,
        gate_cap,
        up_cap,
        I,  # noqa: E741
        BI: tl.constexpr,
):
    """
    `Ops.capped_gate`: a tile of a row's I outputs a program -- from the row's two halves g | u, (gate_cap tanh(g /
    gate_cap)) sigmoid(g) (up_cap tanh(u / up_cap)), in the row's dtype. The grid is (rows, I / BI).
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
    """`Ops.capped_gate`: h [R, 2 I] (contiguous) -> [R, I] in h's dtype."""

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


def _weighted_rows_kernel(
        y_ptr,
        w_ptr,
        o_ptr,
        H,
        K: tl.constexpr,
        BH: tl.constexpr,
):
    """
    `Ops.weighted_rows`: a tile of the hidden axis a program -- its K rows, each times its weight, summed in float32
    and stored in the output's dtype. The grid is (N, H / BH); y [N, K, H], w [N, K].
    """

    n = tl.program_id(0)
    rh = tl.program_id(1) * BH + tl.arange(0, BH)
    hm = rh < H

    acc = tl.zeros((BH,), dtype=tl.float32)
    for j in tl.static_range(K):
        acc += tl.load(y_ptr + (n * K + j) * H + rh, mask=hm, other=0.0).to(tl.float32) * tl.load(w_ptr + n * K + j)
    tl.store(o_ptr + n * H + rh, acc.to(o_ptr.dtype.element_ty), mask=hm)


def weighted_rows(y: torch.Tensor, w: torch.Tensor, dtype: torch.dtype) -> torch.Tensor:
    """`Ops.weighted_rows`: y [N, K, H] (contiguous), w [N, K] float32 -> [N, H] in `dtype`."""

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


# (module globals, as torch_triton.py's are and for its reason: a traced wrapper must find plain `JITFunction`s)
_dense_gemv_jit: ta.Any = None
_dense_rows_jit: ta.Any = None
_kv_append_jit: ta.Any = None
_pair_to_jit: ta.Any = None
_blend_z_jit: ta.Any = None
_blend_out_jit: ta.Any = None
_short_conv_jit: ta.Any = None
_rms_norm_jit: ta.Any = None
_l2_clip_jit: ta.Any = None
_depth_mix_jit: ta.Any = None
_window_partials_jit: ta.Any = None
_partials_merge_jit: ta.Any = None
_route_jit: ta.Any = None
_capped_gate_jit: ta.Any = None
_weighted_rows_jit: ta.Any = None


def ensure_fused_kernels() -> None:
    """Jit the kernels (once); until then nothing here has imported triton or torch."""

    global _blend_z_jit, _blend_out_jit, _short_conv_jit, _l2_clip_jit, _depth_mix_jit, _rms_norm_jit
    global _window_partials_jit, _partials_merge_jit, _route_jit, _capped_gate_jit, _weighted_rows_jit
    global _dense_gemv_jit, _dense_rows_jit, _kv_append_jit, _pair_to_jit

    if _blend_z_jit is not None:
        return

    g = globals()
    g['triton'] = importlib.import_module('triton')
    g['tl'] = importlib.import_module('triton.language')
    g['_tanh'] = triton.jit(_tanh)  # (a kernel calls it by this name)

    _dense_gemv_jit = triton.jit(_dense_gemv_kernel, do_not_specialize=['N', 'K'])
    _dense_rows_jit = triton.jit(_dense_rows_kernel, do_not_specialize=['N', 'K', 'stride_x', 'stride_y'])
    _blend_z_jit = triton.jit(_bottleneck_z_kernel)
    _blend_out_jit = triton.jit(_bottleneck_out_kernel, do_not_specialize=['H'])
    _short_conv_jit = triton.jit(_short_conv_kernel, do_not_specialize=['C', 'G', 'stride_x'])
    _rms_norm_jit = triton.jit(_rms_norm_kernel, do_not_specialize=['H', 'stride_x'])
    _l2_clip_jit = triton.jit(_l2_clip_kernel, do_not_specialize=['G'])
    _depth_mix_jit = triton.jit(_depth_mix_kernel, do_not_specialize=['H', 'Q'])
    _window_partials_jit = triton.jit(_window_partials_kernel, do_not_specialize=['T', 'H', 'N', 'L', 'E', 'window'])
    _pair_to_jit = triton.jit(_pair_to_kernel, do_not_specialize=['N'])
    _kv_append_jit = triton.jit(
        _kv_append_kernel,
        do_not_specialize=['T', 'L', 'stride_kh', 'stride_kt', 'stride_vh', 'stride_vt'],
    )
    _partials_merge_jit = triton.jit(_partials_merge_kernel)
    _route_jit = triton.jit(_sigmoid_route_kernel, do_not_specialize=['E'])
    _capped_gate_jit = triton.jit(_capped_gate_kernel, do_not_specialize=['I'])
    _weighted_rows_jit = triton.jit(_weighted_rows_kernel, do_not_specialize=['H'])
