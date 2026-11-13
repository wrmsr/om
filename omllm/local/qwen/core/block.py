# ruff: noqa: N803 N806 N812
import typing as ta

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from .mixing import CompositeStateLayout
from .mixing import Connection
from .mixing import FeedForward
from .mixing import LayerEmbedding
from .mixing import Mixer
from .mixing import StateLayout
from .mixing import StepContext


##


class Block:
    """
    One layer as a composition: read the mixer's input from the residual stream, mix, write the result back; the same
    for the feed-forward. Which mixer, which feed-forward and which connections to the stream is the architecture's
    choice (arch/); the block only routes. The pre-norms are the connections' (Flash-Next's gated residual is its own).
    """

    def __init__(
            self,
            *,
            index: int,
            mixer: Mixer,
            ffn: FeedForward,
            mixer_conn: Connection,
            ffn_conn: Connection,
            embedding: LayerEmbedding | None = None,
    ) -> None:
        super().__init__()

        self.index = index
        self.mixer = mixer
        self.ffn = ffn
        self.mixer_conn = mixer_conn
        self.ffn_conn = ffn_conn
        self.embedding = embedding

        self._state = (
            mixer.state
            if embedding is None else
            CompositeStateLayout([mixer.state, embedding.state])
        )

    @property
    def state(self) -> StateLayout:
        """The layer's decode state: the mixer's, then the layer embedding's."""

        return self._state

    def __call__(
            self,
            ops: Ops,
            r: Array,
            pos: int,
            state: ta.Any,
            ids: ta.Any = None,
    ) -> tuple[Array, ta.Any]:
        """The functional form; `ids` [B, T] are the token ids (host ints), which a layer embedding reads."""

        i = self.index

        emb_state: tuple[Array, ...] = ()
        if self.embedding is not None:
            n = self.mixer.state.arity(ops)
            mix_state = None if state is None else tuple(state[:n])
            add, emb_state = self.embedding(ops, r, ids, None if state is None else tuple(state[n:]))
            r = r + add
            state = mix_state

        h, carry = self.mixer_conn.read(ops, r)
        m, state = self.mixer(ops, h, pos, state)
        ops.tap(f'layers.{i}.mixer', m)
        r = self.mixer_conn.write(ops, r, m, carry)

        h, carry = self.ffn_conn.read(ops, r)
        r = self.ffn_conn.write(ops, r, self.ffn(ops, h), carry)
        ops.tap(f'layers.{i}.out', r)

        state = (*state, *emb_state)

        # a lazy backend evaluates here, so the graph is one layer's at a time: its scheduling cost and the memory of
        # its temporaries (a prefill expands quantized weights) stay bounded, and the state handed on is a buffer, not
        # a pending graph every later evaluation would walk again (nothing happens elsewhere: see Ops.materialize)
        ops.materialize(r, *state)

        return r, state

    def step(self, ops: Ops, r: Array, ctx: StepContext, state: ta.Any) -> tuple[Array, ta.Any]:
        """Static-shape step for T tokens (no taps: a captured step cannot leave the device)."""

        emb_state: tuple[Array, ...] = ()
        if self.embedding is not None:
            n = self.mixer.state.arity(ops)
            add, emb_state = self.embedding.step(ops, r, ctx, tuple(state[n:]))
            r = r + add
            state = tuple(state[:n])

        h, carry = self.mixer_conn.read(ops, r)
        m, state = self.mixer.step(ops, h, ctx, state)
        r = self.mixer_conn.write(ops, r, m, carry)

        h, carry = self.ffn_conn.read(ops, r)
        r = self.ffn_conn.write(ops, r, self.ffn(ops, h), carry)

        state = (*state, *emb_state)

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
