# ruff: noqa: N803 N806
"""
The Qwen families' own operations: the gated delta rule of their linear-attention layers (core/deltanet.py), each
defined here once, composed from the seam's (ops/base.py) -- the reference: what any backend runs, and what a backend's
kernel is held to. The token step whole (`gdn_step`) is what backends fuse: a Triton kernel on torch (torch.py over
torchkernels.py), a Metal kernel on MLX (mlx.py over mlxmetal.py). `qwen_ops` (backends.py) gives a backend's.
"""
import typing as ta

from omcore import lang

from ....ops.base import Array
from ....ops.base import OpsExtension


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


##


class QwenOps(OpsExtension):
    def l2_norm(self, x: Array, eps: float = 1e-6) -> Array:
        # FLA-style: x / sqrt(sum(x^2) + eps)   (llama.cpp: rms_norm(x, eps/n) / sqrt(n) -- identical)
        return x * self.ops.rsqrt(self.ops.sum(x * x, -1, keepdims=True) + eps)

    gdn_chunk: int = 64

    def gated_delta(
            self,
            q: Array,
            k: Array,
            v: Array,
            g: Array,
            beta: Array,
            state: Array,
    ) -> tuple[Array, Array]:
        if q.shape[2] == 1:
            return self.gated_delta_recurrent(
                q,
                k,
                v,
                g,
                beta,
                state,
            )

        return self.gated_delta_chunked(
            q,
            k,
            v,
            g,
            beta,
            state,
            self.gdn_chunk,
        )

    def gated_delta_recurrent(
            self,
            q: Array,
            k: Array,
            v: Array,
            g: Array,
            beta: Array,
            state: Array,
    ) -> tuple[Array, Array]:
        """Per-token form: O(T) sequential steps, each a handful of small ops. The reference."""

        out, states = self.gated_delta_states(q, k, v, g, beta, state)
        return out, states[-1]

    def gated_delta_states(
            self,
            q: Array,
            k: Array,
            v: Array,
            g: Array,
            beta: Array,
            state: Array,
    ) -> tuple[Array, Array]:
        """
        The recurrence, also returning the state after every token: [T, B, H, dk, dv]. Speculative verify runs T = k + 1
        tokens and then keeps the state after however many were accepted.
        """

        T = q.shape[2]
        S = state
        outs = []
        states = []
        for t in range(T):
            # [B,H,dk] / [B,H,dv]
            q_t = q[:, :, t]
            k_t = k[:, :, t]
            v_t = v[:, :, t]
            S = S * self.ops.exp(g[:, :, t])[..., None, None]  # decay
            mem = self.ops.sum(S * k_t[..., None], -2)  # k^T S -> [B,H,dv]
            delta = (v_t - mem) * beta[:, :, t][..., None]
            S = S + k_t[..., None] * delta[..., None, :]  # rank-1 update
            outs.append(self.ops.sum(S * q_t[..., None], -2))  # q^T S
            states.append(S)
        return self.ops.stack(outs, 2), self.ops.stack(states, 0)

    def gated_delta_chunked(
            self,
            q: Array,
            k: Array,
            v: Array,
            g: Array,
            beta: Array,
            state: Array,
            chunk: int = 64,
    ) -> tuple[Array, Array]:
        """
        Chunkwise (WY-representation) form, Yang et al. 2024 -- the algorithm behind FLA's `chunk_gated_delta_rule` and
        HF's `torch_chunk_gated_delta_rule`, composed from the primitives so it runs (and is graph-friendly) on every
        backend. Within a chunk everything is a batched matmul; across chunks the state is carried sequentially, so cost
        is O(T/chunk) sequential steps instead of O(T).

        The per-chunk triangular inverse (I + A)^-1, A strictly lower, is computed as a Neumann product (I + N)(I +
        N^2)(I + N^4)... with N = -A, which is exact because N is nilpotent -- log2(chunk) matmuls and no item
        assignment, versus a forward-substitution loop.
        """

        B, H, T, dk = q.shape
        dv = v.shape[-1]
        C = chunk
        f32 = q.dtype
        pad = (C - T % C) % C
        if pad:
            q, k, v = [self.ops.concat([x, self.ops.zeros((B, H, pad, x.shape[-1]), f32)], 2) for x in (q, k, v)]
            g, beta = [self.ops.concat([x, self.ops.zeros((B, H, pad), f32)], 2) for x in (g, beta)]
        L = T + pad
        n = L // C
        q, k, v = [self.ops.reshape(x, (B, H, n, C, x.shape[-1])) for x in (q, k, v)]
        g, beta = [self.ops.reshape(x, (B, H, n, C)) for x in (g, beta)]

        tril = self.ops.array(np.tril(np.ones((C, C))), f32)  # i >= j
        strict = self.ops.array(np.tril(np.ones((C, C)), -1), f32)  # i > j
        eye = self.ops.array(np.eye(C), f32)

        gcum = self.ops.cumsum(g, -1)  # [B,H,n,C], decreasing
        # exp(gcum_i - gcum_j) for i >= j (<= 1), 0 above the diagonal; the exponent is masked *before* exp so the
        # positive upper-triangle exponents never overflow
        decay = self.ops.exp((gcum[..., :, None] - gcum[..., None, :]) * tril) * tril  # [B,H,n,C,C]
        kb = k * beta[..., None]
        vb = v * beta[..., None]
        A = (kb @ self.ops.transpose(k, (0, 1, 2, 4, 3))) * decay * strict  # strictly lower
        # (I + A)^-1 by forward substitution, row by row: T_i = e_i - A_i,<i @ T_<i. The Neumann product
        # (I+N)(I+N^2)(I+N^4)... is the same matrix in exact arithmetic but squares the intermediate powers, and
        # with correlated keys and beta near 1 (a repeated token) those powers are huge with cancelling signs:
        # unusable even in float64. Substitution reuses computed rows and is as stable as the recurrence itself.
        Tm = eye[0:1] + A[..., 0:1, :] * 0  # T_0 = e_0, broadcast to [B,H,n,1,C]
        for i in range(1, C):
            Tm = self.ops.concat([Tm, eye[i:i + 1] - A[..., i:i + 1, :i] @ Tm], -2)  # append T_i; Tm has i rows
        W = Tm @ (kb * self.ops.exp(gcum)[..., None])  # [B,H,n,C,dk]
        U = Tm @ vb  # [B,H,n,C,dv]

        S = state
        outs = []
        for i in range(n):
            # [B,H,C,dk]
            q_i = q[:, :, i]
            k_i = k[:, :, i]
            gc = gcum[:, :, i]  # [B,H,C]
            u = U[:, :, i] - W[:, :, i] @ S  # [B,H,C,dv]   v - (decayed) k S
            intra = (q_i @ self.ops.transpose(k_i, (0, 1, 3, 2))) * decay[:, :, i]
            outs.append((q_i * self.ops.exp(gc)[..., None]) @ S + intra @ u)
            g_last = gc[..., -1]  # [B,H]
            k_dec = k_i * self.ops.exp(g_last[..., None] - gc)[..., None]  # [B,H,C,dk]
            S = S * self.ops.exp(g_last)[..., None, None] + self.ops.transpose(k_dec, (0, 1, 3, 2)) @ u
        out = self.ops.reshape(self.ops.stack(outs, 2), (B, H, L, dv))
        if pad:
            out = out[:, :, :T]
        return out, S

    # up to this many tokens the model calls `gdn_step` (fusable); beyond, the chunked path. A backend whose fused
    # kernel takes any T (torch's Triton one) raises it, and its prefill goes through `gdn_step` too
    gdn_fused_max_t: int = 8

    def gdn_step(
            self,
            q: Array,
            k: Array,
            v: Array,
            a: Array,
            b: Array,
            A: Array,
            dt_bias: Array,
            state: Array,
            all_states: bool,
            eps: float = 1e-6,
    ) -> tuple[Array, Array]:
        """
        The whole DeltaNet token step from the projections' outputs, for T <= gdn_fused_max_t: l2-normalise q, k (and
        scale q by 1/sqrt(dk)), broadcast the Hk key heads over the Hv value heads, beta = sigmoid(b), g = A *
        softplus(a + dt_bias), then the recurrence. Layouts are the projections' natural ones -- q, k: [B, T, Hk, dk];
        v: [B, T, Hv, dv]; a, b: [B, T, Hv]; A, dt_bias: [Hv]; state: [B, Hv, dk, dv] -- and the output is [B, T, Hv,
        dv], so no transposes or head repeats are needed around it. Returns (out, state) or, with all_states, (out,
        states [T, B, Hv, dk, dv]). One op so a backend can replace the ~25 small kernels of this composition with a
        single fused one (see torchkernels.gdn_step).
        """

        B, T, Hk, dk = q.shape
        Hv = v.shape[2]
        dv = v.shape[3]  # noqa
        qn = self.ops.transpose(self.l2_norm(q, eps), (0, 2, 1, 3)) * (dk**-0.5)  # [B,Hk,T,dk]
        kn = self.ops.transpose(self.l2_norm(k, eps), (0, 2, 1, 3))
        vt = self.ops.transpose(v, (0, 2, 1, 3))  # [B,Hv,T,dv]
        if Hv != Hk:
            qn = self.ops.repeat(qn, Hv // Hk, 1)
            kn = self.ops.repeat(kn, Hv // Hk, 1)
        beta = self.ops.transpose(self.ops.sigmoid(b), (0, 2, 1))  # [B,Hv,T]
        g = self.ops.transpose(A[None, None, :] * self.ops.softplus(a + dt_bias), (0, 2, 1))
        if all_states:
            out, st = self.gated_delta_states(qn, kn, vt, g, beta, state)
        else:
            out, st = self.gated_delta(qn, kn, vt, g, beta, state)
        return self.ops.transpose(out, (0, 2, 1, 3)), st
