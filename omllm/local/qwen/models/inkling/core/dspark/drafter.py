# ruff: noqa: N806
"""
DSpark, a block drafter (INKLING.md, "The draft model"): the draft model Inkling 2 ships beside its weights.

It never reads tokens of the past. Each position the target has run on is, to each of the drafter's layers, one key
and one value made directly from the target's states there (memory.py): no layer runs over the past. To draft it
runs its layers over one block of slots -- the newest token, which the target has chosen and not yet run on, then a
learned mask vector in each of the others -- every slot attending to that memory and to the whole block, with no
causal order inside it. The mask slots' outputs through the target's own output projection are logits for the next
positions all at once, and a small recurrent head then walks them left to right, correcting each position's logits
by the token drafted before it (markov.py).

The drafter here is the arithmetic, as functions of arrays that a draft source captures and keeps the memory for
(models/inkling/spec/dspark.py). It borrows the target's embedding (and its norm) for the newest token, and its output
projection.
"""
import typing as ta

from .....core.draftheads import DraftHead
from .....core.slab import StepSlabHolder
from .....ops.base import Array
from .....ops.base import Ops
from .....ops.base import Weight
from ...ops.backends import inkling2_ops
from .config import DsparkConfig
from .layers import DsparkLayer
from .layers import DsparkSpan
from .markov import DsparkMarkovHead


##


class DsparkDrafter(StepSlabHolder, DraftHead):
    def __init__(
            self,
            *,
            cfg: DsparkConfig,
            ops: Ops,
            dtype: ta.Any,
            embed: Weight,
            embed_norm: Array,
            unembed: Weight,
            mask: Array,
            layers: ta.Sequence[DsparkLayer],
            norm: Array,
            head: DsparkMarkovHead,
    ) -> None:
        super().__init__()

        if len(layers) != cfg.num_layers:
            raise ValueError(f'{len(layers)} layers for a drafter of {cfg.num_layers}')

        self.cfg = cfg
        self.ops = ops
        self.dtype = dtype
        self._embed = embed
        self._embed_norm = embed_norm
        self._unembed = unembed
        self._mask = mask  # [H]: what a slot whose token is not known starts as
        self.layers = list(layers)
        self._norm = norm
        self.head = head

        self._tables: dict[int, tuple[Array, ...]] = {}  # see tables

    @property
    def num_taps(self) -> int:
        """The target states a position is read from: the hidden output's width is so many times the hidden size."""

        return len(self.cfg.taps)

    def taps(self, hidden: Array) -> Array:
        """The target's hidden output for T positions [1, T, n H] as its states [T, n, H]."""

        return self.ops.reshape(hidden, (hidden.shape[1], self.num_taps, self.cfg.hidden_size))

    def rope_rows(self, start: int, n: int) -> tuple[Array, Array]:
        """The rotary cos / sin rows [n, D] float32 of positions start .. start + n - 1."""

        ops = self.ops
        f32 = ops.dtype('f32')
        cos, sin = ops.rope_tables(start, n, self.cfg.head_dim, self.cfg.rope_theta)
        return ops.array(cos, f32), ops.array(sin, f32)

    def tables(self, capacity: int) -> tuple[Array, ...]:
        """
        What a captured step over `capacity` positions reads by position: (arange(capacity), cos, sin), the rotary
        rows [capacity, D] float32. Built once a capacity and shared by every step captured over it (a captured
        step keeps the arrays it was first called with).
        """

        if capacity not in self._tables:
            if len(self._tables) > 2:
                self._tables.clear()
            self._tables[capacity] = (self.ops.arange(capacity), *self.rope_rows(0, capacity))
        return self._tables[capacity]

    def remember(self, taps: Array, cos: Array, sin: Array) -> list[tuple[Array, Array]]:
        """
        Each layer's keys and values [1, KV, T, D] for T positions, from the target's states there [T, n, H] and the
        positions' rotary rows.
        """

        return [layer.context(self.ops, taps, cos, sin) for layer in self.layers]

    def block(
            self,
            tok: Array,
            cos: Array,
            sin: Array,
            spans: ta.Sequence[DsparkSpan],
    ) -> Array:
        """
        The block's outputs for its drafts, [block - 1, H] in the model's dtype: `tok` [1, 1] the newest token, cos /
        sin [block, D] the rotary rows of its position and the ones after, `spans` each layer's past.
        """

        ops = self.ops
        c = self.cfg

        e = ops.rms_norm(ops.embedding(tok, self._embed, self.dtype), self._embed_norm, c.rms_eps)
        h = ops.concat(
            [
                ops.f32(ops.reshape(e, (1, c.hidden_size))),
                ops.repeat(ops.f32(self._mask)[None, :], c.drafts, 0),
            ],
            0,
        )

        for layer, span in zip(self.layers, spans):
            h = layer(ops, h, cos, sin, span)

        return inkling2_ops(ops).rms_norm_to(h[1:], self._norm, c.rms_eps, self.dtype)

    def base_logits(self, y: Array) -> Array:
        """The block's own logits for its drafts [n, V] float32: the target's output projection of its outputs."""

        return self.ops.f32(self.ops.linear(y, self._unembed))
