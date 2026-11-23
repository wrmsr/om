import typing as ta

from ..ops.base import Array
from ..ops.base import Ops
from .mixing import CompositeStateLayout
from .mixing import Connection
from .mixing import Layer
from .mixing import Mixer
from .mixing import StateLayout
from .mixing import StepContext


##


def _stream_arrays(r: ta.Any) -> list[Array]:
    """
    The arrays a residual stream holds, whatever it is: one array, or tuples of them at any depth (core/inkling2/'s
    block sums and what its loop keeps beside them).
    """

    if r is None:
        return []
    if isinstance(r, tuple):
        return [a for part in r for a in _stream_arrays(part)]
    return [r]


class SublayerBlock(Layer):
    """
    A layer as sublayers in order, each read from the residual stream and written back through its own connection,
    each with decode state of its own: what `Block` is for a mixer and a stateless feed-forward, for an architecture
    whose every sublayer keeps state (core/inkling2/: its feed-forward's output is convolved over time) or whose
    stream is not one array. `index` names its taps -- `layers.{index}.{j}`, sublayer j's output -- and is its place
    in the model's execution order, so two entries built over the same sublayers stay apart.
    """

    def __init__(
            self,
            *,
            index: int,
            sublayers: ta.Sequence[tuple[Mixer, Connection]],
    ) -> None:
        super().__init__()

        self.index = index
        self._sublayers = list(sublayers)
        self._state = CompositeStateLayout([m.state for m, _ in self._sublayers])

    @property
    def sublayers(self) -> ta.Sequence[tuple[Mixer, Connection]]:
        return self._sublayers

    @property
    def state(self) -> StateLayout:
        return self._state

    def _split(self, ops: Ops, state: ta.Any) -> list[tuple[Array, ...]]:
        out: list[tuple[Array, ...]] = []
        o = 0
        for mixer, _ in self._sublayers:
            n = mixer.state.arity(ops)
            out.append(tuple(state[o:o + n]))
            o += n
        return out

    def __call__(
            self,
            ops: Ops,
            r: ta.Any,
            pos: int,
            state: ta.Any,
            ids: ta.Any = None,
    ) -> tuple[ta.Any, ta.Any]:
        out: list[Array] = []

        states: ta.Sequence[tuple[Array, ...] | None] = [None] * len(self._sublayers)
        if state is not None:
            states = self._split(ops, state)

        for j, ((mixer, conn), st) in enumerate(zip(self._sublayers, states)):
            h, carry = conn.read(ops, r)
            y, new = mixer(ops, h, pos, st)
            ops.tap(f'layers.{self.index}.{j}', y)
            r = conn.write(ops, r, y, carry)
            out.extend(new)

        # (as Block does, the stream with the state: a lazy backend's graph is one layer's at a time, and no layer's
        # output is left pending for every later one's evaluation to compute again)
        ops.materialize(*_stream_arrays(r), *out)

        return r, tuple(out)

    def step(self, ops: Ops, r: ta.Any, ctx: StepContext, state: ta.Any) -> tuple[ta.Any, ta.Any]:
        out: list[Array] = []

        for (mixer, conn), st in zip(self._sublayers, self._split(ops, state)):
            h, carry = conn.read(ops, r)
            y, new = mixer.step(ops, h, ctx, st)
            r = conn.write(ops, r, y, carry)
            out.extend(new)

        ops.materialize(*_stream_arrays(r), *out)

        return r, tuple(out)
