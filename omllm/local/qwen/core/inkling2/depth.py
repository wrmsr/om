# ruff: noqa: N803 N806
"""
Inkling 2's residual stream (INKLING.md, "The residual stream"): not one running sum but the sums of whole blocks of
layers kept apart, and a sublayer's input mixed from them by a learned query.

The stream between layers is a `DepthStream`: the `completed` blocks' sums and the `partial` sum of the block under
way. A read normalizes every source to unit RMS, scores each against a query of the sublayer's own, and takes the
softmax-weighted sum of the *normalized* sources (keys and values are the same vectors); all float32. A block's first
layer archives the partial sum it was handed -- after its attention has read it -- and starts a new one from its
attention's output.

The loop (core/inkling2/loop.py) keeps two more things in the stream: the state at the loop's entry, which every pass
starts from, and the last pass's block sums, which the next pass's sublayers read as messages (messages.py).
"""
import typing as ta

from ...ops.base import Array
from ...ops.base import Ops
from ..mixing import ResidualStream


##


class DepthStream(ta.NamedTuple):
    """A plain tuple, deliberately: it is built inside compiled steps (as StepContext is: core/mixing.py)."""

    completed: tuple[Array, ...]  # finished blocks' sums, oldest first, each [B, T, hidden] float32 at unit RMS
    partial: Array  # the block under way: [B, T, hidden]

    entry: tuple[tuple[Array, ...], Array] | None = None  # (completed, partial) at the loop's entry
    messages: tuple[Array, ...] | None = None  # the previous pass's block sums, unit RMS: what messages are read from


def unit_rms(ops: Ops, x: Array, eps: float) -> Array:
    """x / sqrt(mean(x^2) + eps) over the last axis, float32: an RMS norm with no weight."""

    return ops.unit_rms(x, eps)


def depth_read(ops: Ops, queries: Array, r: DepthStream, eps: float) -> Array:
    """
    What `queries` [Q, hidden] read of the stream, [B, T, Q, hidden] float32: `Ops.depth_mix` over the finished
    blocks' sums (kept at unit RMS) and the sum under way (brought to it).
    """

    return ops.depth_mix(queries, [*r.completed, r.partial], raw=1, eps=eps)


class DepthResidualStream(ResidualStream):
    """
    The stream's two ends: entered as the normed embedding with no block finished, left through one last read of
    every block's sum and the final norm.
    """

    def __init__(
            self,
            *,
            embed_norm: Array,
            query: Array,
            norm: Array,
            eps: float,
            dtype: ta.Any,
    ) -> None:
        super().__init__()

        self._embed_norm = embed_norm
        self._query = query  # [1, hidden] float32
        self._norm = norm
        self._eps = eps
        self._dtype = dtype

    def enter(self, ops: Ops, x: Array) -> DepthStream:
        return DepthStream((), ops.rms_norm(x, self._embed_norm, self._eps))

    def exit(self, ops: Ops, r: DepthStream) -> Array:
        mix = depth_read(ops, self._query, r, self._eps)[:, :, 0]
        return ops.cast(ops.rms_norm(mix, self._norm, self._eps), self._dtype)

    def tail(self, ops: Ops, r: DepthStream, n: int) -> DepthStream:
        def cut(xs: ta.Sequence[Array]) -> tuple[Array, ...]:
            return tuple(x[:, -n:] for x in xs)

        return DepthStream(
            cut(r.completed),
            r.partial[:, -n:],
            None if r.entry is None else (cut(r.entry[0]), r.entry[1][:, -n:]),
            None if r.messages is None else cut(r.messages),
        )
