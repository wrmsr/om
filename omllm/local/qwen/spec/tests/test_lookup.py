import typing as ta

import numpy as np

from omcore import check

from ...api import generate
from ...arch.loading import load_qwen35
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
from ...models.qwen.spec.mtp import MtpDraftSource
from ...ops.base import Array
from ...ops.base import Ops
from ...ops.reference import NumpyOps
from ...tests.test_parity import backends
from ...tests.test_parity import synthetic_source
from ..lookup import LookupDraftSource


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


def test_draft_lengths():
    """
    The head with several draft lengths: a round drafts to the shortest and on to each next one while the product of
    the head's probabilities for its drafts holds at the confidence asked for (read two drafts short of each length:
    `MtpDraftSource.LOOKAHEAD`); a length whose step has not been built yet is drafted to at first whatever the
    confidence (so every step shape is compiled in a warm-up); and whatever the lengths, the output is the plain
    decoder's. On CUDA too, where there is one: its captured steps are graphs whose outputs are buffers the next
    replay overwrites, which is what a probability read late would read.
    """

    from ...models.qwen.spec.mtp import MtpDraftSource

    cfg, hf, src = synthetic_source()
    prompt = np.random.default_rng(21).integers(0, 256, 9).tolist()
    lengths = (2, 5, 9)

    all_ops = list(backends())
    try:
        import torch

        from ...backends.torch import TorchOps

        if torch.cuda.is_available() and any(isinstance(o, TorchOps) for o in all_ops):
            all_ops.append(TorchOps('cuda'))
    except ImportError:
        pass

    surenesses: dict[str, tuple[ta.Sequence[int], list[list[float]]]] = {}
    for ops in all_ops:
        if getattr(ops, 'capture_mode', None) == 'auto' and ops.name.endswith('cpu'):
            ops.capture_mode = 'static'  # type: ignore
        model = load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True)
        ref = generate(model, prompt, max_new_tokens=40, capacity=128).tokens

        # per round: (the lengths it may stop at -- negated when it is to go to the last whatever the confidence --,
        # the sureness read at each, the drafts made)
        rounds: list[tuple[tuple[int, ...], list[float], int]] = []

        class Watching(MtpDraftSource):
            def _stops(self, dec: ta.Any, _rounds: list = rounds) -> tuple[tuple[int, ...], bool]:
                stops, forced = super()._stops(dec)
                _rounds.append((tuple(-k for k in stops) if forced else stops, [], 0))
                return stops, forced

            def _sureness(self, read: ta.Any, _rounds: list = rounds) -> float:
                s = super()._sureness(read)
                assert 0 <= s <= 1
                _rounds[-1][1].append(s)
                return s

            def propose(self, gen: Generation, _rounds: list = rounds) -> Drafts | None:
                drafts = check.not_none(super().propose(gen))
                _rounds[-1] = (*_rounds[-1][:2], drafts.n)
                return drafts

        def run(
                confidence: float | None,
                n: int = 40,
                k: ta.Any = lengths,
                _ops: Ops = ops,
                _model: ta.Any = model,
                _cls: ta.Any = Watching,
                _ref: ta.Sequence[int] = ref,
                _rounds: list = rounds,
        ) -> list:
            sampler = Sampler()
            sampler.bind(_ops)
            draft = _cls(
                model=_model,
                sampler=sampler,
                processor=CompositeLogitProcessor(_ops, []),
                k=k,
                confidence=confidence,
            )
            assert draft.max_drafts == (k if isinstance(k, int) else max(k))
            _rounds.clear()
            assert generate(_model, prompt, max_new_tokens=n, draft=draft, capacity=128).tokens == _ref[:n], _ops.name
            return list(_rounds)

        def check_policy(seen: list, confidence: float) -> None:
            for stops, sure, n in seen:
                if stops[0] < 0:  # a length drafted to, to build its step
                    assert n == -stops[-1] and not sure
                    continue
                want, p = stops[-1], 1.
                for stop, s in zip(stops, sure):
                    p *= s
                    if p < confidence:
                        want = stop
                        break
                assert n == want, (stops, sure, n, confidence)

        # the first rounds on this model go through every length, the longest first, whatever the confidence
        seen = run(1.)
        assert [stops for stops, _, _ in seen[:3]] == [(-2, -5, -9), (-2, -5), (-2,)], seen[:4]
        check_policy(seen, 1.)
        assert {n for _, _, n in seen[3:]} == {2}  # (a random head is never certain)

        # a second generation has nothing left to build: the head's confidence decides from its first round on
        seen = run(0.)
        assert all(stops == lengths for stops, _, _ in seen), seen[:2]
        assert {n for _, _, n in seen} == {9}
        first = sorted(sure[0] for _, sure, _ in seen)
        surenesses[ops.name] = (ref, [sure for _, sure, _ in seen])

        # in between, some rounds stop and some go on
        mid = first[len(first) // 2]
        seen = run(mid)
        check_policy(seen, mid)
        assert len({n for _, _, n in seen}) > 1, seen

        # one length is the fixed draft count it always was, and nothing comes to the host for it
        seen = run(None, n=12, k=4)
        assert seen == [((4,), [], 4)] * len(seen)

        assert generate(model, prompt, max_new_tokens=40, spec=lengths, spec_confidence=mid, capacity=128).tokens == ref
        for bad in (dict(k=0), dict(k=16), dict(k=(3, 20)), dict(k=()), dict(k=3, confidence=1.5)):
            try:
                Watching(model=model, sampler=Sampler(), processor=CompositeLogitProcessor(ops, []), **bad)
                raise AssertionError(f'accepted {bad!r}')
            except ValueError:
                pass

    # and the probabilities read are the same ones on every backend that decodes the same tokens
    (name0, (ref0, sure0)), *others = surenesses.items()
    for name, (ref_n, sure_n) in others:
        if list(ref_n) == list(ref0):
            assert np.allclose(np.asarray(sure_n), np.asarray(sure0), rtol=2e-2, atol=1e-12), (name0, name)


def test_draft_runs_equal_drafts_one_by_one():
    """
    The head's drafts come from runs (`MtpDraftSource._stage_fn`: draw, step, draw ... as one function, one captured
    call where the backend can). Against a source that draws them one at a time through the head's one-entry step, the
    way they were first written: the same tokens, rounds and acceptances for a seed, greedy and sampled, at one length
    and at several, over a draft vocabulary or all of it.
    """

    from ...models.qwen.spec.mtp import MtpDraftSource

    class OneByOne(MtpDraftSource):
        def propose(self, gen: Generation) -> Drafts | None:
            ops = self._ops
            dec = self._decoder(gen)
            self._sync_capacity(dec)

            stops, forced = self._stops(dec)
            n = dec.seq_len
            i32 = ops.dtype('i32')
            f32 = ops.dtype('f32')
            vocab = self._model.cfg.vocab_size

            ml = check.not_none(self._mlogits_last)
            hid = check.not_none(self._d_last)
            first = self._processor.rows(gen, None, 1)

            darr: list[Array] = []
            qrows: list[Array] = []
            qds: list[Array] = []
            ps: list[Array] = []
            sure = 1.
            stop = 0
            read = 0  # the drafts whose probabilities have been read

            j = 0
            while True:
                row = first.apply(ml) if j == 0 else ml
                q = self._sampler.probs(row)
                d = ops.cast(self._sampler.draw(q), i32)

                darr.append(d)
                qds.append(Sampler.gather(ops, q, d))
                # (now: the step's next run overwrites the row)
                ps.append(Sampler.gather(ops, ops.softmax(row, -1), d))
                if q.shape[1] < vocab:
                    q = ops.concat([q, ops.zeros((1, vocab - q.shape[1]), f32)], -1)
                qrows.append(q)

                j += 1
                if j == stops[stop]:
                    if stop == len(stops) - 1:
                        break
                    # this length is decided on the drafts up to LOOKAHEAD short of it (one at least), as far as they
                    # have not been read for the length before
                    upto = max(stops[stop - 1] if stop else 0, min(j, max(1, j - self.LOOKAHEAD)))
                    if upto > read and not forced:
                        sure *= float(np.prod(ops.numpy(ops.concat(ps[read:upto], 0)), dtype=np.float64))
                        read = upto
                    if not forced and sure < self._confidence:
                        break
                    stop += 1

                ml, hid, *mkv = self._mfn(dec, 1, n + j - 1)(
                    ops.reshape(d, (1, 1)),
                    hid,
                    ops.scalar(n + j - 1),
                    *dec.tables(),
                    *self._mflat,
                )
                self._mflat = list(mkv)
                ml = ml[:, -1]

            return Drafts(tokens=ops.concat(darr, 0), q=ops.concat(qrows, 0), q_d=ops.concat(qds, 0))

    cfg, hf, src = synthetic_source()

    all_ops = list(backends())
    try:
        import torch

        from ...backends.torch import TorchOps

        if torch.cuda.is_available() and any(isinstance(o, TorchOps) for o in all_ops):
            all_ops.append(TorchOps('cuda'))
    except ImportError:
        pass

    samplings: list[dict] = [
        dict(),
        dict(temperature=1.),
        dict(temperature=.7, top_k=20, top_p=.8),
    ]
    for ops in all_ops:
        if getattr(ops, 'capture_mode', None) == 'auto' and ops.name.endswith('cpu'):
            ops.capture_mode = 'static'  # type: ignore
        # a model each, so that each head has the same steps left to build when a case begins
        models = [load_qwen35(src, ops, dtype='f32', verbose=False, mtp=True) for _ in range(2)]
        compared = 0
        for seed, sampling in enumerate(samplings):
            prompt = np.random.default_rng(30 + seed).integers(0, cfg.vocab_size, 9).tolist()
            for k, confidence, draft_vocab, penalty in (
                    (3, None, 0, 0.),
                    (6, None, 128, 1.5),
                    ((2, 5, 9), 9.5e-3, 0, 0.),  # (a random head's probability of a draft: some rounds go on)
                    ((2, 4), 0., 128, 0.),
            ):
                got = []
                for model, cls in zip(models, (MtpDraftSource, OneByOne)):
                    sampler = Sampler(seed=seed, **sampling)
                    sampler.bind(ops)
                    res = generate(
                        model,
                        prompt,
                        max_new_tokens=32,
                        sampler=sampler,
                        presence_penalty=penalty,
                        draft=cls(
                            model=model,
                            sampler=sampler,
                            processor=CompositeLogitProcessor(ops, []),
                            k=k,
                            draft_vocab=draft_vocab,
                            confidence=confidence,
                        ),
                        capacity=128,
                    )
                    got.append((list(res.tokens), res.rounds, res.drafted, res.accepted))
                assert got[0] == got[1], (ops.name, sampling, k, draft_vocab, got)
                compared += 1
        assert compared == 12
