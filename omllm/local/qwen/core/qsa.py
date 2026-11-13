# ruff: noqa: N803 N806
"""
Qwen Sparse Attention (transformers' Qwen4ExpTextQSAIndexer; FLASHNEXT.md §0, §4.3): Qwen3.5's gated attention, each
query attending only to the tokens an indexer selects -- the top `budget / ratio` complete blocks of `ratio` tokens,
plus the incomplete tail block.

The indexer projects `heads` query heads and one key per token at `head_dim`. Queries are normed and rotated at their
position (the attention's partial RoPE, on the first dims of the index head). Keys are kept raw per token -- the
layer's state gains a one-head "KV" buffer of them, so the KV machinery (write, pad, slice) carries them -- and pooled
per block (a float mean), normed, rotated at the block's first position. A block's score is `Σ_h relu(q_h . k_b) /
sqrt(head_dim)`.

Composed, no kernels of its own. The functional path (prefill, the reference) selects with a keep-mask over every
position and masked dense attention (`Ops.sdpa_masked`), and skips even that whenever every complete block fits the
top-k -- below the budget QSA *is* dense attention, exactly -- for the usual kernels. The static step (decode, verify)
gathers each query's selected tokens' keys and values (`Ops.kv_gather`) and attends over just those, a fixed
`budget + ratio` rows: its cost stays flat with the context, though the block scoring still reads every block key.
Sparse prefill and a fused sparse decode kernel are FLASHNEXT.md phase 4.
"""
import math
import typing as ta

import numpy as np

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from .attention import Attention
from .attention import KvStateLayout
from .config import Qwen4ExpConfig
from .mixing import StateLayout
from .mixing import StepContext


##


class IndexedKvStateLayout(StateLayout):
    """The KV state followed by the indexer's raw keys, [B, 1, L, head_dim]: laid out, padded and sliced like a KV."""

    def __init__(self, kv: KvStateLayout, head_dim: int) -> None:
        super().__init__()

        self._kv = kv
        self._head_dim = head_dim

    def arity(self, ops: Ops) -> int:
        return self._kv.arity(ops) + 1

    def empty(self, ops: Ops, dtype: ta.Any) -> tuple[Array, ...]:
        return (*self._kv.empty(ops, dtype), ops.zeros((1, 1, 0, self._head_dim), dtype))

    def adapt(self, ops: Ops, state: tuple[Array, ...], dtype: ta.Any) -> tuple[Array, ...]:
        return (*self._kv.adapt(ops, state[:-1], dtype), state[-1])

    def pad(self, ops: Ops, state: tuple[Array, ...], capacity: int) -> tuple[Array, ...]:
        keys = state[-1]
        n = keys.shape[2]
        if n < capacity:
            B, H, _, D = keys.shape
            keys = ops.concat([keys, ops.zeros((B, H, capacity - n, D), keys.dtype)], 2)
        return (*self._kv.pad(ops, state[:-1], capacity), ops.copy(keys))

    def export(self, ops: Ops, state: tuple[Array, ...], seq_len: int) -> tuple[Array, ...]:
        return (*self._kv.export(ops, state[:-1], seq_len), ops.copy(state[-1][:, :, :seq_len]))

    def commit(self, ops: Ops, state: tuple[Array, ...], n: int, stacked: bool) -> tuple[Array, ...]:
        return state  # (positions past the commit are rewritten before anything reads them, as for the KV)

    def capacity(self, ops: Ops, state: tuple[Array, ...]) -> int | None:
        return self._kv.capacity(ops, state[:-1])


class IndexedAttention(Attention):
    cfg: Qwen4ExpConfig

    def __init__(self, cfg: Qwen4ExpConfig, p: dict[str, Weight], indexer: dict[str, Weight]) -> None:
        super().__init__(cfg, p)

        self._state = IndexedKvStateLayout(self._kv_state, cfg.indexer_head_dim)
        self.w_index = indexer['index_qk_proj']  # [(heads + 1) * head_dim, hidden]
        self.iq_norm = indexer['q_layernorm']
        self.ik_norm = indexer['k_layernorm']
        self.heads = cfg.indexer_heads
        self.head_dim = cfg.indexer_head_dim
        self.ratio = cfg.indexer_compress_ratio
        self.topk = cfg.block_topk

    # the indexer

    def _index(self, ops: Ops, x: Array, cos: Array, sin: Array) -> tuple[Array, Array]:
        """Query heads [B, heads, T, d], normed and rotated, and the raw keys [B, 1, T, d]."""

        c = self.cfg
        B, T, _ = x.shape
        nh, d = self.heads, self.head_dim

        iq, ik = ops.split(ops.linear(x, self.w_index), [nh * d, d], -1)
        iq = ops.transpose(ops.rms_norm(ops.reshape(iq, (B, T, nh, d)), self.iq_norm, c.rms_eps), (0, 2, 1, 3))
        return ops.rope_with(iq, cos, sin), ops.reshape(ik, (B, 1, T, d))

    def _block_keys(self, ops: Ops, keys: Array, nb: int, cos: Array, sin: Array) -> Array:
        """The first nb blocks' keys [B, 1, nb, d]: pooled, normed, rotated at each block's start (cos, sin rows)."""

        B, _, _, d = keys.shape
        r = self.ratio
        pooled = ops.mean(ops.f32(ops.reshape(keys[:, :, :nb * r], (B, 1, nb, r, d))), 3)
        kb = ops.rms_norm(ops.cast(pooled, keys.dtype), self.ik_norm, self.cfg.rms_eps)
        return ops.rope_with(kb, cos, sin)

    def _scores(self, ops: Ops, iq: Array, kb: Array, qpos: Array, ar: Array) -> tuple[Array, Array]:
        """
        Every block's score for every query (at positions qpos [T]), [B, T, nb] float32 -- -inf for blocks a query has
        not seen completely -- and how many complete blocks each query sees, [T].
        """

        f32 = ops.dtype('f32')
        nb = kb.shape[2]

        s = ops.f32(iq @ ops.transpose(kb, (0, 1, 3, 2)))  # [B, heads, T, nb]
        s = ops.sum(s * ops.cast(s > 0, f32), 1) / math.sqrt(self.head_dim)  # [B, T, nb]

        ncomp = (qpos + 1) // self.ratio  # [T]
        complete = ops.cast(ar[None, :nb] < ncomp[:, None], f32)  # [T, nb]
        return s + (1 - complete)[None] * -1e30, ncomp

    def _keep(self, ops: Ops, iq: Array, kb: Array, qpos: Array, ar: Array) -> Array:
        """
        Which of the L = len(ar) positions each query attends to: [B, T, L], 1 / 0. Blocks picked though incomplete
        (when fewer than top-k exist) are dropped.
        """

        f32 = ops.dtype('f32')
        r = self.ratio
        nb = kb.shape[2]

        s, ncomp = self._scores(ops, iq, kb, qpos, ar)
        vals, idx = ops.topk(s, min(self.topk, nb))  # [B, T, k]
        hit = ops.cast(idx[..., None] == ar[:nb], f32) * ops.cast(vals > -1e29, f32)[..., None]  # [B, T, k, nb]
        sel = ops.repeat(ops.sum(hit, 2), r, -1)  # [B, T, nb * r]: each block's tokens

        L = ar.shape[0]
        if L > nb * r:
            B, T, _ = sel.shape
            sel = ops.concat([sel, ops.zeros((B, T, L - nb * r), f32)], -1)

        # the tail: the tokens of the query's incomplete block, up to itself (disjoint from every selected block)
        tail = ops.cast(ar[None, :] >= (ncomp * r)[:, None], f32) * ops.cast(ar[None, :] <= qpos[:, None], f32)
        return sel + tail[None]

    # the mixer

    def __call__(self, ops: Ops, x: Array, pos: int, state: ta.Any) -> tuple[Array, ta.Any]:
        c = self.cfg
        T = x.shape[1]

        q, gate, k, v = self._heads(ops, x)
        cos_np, sin_np = ops.rope_tables(pos, T, c.rope_dim, c.rope_theta)
        cos, sin = ops.array(cos_np, q.dtype), ops.array(sin_np, q.dtype)
        q = ops.rope_with(q, cos, sin)
        k = ops.rope_with(k, cos, sin)
        iq, ik = self._index(ops, x, cos, sin)

        past = 0
        if state is not None:
            kv = ops.kv_adapt(tuple(state[:-1]))
            past = ops.kv_len(kv)
            kv = ops.kv_concat(kv, k, v)
            keys = ops.concat([state[-1], ik], 2)
        else:
            kv = ops.kv_new(k, v)
            keys = ik

        L = past + T
        if L // self.ratio <= self.topk:
            # every complete block is selected for every query: dense attention, exactly
            o = ops.sdpa_state(q, kv, self.scale, past)
        else:
            nb = L // self.ratio
            kb = self._block_keys(ops, keys, nb, *block_start_tables(ops, c, nb, q.dtype))
            keep = self._keep(ops, iq, kb, ops.arange(T) + past, ops.arange(L))
            kd, vd = ops.kv_dense(kv, q.dtype)
            o = ops.sdpa_masked(q, kd, vd, self.scale, keep)

        return self._out(ops, o, gate), (*kv, keys)

    def step(self, ops: Ops, x: Array, ctx: StepContext, state: ta.Any) -> tuple[Array, ta.Any]:
        """Against capacity-sized buffers; the selection always (see the module docstring). Needs ctx's full tables."""

        if ctx.cos_tab is None or ctx.sin_tab is None:
            raise ValueError('QSA in a static step needs the full rope tables in its StepContext')

        T = x.shape[1]
        q, gate, k, v = self._heads(ops, x)
        q = ops.rope_with(q, ctx.cos, ctx.sin)
        k = ops.rope_with(k, ctx.cos, ctx.sin)
        iq, ik = self._index(ops, x, ctx.cos, ctx.sin)

        kv = ops.kv_write_tokens(tuple(state[:-1]), ctx.pos, k, v)
        keys = state[-1]
        for i in range(T):
            keys = ops.kv_write(keys, ctx.pos + i, ik[:, :, i:i + 1])

        L = keys.shape[2]
        nb = L // self.ratio
        starts = ctx.ar[:nb] * self.ratio
        kb = self._block_keys(ops, keys, nb, ctx.cos_tab[starts], ctx.sin_tab[starts])
        qpos = ops.reshape(ctx.pos, (1,)) + ctx.ar[:T]
        o = self._gathered(ops, q, iq, kb, qpos, kv, ctx.ar)

        return self._out(ops, o, gate), (*kv, keys)

    def _gathered(self, ops: Ops, q: Array, iq: Array, kb: Array, qpos: Array, kv: ta.Any, ar: Array) -> Array:
        """
        Attention over each query's selection gathered: its top blocks' tokens and its tail, `topk * ratio + ratio`
        rows whatever the context (unused picks masked), so a decode step's cost does not grow with it. The same keys
        and softmax as the keep-mask over every position (`_keep`), in another order. Batch 1.
        """

        f32 = ops.dtype('f32')
        r = self.ratio
        nb = kb.shape[2]
        B, H, T, D = q.shape
        if B != 1:
            raise ValueError('the gathered QSA step is batch-1')

        s, ncomp = self._scores(ops, iq, kb, qpos, ar)
        k_sel = min(self.topk, nb)
        vals, idx = ops.topk(s, k_sel)  # [B, T, k]

        rr = ar[:r]
        blk = ops.reshape(idx[0][..., None] * r + rr, (T, k_sel * r))  # [T, k r] token positions
        blk_ok = ops.reshape(ops.repeat(ops.cast(vals[0] > -1e29, f32), r, -1), (T, k_sel * r))
        tail = (ncomp * r)[:, None] + rr[None, :]  # [T, r]
        tail_ok = ops.cast(tail <= qpos[:, None], f32)
        pos = ops.concat([blk, ops.cast(tail, blk.dtype)], -1)  # [T, S]
        ok = ops.concat([blk_ok, tail_ok], -1)
        S = pos.shape[-1]

        kg, vg = ops.kv_gather(kv, ops.reshape(pos, (T * S,)), q.dtype)  # [KV, T S, D]
        KV = kg.shape[0]
        G = H // KV
        kg = ops.reshape(kg, (KV, T, S, D))
        vg = ops.reshape(vg, (KV, T, S, D))
        qg = ops.transpose(ops.reshape(q[0], (KV, G, T, D)), (0, 2, 1, 3))  # [KV, T, G, D]
        scores = ops.f32(qg @ ops.transpose(kg, (0, 1, 3, 2))) * self.scale  # [KV, T, G, S]
        scores = scores + (1 - ok)[None, :, None, :] * -1e30
        o = ops.cast(ops.softmax(scores, -1), vg.dtype) @ vg  # [KV, T, G, D]
        return ops.reshape(ops.transpose(o, (0, 2, 1, 3)), (B, H, T, D))


def block_start_tables(ops: Ops, cfg: Qwen4ExpConfig, nb: int, dtype: ta.Any) -> tuple[Array, Array]:
    """(cos, sin) rows at positions 0, ratio, 2 ratio, ... (nb of them)."""

    r = cfg.indexer_compress_ratio
    cos_np, sin_np = ops.rope_tables(0, nb * r, cfg.rope_dim, cfg.rope_theta)
    return ops.array(np.ascontiguousarray(cos_np[::r]), dtype), ops.array(np.ascontiguousarray(sin_np[::r]), dtype)
