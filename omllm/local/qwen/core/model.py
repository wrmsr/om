# ruff: noqa: N803 N806 N812
"""
Qwen3.5 / 3.6 / 3.8 (dense) text decoder, written once against `Ops` (see ops.py) and run on any backend.

Every op is written out; there is no `transformers` and no backend-specific code here. Layer math is cross-checked
against llama.cpp's `src/models/qwen35.cpp` and HF's `modeling_qwen3_5.py`:

  block:    x = x + mixer(rmsnorm(x));  x = x + swiglu(rmsnorm(x))
  mixer is either
    full:   gated GQA attention -- q_proj emits [q | gate] per head, per-head q/k RMSNorm, partial NeoX RoPE on the
            first `rope_dim` dims, softmax attention, * sigmoid(gate), o_proj
    linear: Gated DeltaNet -- in_proj_qkv -> causal depthwise conv1d(k=4)+silu -> l2norm(q,k) -> gated delta rule
            recurrence (fixed-size state) -> rmsnorm * silu(z) -> out_proj

State is functional: each mixer takes its state (or None) and returns the new one. The gated delta rule lives behind
`Ops.gated_delta`, which dispatches to the per-token form for decode (T == 1) and the chunked WY form for prefill; both
are composed from the primitives, and backends override whichever they have a kernel for.
"""
import typing as ta

from omcore import check
from omcore import lang

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from .block import Block
from .cache import Cache
from .config import Qwen35Config
from .errors import Cancelled
from .mixing import ResidualStream
from .mixing import StateLayout
from .mixing import StepContext
from .mtp import MtpHead
from .slab import StepSlabHolder


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


##


class Qwen35(StepSlabHolder):
    """
    The decoder model, assembled from parts by an architecture (arch/): the embedding and output head, the blocks (each
    a composition of mixer, feed-forward and their connections to the residual stream), the stream's two ends (the
    final norm is its exit's), and the draft head when one is loaded. It
    owns the functional forward and prefill and builds the static step; it knows neither how it was loaded nor how it is
    decoded.
    """

    def __init__(
            self,
            *,
            cfg: Qwen35Config,
            ops: Ops,
            dtype: ta.Any,
            embed: Weight,
            lm_head: Weight,
            blocks: ta.Sequence[Block],
            residual: ResidualStream,
            mtp: MtpHead | None = None,
            nbytes: int = 0,
    ) -> None:
        super().__init__()

        self.cfg = cfg
        self.ops = ops
        self.dtype = dtype
        self.embed = embed
        self.lm_head = lm_head
        self.blocks: list[Block] = list(blocks)
        self.residual = residual
        self.mtp = mtp
        self.nbytes = nbytes

        self._steps: dict[tuple[int, bool, bool, int], ta.Callable[..., tuple[Array, ...]]] = {}  # see step_fn
        self._tables: dict[int, tuple[Array, Array, Array]] = {}  # see decode_tables

    # forward

    def reserve(
            self,
            cache: Cache,
            capacity: int,
            into: ta.Sequence[tuple[Array, ...] | None] | None = None,
    ) -> None:
        """
        Room for `capacity` positions in the cache's growing states (the attention layers' KV), where the backend
        writes such buffers in place (Ops.kv_reserve); a no-op for a state that already has it, and for the rest.
        `into`: per layer, the state arrays an earlier decoder left (a `StepSlab`'s `layers`), whose capacity buffers
        are used in place of new ones.
        """

        layouts = self.state_layouts()
        if into is None or len(into) != len(layouts):
            into = [None] * len(layouts)
        for i, (st, layout, prev) in enumerate(zip(cache.layers, layouts, into)):
            if st is not None:
                cache.layers[i] = layout.reserve(self.ops, st, capacity, prev)

    def prefill(
            self,
            tokens: ta.Sequence[int],
            cache: Cache,
            chunk: int = 4096,
            should_stop: ta.Callable[[], bool] | None = None,
            *,
            reserve: int | None = None,
            reserve_into: ta.Sequence[tuple[Array, ...] | None] | None = None,
            all_hidden: bool = True,
            on_chunk: ta.Callable[[Array, Array], None] | None = None,
    ) -> tuple[Array, Array]:
        """
        `forward` over a prompt in chunks of `chunk` tokens through the growing cache, so activation memory (the [T,
        intermediate] tensors, ~35 KB per token for the 27B) stays bounded whatever the prompt length, and a
        cancellation (`should_stop`) has somewhere to land. Returns the last position's logits [B, 1, V] and the
        final-normed hidden states of every position [B, T, hidden] -- or, without `all_hidden`, of the last position
        only [B, 1, hidden]: every position's is 10 KB a token on the 27B (2.5 GiB at 262k), which only a draft head
        reads.

        `reserve`: the positions the cache's states will be asked to hold in the end (a static decoder's capacity).
        From the second chunk on the KV is then written into buffers of that size (`reserve`), not grown by a
        concatenation per chunk per layer: the same values, without re-copying the whole KV 64 times over a 262k
        prompt (~270 GB on the 27B) through allocations that never fit the last one's hole. The cache's KV states
        then have room past `seq_len`, which a static decoder of that capacity adopts as its buffers without a copy.
        `reserve_into` names the buffers to use (`reserve`'s `into`).

        `on_chunk(logits, hidden)` is called after each chunk with what this method would return had the prompt ended
        there (the chunk's last position's logits, its hidden states), the cache standing at that position: the
        chunk boundaries are where a prefill can be checkpointed (the DeltaNet state exists only at the position
        the prefill has reached).
        """

        ops = self.ops
        toks = np.asarray(tokens, dtype=np.int32).reshape(1, -1)
        T = toks.shape[1]
        hiddens: list[Array] = []
        joined: Array | None = None  # every position's hidden state in one buffer, where the backend writes in place
        logits = None

        for start in range(0, T, max(1, chunk)):
            if should_stop is not None and should_stop():
                raise Cancelled
            if reserve is not None:
                self.reserve(cache, reserve, reserve_into)
            logits, h = self.forward(toks[:, start:start + chunk], cache, last_only=True, return_hidden=True)
            if not all_hidden:
                hiddens[:] = [ops.copy(h[:, -1:])]  # (a copy: a view would keep the chunk's)
            elif T <= chunk:
                hiddens.append(h)
            else:
                # chunks collected and concatenated are held twice over at the end (2.5 GiB of them at 262k tokens on
                # the 27B, at the prefill's fullest); written into one buffer as they come they never are
                if start == 0:
                    joined = ops.rows_buffer(h, T)
                if joined is not None:
                    joined = ops.rows_write(joined, start, h)
                else:
                    hiddens.append(h)
            if on_chunk is not None:
                on_chunk(logits[:, -1:], h)

        if joined is not None:
            hidden = joined
        else:
            hidden = hiddens[0] if len(hiddens) == 1 else ops.concat(hiddens, 1)
        return check.not_none(logits)[:, -1:], hidden

    def forward(
        self,
        tokens: np.ndarray,
        cache: Cache | None = None,
        start_pos: int | None = None,
        last_only: bool = False,
        return_hidden: bool = False,
    ) -> ta.Any:
        """
        tokens: [B, T] ints. Returns logits [B, T, V] (or [B, 1, V] with last_only) in float32; with return_hidden also
        the final-normed hidden states [B, T, hidden] (what the MTP head conditions on) -- every position's, even with
        last_only, which then restricts only the logits.
        """

        ops = self.ops
        tokens = np.asarray(tokens, dtype=np.int32)
        B, T = tokens.shape

        if start_pos is None:
            start_pos = cache.seq_len if cache is not None else 0

        x = ops.embedding(ops.array(tokens), self.embed, self.dtype)
        ops.tap('embed', x)

        r = self.residual.enter(ops, x)
        for i, blk in enumerate(self.blocks):
            r, st = blk(ops, r, start_pos, cache.layers[i] if cache is not None else None, ids=tokens)
            if cache is not None:
                cache.layers[i] = st

        if cache is not None:
            cache.seq_len = start_pos + T

        if last_only and not return_hidden:
            r = r[:, -1:]

        x = self.residual.exit(ops, r)  # final-normed
        ops.tap('final_norm', x)

        # the full-vocabulary logits of a 4096-token prefill chunk are 4 GB in float32: compute only the rows asked for
        logits = ops.f32(ops.linear(x[:, -1:] if last_only else x, self.lm_head))
        ops.tap('logits', logits)

        if return_hidden:
            return logits, x

        return logits

    def step_fn(
            self,
            T: int,
            all_states: bool = False,
            return_hidden: bool = False,
            bucket: int = 0,
    ) -> ta.Callable[..., tuple[Array, ...]]:
        """
        The static T-token step: `fn(toks, pos, ar, cos_tab, sin_tab, *flat_state) -> (logits, [hidden,] *flat_state)`.

        toks: [B, T] int at positions pos..pos+T-1; pos: 0-d int; ar: arange(capacity); cos_tab, sin_tab: [capacity,
        rope_dim]; flat_state: two arrays per layer (kbuf, vbuf) or (conv, S). Everything is an argument (no closed-over
        tensors) so one compiled function serves every Decoder with the same shapes; nothing in the step may allocate
        from the host. Returns logits [B, T, V] float32 (and, with return_hidden, the final-normed hidden [B, T, hidden]
        the draft head conditions on); with all_states the DeltaNet entries come back stacked per token. Pure apart from
        `kv_write`, so a backend may capture it. T == 1 is decode; T == k + 1 with all_states is speculative verify.
        `bucket` is the attention window in positions (see Attention.step; 0 = the whole buffer). Built (and
        `Ops.compile_fn`ed) once per (T, all_states, return_hidden, bucket) and cached on the model.
        """

        key = (T, all_states, return_hidden, bucket)
        fn = self._steps.get(key)
        if fn is None:
            fn = self._steps[key] = self.ops.compile_fn(self._build_step(T, all_states, return_hidden, bucket))
        return fn

    def decode_tables(self, capacity: int) -> tuple[Array, Array, Array]:
        """
        The static step's position tables for `capacity` positions: `ar` = arange(capacity), and the RoPE `cos_tab`,
        `sin_tab` [capacity, rope_dim] in the model's dtype. Read-only, so every decoder of a capacity shares one set:
        building them is ~0.2 s at 131k positions, which was every generation's. Kept per capacity, of which there are
        few (decoders round it to a power of two).
        """

        t = self._tables.get(capacity)
        if t is None:
            ops, c = self.ops, self.cfg
            cos_np, sin_np = ops.rope_tables(0, capacity, c.rope_dim, c.rope_theta)
            t = self._tables[capacity] = (
                ops.arange(capacity),
                ops.array(cos_np, self.dtype),
                ops.array(sin_np, self.dtype),
            )
        return t

    def state_layouts(self) -> list[StateLayout]:
        """Each layer's decode-state layout (its mixer's, and its layer embedding's when it has one)."""

        return [blk.state for blk in self.blocks]

    def state_offsets(self) -> list[tuple[int, int]]:
        """(start, count) of each layer's arrays in a flat state, as its layout says."""

        out = []
        o = 0
        for layout in self.state_layouts():
            n = layout.arity(self.ops)
            out.append((o, n))
            o += n
        return out

    def _build_step(
            self,
            T: int,
            all_states: bool,
            return_hidden: bool,
            bucket: int,
    ) -> ta.Callable[..., tuple[Array, ...]]:
        ops = self.ops
        offsets = self.state_offsets()

        def fn(toks, pos, ar, cos_tab, sin_tab, *flat):
            # index with a 1-element array, not the 0-d one: torch turns a 0-d tensor index into `.item()`, a
            # device->host sync that is illegal inside a CUDA graph capture; a 1-d index is a plain gather
            rows = ops.reshape(pos, (1,)) + ar[:T]
            cos = cos_tab[rows]  # [T, rope_dim]
            sin = sin_tab[rows]

            ctx = StepContext(pos, ar, cos, sin, all_states, bucket, cos_tab, sin_tab, toks)

            r = self.residual.enter(ops, ops.embedding(toks, self.embed, self.dtype))

            out: list[Array] = []
            for i, blk in enumerate(self.blocks):
                o, n = offsets[i]
                r, st = blk.step(ops, r, ctx, tuple(flat[o:o + n]))
                out.extend(st)

            x = self.residual.exit(ops, r)
            logits = ops.f32(ops.linear(x, self.lm_head))

            if return_hidden:
                return (logits, x, *out)

            return (logits, *out)

        return fn

    def decode_fn(self) -> ta.Callable[..., tuple[Array, ...]]:
        """
        The single-token step: `fn(tok, pos, ar, cos_tab, sin_tab, *flat_state) -> (logits [B, 1, V], *flat_state)`.
        """

        return self.step_fn(1)
