# ruff: noqa: N803 N806 N812
import typing as ta
import weakref

from omcore import check
from omcore import lang

from ..core.cache import FullState
from ..core.mtp import MtpHead
from ..core.slab import StepSlab
from ..decode.decoder import Decoder
from ..decode.drafts import DraftSource
from ..decode.generation import Generation
from ..decode.processors import LogitProcessor
from ..decode.rounds import Drafts
from ..decode.rounds import Round
from ..decode.sampling import Sampler
from ..decode.state import Snapshot
from ..ops.base import Array


if ta.TYPE_CHECKING:
    import numpy as np

    from ..core.model import Qwen35
else:
    np = lang.proxy_import('numpy')


##


class MtpDraftSource(DraftSource):
    """
    Qwen3.5's multi-token-prediction head as a draft source. It owns the head's KV (an entry per position p: the
    target's hidden at p and the token at p+1), its captured steps, and the restriction of its output head to a
    vocabulary prefix (`draft_vocab`). Drafts are *sampled* from the head's warped distribution q -- the first one after
    the logit processors' contribution for the next position (an acceptance heuristic: the target's rows get theirs
    regardless) -- and the head recurses on its own normed output for the rest. After every commit the head's entries
    for the verified positions are refreshed with the target's true hidden states, so the next round drafts from them.

    A run of drafts is one function (`_stage_fn`): draw, step the head on the draw, draw again. Where the backend can
    capture that (`Ops.capture_sampling`) a run is one launch; the head's step and the sampler's two dozen small
    operations a draft, launched one by one, kept the host busier than the GPU -- 0.35 ms a draft greedy and 0.63
    sampled on the 27B, against 0.2 for the step itself.

    How many drafts a round. How far the head stays right depends on the text: on the 27B the target keeps ~3 of
    fifteen drafts in prose, ~6 in new code, ~11 in a file being rewritten -- and a draft costs a head step and a row of
    the verify step whether it is kept or not. So `k` may be several lengths (e.g. 5, 9, 15), and a round then drafts
    to the shortest, and on to each next one only while the head itself still believes its drafts: while the product of
    the probabilities it gave them (unwarped: under greedy decoding the warped ones are all 1) is at least
    `confidence`. That is the one thing a round with several lengths brings to the host, once per length it reaches
    but the last -- and it is read `LOOKAHEAD` drafts short of the length, over the drafts before those, so that the
    device is never left waiting on the host's answer. (The head is an optimist: when it puts 0.85 on seven drafts
    together, the target keeps all seven a little over half the time. What the last round kept, which costs no
    read, predicts the next about as well on six kinds of text; the head's own word is the one that knows a copied
    run from its first token.)

    Every length is a verify step and a head refresh of its own to compile, so a round first drafts to any length whose
    step the head has not built yet, the longest first, whatever its confidence -- which puts those compilations in a
    warm-up's first rounds, not in the first request confident enough to reach them.

    Needs the static `Decoder` (its steps run over the target's capacity, position tables and buckets).
    """

    MAX_K: ta.ClassVar[int] = 15  # (a verify step of 16 rows: the GEMV's one pass over each weight)

    # The drafts queued behind a confidence read: what the GPU works on while the host reads, decides, and -- if the
    # round stops at the length in question -- launches the target's verify step (~0.6 ms of host time on the 27B; a
    # draft is ~0.4 of GPU time). Read at the length itself, every round that stopped there idled the GPU that long.
    LOOKAHEAD: ta.ClassVar[int] = 2

    DEFAULT_CONFIDENCE: ta.ClassVar[float] = .9

    def __init__(
            self,
            *,
            model: Qwen35,
            sampler: Sampler,
            processor: LogitProcessor,
            k: int | ta.Sequence[int],
            draft_vocab: int = 0,
            confidence: float | None = None,
    ) -> None:
        super().__init__()

        if model.mtp is None:
            raise ValueError('no MTP head loaded')
        lengths = (k,) if isinstance(k, int) else tuple(sorted(set(k)))
        if not lengths or not all(1 <= n <= self.MAX_K for n in lengths):
            raise ValueError(f'draft tokens must be 1..{self.MAX_K}, got {k}')
        k = lengths[-1]
        if draft_vocab < 0 or draft_vocab > model.cfg.vocab_size:
            raise ValueError(f'draft_vocab must be 0..{model.cfg.vocab_size}')
        if confidence is None:
            confidence = self.DEFAULT_CONFIDENCE
        if not 0 <= confidence <= 1:
            raise ValueError(f'confidence must be 0..1, got {confidence}')

        self._model = model
        self._ops = model.ops
        self._mtp: MtpHead = model.mtp
        self._sampler = sampler
        self._processor = processor
        self._k = k  # the most drafts a round
        self._lengths = lengths  # the lengths a round may draft to (one: always that many)
        self._confidence = confidence
        self._draft_vocab = draft_vocab

        self._mcap = 0  # the capacity the head's KV is padded to (follows the target decoder's)
        # the head's captured steps: (T, draft vocabulary, bucket) -> a T-entry step; ('draft', ...) -> a run of
        # drafts (`_stage`)
        self._mfns: dict[tuple, ta.Callable[..., tuple[Array, ...]]] = {}
        self._mflat: list[Array] = []
        self._mlogits_last: Array | None = None  # [1, V or draft_vocab]: the head's logits from its last entry
        self._d_last: Array | None = None  # [1, 1, H]: the head's normed output at its last entry
        self._leaves: StepSlab | None = None  # the head's buffers and captured steps, for the next generation's
        self._no_noise: Array | None = None  # what a greedy run is handed for its noise
        self._settings_arrays: tuple[Array, ...] | None = None

    @staticmethod
    def _decoder(gen: Generation) -> Decoder:
        dec = gen.require_decoder()
        if not isinstance(dec, Decoder):
            raise TypeError('the MTP draft source needs the static Decoder')
        return dec

    def _sync_capacity(self, dec: Decoder) -> None:
        """Pad the head's KV to the target's capacity (re-capturing its steps) whenever the latter grew."""

        cap = dec.capacity
        if cap == self._mcap:
            return
        self._mflat = list(self._ops.kv_pad(tuple(self._mflat), cap))
        self._mcap = cap
        self._mfns = {}
        if self._leaves is not None:
            self._leaves.capacity, self._leaves.layers, self._leaves.fns = cap, [tuple(self._mflat)], self._mfns

    def _mfn(self, dec: Decoder, T: int, n_last: int) -> ta.Callable[..., tuple[Array, ...]]:
        """The head's captured T-entry step for a round whose last entry is at position n_last - 1."""

        # (the draft vocabulary too: these are kept for the next generation's source, which may be given another)
        key = (T, self._draft_vocab, dec.bucket(n_last))
        if key not in self._mfns:
            self._mfns[key] = self._ops.capture(self._mtp.step_fn(T, self._draft_vocab, key[2]))
        return self._mfns[key]

    # DraftSource

    @property
    def max_drafts(self) -> int:
        return self._k

    def accepts(self, resume: Snapshot) -> bool:
        # entries 0..n-2 must come from the snapshot: there is no hidden state for them anymore
        return resume.draft is not None or resume.n <= 1

    def start(
            self,
            gen: Generation,
            *,
            hidden: Array,
            start: int,
            tokens: ta.Sequence[int],
            state: tuple[Array, ...] | None,
    ) -> None:
        ops = self._ops
        toks = np.asarray([list(tokens)], dtype=np.int32)

        if ops.static_prefill:
            mlogits, d = self._prefill_static(gen, toks, hidden, start, state)
        else:
            # The head's KV goes straight into buffers of the target's capacity (what `_sync_capacity` would pad it
            # to) -- the last generation's, when it left them, and then its captured steps run as they are too
            # (core/slab.py, as for the target's decoder).
            cap = self._decoder(gen).capacity
            slab = self._mtp.take_slab(cap) if ops.kv_in_place else None
            try:
                mlogits, d, mkv = self._mtp.prefill(
                    toks,
                    hidden,
                    start,
                    self._draft_vocab,
                    state,
                    last_only=True,
                    reserve=cap,
                    reserve_into=slab.layers[0] if slab is not None else None,
                )
            except BaseException:
                if slab is not None:
                    self._mtp.put_slab(slab)
                raise
            self._mflat = list(mkv)

            if ops.kv_in_place:
                if slab is not None and slab.holds([tuple(self._mflat)]):
                    self._mfns = slab.fns
                    self._mcap = cap
                self._leaves = StepSlab(cap, [tuple(self._mflat)], self._mfns)
                weakref.finalize(self, self._mtp.put_slab, self._leaves).atexit = False

        self._mlogits_last = mlogits[:, -1]
        self._d_last = ops.copy(d[:, -1:])  # dense: see on_commit

    def _prefill_static(
            self,
            gen: Generation,
            mtoks: np.ndarray,
            hidden: Array,
            start: int,
            state: FullState | None,
    ) -> tuple[Array, Array]:
        """
        The prefill through the head's captured step, `Decoder.PREFILL_T` entries at a time, the last chunk padded with
        its last entry (as Decoder.prefill does; the pad entries are rewritten before anything attends to them): for a
        backend whose eager path is costly (`Ops.static_prefill`). Returns the last chunk's logits and d, the last real
        entry at index -1.
        """

        ops = self._ops
        c = self._model.cfg
        dec = self._decoder(gen)
        T = Decoder.PREFILL_T

        if state is None:
            z = ops.zeros((1, c.num_kv_heads, 0, c.head_dim), self._model.dtype)
            state = ops.kv_new(z, z)
        self._mflat = list(state)
        self._mcap = 0

        total = int(mtoks.shape[1])
        last: tuple[Array, Array] | None = None
        for i in range(0, total, T):
            n = min(T, total - i)
            pos = start + i

            dec.ensure_capacity(pos + T)
            self._sync_capacity(dec)

            tk = mtoks[:, i:i + n]
            hd = hidden[:, i:i + n]
            if n < T:
                tk = np.concatenate([tk, np.repeat(tk[:, -1:], T - n, 1)], 1)
                hd = ops.concat([hd, ops.repeat(hd[:, -1:], T - n, 1)], 1)

            ml, d, *mkv = self._mfn(dec, T, pos + T)(ops.array(tk), hd, ops.scalar(pos), *dec.tables(), *self._mflat)
            self._mflat = list(mkv)
            last = (ml[:, :n], d[:, :n])

        return check.not_none(last)

    def propose(self, gen: Generation) -> Drafts | None:
        """
        The round's drafts on the device: d_1 from the head's last refreshed entry, the rest by recursion at positions
        n, n+1, ..., in runs (`_stage`). With one length that is one run and nothing comes to the host. With several,
        the head's confidence does, once for each length the round reaches but the last (see the class docstring) --
        read `LOOKAHEAD` drafts before that length, with those drafts already queued behind the read.
        """

        ops = self._ops
        dec = self._decoder(gen)
        self._sync_capacity(dec)

        stops, forced = self._stops(dec)
        final = self._lengths[-1]
        n = dec.seq_len
        f32 = ops.dtype('f32')
        V = self._model.cfg.vocab_size
        greedy = self._sampler.greedy

        # the logits for the next position, the processors' contribution applied. A copy: the step that made them
        # will overwrite them, and a captured run keeps its first call's arguments as its input buffers
        lead = ops.copy(self._processor.rows(gen, None, 1).apply(check.not_none(self._mlogits_last)))
        hid = check.not_none(self._d_last)
        width = int(lead.shape[-1])  # of the head's logits: the vocabulary it drafts over

        toks: list[Array] = []
        qs: list[Array] = []
        qds: list[Array] = []

        def run(a: int, b: int, sure: bool) -> Array:
            """Drafts a+1..b; their probabilities under the head's unwarped distribution, if asked for."""

            nonlocal lead, hid
            fn = self._stage(
                dec,
                a,
                b,
                sure,
                width,
                n + b,
            )

            t, q, qd, p, lead, hid, *mkv = fn(
                lead,
                hid,
                ops.scalar(n + max(a - 1, 0)),  # (the run's first step is on draft a, at the position before its own)
                self._noise(b - a, width),
                *self._settings(),
                *dec.tables(),
                *self._mflat,
            )

            self._mflat = list(mkv)
            toks.append(t)
            qs.append(q)
            qds.append(qd)
            return p

        unread: list[Array] = []  # the probabilities of the drafts no read has covered yet
        sure = 1.
        a = 0
        for i, b in enumerate(stops):
            if b == final:
                run(a, b, False)
                break

            # the drafts this length is decided on: all but its last LOOKAHEAD (but one at least)
            d = max(a, min(b, max(1, b - self.LOOKAHEAD)))
            if d > a:
                unread.append(run(a, d, True))
            read = None
            if unread and not forced:
                read = ops.numpy_later(unread[0] if len(unread) == 1 else ops.concat(unread, 0))
                unread = []
            if b > d:
                # behind the read: what the GPU has to do while the host decides -- and, if this is where the round
                # stops, launches the target's verify step, half a millisecond of host time on the 27B
                unread.append(run(d, b, True))

            if i == len(stops) - 1:
                break
            if read is not None:
                sure *= self._sureness(read)
            if not forced and sure < self._confidence:
                break
            a = b

        # (concatenated or copied: a captured run's outputs are buffers its next call overwrites)
        tokens = ops.concat(toks, 0) if len(toks) > 1 else ops.copy(toks[0])
        k = int(tokens.shape[0])
        if greedy:
            # one-hot at the draft, as `Sampler.probs` has it for a greedy row
            q_rows = ops.cast(ops.arange(V)[None, :] == tokens[:, None], f32)
            q_d = ops.zeros((k,), f32) + 1
        else:
            q_rows = ops.concat(qs, 0) if len(qs) > 1 else ops.copy(qs[0])
            if q_rows.shape[1] < V:  # drafting over a vocabulary prefix: zero mass elsewhere
                q_rows = ops.concat([q_rows, ops.zeros((k, V - q_rows.shape[1]), f32)], -1)
            q_d = ops.concat(qds, 0) if len(qds) > 1 else ops.copy(qds[0])

        return Drafts(
            tokens=tokens,
            q=q_rows,
            q_d=q_d,
        )

    def _settings(self) -> tuple[Array, ...]:
        """The sampler's settings as arrays: a captured run takes them as arguments, so one serves every setting."""

        if self._settings_arrays is None:
            ops = self._ops
            f32 = ops.dtype('f32')
            self._settings_arrays = tuple(ops.zeros((), f32) + v for v in self._sampler.settings())
        return self._settings_arrays

    def _noise(self, count: int, width: int) -> Array:
        """
        The uniform draws a run of `count` sampled drafts makes, a [1, width] row each as `Sampler.draw` would take
        them one at a time (so a seed's stream is what it was when drafts were drawn one by one). Greedy takes none.
        """

        ops = self._ops
        if self._sampler.greedy:
            if self._no_noise is None:
                self._no_noise = ops.zeros((1, 1), ops.dtype('f32'))
            return self._no_noise
        rows = [ops.random_uniform((1, width)) for _ in range(count)]
        return rows[0] if count == 1 else ops.concat(rows, 0)

    def _stage_fn(
            self,
            step: ta.Callable[..., tuple[Array, ...]],
            a: int,
            b: int,
            sure: bool,
    ) -> ta.Callable[..., tuple[Array, ...]]:
        """
        Drafts a+1..b as a function of arrays: `fn(lead, hid, pos, noise, temperature, top_p, log_min_p, ar, cos_tab,
        sin_tab, *kv) -> (tokens [b-a], q [b-a, W], q_d [b-a], p [b-a], lead, hid, *kv)`.

        From a = 0, `lead` is the logits [1, W] the first draft is drawn from, and each later one comes from the
        head's step on the draft before it; from a > 0, `lead` is draft a ([1, 1], the run before's) and the run
        starts with the step on it. `hid` is the head's normed output going into the first step, `pos` that step's
        position, `noise` the uniform rows the draws use, and the sampler's settings come in as arrays
        (`Sampler.warp`): the function is this sampler's only in its `shape`. Out come the drafts, the rows of q they
        were drawn from and their probability under them (greedy: neither -- q is one-hot at the draft, and the
        caller says so itself), with `sure` their probability under the head's unwarped distribution (what the
        confidence is made of), and `lead` / `hid` / the head's KV as the next run takes them.
        """

        ops = self._ops
        sampler = self._sampler
        greedy = sampler.greedy
        i32 = ops.dtype('i32')
        f32 = ops.dtype('f32')

        def fn(lead, hid, pos, noise, temperature, top_p, log_min_p, ar, cos_tab, sin_tab, *kv):
            toks = []
            qs = []
            qds = []
            ps = []
            row = lead if a == 0 else None
            tok = None if a == 0 else lead
            for i in range(b - a):
                if row is None:
                    ml, hid, *rest = step(
                        tok,
                        hid,
                        pos + (i if a else i - 1),
                        ar,
                        cos_tab,
                        sin_tab,
                        *kv,
                    )
                    kv = tuple(rest)
                    row = ml[:, -1]

                if greedy:
                    d = ops.cast(sampler.sample(row), i32)  # [1]
                else:
                    q = sampler.warp(row, temperature, top_p, log_min_p)
                    d = ops.cast(sampler.draw(q, noise[i:i + 1]), i32)
                    qs.append(q)
                    qds.append(Sampler.gather(ops, q, d))
                if sure:
                    ps.append(Sampler.gather(ops, ops.softmax(row, -1), d))
                toks.append(d)

                tok = ops.reshape(d, (1, 1))
                row = None

            none = ops.zeros((1,), f32)
            return (
                ops.concat(toks, 0),
                ops.concat(qs, 0) if qs else none,
                ops.concat(qds, 0) if qds else none,
                ops.concat(ps, 0) if ps else none,
                tok,
                hid,
                *kv,
            )

        return fn

    # Captured runs kept, at most. One is a pair of lengths and a sampler shape -- greedy, or what top-k / top-p /
    # min-p do to the operations; the settings' values are arguments -- so a server sees a handful. Each holds its
    # own device memory (a CUDA graph's pool: ~11 MiB a draft on the 27B), hence a bound at all.
    DRAFT_STAGES: ta.ClassVar[int] = 16

    def _stage(
            self,
            dec: Decoder,
            a: int,
            b: int,
            sure: bool,
            width: int,
            n_last: int,
    ) -> ta.Callable[..., tuple[Array, ...]]:
        """
        The run of drafts a+1..b for this generation's sampler, over logits `width` wide, its last step's entry at a
        position below `n_last`: captured as one call where the backend can (`Ops.capture_sampling`; kept with the
        head's steps, so the next generation whose sampler has this shape has it), else the same function run as it
        is over the head's captured step.
        """

        ops = self._ops
        bucket = dec.bucket(n_last)
        if not ops.capture_sampling:
            return self._stage_fn(self._mfn(dec, 1, n_last), a, b, sure)

        key = ('draft', a, b, sure, self._sampler.shape(width), self._draft_vocab, bucket)
        fn = self._mfns.pop(key, None)
        if fn is None:
            stages = [k for k in self._mfns if k[0] == 'draft']
            if len(stages) >= self.DRAFT_STAGES:
                del self._mfns[stages[0]]  # (the one unused longest: the dict keeps them in order of last use)
            step = self._mtp.step_fn(1, self._draft_vocab, bucket)
            fn = ops.capture(self._stage_fn(step, a, b, sure))
        self._mfns[key] = fn
        return fn

    def _stops(self, dec: Decoder) -> tuple[tuple[int, ...], bool]:
        """
        The draft counts this round may stop at, and whether it is to go to the last of them whatever the head's
        confidence: the configured lengths -- or those up to one whose head refresh step (and with it the target's
        verify step: the same rows) has yet to be built, the longest such first.
        """

        lengths = self._lengths
        if len(lengths) > 1:
            n = dec.seq_len
            for i in reversed(range(len(lengths))):
                k = lengths[i]
                if not self._mtp.has_step(k + 1, self._draft_vocab, dec.bucket(n + k + 1)):
                    return lengths[:i + 1], True
        return lengths, False

    def _sureness(self, read: ta.Callable[[], np.ndarray]) -> float:
        """The product of the probabilities a read brings: what the head makes of the drafts it covers."""

        return float(np.prod(read(), dtype=np.float64))

    def on_commit(self, gen: Generation, rnd: Round, n: int) -> None:
        """
        Refresh the head over the round's positions with the target's true hidden states. Entry j (hidden at n0+j,
        token at n0+j+1) for j < m is a kept draft; entry m pairs the hidden after the last accepted token with the new
        pending token -- the one the next round drafts from. Entries past m are junk the next refresh overwrites before
        anything attends to them, and so are those past a terminator's cut (the generation stops; `export` keeps only
        what is committed).
        """

        drafts = rnd.drafts
        if drafts is None:
            raise RuntimeError('the MTP draft source proposes every round')

        ops = self._ops
        dec = self._decoder(gen)
        self._sync_capacity(dec)  # the round's drafts may not be the head's: it may not have drafted since a growth
        i32 = ops.dtype('i32')
        k = drafts.n
        m = rnd.accepted
        n0 = dec.seq_len - n  # the round's first position

        rtoks = ops.reshape(
            ops.concat([drafts.tokens[:m], ops.cast(rnd.next_arr, i32), drafts.tokens[m:]], 0)[:k + 1],
            (1, k + 1),
        )
        ml, d, *mkv = self._mfn(dec, k + 1, n0 + k + 1)(
            rtoks,
            rnd.verified.hidden,
            ops.scalar(n0),
            *dec.tables(),
            *self._mflat,
        )

        self._mflat = list(mkv)
        self._mlogits_last = ml[:, m]
        # a dense copy, not a slice: it is the next draft step's input, and a captured step is guarded on its inputs'
        # strides when captured -- on its first use in a generation. A slice of this [1, k + 1, H] output has strides
        # that depend on the round's draft count, so a generation whose head first drafted after a longer lookup round
        # (a follow-up turn, where lookup matches at once) recompiled the draft step mid-request.
        self._d_last = ops.copy(d[:, m:m + 1])

    def export(self, gen: Generation) -> tuple[Array, ...] | None:
        n = gen.require_decoder().seq_len
        return self._ops.kv_slice(tuple(self._mflat), n - 1) if n > 1 else None

    def export_at(self, gen: Generation, n: int) -> tuple[Array, ...] | None:
        # entry j pairs the hidden state at j with the token at j + 1: entries 0..n-2 lie within the first n tokens
        return self._ops.kv_slice(tuple(self._mflat), n - 1) if n > 1 else None
