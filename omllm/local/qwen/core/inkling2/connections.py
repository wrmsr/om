# ruff: noqa: N803 N806
"""
How an Inkling 2 layer's two sublayers meet its residual stream (depth.py): each reads its input with learned queries
over the block sums -- blended with a message from the previous pass inside the loop (messages.py) -- through norms of
its own, and adds its output to the block under way.
"""
import typing as ta

from ...ops.base import Array
from ...ops.base import Ops
from ..mixing import Connection
from .depth import DepthStream
from .depth import depth_read
from .depth import unit_rms
from .messages import MessageReader


##


class DepthAttentionConnection(Connection):
    """
    The attention's: its query, key and value inputs, as a triple. A global layer reads each with a query and a norm
    of its own; a local layer reads one input (one query, one norm) that only messages tell apart; the model's first
    layer has no query and takes the stream -- the normed embedding -- as it is.

    With `boundary`, its write is a block's start: the sum it read goes among the finished ones, and the attention's
    output begins the next (it is not added to what was archived).
    """

    def __init__(
            self,
            *,
            queries: Array | None,
            norms: ta.Sequence[Array],
            eps: float,
            dtype: ta.Any,
            boundary: bool = False,
            messages: MessageReader | None = None,
    ) -> None:
        super().__init__()

        if queries is not None and int(queries.shape[0]) != len(norms):
            raise ValueError('a norm per query')
        if messages is not None and len(messages) != 3:
            raise ValueError('messages for the query, key and value inputs')

        self._queries = queries  # [1 | 3, hidden] float32
        self._norms = list(norms)
        self._eps = eps
        self._dtype = dtype
        self._boundary = boundary
        self._messages = messages

    def read(self, ops: Ops, r: DepthStream) -> tuple[ta.Any, ta.Any]:
        if self._queries is None:
            xs = [ops.f32(r.partial)]
        else:
            mix = depth_read(ops, self._queries, r, self._eps)
            xs = [mix[:, :, i] for i in range(len(self._norms))]

        if self._messages is not None and r.messages is not None:
            xs = self._messages.read(ops, r.messages, xs)

        norms = self._norms
        out = [
            ops.rms_norm_to(x, norms[i if len(norms) > 1 else 0], self._eps, self._dtype)
            for i, x in enumerate(xs)
        ]
        if len(out) == 1:
            out = out * 3

        return tuple(out), None

    def write(self, ops: Ops, r: DepthStream, y: Array, carry: ta.Any) -> DepthStream:
        # (the sum stays float32 from here to the layer's end: the feed-forward's connection rounds it)
        if self._boundary:
            return r._replace(
                completed=(*r.completed, unit_rms(ops, r.partial, self._eps)),
                partial=ops.f32(y),
            )

        return r._replace(partial=ops.sum_to(r.partial, y, ops.dtype('f32')))


class DepthFeedForwardConnection(Connection):
    def __init__(
            self,
            *,
            query: Array,
            norm: Array,
            eps: float,
            dtype: ta.Any,
            messages: MessageReader | None = None,
    ) -> None:
        super().__init__()

        if messages is not None and len(messages) != 1:
            raise ValueError('one message for the feed-forward input')

        self._query = query  # [1, hidden] float32
        self._norm = norm
        self._eps = eps
        self._dtype = dtype
        self._messages = messages

    def read(self, ops: Ops, r: DepthStream) -> tuple[ta.Any, ta.Any]:
        xs = [depth_read(ops, self._query, r, self._eps)[:, :, 0]]

        if self._messages is not None and r.messages is not None:
            xs = self._messages.read(ops, r.messages, xs)

        return ops.rms_norm_to(xs[0], self._norm, self._eps, self._dtype), None

    def write(self, ops: Ops, r: DepthStream, y: Array, carry: ta.Any) -> DepthStream:
        return r._replace(partial=ops.sum_to(r.partial, y, self._dtype))
