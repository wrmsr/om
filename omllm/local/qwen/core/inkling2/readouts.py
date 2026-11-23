import typing as ta

from ...ops.base import Array
from ...ops.base import Ops
from ..readouts import StackedReadout
from .depth import DepthStream


##


class BlockSumReadout(StackedReadout):
    """
    What Inkling 2's drafter reads of a position (core/dspark/): the sum of the block under way as each tapped layer
    receives it -- before the layer reads it or adds to it, with no norm, and none of the finished blocks' sums or of
    the embedding in it -- and then the final normed state.
    """

    def tap(self, ops: Ops, r: ta.Any) -> Array:
        stream: DepthStream = r
        return stream.partial
