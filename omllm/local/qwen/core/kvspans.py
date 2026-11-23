# ruff: noqa: N803 N806
"""
Which earlier positions an attention layer's queries see, and how their keys and values are kept between steps: the
whole sequence in append-only buffers (what core/attention.py's layers keep), or a sliding window of the last few
positions in a fixed-size state. For a prefill a span hands the attention the keys and values its queries can reach,
plain, with their positions; a static step's attention it runs itself, over what it keeps, since how much of that a
step has to read is the span's to know. The attention here is the kind with a relative term and a sink
(`Ops.sdpa_sink`, `Ops.rel_bias`: core/inkling2/attention.py).

The KV itself stays in whatever format the backend keeps it (`Ops.kv_*`): a span moves states around and never looks
inside one.
"""
import abc
import typing as ta

from omcore import lang

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from .attention import KvStateLayout
from .attention import extend_kv
from .mixing import StateLayout
from .mixing import StepContext


##


class KvSpan(lang.Abstract):
    @property
    @abc.abstractmethod
    def state(self) -> StateLayout:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def reach(self) -> int | None:
        """How many positions a query sees, its own included; None for every one so far."""

        raise NotImplementedError

    @abc.abstractmethod
    def sees(self, ops: Ops, delta: Array) -> Array:
        """float32 1 / 0 over `delta`, integer distances from a query back to a key: whether the query sees it."""

        raise NotImplementedError

    @abc.abstractmethod
    def extend(
            self,
            ops: Ops,
            state: tuple[Array, ...] | None,
            pos: int,
            k: Array,
            v: Array,
            dtype: ta.Any,
    ) -> tuple[tuple[Array, ...], Array, Array, int]:
        """
        Functional form: the state taken past T new positions' k, v [B, KV, T, D] at positions pos.., and what those
        positions' queries can reach -- plain keys and values [B, KV, n, D] in `dtype` for the consecutive positions
        `first` .. pos + T - 1. Returns (state, keys, values, first).
        """

        raise NotImplementedError

    @abc.abstractmethod
    def attend(
            self,
            ops: Ops,
            state: tuple[Array, ...],
            ctx: StepContext,
            q: Array,
            k: Array,
            v: Array,
            *,
            scale: float,
            rel: Array,
            rel_proj: Weight,
            sink: Array,
    ) -> tuple[tuple[Array, ...], Array]:
        """
        Static form, every shape independent of the position: the step's T keys and values [B, KV, T, D] taken into
        the state, and its queries q [B, H, T, D] attended over what they see -- their relative term for a key d
        back being rel[t, h] . rel_proj[d] (`rel` [T, H, R], `rel_proj` [E, R]), `sink` [B, H, T] theirs. Returns
        (state, output [B, H, T, D]); with `ctx.all_states` the state is one a commit can cut at any of the step's
        tokens.
        """

        raise NotImplementedError


class FullKvSpan(KvSpan):
    """Every position so far, in append-only KV buffers of the decoder's capacity (written in place by a step)."""

    def __init__(self, *, num_kv_heads: int, head_dim: int) -> None:
        super().__init__()

        self._state = KvStateLayout(num_kv_heads=num_kv_heads, head_dim=head_dim)

    @property
    def state(self) -> StateLayout:
        return self._state

    @property
    def reach(self) -> int | None:
        return None

    def sees(self, ops: Ops, delta: Array) -> Array:
        return ops.cast(delta >= 0, ops.dtype('f32'))

    def extend(
            self,
            ops: Ops,
            state: tuple[Array, ...] | None,
            pos: int,
            k: Array,
            v: Array,
            dtype: ta.Any,
    ) -> tuple[tuple[Array, ...], Array, Array, int]:
        state, seen, past = extend_kv(ops, state, pos, k, v)
        if past != pos:
            raise ValueError(f'a KV state of {past} positions at position {pos}')

        kd, vd = ops.kv_dense(seen, dtype)
        return state, kd, vd, 0

    def attend(
            self,
            ops: Ops,
            state: tuple[Array, ...],
            ctx: StepContext,
            q: Array,
            k: Array,
            v: Array,
            *,
            scale: float,
            rel: Array,
            rel_proj: Weight,
            sink: Array,
    ) -> tuple[tuple[Array, ...], Array]:
        state = ops.kv_write_tokens(state, ctx.pos, k, v)

        # over the whole buffer, or the decoder's window of it (`ctx.bucket`: a power of two covering the step)
        n = ops.kv_len(state)
        seen = state
        if ctx.bucket and ctx.bucket < n:
            n = ctx.bucket
            seen = ops.kv_window(state, n)

        return state, ops.sdpa_static_rel(q, seen, ctx.pos, ctx.ar[:n], scale, rel, rel_proj, sink)


class SlidingKvStateLayout(StateLayout):
    """
    The keys and values of the last `window - 1` positions, oldest first. Between functional steps and in snapshots it
    is exactly as long as the positions there are (fewer near the start); a static decoder carries it at full length,
    right-aligned, the missing positions' slots zeroed (the step masks them by position). Fixed-size either way: no
    capacity, nothing written in place. After a T-token step that keeps every state, it comes back T positions
    longer, and a commit of n tokens is the window ending at the n-th.
    """

    def __init__(self, *, num_kv_heads: int, head_dim: int, window: int) -> None:
        super().__init__()

        self._num_kv_heads = num_kv_heads
        self._head_dim = head_dim
        self._kept = window - 1

    def arity(self, ops: Ops) -> int:
        return ops.kv_arity

    def empty(self, ops: Ops, dtype: ta.Any) -> tuple[Array, ...]:
        z = ops.zeros((1, self._num_kv_heads, 0, self._head_dim), dtype)
        return ops.kv_new(z, z)

    def adapt(self, ops: Ops, state: tuple[Array, ...], dtype: ta.Any) -> tuple[Array, ...]:
        return ops.kv_adapt(state, dtype)

    def pad(self, ops: Ops, state: tuple[Array, ...], capacity: int) -> tuple[Array, ...]:
        n = ops.kv_len(state)
        if n > self._kept:
            return ops.kv_range(state, n - self._kept, n)
        if n == self._kept:
            return tuple(ops.copy(a) for a in state)

        # zeros in front (the backend's own, for its format: an empty state padded out)
        front = ops.kv_pad(ops.kv_window(state, 0), self._kept - n)
        return tuple(ops.copy(a) for a in ops.kv_join(front, state))

    def export(self, ops: Ops, state: tuple[Array, ...], seq_len: int) -> tuple[Array, ...]:
        n = ops.kv_len(state)
        return ops.kv_range(state, n - min(seq_len, self._kept, n), n)

    def commit(self, ops: Ops, state: tuple[Array, ...], n: Array, stacked: bool) -> tuple[Array, ...]:
        if not stacked:
            return state
        return ops.kv_take(state, ops.reshape(n, (1,)) + ops.arange(self._kept))

    def capacity(self, ops: Ops, state: tuple[Array, ...]) -> int | None:
        return None


class SlidingKvSpan(KvSpan):
    """
    The `window` positions up to a query's own. A step never writes into the state it was given -- the window after
    it is a new one -- so a step whose tokens are not all kept (a speculative verify) leaves nothing to undo.
    """

    def __init__(self, *, num_kv_heads: int, head_dim: int, window: int) -> None:
        super().__init__()

        if window < 2:
            raise ValueError(window)

        self._window = window
        self._state = SlidingKvStateLayout(num_kv_heads=num_kv_heads, head_dim=head_dim, window=window)

    @property
    def state(self) -> StateLayout:
        return self._state

    @property
    def reach(self) -> int | None:
        return self._window

    def sees(self, ops: Ops, delta: Array) -> Array:
        f32 = ops.dtype('f32')
        return ops.cast(delta >= 0, f32) * ops.cast(delta < self._window, f32)

    def extend(
            self,
            ops: Ops,
            state: tuple[Array, ...] | None,
            pos: int,
            k: Array,
            v: Array,
            dtype: ta.Any,
    ) -> tuple[tuple[Array, ...], Array, Array, int]:
        T = k.shape[2]
        kept = self._window - 1

        if state is None:
            n = 0
            seen = ops.kv_new(k, v)
        else:
            state = ops.kv_adapt(state)
            n = ops.kv_len(state)
            seen = ops.kv_concat(state, k, v)
        if n != min(pos, kept):
            raise ValueError(f'a window of {n} positions at position {pos}')

        kd, vd = ops.kv_dense(seen, dtype)
        return ops.kv_range(seen, n + T - min(n + T, kept), n + T), kd, vd, pos - n

    def attend(
            self,
            ops: Ops,
            state: tuple[Array, ...],
            ctx: StepContext,
            q: Array,
            k: Array,
            v: Array,
            *,
            scale: float,
            rel: Array,
            rel_proj: Weight,
            sink: Array,
    ) -> tuple[tuple[Array, ...], Array]:
        T = k.shape[2]
        kept = self._window - 1

        seen = ops.kv_concat(state, k, v)  # the window, then the step's own positions
        kd, vd = ops.kv_dense(seen, q.dtype)

        # (slot j of those stands for position pos - kept + j: none, where that is before the sequence's start)
        o = ops.sdpa_window_rel(
            q,
            kd,
            vd,
            ctx.pos,
            scale=scale,
            rel=rel,
            rel_proj=rel_proj,
            sink=sink,
            window=self._window,
        )

        return (seen if ctx.all_states else ops.kv_range(seen, T, T + kept)), o


class RunningKvStateLayout(StateLayout):
    """
    A sliding window kept where it runs: the keys and values of the last `window - 1` positions in buffers of `room`
    slots more, written in place, and with them how many of the slots are in use (a 0-d int array). A step appends
    its positions after the ones in use, and its window is the slots ending there; the slots past a commit are
    junk the next step writes over, as in an append-only buffer, so a commit moves nothing -- it advances the count
    -- and a rejected draft leaves nothing to undo. When the room runs out the last `window - 1` slots in use go
    back to the front (`make_room`), once in `room` positions.

    Between functional steps and in snapshots the window is exactly as long as the positions there are, as
    `SlidingKvStateLayout`'s is, the count beside it unused (the state has one arity in both forms).
    """

    def __init__(
            self,
            *,
            num_kv_heads: int,
            head_dim: int,
            window: int,
            room: int,
    ) -> None:
        super().__init__()

        if room < 1:
            raise ValueError(room)

        self._num_kv_heads = num_kv_heads
        self._head_dim = head_dim
        self._kept = window - 1
        self._slots = window - 1 + room

    def arity(self, ops: Ops) -> int:
        return ops.kv_arity + 1

    def empty(self, ops: Ops, dtype: ta.Any) -> tuple[Array, ...]:
        z = ops.zeros((1, self._num_kv_heads, 0, self._head_dim), dtype)
        return (*ops.kv_new(z, z), ops.scalar(0))

    def adapt(self, ops: Ops, state: tuple[Array, ...], dtype: ta.Any) -> tuple[Array, ...]:
        return (*ops.kv_adapt(tuple(state[:-1]), dtype), state[-1])

    def _used(self, ops: Ops, state: tuple[Array, ...]) -> int:
        return int(ops.numpy(state[-1]).reshape(-1)[0])

    def pad(self, ops: Ops, state: tuple[Array, ...], capacity: int) -> tuple[Array, ...]:
        kv = tuple(state[:-1])
        n = ops.kv_len(kv)
        if n == self._slots:
            return state  # (its buffers already)

        if n > self._kept:
            kv = ops.kv_range(kv, n - self._kept, n)
            n = self._kept

        # zeros before the window (positions there are none of: the step masks them) and in the room after it
        none = ops.kv_window(kv, 0)
        front = ops.kv_pad(none, self._kept - n)
        room = ops.kv_pad(none, self._slots - self._kept)
        return (*(ops.copy(a) for a in ops.kv_join(ops.kv_join(front, kv), room)), ops.scalar(self._kept))

    def export(self, ops: Ops, state: tuple[Array, ...], seq_len: int) -> tuple[Array, ...]:
        kv = tuple(state[:-1])
        n = ops.kv_len(kv)
        end = self._used(ops, state) if n == self._slots else n  # (in its buffers, or already as long as it is)
        return (*ops.kv_range(kv, end - min(seq_len, self._kept, end), end), ops.scalar(0))

    def commit(self, ops: Ops, state: tuple[Array, ...], n: Array, stacked: bool) -> tuple[Array, ...]:
        if not stacked:
            return state
        return (*state[:-1], state[-1] + n)

    def capacity(self, ops: Ops, state: tuple[Array, ...]) -> int | None:
        return None

    def room(self, ops: Ops, state: tuple[Array, ...]) -> int | None:
        return self._slots - self._used(ops, state)

    def make_room(self, ops: Ops, state: tuple[Array, ...]) -> tuple[Array, ...]:
        used = self._used(ops, state)
        if used == self._kept:
            return state
        return (*ops.kv_move(tuple(state[:-1]), used - self._kept, 0, self._kept), ops.scalar(self._kept))


class RunningKvSpan(KvSpan):
    """
    `SlidingKvSpan`'s window for a backend that writes buffers in place (`Ops.kv_in_place`): kept in place
    (`RunningKvStateLayout`) and read where it lies (`Ops.sdpa_window_rel_at`), where the sliding span's window is a
    new array every step -- joined to the step's keys to be read, cut again to be kept: the whole window moved
    twice a token and three times a verified round, for forty layers.
    """

    def __init__(
            self,
            *,
            num_kv_heads: int,
            head_dim: int,
            window: int,
            room: int,
    ) -> None:
        super().__init__()

        self._window = window
        self._functional = SlidingKvSpan(num_kv_heads=num_kv_heads, head_dim=head_dim, window=window)
        self._state = RunningKvStateLayout(num_kv_heads=num_kv_heads, head_dim=head_dim, window=window, room=room)

    @property
    def state(self) -> StateLayout:
        return self._state

    @property
    def reach(self) -> int | None:
        return self._window

    def sees(self, ops: Ops, delta: Array) -> Array:
        return self._functional.sees(ops, delta)

    def extend(
            self,
            ops: Ops,
            state: tuple[Array, ...] | None,
            pos: int,
            k: Array,
            v: Array,
            dtype: ta.Any,
    ) -> tuple[tuple[Array, ...], Array, Array, int]:
        window, kd, vd, first = self._functional.extend(
            ops,
            None if state is None else tuple(state[:-1]),
            pos,
            k,
            v,
            dtype,
        )
        return (*window, ops.scalar(0)), kd, vd, first

    def attend(
            self,
            ops: Ops,
            state: tuple[Array, ...],
            ctx: StepContext,
            q: Array,
            k: Array,
            v: Array,
            *,
            scale: float,
            rel: Array,
            rel_proj: Weight,
            sink: Array,
    ) -> tuple[tuple[Array, ...], Array]:
        T = k.shape[2]
        kept = self._window - 1
        used = state[-1]

        kv = ops.kv_write_tokens(tuple(state[:-1]), used, k, v)

        # (the window, then the step's own positions: slot j of those stands for position pos - kept + j)
        o = ops.sdpa_window_rel_at(
            q,
            kv,
            used - kept,
            kept + T,
            ctx.pos,
            scale=scale,
            rel=rel,
            rel_proj=rel_proj,
            sink=sink,
            window=self._window,
        )

        # (a step that keeps every state leaves the count to the commit)
        return (*kv, used if ctx.all_states else used + T), o
