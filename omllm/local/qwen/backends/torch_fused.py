# ruff: noqa: N803 N806
"""
Triton kernels that fuse small, regular pieces of a step: each replaces a chain of a dozen or more elementwise
operations, reductions and little matmuls that read almost nothing -- so that on a GPU their cost was their launches,
one or two microseconds apiece, and a model made of such pieces (Inkling 2: 12,600 launches a token) was bound by
them. A kernel here is one launch for the whole piece, over every row (token) of a step at once.

Each is the override of an `Ops` operation whose composed form (ops/base.py) is its definition and what its parity
test holds it to (tests/test_fused.py); none knows the model it is used in. The kernels for a family's own
operations are with the family (models/), behind its `OpsExtension`.

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


# (module globals, as torch_triton.py's are and for its reason: a traced wrapper must find plain `JITFunction`s)
_dense_gemv_jit: ta.Any = None
_dense_rows_jit: ta.Any = None
_kv_append_jit: ta.Any = None
_short_conv_jit: ta.Any = None
_window_partials_jit: ta.Any = None
_partials_merge_jit: ta.Any = None


def ensure_fused_kernels() -> None:
    """Jit the kernels (once); until then nothing here has imported triton or torch."""

    global _dense_gemv_jit, _dense_rows_jit, _kv_append_jit
    global _short_conv_jit, _window_partials_jit, _partials_merge_jit

    if _dense_gemv_jit is not None:
        return

    g = globals()
    g['triton'] = importlib.import_module('triton')
    g['tl'] = importlib.import_module('triton.language')

    _dense_gemv_jit = triton.jit(_dense_gemv_kernel, do_not_specialize=['N', 'K'])
    _dense_rows_jit = triton.jit(_dense_rows_kernel, do_not_specialize=['N', 'K', 'stride_x', 'stride_y'])
    _short_conv_jit = triton.jit(_short_conv_kernel, do_not_specialize=['C', 'G', 'stride_x'])
    _window_partials_jit = triton.jit(_window_partials_kernel, do_not_specialize=['T', 'H', 'N', 'L', 'E', 'window'])
    _kv_append_jit = triton.jit(
        _kv_append_kernel,
        do_not_specialize=['T', 'L', 'stride_kh', 'stride_kt', 'stride_vh', 'stride_vt'],
    )
    _partials_merge_jit = triton.jit(_partials_merge_kernel)
