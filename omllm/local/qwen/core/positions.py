# ruff: noqa: N806
"""
What a static step is handed about positions besides its 0-d position and `arange(capacity)`: the tables an
architecture's mixers read by position, built once per capacity and shared by every decoder of it, and the step's
`StepContext` made from them. Rotary tables for Qwen; nothing for an architecture whose mixers work from the positions
themselves.
"""
import abc
import typing as ta

from omcore import lang

from ..ops.base import Array
from ..ops.base import Ops
from .mixing import StepContext


##


class StepPositions(lang.Abstract):
    @abc.abstractmethod
    def tables(self, ops: Ops, capacity: int, dtype: ta.Any) -> tuple[Array, ...]:
        """The read-only tables for `capacity` positions, in the model's dtype: a step's arguments after `ar`."""

        raise NotImplementedError

    @abc.abstractmethod
    def context(
            self,
            ops: Ops,
            toks: Array,
            pos: Array,
            ar: Array,
            tables: ta.Sequence[Array],
            *,
            all_states: bool,
            bucket: int,
    ) -> StepContext:
        """
        A T-token step's context, built inside the step (so from its arguments only, with nothing from the host):
        `toks` [B, T] at positions pos..pos+T-1, `ar` = arange(capacity), `tables` as `tables` returned them.
        """

        raise NotImplementedError


class RopeStepPositions(StepPositions):
    """The rotary cos / sin tables [capacity, rope_dim], and each step's rows of them."""

    def __init__(self, *, rope_dim: int, rope_theta: float) -> None:
        super().__init__()

        self._rope_dim = rope_dim
        self._rope_theta = rope_theta

    def tables(self, ops: Ops, capacity: int, dtype: ta.Any) -> tuple[Array, ...]:
        cos_np, sin_np = ops.rope_tables(0, capacity, self._rope_dim, self._rope_theta)
        return (ops.array(cos_np, dtype), ops.array(sin_np, dtype))

    def context(
            self,
            ops: Ops,
            toks: Array,
            pos: Array,
            ar: Array,
            tables: ta.Sequence[Array],
            *,
            all_states: bool,
            bucket: int,
    ) -> StepContext:
        cos_tab, sin_tab = tables
        T = toks.shape[1]

        # index with a 1-element array, not the 0-d one: torch turns a 0-d tensor index into `.item()`, a
        # device->host sync that is illegal inside a CUDA graph capture; a 1-d index is a plain gather
        rows = ops.reshape(pos, (1,)) + ar[:T]
        cos = cos_tab[rows]  # [T, rope_dim]
        sin = sin_tab[rows]

        return StepContext(pos, ar, cos, sin, all_states, bucket, cos_tab, sin_tab, toks)


class PlainStepPositions(StepPositions):
    """No tables: the mixers read the step's position and `arange(capacity)` themselves."""

    def tables(self, ops: Ops, capacity: int, dtype: ta.Any) -> tuple[Array, ...]:
        return ()

    def context(
            self,
            ops: Ops,
            toks: Array,
            pos: Array,
            ar: Array,
            tables: ta.Sequence[Array],
            *,
            all_states: bool,
            bucket: int,
    ) -> StepContext:
        return StepContext(pos, ar, None, None, all_states, bucket, None, None, toks)
