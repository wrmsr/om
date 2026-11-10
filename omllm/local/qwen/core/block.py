# ruff: noqa: N803 N806 N812
import typing as ta

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from .mixing import FeedForward
from .mixing import Mixer
from .mixing import ResidualStream
from .mixing import StepContext


##


class Block:
    """
    One layer as a composition: read the residual stream, norm, mix, write; read, norm, feed forward, write. Which
    mixer, which feed-forward and which residual stream is the architecture's choice (arch/); the block only routes.
    """

    def __init__(
            self,
            *,
            index: int,
            mixer: Mixer,
            ffn: FeedForward,
            residual: ResidualStream,
            ln1: Weight,
            ln2: Weight,
            eps: float,
    ) -> None:
        super().__init__()

        self.index = index
        self.mixer = mixer
        self.ffn = ffn
        self.residual = residual
        self.ln1 = ln1
        self.ln2 = ln2
        self.eps = eps

    def __call__(self, ops: Ops, r: Array, pos: int, state: ta.Any) -> tuple[Array, ta.Any]:
        res = self.residual
        i = self.index

        h = ops.rms_norm(res.read(ops, r, 2 * i), self.ln1, self.eps)
        m, state = self.mixer(ops, h, pos, state)
        ops.tap(f'layers.{i}.mixer', m)
        r = res.write(ops, r, m, 2 * i)

        f = self.ffn(ops, ops.rms_norm(res.read(ops, r, 2 * i + 1), self.ln2, self.eps))
        r = res.write(ops, r, f, 2 * i + 1)
        ops.tap(f'layers.{i}.out', r)

        # a lazy backend evaluates here, so the graph is one layer's at a time: its scheduling cost and the memory of
        # its temporaries (a prefill expands quantized weights) stay bounded, and the state handed on is a buffer, not
        # a pending graph every later evaluation would walk again (nothing happens elsewhere: see Ops.materialize)
        ops.materialize(r, *state)

        return r, state

    def step(self, ops: Ops, r: Array, ctx: StepContext, state: ta.Any) -> tuple[Array, ta.Any]:
        """Static-shape step for T tokens (no taps: a captured step cannot leave the device)."""

        res = self.residual
        i = self.index

        h = ops.rms_norm(res.read(ops, r, 2 * i), self.ln1, self.eps)
        m, state = self.mixer.step(ops, h, ctx, state)
        r = res.write(ops, r, m, 2 * i)

        f = self.ffn(ops, ops.rms_norm(res.read(ops, r, 2 * i + 1), self.ln2, self.eps))
        r = res.write(ops, r, f, 2 * i + 1)

        ops.materialize(r, *state)  # as in __call__; a captured step records it, so the replay is unaffected
        return r, state


def block_params(params: ta.Mapping[str, Weight], prefix: str) -> dict[str, Weight]:
    """Collapse "prefix.self_attn.q_proj.weight" -> "q_proj", "prefix.linear_attn.A" -> "A", ..."""

    p = {}
    for k, v in params.items():
        if k.startswith(prefix):
            parts = k[len(prefix):].split('.')
            if parts[-1] == 'weight':
                parts = parts[:-1]
            p[parts[-1]] = v
    return p
