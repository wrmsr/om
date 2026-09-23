# ruff: noqa: N803 N806 N812
"""
The fused DeltaNet token step for MLX as an `mx.fast.metal_kernel` -- the Metal twin of torch_triton.gdn_step.

One launch per layer instead of the ~8 kernels per token of the composed recurrence (1,500 of them in a T = 4 verify
step, each a Metal command at ~20 us). A threadgroup owns one head's state for a slice of TGV value columns: the [dk,
TGV] tile is loaded into threadgroup memory once, the T tokens are folded through it in place -- l2-norm of q/k, the
gate and the decay computed in-kernel, key heads broadcast by index -- and it is written back once (or after every token
when the caller needs the per-token states for speculative verify).

Layouts are Ops.gdn_step's: q, k [B, T, Hk, dk]; v [B, T, Hv, dv]; a, b [B, T, Hv]; A, dt_bias [Hv]; state [B, Hv, dk,
dv]; all float32, row-contiguous (the kernel wrapper ensures it). Outputs out [B, T, Hv, dv] and the final [B, Hv, dk,
dv] or per-token [T, B, Hv, dk, dv] state.

Only runs where Metal is available; `tests/test_mlx_metal.py` checks it against the composed reference there.
"""
import functools

import mlx.core as mx


##


SOURCE = r"""
    // shapes (row-contiguous inputs)
    const int B = q_shape[0];
    const int TT = q_shape[1];
    const int Hk = q_shape[2];
    const int Hv = v_shape[2];
    const int R = Hv / Hk;
    const int nvb = DV / TGV;

    const uint g = threadgroup_position_in_grid.x;
    const uint tid = thread_position_in_threadgroup.x;
    const int vb = g % nvb;
    const int bh = g / nvb;      // b * Hv + h
    const int bi = bh / Hv;
    const int h = bh % Hv;
    const int kh = h / R;
    const int vcol = vb * TGV + tid;

    const float EPS = consts[0];
    const float QSCALE = consts[1];

    threadgroup float S_tg[DK * TGV];
    threadgroup float qn[DK];
    threadgroup float kn[DK];

    // this thread's state column, for all T tokens
    const size_t s_base = (size_t)bh * DK * DV;
    for (int i = 0; i < DK; ++i) {
        S_tg[i * TGV + tid] = S[s_base + (size_t)i * DV + vcol];
    }
    const float A_h = A[h];
    const float dt_h = dt[h];

    for (int t = 0; t < TT; ++t) {
        // cooperative load of the raw q / k vectors for (b, t, kh)
        const size_t qk_base = (((size_t)bi * TT + t) * Hk + kh) * DK;
        for (int i = tid; i < DK; i += TGV) {
            qn[i] = q[qk_base + i];
            kn[i] = k[qk_base + i];
        }
        metal::threadgroup_barrier(metal::mem_flags::mem_threadgroup);

        // l2 norms (each thread redundantly; DK values from threadgroup memory)
        float sq = 0.0f;
        float sk = 0.0f;
        for (int i = 0; i < DK; ++i) {
            sq += qn[i] * qn[i];
            sk += kn[i] * kn[i];
        }
        const float qs = metal::rsqrt(sq + EPS) * QSCALE;
        const float ks = metal::rsqrt(sk + EPS);

        // gate and decay for this (b, t, h)
        const size_t ab_off = ((size_t)bi * TT + t) * Hv + h;
        const float beta = 1.0f / (1.0f + metal::exp(-b[ab_off]));
        const float xg = a[ab_off] + dt_h;
        const float sp = xg > 20.0f ? xg : metal::log(1.0f + metal::exp(xg));
        const float decay = metal::exp(A_h * sp);

        // S = S * decay; mem = k^T S
        float mem = 0.0f;
        for (int i = 0; i < DK; ++i) {
            const float s = S_tg[i * TGV + tid] * decay;
            S_tg[i * TGV + tid] = s;
            mem += s * (kn[i] * ks);
        }
        const size_t v_off = (((size_t)bi * TT + t) * Hv + h) * DV + vcol;
        const float delta = (v[v_off] - mem) * beta;

        // S = S + k (x) delta; o = q^T S
        float o = 0.0f;
        for (int i = 0; i < DK; ++i) {
            const float s = S_tg[i * TGV + tid] + (kn[i] * ks) * delta;
            S_tg[i * TGV + tid] = s;
            o += s * (qn[i] * qs);
        }
        out[v_off] = o;
        if (ALL) {
            const size_t so = (((size_t)t * B * Hv) + bh) * DK * DV;
            for (int i = 0; i < DK; ++i) {
                S_out[so + (size_t)i * DV + vcol] = S_tg[i * TGV + tid];
            }
        }
        // qn / kn are rewritten for the next token
        metal::threadgroup_barrier(metal::mem_flags::mem_threadgroup);
    }
    if (!ALL) {
        for (int i = 0; i < DK; ++i) {
            S_out[s_base + (size_t)i * DV + vcol] = S_tg[i * TGV + tid];
        }
    }
"""


# Register-only variant: KS lanes share one state column, each holding DK/KS entries in registers; the four reductions a
# token needs (the two norms, k^T S, q^T S) finish with SIMD shuffles across those lanes. No threadgroup memory, no
# barriers, KS times the threads of the threadgroup-memory variant -- which was occupancy-bound (6k threads for a 27B
# layer) -- and no 32 KB tile limit. The KS lanes of a column are adjacent within a SIMD group (KS divides 32), which is
# what the xor-shuffle butterfly needs.
SOURCE_SIMD = r"""
    const int B = q_shape[0];
    const int TT = q_shape[1];
    const int Hk = q_shape[2];
    const int Hv = v_shape[2];
    const int R = Hv / Hk;
    const int nvb = DV / TGV;
    const int DKS = DK / KS;

    const uint g = threadgroup_position_in_grid.x;
    const uint tid = thread_position_in_threadgroup.x;  // TGV * KS threads: column-major, KS lanes per column
    const int vb = g % nvb;
    const int bh = g / nvb;      // b * Hv + h
    const int bi = bh / Hv;
    const int h = bh % Hv;
    const int kh = h / R;
    const int lc = tid / KS;
    const int ks = tid % KS;
    const int vcol = vb * TGV + lc;
    const int k0 = ks * DKS;

    const float EPS = consts[0];
    const float QSCALE = consts[1];

    float sv[DKS];
    const size_t s_base = (size_t)bh * DK * DV;
    for (int i = 0; i < DKS; ++i) {
        sv[i] = S[s_base + (size_t)(k0 + i) * DV + vcol];
    }
    const float A_h = A[h];
    const float dt_h = dt[h];

    for (int t = 0; t < TT; ++t) {
        float qv[DKS];
        float kv[DKS];
        const size_t qk_base = (((size_t)bi * TT + t) * Hk + kh) * DK + k0;
        float sq = 0.0f;
        float sk = 0.0f;
        for (int i = 0; i < DKS; ++i) {
            qv[i] = q[qk_base + i];
            kv[i] = k[qk_base + i];
            sq += qv[i] * qv[i];
            sk += kv[i] * kv[i];
        }
        for (ushort o = 1; o < KS; o <<= 1) {
            sq += metal::simd_shuffle_xor(sq, o);
            sk += metal::simd_shuffle_xor(sk, o);
        }
        const float qs = metal::rsqrt(sq + EPS) * QSCALE;
        const float kn_s = metal::rsqrt(sk + EPS);

        const size_t ab_off = ((size_t)bi * TT + t) * Hv + h;
        const float beta = 1.0f / (1.0f + metal::exp(-b[ab_off]));
        const float xg = a[ab_off] + dt_h;
        const float sp = xg > 20.0f ? xg : metal::log(1.0f + metal::exp(xg));
        const float decay = metal::exp(A_h * sp);

        float mem = 0.0f;
        for (int i = 0; i < DKS; ++i) {
            sv[i] *= decay;
            mem += sv[i] * (kv[i] * kn_s);
        }
        for (ushort o = 1; o < KS; o <<= 1) {
            mem += metal::simd_shuffle_xor(mem, o);
        }
        const size_t v_off = (((size_t)bi * TT + t) * Hv + h) * DV + vcol;
        const float delta = (v[v_off] - mem) * beta;

        float o = 0.0f;
        for (int i = 0; i < DKS; ++i) {
            sv[i] += (kv[i] * kn_s) * delta;
            o += sv[i] * (qv[i] * qs);
        }
        for (ushort sh = 1; sh < KS; sh <<= 1) {
            o += metal::simd_shuffle_xor(o, sh);
        }
        if (ks == 0) {
            out[v_off] = o;
        }
        if (ALL) {
            const size_t so = (((size_t)t * B * Hv) + bh) * DK * DV;
            for (int i = 0; i < DKS; ++i) {
                S_out[so + (size_t)(k0 + i) * DV + vcol] = sv[i];
            }
        }
    }
    if (!ALL) {
        for (int i = 0; i < DKS; ++i) {
            S_out[s_base + (size_t)(k0 + i) * DV + vcol] = sv[i];
        }
    }
"""


@functools.lru_cache(maxsize=2)
def _kernel(variant: str = 'simd'):
    return mx.fast.metal_kernel(
        name=f'qwen35_gdn_step_{variant}',
        input_names=[
            'q',
            'k',
            'v',
            'a',
            'b',
            'A',
            'dt',
            'S',
            'consts',
        ],
        output_names=[
            'out',
            'S_out',
        ],
        source=SOURCE_SIMD if variant == 'simd' else SOURCE,
    )


def gdn_step_metal(
        q: mx.array,
        k: mx.array,
        v: mx.array,
        a: mx.array,
        b: mx.array,
        A: mx.array,
        dt_bias: mx.array,
        state: mx.array,
        all_states: bool,
        eps: float = 1e-6,
        tgv: int = 32,
        variant: str = 'simd',
        ks: int = 4,
) -> tuple[mx.array, mx.array]:
    """
    variant 'simd' (default): KS lanes per state column, registers + SIMD shuffles, TGV*KS threads per group. variant
    'tg': one lane per column with the [dk, TGV] tile in threadgroup memory (TGV <= 32 for dk = 128, the 32 KB limit);
    slower, kept as the fallback that was verified first.
    """

    B, T, Hk, dk = q.shape
    Hv, dv = v.shape[2], v.shape[3]
    f32 = mx.float32
    consts = mx.array([eps, dk ** -0.5], dtype=f32)
    inputs = [
        x.astype(f32)
        for x in (
            q,
            k,
            v,
            a,
            b,
            A,
            dt_bias,
            state,
        )
    ] + [consts]
    s_shape = (T, B, Hv, dk, dv) if all_states else (B, Hv, dk, dv)
    if variant == 'simd':
        ks = min(ks, dk)
        if dk % ks or 32 % ks:
            raise ValueError(f'ks={ks} must divide dk={dk} and 32')
        tgv = min(tgv, dv)
        while (tgv * ks) % 32 and tgv < dv:  # whole SIMD groups per threadgroup
            tgv *= 2
        if dv % tgv:
            raise ValueError(f'dv={dv} is not a multiple of tgv={tgv}')
        template = [('T', f32), ('DK', dk), ('DV', dv), ('TGV', tgv), ('KS', ks), ('ALL', bool(all_states))]
        grid = (B * Hv * dv * ks, 1, 1)
        threadgroup = (tgv * ks, 1, 1)
    else:
        tgv = min(tgv, dv, (32 * 1024 - 2 * 4 * dk) // (4 * dk))  # the tile + q/k vectors must fit in 32 KB
        if dv % tgv:
            raise ValueError(f'dv={dv} is not a multiple of tgv={tgv}')
        template = [('T', f32), ('DK', dk), ('DV', dv), ('TGV', tgv), ('ALL', bool(all_states))]
        grid = (B * Hv * dv, 1, 1)
        threadgroup = (tgv, 1, 1)
    out, s_out = _kernel(variant)(
        inputs=inputs,
        template=template,
        grid=grid,
        threadgroup=threadgroup,
        output_shapes=[(B, T, Hv, dv), s_shape],
        output_dtypes=[f32, f32],
    )
    return out, s_out
