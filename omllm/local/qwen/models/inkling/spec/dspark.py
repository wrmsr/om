# ruff: noqa: N803 N806
import typing as ta
import weakref

from omcore import check
from omcore import lang

from ....core.slab import StepSlab
from ....decode.decoder import Decoder
from ....decode.drafts import DraftSource
from ....decode.generation import Generation
from ....decode.rounds import Drafts
from ....decode.rounds import Round
from ....decode.sampling import Sampler
from ....decode.state import Snapshot
from ....ops.base import Array
from ....spec.draws import DraftDraws
from ..core.dspark.drafter import DsparkDrafter
from ..core.dspark.layers import DsparkSpan


if ta.TYPE_CHECKING:
    import numpy as np

    from ....core.model import Qwen35
else:
    np = lang.proxy_import('numpy')


##


class DsparkDraftSource(DraftSource):
    """
    Inkling 2's block drafter (models/inkling/core/dspark/) as a draft source. It owns the drafter's memory -- for each
    of its layers a key and a value at every position the target has run on, made from the target's hidden output there
    (the states inside the stack that the model's readout hands out: core/readouts.py) -- in buffers of the target
    decoder's capacity, and its captured steps over them: the one that drafts a block, and for each row count of a
    target step the one that writes that step's positions.

    A round's drafts are made all at once and cost the same however they fare: the drafter's layers once over the
    block, then the head's walk over its drafts. What is left to decide is how many of them the target is handed.
    A row of the target's step costs whether it is kept or not -- each row runs its own experts, so a step's cost
    grows by `ROW_COST` of a one-token step a row -- and the head's own word on a draft, the probability it drew it
    with, says how likely the row is to be kept. So a round submits the count, of those it is allowed (`k`), that
    makes the most of the target's time: the expected tokens of the round, one and the chance of each draft's being
    reached, over the round's cost; and none at all when the head's first draft is a guess. The head is an optimist,
    as the MTP head is: of the drafts it gave 0.9 the target kept 0.6, of those it gave 0.99 and more, 0.95 -- so
    its word is read through `CALIBRATION` first.

    Every count is a verify step of its own for the target to capture, so a round first submits any allowed count
    whose step has not been built, the longest first, whatever the head says of its drafts -- which puts those
    captures in a warm-up's first rounds (as the MTP source does with its lengths).

    A sampled generation's drafts are drawn from the head's distribution at the sampler's temperature and nothing
    else of the sampler: its truncations are the target's to apply (a draft outside the target's nucleus is
    rejected like any other the target would not have drawn), and warping seven rows of the vocabulary a round to
    match them cost more than the rows it saved -- 0.95 of the plain speed on a story, sampled, where greedy
    drafting is 1.19. The logit processors' contribution is not applied to drafts either: the head's walk is one
    captured run with nothing from the host in it, and the target's rows get theirs regardless, so a draft a
    grammar forbids is simply not kept.

    Needs the static `Decoder` (its steps run over the target's capacity).
    """

    # What the rule takes a round to cost, in plain rounds: 1 + DRAFT_COST + ROW_COST * the drafts submitted. As
    # measured on Inkling 2 Mini (5090, bf16, 2026-11-23) a drafted round is 1.67 plain rounds with one draft
    # submitted and 0.19 more for each further one, to 2.8 with seven: a plain round being 7.7 ms, a block's
    # drafts 2.5, a row of the target's step 1.6 to 1.7, and the rest the round's commit, reads and launches.
    # Scored on recorded rounds with measured costs, these constants and measured ones choose equally well (1.53
    # tokens per plain round's time over seven kinds of text, when a plain round was 9 ms) -- and resting the
    # drafter for a stretch after rounds that lost, which brings a story to par from 0.95, costs more than that
    # elsewhere.
    DRAFT_COST: ta.ClassVar[float] = .3
    ROW_COST: ta.ClassVar[float] = .18

    # The chance the target keeps a draft the head drew with probability p, if it gets that far: sigmoid(a logit(p)
    # + b), (a, b) fitted to 6,137 drafts of the released checkpoint's greedy decoding of seven kinds of text --
    # reasoning, a tutorial, a module, chat, a code review, a story, JSON (2026-11-23). By the cost above, on those
    # 1,944 rounds: 1.60 tokens per round's cost as the rule takes it taking p at its word, 1.69 with this, 1.93
    # knowing the outcome, 1.29 always submitting all seven. (The drafter is rarely right about what comes next in
    # a story: 0.8 of seven kept.)
    CALIBRATION: ta.ClassVar[tuple[float, float]] = (.57, -.79)

    START_ROWS: ta.ClassVar[int] = 4096  # the prompt's positions are remembered so many at a time

    MIN_BUCKET: ta.ClassVar[int] = 1024

    def __init__(
            self,
            *,
            model: Qwen35,
            sampler: Sampler,
            k: int | ta.Sequence[int] = 0,
            row_cost: float | None = None,
    ) -> None:
        super().__init__()

        if not isinstance(model.mtp, DsparkDrafter):
            raise ValueError('no DSpark drafter loaded')  # noqa: TRY004
        drafter = model.mtp
        most = drafter.cfg.drafts
        # a number: any count up to it (0: up to a block's); several: those counts
        lengths = tuple(range(1, (k or most) + 1)) if isinstance(k, int) else tuple(sorted(set(k)))
        if not lengths or not all(1 <= n <= most for n in lengths):
            raise ValueError(f'draft tokens must be 1..{most}, got {k}')

        self._model = model
        self._ops = model.ops
        self._drafter = drafter
        self._sampler = sampler
        self._lengths = lengths  # the draft counts a round may hand the target
        self._row_cost = self.ROW_COST if row_cost is None else row_cost
        self._draws = DraftDraws(self._ops, sampler)

        self._cap = 0  # the capacity the memory is padded to (follows the target decoder's)
        self._mem: list[Array] = []  # each layer's KV state, flat
        self._last: Array | None = None  # [1, 1, F]: the target's hidden output at the last committed position
        # the captured steps: ('draft', sampler shape, bucket) and ('write', rows)
        self._fns: dict[tuple, ta.Callable[..., tuple[Array, ...]]] = {}
        self._leaves: StepSlab | None = None  # the buffers and captured steps, for the next generation's source

        self.rounds = 0  # rounds drafted
        self.submitted = 0  # drafts handed to the target over them

    @staticmethod
    def _decoder(gen: Generation) -> Decoder:
        dec = gen.require_decoder()
        if not isinstance(dec, Decoder):
            raise TypeError('the DSpark draft source needs the static Decoder')
        return dec

    def _layers(self) -> list[tuple[Array, ...]]:
        a = self._ops.kv_arity
        return [tuple(self._mem[i:i + a]) for i in range(0, len(self._mem), a)]

    def _sync_capacity(self, dec: Decoder) -> None:
        """Pad the memory to the target's capacity (its steps are captured again) whenever the latter grew."""

        cap = dec.capacity
        if cap == self._cap:
            return
        layers = [self._ops.kv_pad(st, cap) for st in self._layers()]
        self._mem = [a for st in layers for a in st]
        self._cap = cap
        self._fns = {}
        if self._leaves is not None:
            self._leaves.capacity, self._leaves.layers, self._leaves.fns = cap, list(layers), self._fns

    # DraftSource

    @property
    def max_drafts(self) -> int:
        return self._lengths[-1]

    def accepts(self, resume: Snapshot) -> bool:
        # the memory of positions 0..n-2 must come from the snapshot: their hidden output is gone
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
        d = self._drafter
        arity = ops.kv_arity
        cap = self._decoder(gen).capacity
        R = int(hidden.shape[1])

        # each layer's keys and values at the prompt's positions
        chunks: list[list[tuple[Array, Array]]] = [[] for _ in d.layers]
        for a in range(0, R, self.START_ROWS):
            b = min(a + self.START_ROWS, R)
            cos, sin = d.rope_rows(start + a, b - a)
            for i, kv in enumerate(d.remember(d.taps(hidden[:, a:b]), cos, sin)):
                chunks[i].append(kv)

        # ... in buffers of the target's capacity: the last generation's, when it left them, and then its captured
        # steps run as they are (core/slab.py, as for the target's decoder)
        slab = d.take_slab(cap) if ops.kv_in_place else None
        layers: list[tuple[Array, ...]] = []
        try:
            for i, kvs in enumerate(chunks):
                k = kvs[0][0] if len(kvs) == 1 else ops.concat([kv[0] for kv in kvs], 2)
                v = kvs[0][1] if len(kvs) == 1 else ops.concat([kv[1] for kv in kvs], 2)
                st = ops.kv_new(k, v)
                if state is not None:
                    st = ops.kv_join(ops.kv_adapt(tuple(state[i * arity:(i + 1) * arity]), d.dtype), st)
                layers.append(ops.kv_pad(ops.kv_reserve(st, cap, slab.layers[i] if slab is not None else None), cap))
        except BaseException:
            if slab is not None:
                d.put_slab(slab)
            raise

        self._mem = [a for st in layers for a in st]
        self._cap = cap
        self._fns = {}
        if ops.kv_in_place:
            if slab is not None and slab.holds(layers):
                self._fns = slab.fns
            self._leaves = StepSlab(cap, list(layers), self._fns)
            weakref.finalize(self, d.put_slab, self._leaves).atexit = False

        # (a copy: a view would hold every prompt position's hidden output until the first commit)
        self._last = ops.copy(hidden[:, -1:])

    def _bucket(self, n: int) -> int:
        """The memory positions scored by a layer that sees all of them, for a block ending below n: a power of two."""

        b = self.MIN_BUCKET
        while b < n:
            b *= 2
        return min(b, self._cap)

    @staticmethod
    def _spans(
            d: DsparkDrafter,
            pos: Array,
            ar: Array,
            mem: ta.Sequence[Array],
            bucket: int,
    ) -> list[DsparkSpan]:
        """
        Each layer's past for a block at `pos`, from its buffers `mem` (of ar's length): the positions before `pos`
        within the first `bucket`, or its last window.
        """

        ops = d.ops
        arity = ops.kv_arity
        i32 = ops.dtype('i32')
        cap = int(ar.shape[0])

        spans: list[DsparkSpan] = []
        for i, layer in enumerate(d.layers):
            st = tuple(mem[i * arity:(i + 1) * arity])

            if layer.window is None:
                k, v = ops.kv_dense(ops.kv_window(st, bucket), d.dtype)
                spans.append(DsparkSpan(k, v, pos * 0, pos, ar[:bucket]))
                continue

            # the window's positions, gathered: pos - W .. pos - 1, of which those below 0 are not there (their
            # slots hold position 0 and are not seen)
            W = min(layer.window, cap)
            at = ops.reshape(pos, (1,)) - W + ar[:W]
            k, v = ops.kv_gather(st, at * ops.cast(at >= 0, i32), d.dtype)
            short = W - pos
            spans.append(DsparkSpan(k[None], v[None], short * ops.cast(short > 0, i32), pos * 0 + W, ar[:W]))

        return spans

    # (The functions below are kept with the source's buffers, which outlive it for the next generation's: they hold
    # the drafter and the sampler and nothing of the source itself, or it would never be collected.)

    def _draft_fn(self, bucket: int) -> ta.Callable[..., tuple[Array, ...]]:
        """
        A block's drafts as a function of arrays: `fn(tok, last, pos, noise, temperature, top_p, log_min_p, ar, cos,
        sin, *mem) -> (tokens [n], q [n, V], q_d [n], p [n])` -- `tok` [1] the pending token at position `pos`, `last`
        the target's hidden output at the position before, `noise` the uniform rows the draws use and the sampler's
        settings as arrays (of which the temperature is used); out come the drafts, the rows of q they were drawn
        from and their probability under them (greedy: neither -- q is one-hot at the draft, and the caller says so
        itself), and `p`, each draft's probability under the head's distribution at temperature 1.
        """

        ops = self._ops
        d = self._drafter
        sampler = self._sampler
        greedy = sampler.greedy
        i32 = ops.dtype('i32')
        f32 = ops.dtype('f32')
        B = d.cfg.block
        spans = self._spans

        def fn(tok, last, pos, noise, temperature, top_p, log_min_p, ar, cos_tab, sin_tab, *mem):
            rows = ops.reshape(pos, (1,)) + ar[:B]
            y = d.block(ops.reshape(tok, (1, 1)), cos_tab[rows], sin_tab[rows], spans(d, pos, ar, mem, bucket))

            head = d.head
            r_in = head.inputs(ops, y, head.view(ops, d.taps(last)))
            base = d.base_logits(y)

            toks = []
            qs = []
            qds = []
            ps = []
            s = ops.zeros((1, head.rank), f32)
            prev = tok
            for j in range(B - 1):
                s, row = head.step(ops, s, prev, r_in[j:j + 1], base[j:j + 1])

                if greedy:
                    t = ops.cast(sampler.sample(row), i32)  # [1]
                else:
                    q = ops.softmax(row / temperature, -1)
                    t = ops.cast(sampler.draw(q, noise[j:j + 1]), i32)
                    qs.append(q)
                    qds.append(Sampler.gather(ops, q, t))
                # (its probability alone, not the row's softmax: that was a tenth of the block's time)
                e = ops.exp(row - ops.amax(row, -1, keepdims=True))
                ps.append(Sampler.gather(ops, e, t) / ops.sum(e, -1))
                toks.append(t)
                prev = t

            none = ops.zeros((1,), f32)
            return (
                ops.concat(toks, 0),
                ops.concat(qs, 0) if qs else none,
                ops.concat(qds, 0) if qds else none,
                ops.concat(ps, 0),
            )

        return fn

    def _write_fn(self) -> ta.Callable[..., tuple[Array, ...]]:
        """
        A target step's positions into the memory: `fn(hidden, pos, ar, cos, sin, *mem) -> mem` -- `hidden` [1, T, F]
        the target's hidden output at positions pos .. pos + T - 1.
        """

        ops = self._ops
        d = self._drafter
        arity = ops.kv_arity

        def fn(hidden, pos, ar, cos_tab, sin_tab, *mem):
            rows = ops.reshape(pos, (1,)) + ar[:hidden.shape[1]]
            out: list[Array] = []
            for i, (k, v) in enumerate(d.remember(d.taps(hidden), cos_tab[rows], sin_tab[rows])):
                out.extend(ops.kv_write_tokens(tuple(mem[i * arity:(i + 1) * arity]), pos, k, v))
            return tuple(out)

        return fn

    def _fn(
            self,
            key: tuple,
            make: ta.Callable[[], ta.Callable[..., tuple[Array, ...]]],
    ) -> ta.Callable[..., tuple[Array, ...]]:
        if key not in self._fns:
            self._fns[key] = self._ops.capture(make())
        return self._fns[key]

    def _count(self, p: np.ndarray) -> int:
        """
        How many of a block's drafts to hand the target, given the probabilities the head drew them with: the
        allowed count -- or none -- with the most expected tokens for the target step's cost (see the class
        docstring).
        """

        a, b = self.CALIBRATION
        p = np.clip(p.astype(np.float64), 1e-6, 1 - 1e-6)
        kept = 1. / (1. + np.exp(-(a * np.log(p / (1. - p)) + b)))
        reach = np.cumprod(kept)  # the chance each draft is reached and kept
        base = 1. + self.DRAFT_COST  # (the block is paid for already, whatever is done with its drafts)
        best, best_rate = 0, 1. / base
        for n in self._lengths:
            rate = (1. + float(reach[:n].sum())) / (base + self._row_cost * n)
            if rate > best_rate:
                best, best_rate = n, rate
        return best

    def propose(self, gen: Generation) -> Drafts | None:
        ops = self._ops
        d = self._drafter
        dec = self._decoder(gen)
        self._sync_capacity(dec)

        n = dec.seq_len
        V = self._model.cfg.vocab_size
        f32 = ops.dtype('f32')
        i32 = ops.dtype('i32')
        greedy = self._sampler.greedy
        bucket = self._bucket(n + d.cfg.block)

        fn = self._fn(('draft', greedy, bucket), lambda: self._draft_fn(bucket))
        toks, q, q_d, p = fn(
            ops.cast(check.not_none(gen.pending_arr), i32),
            check.not_none(self._last),
            ops.scalar(n),
            self._draws.noise(d.cfg.drafts, V),
            *self._draws.settings(),
            *d.tables(self._cap),
            *self._mem,
        )

        unbuilt = [c for c in reversed(self._lengths) if not dec.has_step(c + 1)]
        k = unbuilt[0] if unbuilt else self._count(ops.numpy(p))
        self.rounds += 1
        self.submitted += k
        if not k:
            return None

        # (copies: a captured run's outputs are buffers its next call overwrites)
        tokens = ops.copy(toks[:k])
        if greedy:
            # one-hot at the draft, as `Sampler.probs` has it for a greedy row
            return Drafts(
                tokens=tokens,
                q=ops.cast(ops.arange(V)[None, :] == tokens[:, None], f32),
                q_d=ops.zeros((k,), f32) + 1,
            )
        return Drafts(
            tokens=tokens,
            q=ops.copy(q[:k]),
            q_d=ops.copy(q_d[:k]),
        )

    def on_commit(self, gen: Generation, rnd: Round, n: int) -> None:
        """
        Remember the round's positions: every row of the target's step is written -- the rows past the n kept are
        junk the next step's write covers before a block sees that far -- and the last kept row's hidden output is
        what the head views from the next block.
        """

        ops = self._ops
        dec = self._decoder(gen)
        self._sync_capacity(dec)  # (the round's drafts may not be this source's: no draft of its own since a growth)

        hidden = rnd.verified.hidden
        T = int(hidden.shape[1])
        n0 = dec.seq_len - n  # the round's first position

        mem = self._fn(('write', T), self._write_fn)(
            hidden,
            ops.scalar(n0),
            *self._drafter.tables(self._cap),
            *self._mem,
        )
        self._mem = list(mem)

        if n:
            # (a dense copy, not a slice of the step's output: the draft step is captured over it)
            self._last = ops.copy(hidden[:, n - 1:n])

    def export(self, gen: Generation) -> tuple[Array, ...] | None:
        return self.export_at(gen, gen.require_decoder().seq_len)

    def export_at(self, gen: Generation, n: int) -> tuple[Array, ...] | None:
        # the memory of positions 0..n-2: position n-1's is made again from the snapshot's hidden output
        if n <= 1:
            return None
        return tuple(a for st in self._layers() for a in self._ops.kv_slice(st, n - 1))
