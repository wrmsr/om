# ruff: noqa: N803 N806 N812
import typing as ta

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from .cache import LinearState
from .config import Qwen35Config
from .mixing import Mixer
from .mixing import StateLayout
from .mixing import StepContext


##


class RecurrentStateLayout(StateLayout):
    """
    A Gated DeltaNet layer's state: (conv history [B, conv_dim, K-1], recurrent state S [B, Hv, dk, dv]), float32 and
    fixed-size -- nothing to pad, and a T-token step that returns the state after every token commits by selecting one.
    """

    def __init__(
            self,
            *,
            conv_dim: int,
            conv_kernel: int,
            num_v_heads: int,
            head_k_dim: int,
            head_v_dim: int,
    ) -> None:
        super().__init__()

        self._conv_dim = conv_dim
        self._conv_kernel = conv_kernel
        self._num_v_heads = num_v_heads
        self._head_k_dim = head_k_dim
        self._head_v_dim = head_v_dim

    def arity(self, ops: Ops) -> int:
        return 2

    def empty(self, ops: Ops, dtype: ta.Any) -> tuple[Array, ...]:
        f32 = ops.dtype('f32')
        return (
            ops.zeros((1, self._conv_dim, self._conv_kernel - 1), f32),
            ops.zeros((1, self._num_v_heads, self._head_k_dim, self._head_v_dim), f32),
        )

    def adapt(self, ops: Ops, state: tuple[Array, ...], dtype: ta.Any) -> tuple[Array, ...]:
        return state

    def pad(self, ops: Ops, state: tuple[Array, ...], capacity: int) -> tuple[Array, ...]:
        # fixed-size: nothing to pad -- but dense copies, whatever came in. This is where every generation's state
        # enters the static decoder, and a compiled step is guarded on its inputs' strides: a prefill's conv history
        # was once a slice whose strides depended on the prompt's length, so every new length recompiled (~20 s on
        # the 27B). The mixer now hands over dense state itself (see GatedDeltaNet.__call__); this keeps it so.
        return tuple(ops.copy(a) for a in state)

    def export(self, ops: Ops, state: tuple[Array, ...], seq_len: int) -> tuple[Array, ...]:
        return tuple(ops.copy(a) for a in state)

    def commit(self, ops: Ops, state: tuple[Array, ...], n: int, stacked: bool) -> tuple[Array, ...]:
        if not stacked:
            return state
        return tuple(ops.select(a, n - 1) for a in state)

    def capacity(self, ops: Ops, state: tuple[Array, ...]) -> int | None:
        return None


class GatedDeltaNet(Mixer):
    def __init__(self, cfg: Qwen35Config, p: dict[str, Weight]) -> None:
        super().__init__()

        self._state = RecurrentStateLayout(
            conv_dim=cfg.conv_dim,
            conv_kernel=cfg.conv_kernel,
            num_v_heads=cfg.num_v_heads,
            head_k_dim=cfg.head_k_dim,
            head_v_dim=cfg.head_v_dim,
        )
        self.cfg = cfg
        self.w_qkvz = p.get('in_proj_qkvz')  # fused [qkv | z] when the loader provides it
        self.w_qkv = p.get('in_proj_qkv')
        self.w_z = p.get('in_proj_z')
        # the two low-rank [n_v, hidden] projections are fused into one [2 n_v, hidden] matmul when the loader provides
        # it (see from_source); separate weights are still accepted
        self.w_ab = p.get('in_proj_ab')
        self.w_a = p.get('in_proj_a')
        self.w_b = p.get('in_proj_b')
        self.conv_w = p['conv1d']  # [conv_dim, K] float32
        self.A = p['A']  # [n_v] == -exp(A_log), float32
        self.dt_bias = p['dt_bias']  # [n_v] float32
        self.norm_w = p['norm']
        self.w_out = p['out_proj']

    @property
    def state(self) -> StateLayout:
        return self._state

    def __call__(self, ops: Ops, x: Array, pos: int, state: LinearState | None) -> tuple[Array, LinearState]:
        return self._mix(ops, x, state, False)

    def step(self, ops: Ops, x: Array, ctx: StepContext, state: LinearState) -> tuple[Array, LinearState]:
        return self._mix(ops, x, state, ctx.all_states)

    def _mix(
            self,
            ops: Ops,
            x: Array,
            state: LinearState | None,
            all_states: bool,
    ) -> tuple[Array, LinearState]:
        """
        With all_states the returned pair is stacked per token -- conv [T, B, C, K-1], S [T, B, H, dk, dv] -- so a
        speculative verify can keep the state after exactly the accepted prefix (the KV side needs no rollback: stale
        positions are masked by `pos`).
        """

        c = self.cfg
        B, T, _ = x.shape
        Hk = c.num_k_heads
        Hv = c.num_v_heads
        dk = c.head_k_dim
        dv = c.head_v_dim
        K = c.conv_kernel
        f32 = ops.dtype('f32')

        if self.w_qkvz is not None:
            qkv, z = ops.split(ops.f32(ops.linear(x, self.w_qkvz)), [c.conv_dim, c.value_dim], -1)
        else:
            qkv = ops.f32(ops.linear(x, self.w_qkv))
            z = ops.f32(ops.linear(x, self.w_z))  # [B, T, value_dim]
        qkv = ops.transpose(qkv, (0, 2, 1))  # [B, conv_dim, T]

        if self.w_ab is not None:
            a, b = ops.split(ops.f32(ops.linear(x, self.w_ab)), [Hv, Hv], -1)  # [B, T, n_v] each
        else:
            a = ops.f32(ops.linear(x, self.w_a))  # [B, T, n_v]
            b = ops.f32(ops.linear(x, self.w_b))

        # causal depthwise conv1d over [history | new]
        hist = state[0] if state is not None else ops.zeros((B, c.conv_dim, K - 1), f32)
        inp = ops.concat([hist, qkv], -1)
        conv = ops.transpose(ops.silu(ops.conv1d_causal(inp, self.conv_w)), (0, 2, 1))  # [B, T, conv_dim]
        q, k, v = ops.split(conv, [c.key_dim, c.key_dim, c.value_dim], -1)

        S = state[1] if state is not None else ops.zeros((B, Hv, dk, dv), f32)

        if all_states:
            conv_state = ops.stack([inp[..., t + 1:t + K] for t in range(T)], 0)  # [T, B, C, K-1]
        else:
            # a dense copy, not a slice of the input: a view would keep this layer's whole [B, conv_dim, T + K - 1]
            # float32 input alive in the cache (40 KB per token per layer, ~7.5 GB across the 48 DeltaNet layers of a
            # 4096-token prefill chunk on the 27B), and its strides depend on T. A compiled step is guarded on its
            # inputs' strides, so when plain and verify rounds first mixed in one generation (prompt lookup over no
            # draft head does exactly that) the decode step, fed a verify's commit after its own sliced output,
            # recompiled mid-request: minutes on the 27B.
            conv_state = ops.copy(inp[..., -(K - 1):])

        if T <= ops.gdn_fused_max_t:
            # decode / verify -- and prefill, on a backend whose kernel takes any T -- as one op from the raw
            # projections (fusable into a single kernel per layer)
            out, S = ops.gdn_step(
                ops.reshape(q, (B, T, Hk, dk)),
                ops.reshape(k, (B, T, Hk, dk)),
                ops.reshape(v, (B, T, Hv, dv)),
                a,
                b,
                self.A,
                self.dt_bias,
                S,
                all_states,
                c.rms_eps,
            )  # out: [B,T,Hv,dv]; S: [B,Hv,dk,dv] or [T,B,Hv,dk,dv]

        else:
            # prefill: normalise, broadcast heads, chunked recurrence
            q = ops.transpose(ops.l2_norm(ops.reshape(q, (B, T, Hk, dk)), c.rms_eps), (0, 2, 1, 3)) * (dk**-0.5)
            k = ops.transpose(ops.l2_norm(ops.reshape(k, (B, T, Hk, dk)), c.rms_eps), (0, 2, 1, 3))  # [B,Hk,T,dk]
            v = ops.transpose(ops.reshape(v, (B, T, Hv, dv)), (0, 2, 1, 3))  # [B,Hv,T,dv]
            if Hv != Hk:  # canonical grouped V order -> repeat_interleave (llama.cpp's tiled order would tile)
                q = ops.repeat(q, Hv // Hk, 1)
                k = ops.repeat(k, Hv // Hk, 1)
            beta = ops.transpose(ops.sigmoid(b), (0, 2, 1))  # [B,Hv,T]
            g = ops.transpose(self.A[None, None, :] * ops.softplus(a + self.dt_bias), (0, 2, 1))  # <= 0
            if all_states:
                out, S = ops.gated_delta_states(q, k, v, g, beta, S)
            else:
                out, S = ops.gated_delta(q, k, v, g, beta, S)
            out = ops.transpose(out, (0, 2, 1, 3))  # [B,T,Hv,dv]

        z = ops.reshape(z, (B, T, Hv, dv))
        gate = ops.sigmoid(z) if c.output_gate == 'sigmoid' else ops.silu(z)
        out = ops.rms_norm(out, self.norm_w, c.rms_eps) * gate  # gated RMSNorm
        y = ops.linear(ops.cast(ops.reshape(out, (B, T, c.value_dim)), x.dtype), self.w_out)
        return y, (conv_state, S)
