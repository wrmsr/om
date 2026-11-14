# ruff: noqa: N803 N806
"""
The parts a block is composed of, as interfaces: a mixer (attention, Gated DeltaNet; Flash-Next adds QSA) with the
layout of its decode state, a feed-forward (dense SwiGLU; Flash-Next adds MoE), each sublayer's connection to the
residual stream (pre-norm and add; Flash-Next's four-branch gated residual), and the stream's two ends. An
architecture (arch/) builds blocks from these for its config.
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
    rope rows for positions pos..pos+T-1, whether to return the state after every token, the attention window (0 = the
    whole buffer), the full rope tables (QSA rotates its block keys at their own positions), and the step's token ids
    [B, T] (the n-gram layer hashes them). Built inside the captured / compiled step, hence a stdlib dataclass.
    """

    pos: Array
    ar: Array
    cos: Array
    sin: Array
    all_states: bool = False
    bucket: int = 0
    cos_tab: Array | None = None
    sin_tab: Array | None = None
    ids: Array | None = None


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

    def reserve(
            self,
            ops: Ops,
            state: tuple[Array, ...],
            capacity: int,
            into: tuple[Array, ...] | None = None,
    ) -> tuple[Array, ...]:
        """
        A functional state given room for `capacity` positions ahead of a long prefill, for a layout whose functional
        form can write into spare room (attention's KV: Ops.kv_reserve). `into`: this layer's state arrays as an
        earlier decoder left them, whose capacity buffers are used where they fit. Default: the state as it is.
        """

        return state

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


class CompositeStateLayout(StateLayout):
    """Several parts' states side by side, in order: a block whose layer embedding has state of its own."""

    def __init__(self, parts: ta.Sequence[StateLayout]) -> None:
        super().__init__()

        self._parts = list(parts)

    def _split(self, ops: Ops, state: tuple[Array, ...]) -> list[tuple[Array, ...]]:
        out = []
        o = 0
        for p in self._parts:
            n = p.arity(ops)
            out.append(tuple(state[o:o + n]))
            o += n
        return out

    def arity(self, ops: Ops) -> int:
        return sum(p.arity(ops) for p in self._parts)

    def empty(self, ops: Ops, dtype: ta.Any) -> tuple[Array, ...]:
        return tuple(a for p in self._parts for a in p.empty(ops, dtype))

    def adapt(self, ops: Ops, state: tuple[Array, ...], dtype: ta.Any) -> tuple[Array, ...]:
        return tuple(a for p, s in zip(self._parts, self._split(ops, state)) for a in p.adapt(ops, s, dtype))

    def pad(self, ops: Ops, state: tuple[Array, ...], capacity: int) -> tuple[Array, ...]:
        return tuple(a for p, s in zip(self._parts, self._split(ops, state)) for a in p.pad(ops, s, capacity))

    def reserve(
            self,
            ops: Ops,
            state: tuple[Array, ...],
            capacity: int,
            into: tuple[Array, ...] | None = None,
    ) -> tuple[Array, ...]:
        parts = self._split(ops, state)
        intos: ta.Sequence[tuple[Array, ...] | None] = [None] * len(parts)
        if into is not None and len(into) == len(state):
            intos = self._split(ops, into)
        return tuple(a for p, s, i in zip(self._parts, parts, intos) for a in p.reserve(ops, s, capacity, i))

    def export(self, ops: Ops, state: tuple[Array, ...], seq_len: int) -> tuple[Array, ...]:
        return tuple(a for p, s in zip(self._parts, self._split(ops, state)) for a in p.export(ops, s, seq_len))

    def commit(self, ops: Ops, state: tuple[Array, ...], n: int, stacked: bool) -> tuple[Array, ...]:
        return tuple(a for p, s in zip(self._parts, self._split(ops, state)) for a in p.commit(ops, s, n, stacked))

    def capacity(self, ops: Ops, state: tuple[Array, ...]) -> int | None:
        caps = [c for p, s in zip(self._parts, self._split(ops, state)) if (c := p.capacity(ops, s)) is not None]
        return caps[0] if caps else None


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


class LayerEmbedding(lang.Abstract):
    """
    What a block adds into the residual stream before its mixer reads it, computed from the token ids and the stream
    itself: Flash-Next's n-gram layer (core/ple.py). It carries decode state of its own (the block's state is the
    mixer's followed by this).
    """

    @property
    @abc.abstractmethod
    def state(self) -> StateLayout:
        raise NotImplementedError

    @abc.abstractmethod
    def __call__(
            self,
            ops: Ops,
            r: Array,
            ids: ta.Any,
            state: tuple[Array, ...] | None,
    ) -> tuple[Array, tuple[Array, ...]]:
        """The addend for `r` [B, T, ...] at token ids [B, T] (host ints), and the state after them."""

        raise NotImplementedError

    @abc.abstractmethod
    def step(
            self,
            ops: Ops,
            r: Array,
            ctx: StepContext,
            state: tuple[Array, ...],
    ) -> tuple[Array, tuple[Array, ...]]:
        """The static form, at ctx.ids (on the device); the state after every token when ctx.all_states."""

        raise NotImplementedError


class Connection(lang.Abstract):
    """
    How one sublayer meets the residual stream: what it reads as its input -- the pre-norm included -- and how its
    output is written back. `read` also returns whatever `write` needs from what it read (Flash-Next's gated residual
    writes with gates computed from the state it read). Each sublayer has its own: a strategy with per-sublayer
    parameters keeps them here.
    """

    @abc.abstractmethod
    def read(self, ops: Ops, r: Array) -> tuple[Array, ta.Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, ops: Ops, r: Array, y: Array, carry: ta.Any) -> Array:
        raise NotImplementedError


class ResidualStream(lang.Abstract):
    """The residual stream's two ends: entered from the embedding, and left for the output head (its norm included)."""

    @abc.abstractmethod
    def enter(self, ops: Ops, x: Array) -> Array:
        raise NotImplementedError

    @abc.abstractmethod
    def exit(self, ops: Ops, r: Array) -> Array:
        """What the output head reads: final-normed."""

        raise NotImplementedError


class PlainConnection(Connection):
    """`x + sublayer(rmsnorm(x))`: the pre-norm, and a write by addition."""

    def __init__(self, norm: Array, eps: float) -> None:
        super().__init__()

        self.norm = norm
        self.eps = eps

    def read(self, ops: Ops, r: Array) -> tuple[Array, ta.Any]:
        return ops.rms_norm(r, self.norm, self.eps), None

    def write(self, ops: Ops, r: Array, y: Array, carry: ta.Any) -> Array:
        return r + y


class PlainResidual(ResidualStream):
    """One vector: the embedding as is, and the final norm on the way out."""

    def __init__(self, norm: Array, eps: float) -> None:
        super().__init__()

        self.norm = norm
        self.eps = eps

    def enter(self, ops: Ops, x: Array) -> Array:
        return x

    def exit(self, ops: Ops, r: Array) -> Array:
        return ops.rms_norm(r, self.norm, self.eps)
