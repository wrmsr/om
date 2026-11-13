# ruff: noqa: N803 N806 N812
import typing as ta

from omcore import check
from omcore import lang

from ..ops.base import Array
from ..ops.base import Ops
from ..ops.base import Weight
from .block import Block
from .cache import FullState
from .config import Qwen35Config
from .mixing import ResidualStream
from .mixing import StepContext


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


##


class MtpHead:
    """
    Qwen3.5's multi-token-prediction head (the `nextn` block of the GGUF, `mtp.*` in HF): given the target's
    final-normed hidden state at position p and the token at p+1, it predicts the token at p+2 --

        e = rmsnorm(embed(x_{p+1}), pre_fc_norm_embedding)
        h = rmsnorm(h_p, pre_fc_norm_hidden)
        u = fc(concat(e, h))                       # embedding first, hidden second
        u = one gated-attention block (text geometry, private weights, private KV)
        d = rmsnorm(u, norm);  logits = lm_head(d)  # the target's output head

    and can recurse, feeding its own normed output `d` back in as the next hidden. All norm weights are stored with the
    +1 already applied, like the text model's. The block runs through `Block.step` on its own KV buffers (positions
    are the hidden's position). It shares the target's embedding and output head; its block and its residual stream
    (whose exit is the final `norm`) are built by the architecture like the target's.
    """

    def __init__(
            self,
            *,
            cfg: Qwen35Config,
            ops: Ops,
            dtype: ta.Any,
            embed: Weight,
            lm_head: Weight,
            fc: Weight,
            enorm: Weight,
            hnorm: Weight,
            residual: ResidualStream,
            block: Block,
    ) -> None:
        super().__init__()

        self.cfg = cfg
        self.ops = ops
        self.dtype = dtype
        self.embed = embed
        self.lm_head = lm_head
        self.fc = fc
        self.enorm = enorm
        self.hnorm = hnorm
        self.residual = residual
        self.block = block
        self._steps: dict[tuple[int, int, int], ta.Callable[..., tuple[Array, ...]]] = {}
        self._heads: dict[int, Weight] = {}

    def stem(self, ops: Ops, toks: Array, hidden: Array) -> Array:
        c = self.cfg
        e = ops.rms_norm(ops.embedding(toks, self.embed, self.dtype), self.enorm, c.rms_eps)
        h = ops.rms_norm(ops.cast(hidden, self.dtype), self.hnorm, c.rms_eps)
        return ops.linear(ops.concat([e, h], -1), self.fc)

    def head(self, ops: Ops, d: Array, draft_vocab: int = 0) -> Array:
        """
        The output head over the final-normed `d`. draft_vocab > 0 restricts it to the first that many vocabulary ids:
        Qwen's BPE ids are roughly in merge-frequency order, so the first 32-64k cover almost every token the target
        will pick while costing a fraction of the 248k-row matmul (ninfer's `--lm-head-draft`).
        """

        head = self.lm_head
        if draft_vocab:
            key = draft_vocab
            head = self._heads.get(key)
            if head is None:
                head = self._heads[key] = ops.head_rows(self.lm_head, draft_vocab)
        return ops.f32(ops.linear(d, head))

    def prefill(
            self,
            toks: np.ndarray,
            hidden: Array,
            pos: int = 0,
            draft_vocab: int = 0,
            state: FullState | None = None,
            last_only: bool = False,
            chunk: int = 4096,
            reserve: int | None = None,
    ) -> tuple[Array, Array, FullState]:
        """
        Functional (growing-cache) pass over T entries: toks [B, T] are the tokens at positions pos+1..pos+T, hidden [B,
        T, H] the target's hidden states at pos..pos+T-1, `state` the head's KV for entries 0..pos-1 (None to start
        empty). Returns logits, d, (k, v) covering entries 0..pos+T-1. With last_only, logits and d are the last entry's
        only ([B, 1, ...]): the generation loop needs nothing else, and every entry's draft logits over a long prompt
        are gigabytes (32k entries x 64k ids in float32 is 8 GB). The entries go through the block `chunk` at a time, as
        Qwen35.prefill does, so its activations stay bounded too -- and, as there, into KV buffers of `reserve`
        positions from the second chunk on when one is given (the returned state then has room past the entries).
        """

        ops = self.ops
        toks = np.asarray(toks, dtype=np.int32)
        T = toks.shape[1]

        ds: list[Array] = []
        for s in range(0, T, max(1, chunk)):
            if reserve is not None and state is not None:
                state = self.block.state.reserve(ops, state, reserve)
            u = self.stem(ops, ops.array(toks[:, s:s + chunk]), hidden[:, s:s + chunk])
            r, state = self.block(ops, self.residual.enter(ops, u), pos + s, state)
            d = self.residual.exit(ops, r)
            if last_only:
                ds[:] = [ops.copy(d[:, -1:])]  # a copy: a view would keep the whole chunk's, every chunk
            else:
                ds.append(d)

        d = ds[0] if len(ds) == 1 else ops.concat(ds, 1)
        return self.head(ops, d, draft_vocab), d, check.not_none(state)

    def step_fn(self, T: int, draft_vocab: int = 0, bucket: int = 0) -> ta.Callable[..., tuple[Array, ...]]:
        """
        Static T-entry step: `fn(toks [B,T], hidden [B,T,H], pos, ar, cos_tab, sin_tab, kbuf, vbuf) -> (logits, d, kbuf,
        vbuf)`; built and compiled once per (T, draft_vocab), cached on the head. With draft_vocab the logits cover only
        the first that many ids (see `head`).
        """

        key = (T, draft_vocab, bucket)
        fn = self._steps.get(key)
        if fn is None:
            ops = self.ops

            def raw(
                    toks,
                    hidden,
                    pos,
                    ar,
                    cos_tab,
                    sin_tab,
                    *kv,
            ):
                rows = ops.reshape(pos, (1,)) + ar[:T]
                u = self.stem(ops, toks, hidden)
                ctx = StepContext(pos, ar, cos_tab[rows], sin_tab[rows], False, bucket, cos_tab, sin_tab, toks)
                r, kv = self.block.step(ops, self.residual.enter(ops, u), ctx, tuple(kv))
                d = self.residual.exit(ops, r)
                return (self.head(ops, d, draft_vocab), d, *kv)

            fn = self._steps[key] = ops.compile_fn(raw)

        return fn
