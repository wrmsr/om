"""
The output head: from the residual stream's exit to the logits a sampler reads, float32 over the ids a model can
produce. Which one is an architecture's choice (arch/).
"""
import abc

from omcore import lang

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight


##


class OutputHead(lang.Abstract):
    @abc.abstractmethod
    def __call__(self, ops: Ops, x: Array) -> Array:
        """Final-normed hidden states [..., hidden] -> logits [..., V] float32."""

        raise NotImplementedError


class LinearOutputHead(OutputHead):
    """The projection alone."""

    def __init__(self, weight: Weight) -> None:
        super().__init__()

        self._weight = weight

    def __call__(self, ops: Ops, x: Array) -> Array:
        return ops.f32(ops.linear(x, self._weight))


class SoftcappedOutputHead(OutputHead):
    """
    The projection, then `cap * tanh(logits / cap)` in float32: logits kept within (-cap, cap). Monotonic, so the
    greedy token is the uncapped one's; the distribution a sampler draws from is not.
    """

    def __init__(self, weight: Weight, cap: float) -> None:
        super().__init__()

        self._weight = weight
        self._cap = cap

    def __call__(self, ops: Ops, x: Array) -> Array:
        return ops.tanh(ops.f32(ops.linear(x, self._weight)) / self._cap) * self._cap
