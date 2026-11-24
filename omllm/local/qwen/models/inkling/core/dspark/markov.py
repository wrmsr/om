# ruff: noqa: N806
import typing as ta

from .....ops.base import Array
from .....ops.base import Ops
from .....ops.base import Weight
from .memory import DsparkTapMix


##


class DsparkMarkovHead:
    """
    The head that walks a block's drafts left to right (the checkpoint's `rnn_hidden`): a recurrent state of
    `rank`, zero at the block's start, stepped at each draft on the token before it, the block's output there and the
    head's own view of the last position the target ran on, giving a correction to that draft's logits --

        r = state_proj [s | tokens[prev]] + input_proj [y | g] + bias          three parts of `rank`
        s = sigmoid(r_gate) s + (1 - sigmoid(r_gate)) tanh(r_cand)
        logits = cap tanh((base + out tanh(r_out) + out_bias) / cap)

    where `base` are the block's own logits there. The checkpoint has the correction in hidden space (a `hidden_out`
    of [H, rank] and a bias, added to y before the target's output projection) and one `rnn_proj` over the four
    inputs side by side; the loader hands them over as the same thing done cheaper (models/inkling/load/checkpoints.py):
    `out` = unembed hidden_out [V, rank], a pass over 256 columns a draft and not 2304, and the projection in its two
    halves, of which the second is run for every draft at once.
    """

    def __init__(
            self,
            *,
            mix: DsparkTapMix,
            tokens: Weight,
            state_proj: Weight,
            input_proj: Weight,
            bias: Array,
            out: Weight,
            out_bias: Array,
            rank: int,
            cap: float,
            dtype: ta.Any,
    ) -> None:
        super().__init__()

        self._mix = mix
        self._tokens = tokens  # [ids, rank]
        self._state_proj = state_proj  # [3 rank, 2 rank]
        self._input_proj = input_proj  # [3 rank, 2 H]
        self._bias = bias  # [3 rank] float32
        self._out = out  # [V, rank]
        self._out_bias = out_bias  # [V] float32
        self._rank = rank
        self._cap = cap
        self._dtype = dtype

    @property
    def rank(self) -> int:
        return self._rank

    def view(self, ops: Ops, taps: Array) -> Array:
        """The head's view [1, H] of the last position the target ran on, from its states there [1, n, H]."""

        return self._mix(ops, taps)

    def inputs(self, ops: Ops, y: Array, g: Array) -> Array:
        """What every draft's step takes of the block's outputs y [n, H] and the view g [1, H]: [n, 3 rank] float32."""

        n = y.shape[0]
        x = ops.concat([y, ops.repeat(g, n, 0)], -1)
        return ops.f32(ops.linear(x, self._input_proj)) + self._bias

    def step(
            self,
            ops: Ops,
            s: Array,
            prev: Array,
            r_in: Array,
            base: Array,
    ) -> tuple[Array, Array]:
        """
        One draft: the state s [1, rank] float32, the token before `prev` [1] (int), this draft's row of `inputs`
        [1, 3 rank] and of the block's logits `base` [1, V] float32 -> the state after, and the draft's logits
        [1, V] float32.
        """

        R = self._rank
        dtype = self._dtype

        x = ops.concat([ops.cast(s, dtype), ops.embedding(prev, self._tokens, dtype)], -1)
        r = ops.f32(ops.linear(x, self._state_proj)) + r_in

        gate = ops.sigmoid(r[:, :R])
        s = gate * s + (1 - gate) * ops.tanh(r[:, R:2 * R])
        u = ops.cast(ops.tanh(r[:, 2 * R:]), dtype)

        logits = base + ops.f32(ops.linear(u, self._out)) + self._out_bias
        return s, ops.tanh(logits / self._cap) * self._cap
