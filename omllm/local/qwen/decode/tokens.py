# ruff: noqa: N803 N806 N812
import abc
import typing as ta

from omcore import check
from omcore import lang

from ..core.cache import Cache
from ..ops.base import Array
from .decoder import Decoder
from .decoder import FunctionalDecoder
from .decoder import TargetDecoder
from .drafts import DraftSource
from .generation import Generation
from .processors import LogitProcessor
from .rounds import Round
from .sampling import Sampler
from .sampling import speculative_accept
from .state import Snapshot


if ta.TYPE_CHECKING:
    import numpy as np

    from ..core.model import Qwen35
else:
    np = lang.proxy_import('numpy')


##


class TokenSource(lang.Abstract):
    """
    Produces a generation's tokens round by round: `step` returns the tokens the target accepted, and nothing is
    committed until `commit` keeps a prefix of them -- the terminator decides how long, before the recurrent state
    moves.
    """

    @abc.abstractmethod
    def start(
            self,
            gen: Generation,
            *,
            resume: Snapshot | None,
            poll: ta.Callable[[], bool] | None = None,
    ) -> None:
        """Prefill the prompt (or the part of it past `resume`), and draw the first pending token."""

        raise NotImplementedError

    @abc.abstractmethod
    def step(self, gen: Generation) -> Round:
        raise NotImplementedError

    @abc.abstractmethod
    def commit(self, gen: Generation, rnd: Round, n: int) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def export(self, gen: Generation) -> Snapshot:
        """The resumable state at the committed position: exactly prompt + emitted tokens."""

        raise NotImplementedError


class VerifyTokenSource(TokenSource):
    """
    The one token source. A round: the draft source proposes up to k tokens after the pending one; the target verifies
    [pending, d_1..d_n] in one step; the logit processors contribute to every verify row given the drafts before it; the
    rejection step (speculative_accept) accepts a prefix of the drafts and draws the token after it. With no drafts --
    `NullDraftSource`, or a draft source with nothing to say this round -- that is plain decode: a one-token step and a
    `Sampler.sample` draw, no per-token states, no vocabulary-wide distributions. Either way a round reads the device
    once (the drafts, the accept flags and the corrections together), plus once more when a processor needs the drafts
    on the host.

    The output is exactly the target's (processed, warped) distribution whatever the drafts are -- the
    speculative-sampling theorem -- so draft sources only change the speed.
    """

    def __init__(
            self,
            *,
            model: Qwen35,
            sampler: Sampler,
            processor: LogitProcessor,
            draft: DraftSource,
            static: bool = True,
            prefill_chunk: int = 4096,
    ) -> None:
        super().__init__()

        self._model = model
        self._ops = model.ops
        self._sampler = sampler
        self._processor = processor
        self._draft = draft
        self._static = static
        self._prefill_chunk = prefill_chunk

        self._logits_last: Array | None = None  # [1, V]: the target's logits for the position after the committed ones
        self._hidden_last: Array | None = None  # [1, 1, H]: the target's hidden state at the last committed position

    # start

    def _prefill(
            self,
            gen: Generation,
            cache: Cache,
            ids: ta.Sequence[int],
            poll: ta.Callable[[], bool] | None,
    ) -> tuple[Array, Array, TargetDecoder | None]:
        """Logits [1, 1, V] after `ids` and the hidden states of their positions [1, len, H]."""

        ops = self._ops

        if self._static and ops.static_prefill:
            # a backend whose eager forward is costly prefills through the captured step (see Decoder.prefill)
            dec = Decoder(self._model, cache, capacity=gen.capacity, consume=True)
            logits, hidden = dec.prefill(ids, poll)
            return logits, hidden, dec

        logits, hidden = self._model.prefill(ids, cache, self._prefill_chunk, poll)
        return logits, hidden, None

    def start(
            self,
            gen: Generation,
            *,
            resume: Snapshot | None,
            poll: ta.Callable[[], bool] | None = None,
    ) -> None:
        ops = self._ops
        model = self._model
        n = len(gen.prompt)

        if resume is not None and not self._draft.accepts(resume):
            resume = None

        dec: TargetDecoder | None
        if resume is not None:
            # resume: the snapshot's cache is a private copy; prefill only the tokens past it
            cache = resume.cache
            n0 = resume.n
            gen.reused = n0

            if n0 < n:
                logits, hidden_new, dec = self._prefill(gen, cache, gen.prompt[n0:], poll)
                hidden = ops.concat([resume.hidden, hidden_new], 1)  # positions n0-1 .. n-1
            else:
                logits = ops.reshape(resume.logits, (1, 1, -1))
                hidden = resume.hidden  # position n-1
                dec = None

            start = n0 - 1  # the position of hidden's first row
            draft_state = resume.draft

        else:
            cache = Cache(model.cfg)
            logits, hidden, dec = self._prefill(gen, cache, gen.prompt, poll)
            start = 0
            draft_state = None

        if dec is None:
            if self._static:
                # the cache is ours to give away (a prefill's, or a store's private copy): the decoder takes its
                # state layer by layer, so the exact-length KV and the buffers are never both held whole
                dec = Decoder(model, cache, capacity=gen.capacity, consume=True)
            else:
                dec = FunctionalDecoder(model, cache)
        gen.decoder = dec

        # the prefill's cache now lives in the decoder (a static one has taken its state; a functional one holds the
        # object): no reference to it stays here through the draft source's own prefill, which is where a long
        # prompt's memory peaks
        del cache
        resume = None

        self._logits_last = logits[:, -1]
        self._hidden_last = hidden[:, -1:]

        self._set_pending(gen, self._sample(gen, logits[:, -1]))

        self._draft.start(
            gen,
            hidden=hidden,
            start=start,
            tokens=[*gen.prompt[start + 1:n], check.not_none(gen.pending)],
            state=draft_state,
        )

    def _sample(self, gen: Generation, row: Array) -> Array:
        """One token from a [1, V] logits row after the processors: [1] int32 on the device."""

        contribution = self._processor.rows(gen, None, 1)
        return self._sampler.sample(contribution.apply(row))

    def _set_pending(self, gen: Generation, arr: Array, tok: int | None = None) -> None:
        if tok is None:
            tok = int(self._ops.numpy(arr)[0])
        gen.pending = tok
        gen.pending_arr = arr
        self._processor.after(gen, [tok], arr)

    # rounds

    def step(self, gen: Generation) -> Round:
        ops = self._ops
        dec = gen.require_decoder()
        i32 = ops.dtype('i32')
        pending = check.not_none(gen.pending)
        pending_arr = check.not_none(gen.pending_arr)

        dec.ensure_capacity(dec.seq_len + self._draft.max_drafts + 2)

        drafts = self._draft.propose(gen)

        if drafts is None:
            # plain decode: one token through the step, one draw
            verified = dec.verify(ops.reshape(ops.cast(pending_arr, i32), (1, 1)), all_states=False)
            nxt = self._sample(gen, verified.logits[:, -1])
            return Round(
                tokens=(pending,),
                verified=verified,
                drafts=None,
                accepted=0,
                next_tok=int(ops.numpy(nxt)[0]),
                next_arr=nxt,
            )

        k = drafts.n
        toks = ops.reshape(ops.concat([ops.cast(pending_arr, i32), drafts.tokens], 0), (1, k + 1))
        verified = dec.verify(toks)

        # row i is the target's distribution for the position after the pending token and drafts[:i]
        contribution = self._processor.rows(gen, drafts.tokens, k + 1)
        p_rows = self._sampler.probs(contribution.apply(verified.logits[0]))
        accept, corr = speculative_accept(ops, self._sampler, p_rows, drafts.q, drafts.tokens, drafts.q_d)

        got = ops.numpy(ops.concat([drafts.tokens, accept, ops.cast(corr, i32)], 0)).tolist()
        draft_ids, flags, corrections = got[:k], got[k:2 * k], got[2 * k:]

        m = 0
        while m < k and flags[m]:
            m += 1

        return Round(
            tokens=(pending, *draft_ids[:m]),
            verified=verified,
            drafts=drafts,
            accepted=m,
            next_tok=corrections[m],
            next_arr=corr[m:m + 1],
        )

    def commit(self, gen: Generation, rnd: Round, n: int) -> None:
        ops = self._ops
        dec = gen.require_decoder()

        dec.commit(rnd.verified, n)

        if n > 0:
            self._logits_last = rnd.verified.logits[:, n - 1]
            self._hidden_last = rnd.verified.hidden[:, n - 1:n]

        if n == len(rnd.tokens):
            # all kept: the processors advance over the kept drafts, then the new pending token
            if rnd.accepted:
                drafts = check.not_none(rnd.drafts)
                kept = ops.cast(drafts.tokens[:rnd.accepted], ops.dtype('i32'))
                self._processor.after(gen, rnd.tokens[1:], kept)
            self._set_pending(gen, rnd.next_arr, rnd.next_tok)

        else:
            gen.pending = None  # cut: the generation stops here
            gen.pending_arr = None

        self._draft.on_commit(gen, rnd, n)

    def export(self, gen: Generation) -> Snapshot:
        ops = self._ops
        dec = gen.require_decoder()
        ids = gen.ids
        if dec.seq_len != len(ids):
            raise RuntimeError(f'decoder at {dec.seq_len}, committed ids {len(ids)}')

        return Snapshot(
            tuple(ids),
            dec.export_cache(),
            ops.copy(check.not_none(self._logits_last)),
            ops.copy(check.not_none(self._hidden_last)),
            self._draft.export(gen),
        )
