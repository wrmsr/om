# ruff: noqa: N803 N806 N812
import math
import typing as ta

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from .cache import FullState
from .config import Qwen35Config
from .mixing import Mixer
from .mixing import StateLayout
from .mixing import StepContext


##


class KvStateLayout(StateLayout):
    """
    An attention layer's KV state, in whatever format the backend keeps it (`Ops.kv_arity` arrays: bf16 (k, v), or fp8
    codes plus scales). The static decoder holds it in capacity-sized buffers that need no rollback: positions past the
    sequence are masked by `pos` and rewritten by the next step.
    """

    def __init__(self, *, num_kv_heads: int, head_dim: int) -> None:
        super().__init__()

        self._num_kv_heads = num_kv_heads
        self._head_dim = head_dim

    def arity(self, ops: Ops) -> int:
        return ops.kv_arity

    def empty(self, ops: Ops, dtype: ta.Any) -> tuple[Array, ...]:
        z = ops.zeros((1, self._num_kv_heads, 0, self._head_dim), dtype)
        return ops.kv_new(z, z)

    def adapt(self, ops: Ops, state: tuple[Array, ...], dtype: ta.Any) -> tuple[Array, ...]:
        return ops.kv_adapt(state, dtype)

    def pad(self, ops: Ops, state: tuple[Array, ...], capacity: int) -> tuple[Array, ...]:
        return ops.kv_pad(state, capacity)

    def reserve(
            self,
            ops: Ops,
            state: tuple[Array, ...],
            capacity: int,
            into: tuple[Array, ...] | None = None,
    ) -> tuple[Array, ...]:
        return ops.kv_reserve(ops.kv_adapt(state), capacity, into)  # (adapted as the functional form adapts it)

    def export(self, ops: Ops, state: tuple[Array, ...], seq_len: int) -> tuple[Array, ...]:
        return ops.kv_slice(state, seq_len)

    def commit(self, ops: Ops, state: tuple[Array, ...], n: int, stacked: bool) -> tuple[Array, ...]:
        return state

    def capacity(self, ops: Ops, state: tuple[Array, ...]) -> int | None:
        return ops.kv_len(state)


class Attention(Mixer):
    def __init__(self, cfg: Qwen35Config, p: dict[str, Weight]) -> None:
        super().__init__()

        self._kv_state = KvStateLayout(num_kv_heads=cfg.num_kv_heads, head_dim=cfg.head_dim)
        self._state: StateLayout = self._kv_state
        self.cfg = cfg
        self.wqkv = p.get('qkv_proj')  # fused [q | k | v] when the loader provides it
        self.wq = p.get('q_proj')
        self.wk = p.get('k_proj')
        self.wv = p.get('v_proj')
        self.wo = p['o_proj']
        self.q_norm = p['q_norm']
        self.k_norm = p['k_norm']
        self.scale = 1.0 / math.sqrt(cfg.head_dim)

    @property
    def state(self) -> StateLayout:
        return self._state

    def project(self, ops: Ops, x: Array) -> tuple[Array, Array, Array]:
        """[q | gate] [B, T, H*2D], k [B, T, KV*D], v [B, T, KV*D] -- one GEMV when fused."""

        c = self.cfg

        if self.wqkv is not None:
            nq = c.num_heads * c.head_dim * 2
            nkv = c.num_kv_heads * c.head_dim
            qg, k, v = ops.split(ops.linear(x, self.wqkv), [nq, nkv, nkv], -1)
            return qg, k, v

        return ops.linear(x, self.wq), ops.linear(x, self.wk), ops.linear(x, self.wv)

    def _heads(self, ops: Ops, x: Array) -> tuple[Array, Array, Array, Array]:
        """q [B, H, T, D], gate [B, T, H * D], k, v [B, KV, T, D]: projected, q and k normed, not yet rotated."""

        c = self.cfg
        B, T, _ = x.shape
        H = c.num_heads
        KV = c.num_kv_heads
        D = c.head_dim

        qg, k, v = self.project(ops, x)
        qg = ops.reshape(qg, (B, T, H, 2 * D))

        # per-head [q | gate]
        q = qg[..., :D]
        gate = ops.reshape(qg[..., D:], (B, T, H * D))
        k = ops.reshape(k, (B, T, KV, D))
        v = ops.reshape(v, (B, T, KV, D))
        q = ops.transpose(ops.rms_norm(q, self.q_norm, c.rms_eps), (0, 2, 1, 3))  # [B,H,T,D]
        k = ops.transpose(ops.rms_norm(k, self.k_norm, c.rms_eps), (0, 2, 1, 3))  # [B,KV,T,D]
        v = ops.transpose(v, (0, 2, 1, 3))
        return q, gate, k, v

    def _out(self, ops: Ops, o: Array, gate: Array) -> Array:
        """The attention output o [B, H, T, D] gated and projected: [B, T, hidden]."""

        B, H, T, D = o.shape
        o = ops.reshape(ops.transpose(o, (0, 2, 1, 3)), (B, T, H * D))
        o = o * ops.cast(ops.sigmoid(ops.f32(gate)), o.dtype)
        return ops.linear(o, self.wo)

    def __call__(self, ops: Ops, x: Array, pos: int, state: FullState | None) -> tuple[Array, FullState]:
        c = self.cfg

        q, gate, k, v = self._heads(ops, x)
        q = ops.rope(q, pos, c.rope_dim, c.rope_theta)
        k = ops.rope(k, pos, c.rope_dim, c.rope_theta)

        T = x.shape[1]
        past = 0
        if state is None:
            state = seen = ops.kv_new(k, v)
        else:
            state = ops.kv_adapt(state)
            past = ops.kv_len(state)
            if past >= pos + T:
                # A reserved state (StateLayout.reserve): `pos` positions and room past them. The new keys and values
                # are written into the room in place, where concatenating would re-copy the whole KV into an
                # ever-larger allocation every chunk of a long prefill; attention sees the filled part.
                past = pos
                state = ops.kv_write_tokens(state, ops.scalar(pos), k, v)
                seen = ops.kv_window(state, pos + T)
            else:
                if past > pos:  # room, but not enough of it: back to an exact-length state
                    past = pos
                    state = ops.kv_slice(state, pos)
                state = seen = ops.kv_concat(state, k, v)

        o = ops.sdpa_state(q, seen, self.scale, past)  # [B,H,T,D]
        return self._out(ops, o, gate), state

    def step(self, ops: Ops, x: Array, ctx: StepContext, state: FullState) -> tuple[Array, FullState]:
        """
        T tokens against fixed-capacity KV buffers. x: [B, T, hidden] at positions ctx.pos..pos+T-1; ctx.ar:
        arange(L); ctx.cos, ctx.sin: [T, rope_dim] rows for those positions; state: (kbuf, vbuf) [B, KV, L, D]. Every
        shape is static in `pos`; T == 1 is decode, T == k + 1 speculative verify. ctx.bucket > 0 attends over only the
        first that many positions of the buffers (the Decoder picks a power of two covering pos + T, so the
        attention's cost follows the sequence rather than the capacity); 0 = the whole buffer (backends whose kernel
        reads `pos` itself).
        """

        pos = ctx.pos
        ar = ctx.ar
        cos = ctx.cos
        sin = ctx.sin
        bucket = ctx.bucket

        q, gate, k, v = self._heads(ops, x)
        q = ops.rope_with(q, cos, sin)
        k = ops.rope_with(k, cos, sin)

        state = ops.kv_write_tokens(state, pos, k, v)

        if bucket and bucket < ops.kv_len(state):
            o = ops.sdpa_static_state(q, ops.kv_window(state, bucket), pos, ar[:bucket], self.scale)
        else:
            o = ops.sdpa_static_state(q, state, pos, ar, self.scale)  # [B,H,T,D]

        return self._out(ops, o, gate), state
