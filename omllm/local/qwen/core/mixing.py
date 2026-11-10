# ruff: noqa: N803 N806
"""
The parts a block is composed of, as interfaces: a mixer (attention, Gated DeltaNet; Flash-Next adds QSA) with the
layout of its decode state, a feed-forward (dense SwiGLU; Flash-Next adds MoE), and the residual stream the sublayers
read from and write to (plain; Flash-Next adds the four-branch Gated Residual). An architecture (arch/) builds blocks
from these for its config.
"""
import abc
import dataclasses as dc  # STDLIB, deliberately: StepContext is built in compiled steps (backends/torch_triton.py)
import typing as ta

from omcore import lang

from ..ops.base import Array
from ..ops.base import Ops


##


@dc.dataclass(frozen=True)
class StepContext:
    """
    What a static T-token step hands every mixer besides its input and state: the 0-d position, `arange(capacity)`, the
    rope rows for positions pos..pos+T-1, whether to return the state after every token, and the attention window
    (0 = the whole buffer). Built inside the captured / compiled step, hence a stdlib dataclass.
    """

    pos: Array
    ar: Array
    cos: Array
    sin: Array
    all_states: bool = False
    bucket: int = 0


class StateLayout(lang.Abstract):
    """
    How one layer's decode state is laid out and carried by the static decoder: the decoder holds a flat list of every
    layer's arrays and asks each layer's layout what to do with its own. The functional `Cache` holds the same tuples
    at exact length.
    """

    @abc.abstractmethod
    def arity(self, ops: Ops) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def empty(self, ops: Ops, dtype: ta.Any) -> tuple[Array, ...]:
        """The state before any token."""

        raise NotImplementedError

    @abc.abstractmethod
    def adapt(self, ops: Ops, state: tuple[Array, ...], dtype: ta.Any) -> tuple[Array, ...]:
        """A state made elsewhere (another backend format, a snapshot) in this backend's format."""

        raise NotImplementedError

    @abc.abstractmethod
    def pad(self, ops: Ops, state: tuple[Array, ...], capacity: int) -> tuple[Array, ...]:
        """The state in fixed-capacity buffers (positions past the sequence are padding)."""

        raise NotImplementedError

    @abc.abstractmethod
    def export(self, ops: Ops, state: tuple[Array, ...], seq_len: int) -> tuple[Array, ...]:
        """A copy at exact length, for the functional cache and snapshots."""

        raise NotImplementedError

    @abc.abstractmethod
    def commit(self, ops: Ops, state: tuple[Array, ...], n: int, stacked: bool) -> tuple[Array, ...]:
        """After a T-token step: the state after its first n tokens (`stacked`: the step returned one per token)."""

        raise NotImplementedError

    @abc.abstractmethod
    def capacity(self, ops: Ops, state: tuple[Array, ...]) -> int | None:
        """The positions the state's buffers hold, or None for a fixed-size state."""

        raise NotImplementedError


class Mixer(lang.Abstract):
    """A block's sequence-mixing sublayer: everything that sees other positions."""

    @property
    @abc.abstractmethod
    def state(self) -> StateLayout:
        raise NotImplementedError

    @abc.abstractmethod
    def __call__(
            self,
            ops: Ops,
            x: Array,
            pos: int,
            state: tuple[Array, ...] | None,
    ) -> tuple[Array, tuple[Array, ...]]:
        """Functional form (prefill, the reference): x [B, T, hidden] at positions pos.., growing state in and out."""

        raise NotImplementedError

    @abc.abstractmethod
    def step(self, ops: Ops, x: Array, ctx: StepContext, state: tuple[Array, ...]) -> tuple[Array, tuple[Array, ...]]:
        """Static form: T tokens against fixed-shape state (every shape independent of the position)."""

        raise NotImplementedError


class FeedForward(lang.Abstract):
    @abc.abstractmethod
    def __call__(self, ops: Ops, x: Array) -> Array:
        raise NotImplementedError


class ResidualStream(lang.Abstract):
    """
    How sublayers read their input from and write their output to the residual stream. `slot` numbers the sublayers
    (2 i for block i's mixer, 2 i + 1 for its feed-forward) so a strategy with per-sublayer parameters (Flash-Next's
    Gated Residual) can find its own.
    """

    @abc.abstractmethod
    def enter(self, ops: Ops, x: Array) -> Array:
        """The stream from the embedding."""

        raise NotImplementedError

    @abc.abstractmethod
    def read(self, ops: Ops, r: Array, slot: int) -> Array:
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, ops: Ops, r: Array, y: Array, slot: int) -> Array:
        raise NotImplementedError

    @abc.abstractmethod
    def exit(self, ops: Ops, r: Array) -> Array:
        """What the final norm reads."""

        raise NotImplementedError


class PlainResidual(ResidualStream):
    """x + sublayer(norm(x)): one vector, read as is, written by addition."""

    def enter(self, ops: Ops, x: Array) -> Array:
        return x

    def read(self, ops: Ops, r: Array, slot: int) -> Array:
        return r

    def write(self, ops: Ops, r: Array, y: Array, slot: int) -> Array:
        return r + y

    def exit(self, ops: Ops, r: Array) -> Array:
        return r
