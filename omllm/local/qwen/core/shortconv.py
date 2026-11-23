# ruff: noqa: N803 N806
"""
Short causal convolutions over time, per channel, with a residual: a few taps over a sublayer's own recent outputs.
Their decode state is the last K - 1 raw inputs.

    static    y[t] = (x[t] + sum_a w[a] x[t - (K - 1) + a]) / sqrt(1 + K)          taps oldest first, per channel
    dynamic   y[t] = (x[t] + sum_lag (w[lag] + d[t, lag]) x[t - lag]) / sqrt(1 + 2 K)

where the dynamic form's `d` are taps predicted at each output position from a hidden state (`cond`), one set per head
shared by the head's channels. All in float32; inputs before the sequence starts are zero.
"""
import abc
import typing as ta

from omcore import lang

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from .mixing import CompositeStateLayout
from .mixing import EmptyStateLayout
from .mixing import FeedForward
from .mixing import Mixer
from .mixing import StateLayout
from .mixing import StepContext


##


class ShortConvStateLayout(StateLayout):
    """
    A short convolution's state: its last K - 1 inputs [B, C, K - 1], float32 and fixed-size -- nothing to pad, and a
    T-token step that returns the state after every token commits by selecting one.
    """

    def __init__(self, *, channels: int, kernel: int) -> None:
        super().__init__()

        self._channels = channels
        self._kernel = kernel

    def arity(self, ops: Ops) -> int:
        return 1

    def empty(self, ops: Ops, dtype: ta.Any) -> tuple[Array, ...]:
        return (ops.zeros((1, self._channels, self._kernel - 1), ops.dtype('f32')),)

    def adapt(self, ops: Ops, state: tuple[Array, ...], dtype: ta.Any) -> tuple[Array, ...]:
        return state

    def pad(self, ops: Ops, state: tuple[Array, ...], capacity: int) -> tuple[Array, ...]:
        return tuple(ops.copy(a) for a in state)  # (dense, whatever came in: see RecurrentStateLayout.pad)

    def export(self, ops: Ops, state: tuple[Array, ...], seq_len: int) -> tuple[Array, ...]:
        return tuple(ops.copy(a) for a in state)

    def commit(self, ops: Ops, state: tuple[Array, ...], n: int, stacked: bool) -> tuple[Array, ...]:
        if not stacked:
            return state
        return tuple(ops.select(a, n - 1) for a in state)

    def capacity(self, ops: Ops, state: tuple[Array, ...]) -> int | None:
        return None


class ShortConv(lang.Abstract):
    @property
    @abc.abstractmethod
    def state(self) -> StateLayout:
        raise NotImplementedError

    @abc.abstractmethod
    def __call__(
            self,
            ops: Ops,
            x: Array,
            cond: Array | None,
            state: tuple[Array, ...] | None,
            all_states: bool,
    ) -> tuple[Array, tuple[Array, ...]]:
        """
        x [B, T, C] -> [B, T, C] in x's dtype, and the state after the T inputs -- after each of them, stacked along a
        leading axis, with `all_states`. `cond` [B, T, hidden] is what a dynamic convolution predicts its taps from.
        """

        raise NotImplementedError


def _short_conv_inputs(
        ops: Ops,
        x: Array,
        state: tuple[Array, ...] | None,
        kernel: int,
) -> tuple[Array, Array]:
    """x as [B, C, T] float32, and [history | x] along time, [B, C, K - 1 + T]."""

    B, T, C = x.shape
    f32 = ops.dtype('f32')

    xf = ops.transpose(ops.f32(x), (0, 2, 1))
    hist = state[0] if state is not None else ops.zeros((B, C, kernel - 1), f32)
    return xf, ops.concat([hist, xf], -1)


def _short_conv_history(ops: Ops, inp: Array, T: int, kernel: int, all_states: bool) -> tuple[Array, ...]:
    if all_states:
        return (ops.stack([inp[..., t + 1:t + kernel] for t in range(T)], 0),)  # [T, B, C, K - 1]

    # a dense copy, not a slice of the input (which a view would keep alive, with strides that depend on T: see
    # GatedDeltaNet._mix)
    return (ops.copy(inp[..., -(kernel - 1):]),)


class StaticShortConv(ShortConv):
    def __init__(self, weight: Array) -> None:
        """`weight`: [C, K] float32, each channel's taps oldest first (a conv1d weight with its unit axis dropped)."""

        super().__init__()

        self._weight = weight
        self._kernel = K = int(weight.shape[-1])
        self._scale = (1 + K) ** -0.5
        self._state = ShortConvStateLayout(channels=int(weight.shape[0]), kernel=K)

    @property
    def state(self) -> StateLayout:
        return self._state

    def __call__(
            self,
            ops: Ops,
            x: Array,
            cond: Array | None,
            state: tuple[Array, ...] | None,
            all_states: bool,
    ) -> tuple[Array, tuple[Array, ...]]:
        T = x.shape[1]
        K = self._kernel

        xf, inp = _short_conv_inputs(ops, x, state, K)
        y = (xf + ops.conv1d_causal(inp, self._weight)) * self._scale

        return ops.cast(ops.transpose(y, (0, 2, 1)), x.dtype), _short_conv_history(ops, inp, T, K, all_states)


class DynamicShortConv(ShortConv):
    def __init__(self, *, weight: Array, proj: Weight, heads: int) -> None:
        """
        `weight`: [K, C] float32, the static taps by backward lag (0: the current input); `proj`: [heads * K, hidden],
        each position's dynamic taps -- [heads, K], by lag too -- from `cond`, a head's shared by its C / heads
        channels.
        """

        super().__init__()

        self._weight = weight
        self._proj = proj
        self._heads = heads
        self._kernel = K = int(weight.shape[0])
        self._scale = (1 + 2 * K) ** -0.5
        self._state = ShortConvStateLayout(channels=int(weight.shape[1]), kernel=K)

    @property
    def state(self) -> StateLayout:
        return self._state

    def __call__(
            self,
            ops: Ops,
            x: Array,
            cond: Array | None,
            state: tuple[Array, ...] | None,
            all_states: bool,
    ) -> tuple[Array, tuple[Array, ...]]:
        B, T, C = x.shape
        K = self._kernel
        H = self._heads

        xf, inp = _short_conv_inputs(ops, x, state, K)
        dyn = ops.reshape(ops.f32(ops.linear(cond, self._proj)), (B, T, H, K))

        acc = None
        for lag in range(K):
            at = K - 1 - lag
            tap = self._weight[lag][None, :, None] + ops.repeat(ops.transpose(dyn[..., lag], (0, 2, 1)), C // H, 1)
            term = tap * inp[..., at:at + T]
            acc = term if acc is None else acc + term

        y = (xf + acc) * self._scale

        return ops.cast(ops.transpose(y, (0, 2, 1)), x.dtype), _short_conv_history(ops, inp, T, K, all_states)


##


class FeedForwardMixer(Mixer):
    """A feed-forward where a mixer is taken: it sees no other position and has no state."""

    def __init__(self, ffn: FeedForward) -> None:
        super().__init__()

        self._ffn = ffn
        self._state = EmptyStateLayout()

    @property
    def state(self) -> StateLayout:
        return self._state

    def __call__(
            self,
            ops: Ops,
            x: Array,
            pos: int,
            state: tuple[Array, ...] | None,
    ) -> tuple[Array, tuple[Array, ...]]:
        return self._ffn(ops, x), ()

    def step(self, ops: Ops, x: Array, ctx: StepContext, state: tuple[Array, ...]) -> tuple[Array, tuple[Array, ...]]:
        return self._ffn(ops, x), ()


class ConvolvedMixer(Mixer):
    """
    A mixer whose output goes through a short convolution on its way to the residual stream: the mixer's state, then
    the convolution's history.
    """

    def __init__(self, inner: Mixer, conv: ShortConv) -> None:
        super().__init__()

        self._inner = inner
        self._conv = conv
        self._state = CompositeStateLayout([inner.state, conv.state])

    @property
    def state(self) -> StateLayout:
        return self._state

    def __call__(
            self,
            ops: Ops,
            x: Array,
            pos: int,
            state: tuple[Array, ...] | None,
    ) -> tuple[Array, tuple[Array, ...]]:
        n = self._inner.state.arity(ops)

        y, st = self._inner(ops, x, pos, None if state is None else tuple(state[:n]))
        y, cst = self._conv(ops, y, None, None if state is None else tuple(state[n:]), False)

        return y, (*st, *cst)

    def step(self, ops: Ops, x: Array, ctx: StepContext, state: tuple[Array, ...]) -> tuple[Array, tuple[Array, ...]]:
        n = self._inner.state.arity(ops)

        y, st = self._inner.step(ops, x, ctx, tuple(state[:n]))
        y, cst = self._conv(ops, y, None, tuple(state[n:]), ctx.all_states)

        return y, (*st, *cst)
