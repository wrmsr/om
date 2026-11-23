"""
What a draft head reads of the target at each position: the model's "hidden" output, which the decode loop hands to a
draft source over the prompt (`DraftSource.start`) and after every verified step (`Verified.hidden`). For most heads
it is the stream's exit, the final normed state, and nothing else; a head that also reads states inside the stack
(Inkling 2's drafter: core/dspark/) has an architecture supply a readout that keeps them as the layers run.
"""
import abc
import typing as ta

from omcore import lang

from ..ops.base import Array
from ..ops.base import Ops


##


class Readout(lang.Abstract):
    @property
    @abc.abstractmethod
    def taps(self) -> ta.Sequence[int]:
        """The layers, by place in the model's execution order, whose incoming stream is kept; ascending."""

        raise NotImplementedError

    @abc.abstractmethod
    def tap(self, ops: Ops, r: ta.Any) -> Array:
        """What is kept of the stream as a tapped layer receives it: [B, T, H]."""

        raise NotImplementedError

    @abc.abstractmethod
    def join(self, ops: Ops, tapped: ta.Sequence[Array], x: Array) -> Array:
        """The hidden output [B, T, F], from what was tapped and the final normed state x [B, T, H]."""

        raise NotImplementedError


class FinalStateReadout(Readout):
    """The final normed state as it is."""

    @property
    def taps(self) -> ta.Sequence[int]:
        return ()

    def tap(self, ops: Ops, r: ta.Any) -> Array:
        raise TypeError('nothing is tapped')

    def join(self, ops: Ops, tapped: ta.Sequence[Array], x: Array) -> Array:
        return x


class StackedReadout(Readout, lang.Abstract):
    """
    The tapped states and the final one side by side along the last axis, [B, T, (n + 1) H], in the final state's
    dtype: a subclass says what a tap keeps of its stream.
    """

    def __init__(self, taps: ta.Sequence[int]) -> None:
        super().__init__()

        self._taps = tuple(sorted(taps))

    @property
    def taps(self) -> ta.Sequence[int]:
        return self._taps

    def join(self, ops: Ops, tapped: ta.Sequence[Array], x: Array) -> Array:
        return ops.concat([*(ops.cast(t, x.dtype) for t in tapped), x], -1)
