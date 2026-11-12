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


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


##


class Qwen35:
    """
    The decoder model, assembled from parts by an architecture (arch/): the embedding and output head, the blocks (each
    a composition of residual stream, mixer and feed-forward), the final norm, and the draft head when one is loaded. It
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
            norm: Weight,
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
        self.norm_w = norm
        self.blocks: list[Block] = list(blocks)
        self.residual = residual
        self.mtp = mtp
        self.nbytes = nbytes

        self._steps: dict[tuple[int, bool, bool, int], ta.Callable[..., tuple[Array, ...]]] = {}  # see step_fn
        self._tables: dict[int, tuple[Array, Array, Array]] = {}  # see decode_tables

    # forward

    def prefill(
            self,
            tokens: ta.Sequence[int],
            cache: Cache,
            chunk: int = 4096,
            should_stop: ta.Callable[[], bool] | None = None,
    ) -> tuple[Array, Array]:
        """
        `forward` over a prompt in chunks of `chunk` tokens through the growing cache, so activation memory (the [T,
        intermediate] tensors, ~35 KB per token for the 27B) stays bounded whatever the prompt length, and a
        cancellation (`should_stop`) has somewhere to land. Returns the last position's logits [B, 1, V] and the
        final-normed hidden states of every position [B, T, hidden].
        """

        ops = self.ops
        toks = np.asarray(tokens, dtype=np.int32).reshape(1, -1)
        T = toks.shape[1]
        hiddens: list[Array] = []
        logits = None

        for start in range(0, T, max(1, chunk)):
            if should_stop is not None and should_stop():
                raise Cancelled
            logits, h = self.forward(toks[:, start:start + chunk], cache, last_only=True, return_hidden=True)
            hiddens.append(h)

        return (
            check.not_none(logits)[:, -1:],
            (hiddens[0] if len(hiddens) == 1 else ops.concat(hiddens, 1)),
        )

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
        c = self.cfg
        tokens = np.asarray(tokens, dtype=np.int32)
        B, T = tokens.shape

        if start_pos is None:
            start_pos = cache.seq_len if cache is not None else 0

        x = ops.embedding(ops.array(tokens), self.embed, self.dtype)
        ops.tap('embed', x)

        r = self.residual.enter(ops, x)
        for i, blk in enumerate(self.blocks):
            r, st = blk(ops, r, start_pos, cache.layers[i] if cache is not None else None)
            if cache is not None:
                cache.layers[i] = st
        x = self.residual.exit(ops, r)

        if cache is not None:
            cache.seq_len = start_pos + T

        if last_only and not return_hidden:
            x = x[:, -1:]

        x = ops.rms_norm(x, self.norm_w, c.rms_eps)
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
        """Each layer's decode-state layout, from its mixer."""

        return [blk.mixer.state for blk in self.blocks]

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
        ops, c = self.ops, self.cfg
        offsets = self.state_offsets()

        def fn(toks, pos, ar, cos_tab, sin_tab, *flat):
            # index with a 1-element array, not the 0-d one: torch turns a 0-d tensor index into `.item()`, a
            # device->host sync that is illegal inside a CUDA graph capture; a 1-d index is a plain gather
            rows = ops.reshape(pos, (1,)) + ar[:T]
            cos = cos_tab[rows]  # [T, rope_dim]
            sin = sin_tab[rows]

            ctx = StepContext(pos, ar, cos, sin, all_states, bucket)

            r = self.residual.enter(ops, ops.embedding(toks, self.embed, self.dtype))

            out: list[Array] = []
            for i, blk in enumerate(self.blocks):
                o, n = offsets[i]
                r, st = blk.step(ops, r, ctx, tuple(flat[o:o + n]))
                out.extend(st)

            x = ops.rms_norm(self.residual.exit(ops, r), self.norm_w, c.rms_eps)
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
