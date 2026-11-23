# ruff: noqa: N803 N806
"""
Inkling 2's attention (INKLING.md, "Attention"): grouped-query attention with no rotary embedding. Position enters as
a learned relative term on the scores; every query also has a sink in its softmax; keys and values pass through short
convolutions over time before they are stored; and the heads' outputs are gated before the output projection.

    q    = clip(scale_q * W_q x_q)                       per head, by l2 norm (`qk_clip`)
    k    = clip(conv_k(W_k x_k))                         stored
    v    = rms(conv_v(W_v x_v))                          stored, at unit RMS with no weight
    rel  = clip(scale_r * W_r x_q) @ P                   per query head, a bias for each backward distance < `extent`
    sink = W_s x_q                                       per query head
    a    = softmax([q . k / sqrt(d) + rel[distance] | sink]) over a query's keys and its sink
    y    = W_o (sigmoid(W_g x_q) * sum_keys a v)

A local layer's query sees a sliding window of positions up to its own; a global layer's sees every earlier one, the
relative term being zero (not a mask) past its extent, and scales its queries and relative features by
1 + alpha log(max((pos + 1) / floor, 1)). Which of the two a layer is, is its `KvSpan` (core/kvspans.py), which also
keeps its keys and values: capacity buffers for a global layer, the window itself -- a fixed-size state, whatever the
context's length -- for a local one. The three inputs x_q, x_k, x_v come apart from the residual stream
(connections.py).

The decode state is the span's, then the two convolutions' histories.
"""
import math
import typing as ta

from omcore import check
from omcore import lang

from ...ops.base import Array
from ...ops.base import Ops
from ...ops.base import Weight
from ..kvspans import KvSpan
from ..mixing import CompositeStateLayout
from ..mixing import Mixer
from ..mixing import StateLayout
from ..mixing import StepContext
from ..shortconv import ShortConv
from .depth import unit_rms


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


##


class LogScaling(ta.NamedTuple):
    """1 + alpha log(max((pos + 1) / floor, 1)): what a global layer's queries grow by with their position."""

    floor: int
    alpha: float


class Inkling2Attention(Mixer):
    # the float32 scores of a prefill's attention are held for this many (query, key, head) triples at a time: its
    # queries go through in tiles, each against the keys its tile can see
    SCORE_TILE: ta.ClassVar[int] = 1 << 26

    def __init__(
            self,
            *,
            num_heads: int,
            num_kv_heads: int,
            head_dim: int,
            wq: Weight,
            wk: Weight,
            wv: Weight,
            wr: Weight,
            wo: Weight,
            sink: Weight,
            gate: Weight,
            q_scale: Array,
            rel_scale: Array,
            rel_proj: Weight,
            k_conv: ShortConv,
            v_conv: ShortConv,
            span: KvSpan,
            qk_clip: float,
            rel_clip: float,
            log_scaling: LogScaling | None,
            eps: float,
    ) -> None:
        """
        `rel_proj`: [extent, rel_dim], a distance's bias from a head's relative features; `span`: which positions a
        query sees and how their keys and values are kept; `log_scaling`: a global layer's.
        """

        super().__init__()

        self._num_heads = num_heads
        self._num_kv_heads = num_kv_heads
        self._head_dim = head_dim
        self._wq = wq
        self._wk = wk
        self._wv = wv
        self._wr = wr
        self._wo = wo
        self._sink = sink
        self._gate = gate
        self._q_scale = q_scale  # [heads, head_dim]
        self._rel_scale = rel_scale  # [heads, rel_dim]
        self._rel_proj = rel_proj
        self._k_conv = k_conv
        self._v_conv = v_conv
        self._span = span
        self._qk_clip = qk_clip
        self._rel_clip = rel_clip
        self._log_scaling = log_scaling
        self._eps = eps

        self._scale = 1.0 / math.sqrt(head_dim)

        self._state = CompositeStateLayout([span.state, k_conv.state, v_conv.state])

    @property
    def state(self) -> StateLayout:
        return self._state

    # the parts both forms share

    def _queries(self, ops: Ops, xq: Array, tau: Array | None) -> tuple[Array, Array, Array, Array]:
        """
        From the query input [B, T, hidden]: q [B, H, T, D]; each query's bias by backward distance [B, T, H, extent]
        float32; the sinks [B, H, T] float32; the output gate's logits [B, T, H * D]. `tau`: [T] float32, a global
        layer's scaling at each position.
        """

        B, T, _ = xq.shape
        H = self._num_heads
        D = self._head_dim

        # (a global layer's scaling comes after the clip, each rounded to the model's dtype first)
        q = ops.l2_clip(
            ops.reshape(ops.linear(xq, self._wq), (B, T, H, D)),
            self._qk_clip,
            scale=self._q_scale,
            after=tau,
        )
        rel = ops.l2_clip(
            ops.reshape(ops.linear(xq, self._wr), (B, T, H, -1)),
            self._rel_clip,
            scale=self._rel_scale,
            after=tau,
        )

        sink = ops.transpose(ops.f32(ops.linear(xq, self._sink)), (0, 2, 1))
        gate = ops.linear(xq, self._gate)

        return ops.transpose(q, (0, 2, 1, 3)), rel, sink, gate

    def _keys(
            self,
            ops: Ops,
            xk: Array,
            xv: Array,
            k_hist: tuple[Array, ...] | None,
            v_hist: tuple[Array, ...] | None,
            all_states: bool,
    ) -> tuple[Array, Array, tuple[Array, ...], tuple[Array, ...]]:
        """k, v [B, KV, T, D] as they are stored, and the two convolutions' new histories."""

        B, T, _ = xk.shape
        KV = self._num_kv_heads
        D = self._head_dim

        k, k_hist = self._k_conv(ops, ops.linear(xk, self._wk), xk, k_hist, all_states)
        v, v_hist = self._v_conv(ops, ops.linear(xv, self._wv), xv, v_hist, all_states)

        k = ops.l2_clip(ops.reshape(k, (B, T, KV, D)), self._qk_clip)
        v = ops.reshape(v, (B, T, KV, D))
        v = ops.cast(unit_rms(ops, v, self._eps), v.dtype)

        return ops.transpose(k, (0, 2, 1, 3)), ops.transpose(v, (0, 2, 1, 3)), k_hist, v_hist

    def _out(self, ops: Ops, o: Array, gate: Array) -> Array:
        B, H, T, D = o.shape
        o = ops.reshape(ops.transpose(o, (0, 2, 1, 3)), (B, T, H * D))
        return ops.linear(ops.sigmoid_gated(o, gate, o.dtype), self._wo)

    def _split(self, ops: Ops, state: ta.Any) -> tuple[ta.Any, ta.Any, ta.Any]:
        if state is None:
            return None, None, None
        n = self._span.state.arity(ops)
        return tuple(state[:n]), tuple(state[n:n + 1]), tuple(state[n + 1:n + 2])

    # the functional form

    def __call__(
            self,
            ops: Ops,
            x: ta.Any,
            pos: int,
            state: tuple[Array, ...] | None,
    ) -> tuple[Array, tuple[Array, ...]]:
        xq, xk, xv = x
        B, T, _ = xq.shape
        check.state(B == 1, 'batch 1')
        f32 = ops.dtype('f32')

        kv, k_hist, v_hist = self._split(ops, state)

        tau: Array | None = None
        if (ls := self._log_scaling) is not None:
            qp = np.arange(pos, pos + T, dtype=np.float64)
            tau = ops.array((1 + ls.alpha * np.log(np.maximum((qp + 1) / ls.floor, 1))).astype(np.float32), f32)

        q, rel, sink, gate = self._queries(ops, xq, tau)
        k, v, k_hist, v_hist = self._keys(ops, xk, xv, k_hist, v_hist, False)

        kv, kd, vd, first = self._span.extend(ops, kv, pos, k, v, q.dtype)

        # One softmax a query, in parts. Where a query sees every earlier position, the keys past its relative
        # term's extent -- in a long prefill, nearly all of them -- carry no term, and are scored as plain causal
        # attention ending `extent` positions before the query: no bias is built for them, and a backend's kernel
        # reads them where they are. The keys within the query's reach, or its extent, are a window to it, scored
        # with the term as a step's are (`Ops.sdpa_window_rel`), a tile of queries at a time against the keys the
        # tile can see.
        reach = self._span.reach
        extent = int(self._rel_proj.shape[0])
        near = reach if reach is not None else extent
        far = None
        if reach is None and pos + T - 1 - extent >= first:
            far = ops.sdpa_causal_partials(q, kd, vd, pos - extent - first, self._scale)

        outs = []
        # (t queries score t + near - 1 keys: the largest t whose scores fit the tile)
        tile = max(1, int((math.sqrt(near * near + 4 * self.SCORE_TILE / self._num_heads) - near) / 2))
        for a in range(0, T, tile):
            b = min(a + tile, T)
            lo = max(pos + a - (near - 1), first)
            hi = pos + b

            # the tile's window as a step's is laid out: near - 1 slots before its first query, the ones for
            # positions there are no keys at empty (a kernel that walks the slots in tiles then sums a token's
            # scores in the order a step does: under a KV format that rounds, a last bit decides a code)
            kt = kd[:, :, lo - first:hi - first]
            vt = vd[:, :, lo - first:hi - first]
            short = lo - (pos + a - (near - 1))
            if short:
                pad = ops.zeros((kt.shape[0], kt.shape[1], short, kt.shape[3]), kt.dtype)
                kt = ops.concat([pad, kt], 2)
                vt = ops.concat([pad, vt], 2)

            outs.append(ops.sdpa_window_rel(
                q[:, :, a:b],
                kt,
                vt,
                ops.scalar(pos + a),
                scale=self._scale,
                rel=rel[0, a:b],
                rel_proj=self._rel_proj,
                sink=sink[:, :, a:b],
                window=near,
                more=() if far is None else [(far[0][:, :, a:b], far[1][:, :, a:b], far[2][:, :, a:b])],
            ))

        o = outs[0] if len(outs) == 1 else ops.concat(outs, 2)

        return self._out(ops, o, gate), (*kv, *k_hist, *v_hist)

    # the static form

    def step(self, ops: Ops, x: ta.Any, ctx: StepContext, state: tuple[Array, ...]) -> tuple[Array, tuple[Array, ...]]:
        """T tokens against the span's fixed-shape state, every shape static in the position."""

        xq, xk, xv = x
        T = xq.shape[1]

        kv, k_hist, v_hist = self._split(ops, state)

        tau: Array | None = None
        if (ls := self._log_scaling) is not None:
            qpos = ops.reshape(ctx.pos, (1,)) + ops.arange(T)  # [T]
            tau = ops.log(ops.maximum(ops.f32(qpos + 1) / ls.floor, 1.0)) * ls.alpha + 1

        q, rel, sink, gate = self._queries(ops, xq, tau)
        k, v, k_hist, v_hist = self._keys(ops, xk, xv, k_hist, v_hist, ctx.all_states)

        kv, o = self._span.attend(
            ops,
            kv,
            ctx,
            q,
            k,
            v,
            scale=self._scale,
            rel=rel[0],
            rel_proj=self._rel_proj,
            sink=sink,
        )

        return self._out(ops, o, gate), (*kv, *k_hist, *v_hist)
