import typing as ta

import numpy as np

from ...api import generate
from ...arch.qwen35 import load_qwen35
from ...decode.drafts import DraftSource
from ...decode.drafts import NullDraftSource
from ...decode.drafts import point_drafts
from ...decode.generation import Generation
from ...decode.observers import Observer
from ...decode.processors import CompositeLogitProcessor
from ...decode.rounds import Drafts
from ...decode.rounds import Round
from ...decode.rounds import Verified
from ...decode.sampling import Sampler
from ...decode.state import Snapshot
from ...ops.base import Array
from ...ops.base import Ops
from ...ops.reference import NumpyOps
from ...tests.test_parity import backends
from ...tests.test_parity import synthetic_source
from ..lookup import LookupDraftSource
from ..mtp import MtpDraftSource


##


def _round(tokens: tuple[int, ...]) -> Round:
    """A round as the token source commits it: [pending, accepted drafts...] (nothing here reads the rest)."""

    return Round(
        tokens=tokens,
        verified=Verified(logits=None, hidden=None, states=None, stacked=False),
        drafts=None,
        accepted=len(tokens) - 1,
        next_tok=0,
        next_arr=None,
    )


class _Lookup:
    def __init__(self, prompt: list[int], k: int = 3) -> None:
        super().__init__()

        self.ops = NumpyOps()
        self.k = k
        self.src = LookupDraftSource(self.ops, vocab_size=32, wrapped=NullDraftSource(), ngram=2, k=k)
        self.gen = Generation(prompt=prompt, capacity=64)
        self.src.start(self.gen, hidden=None, start=0, tokens=(), state=None)

    def propose(self, pending: int) -> list[int] | None:
        self.gen.pending = pending
        d = self.src.propose(self.gen)
        if d is None:
            return None
        toks = np.asarray(self.ops.numpy(d.tokens)).tolist()
        q = np.asarray(self.ops.numpy(d.q))
        assert q.shape == (self.k, 32)
        assert (q.sum(1) == 1).all() and (q[np.arange(self.k), toks] == 1).all()  # point masses at the drafts
        return toks


def test_lookup_index():
    """The continuation after the latest earlier occurrence of the tail, padded to k; no match: the wrapped source's."""

    lk = _Lookup([5, 1, 2, 3, 4, 1, 2, 7, 8, 9, 6])
    assert lk.src.max_drafts == 3

    assert lk.propose(0) is None  # (6, 0) never occurred: Null below says no drafts

    # commit the pending 1; then (1, 2) occurred twice: the latest occurrence wins (7, 8, 9, not 3, 4, 1)
    lk.src.on_commit(lk.gen, _round((1,)), 1)
    assert lk.propose(2) == [7, 8, 9]

    # commit pending 2 with drafts 7, 8 accepted; (8, 9) now continues as in the prompt
    lk.src.on_commit(lk.gen, _round((2, 7, 8)), 3)
    assert lk.propose(9) == [6, 1, 2]

    # a cut round commits only its first n tokens
    lk.src.on_commit(lk.gen, _round((9, 6, 1)), 1)
    assert lk.src._ids[-2:] == [8, 9]  # noqa

    assert lk.src.hits == 2

    # a continuation that runs off the end of the context is padded with its last token
    assert _Lookup([1, 2, 3, 1]).propose(2) == [3, 1, 1]

    # a match ending at the last committed token has no continuation yet
    assert _Lookup([4, 4]).propose(4) is None


def test_lookup_parity():
    """
    Lookup drafting reproduces plain greedy decoding token for token, on its own (plain rounds when nothing matches)
    and on top of the MTP head (whose refresh then runs over drafts it did not propose), with lookups hitting and
    accepted along the way: a random model's greedy output falls into a cycle, which lookup then predicts.
    """

    cfg, _, src = synthetic_source()
    prompt = [10, 11, 12, 13, 14] * 3
    n_new = 40
    k = 3

    def lookup_over(ops: Ops, wrapped: DraftSource) -> LookupDraftSource:
        return LookupDraftSource(ops, vocab_size=cfg.vocab_size, wrapped=wrapped, ngram=2, k=k)

    for ops in backends():
        if getattr(ops, 'capture_mode', None) == 'auto' and ops.name.endswith('cpu'):
            ops.capture_mode = 'static'  # type: ignore
        model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)
        ref = generate(model, prompt, max_new_tokens=n_new, static=True).tokens

        alone = lookup_over(ops, NullDraftSource())
        res = generate(model, prompt, max_new_tokens=n_new, draft=alone)
        assert res.tokens == ref, (ops.name, res.tokens, ref)
        assert alone.hits, ops.name  # (all rejected: this model never repeats itself; test_mtp_under_foreign_drafts)

        sampler = Sampler()
        sampler.bind(ops)
        mtp = MtpDraftSource(model=model, sampler=sampler, processor=CompositeLogitProcessor(ops, []), k=k)
        over = lookup_over(ops, mtp)
        res = generate(model, prompt, max_new_tokens=n_new, draft=over)
        assert res.tokens == ref, (ops.name, 'over mtp', res.tokens, ref)
        assert over.hits < res.rounds, (ops.name, over.hits, res.rounds)  # the head drafted some rounds too

        # longer lookup drafts than the head's: two verify shapes, and the head refreshes over k + 1 = 6 positions
        mtp = MtpDraftSource(model=model, sampler=sampler, processor=CompositeLogitProcessor(ops, []), k=k)
        longer = LookupDraftSource(ops, vocab_size=cfg.vocab_size, wrapped=mtp, ngram=2, k=5)
        assert longer.max_drafts == 5
        res = generate(model, prompt, max_new_tokens=n_new, draft=longer)
        assert res.tokens == ref, (ops.name, 'k=5 over the head', res.tokens, ref)
        assert longer.hits, ops.name

        # and through api.generate's own wiring
        assert generate(model, prompt, max_new_tokens=n_new, spec=k, lookup_ngram=2).tokens == ref
        print(f'{ops.name}: lookup == greedy ({alone.hits} lookup rounds alone, {over.hits} over the head)')


class _Alternate(DraftSource):
    """
    Every other round the true continuation (accepted unless the generation ends first), else the wrapped source's.
    """

    def __init__(self, ops: Ops, vocab_size: int, full: list[int], wrapped: DraftSource) -> None:
        super().__init__()

        self._ops = ops
        self._vocab_size = vocab_size
        self._full = full
        self._wrapped = wrapped
        self.expected: list[int | None] = []  # per round: the acceptance a foreign round must get, None for the head's

    @property
    def max_drafts(self) -> int:
        return self._wrapped.max_drafts

    def accepts(self, resume: Snapshot) -> bool:
        return self._wrapped.accepts(resume)

    def start(
            self,
            gen: Generation,
            *,
            hidden: Array,
            start: int,
            tokens: ta.Sequence[int],
            state: tuple[Array, ...] | None,
    ) -> None:
        self._wrapped.start(
            gen,
            hidden=hidden,
            start=start,
            tokens=tokens,
            state=state,
        )

    def propose(self, gen: Generation) -> Drafts | None:
        if len(self.expected) % 2:
            self.expected.append(None)
            return self._wrapped.propose(gen)

        k = self.max_drafts
        p = len(gen.ids)  # the pending token's position
        d = self._full[p + 1:p + 1 + k]
        self.expected.append(min(k, len(d)))
        return point_drafts(self._ops, self._vocab_size, d + [0] * (k - len(d)))

    def on_commit(self, gen: Generation, rnd: Round, n: int) -> None:
        self._wrapped.on_commit(gen, rnd, n)

    def export(self, gen: Generation) -> tuple[Array, ...] | None:
        return self._wrapped.export(gen)


def test_mtp_under_foreign_drafts():
    """
    The MTP head below another source refreshes over rounds whose drafts it did not propose, accepted ones included
    (a lookup source over the head does exactly that whenever the context repeats); its own rounds after them still
    reproduce plain greedy decoding, and so do restricted-vocabulary drafts.
    """

    class Accepted(Observer):
        def __init__(self) -> None:
            super().__init__()

            self.accepted: list[int] = []

        def on_prefill(self, gen):
            pass

        def on_round(self, gen, rnd, kept):
            self.accepted.append(rnd.accepted)

    cfg, _, src = synthetic_source()
    prompt = np.random.default_rng(6).integers(0, 256, 6).tolist()
    n_new = 30
    k = 3

    for ops in backends():
        if getattr(ops, 'capture_mode', None) == 'auto' and ops.name.endswith('cpu'):
            ops.capture_mode = 'static'  # type: ignore
        model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)
        ref = generate(model, prompt, max_new_tokens=n_new, static=True).tokens

        for draft_vocab in (0, 64):
            sampler = Sampler()
            sampler.bind(ops)
            mtp = MtpDraftSource(
                model=model,
                sampler=sampler,
                processor=CompositeLogitProcessor(ops, []),
                k=k,
                draft_vocab=draft_vocab,
            )
            alt = _Alternate(ops, cfg.vocab_size, prompt + ref, mtp)
            obs = Accepted()
            res = generate(model, prompt, max_new_tokens=n_new, draft=alt, observers=[obs])

            assert res.tokens == ref, (ops.name, draft_vocab, res.tokens, ref)
            foreign = [(a, e) for a, e in zip(obs.accepted, alt.expected) if e is not None]
            assert all(a == e for a, e in foreign), (ops.name, draft_vocab, foreign)
            assert sum(a for a, _ in foreign) >= 3 * k, (ops.name, foreign)
