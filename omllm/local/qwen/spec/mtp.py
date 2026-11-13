# ruff: noqa: N803 N806 N812
import typing as ta

from omcore import check
from omcore import lang

from ..core.cache import FullState
from ..core.mtp import MtpHead
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

    Needs the static `Decoder` (its steps run over the target's capacity, position tables and buckets).
    """

    def __init__(
            self,
            *,
            model: Qwen35,
            sampler: Sampler,
            processor: LogitProcessor,
            k: int,
            draft_vocab: int = 0,
    ) -> None:
        super().__init__()

        if model.mtp is None:
            raise ValueError('no MTP head loaded')
        if not 1 <= k <= 8:
            raise ValueError(f'draft tokens must be 1..8, got {k}')
        if draft_vocab < 0 or draft_vocab > model.cfg.vocab_size:
            raise ValueError(f'draft_vocab must be 0..{model.cfg.vocab_size}')

        self._model = model
        self._ops = model.ops
        self._mtp: MtpHead = model.mtp
        self._sampler = sampler
        self._processor = processor
        self._k = k
        self._draft_vocab = draft_vocab

        self._mcap = 0  # the capacity the head's KV is padded to (follows the target decoder's)
        self._mfns: dict[tuple[int, int], ta.Callable[..., tuple[Array, ...]]] = {}
        self._mflat: list[Array] = []
        self._mlogits_last: Array | None = None  # [1, V or draft_vocab]: the head's logits from its last entry
        self._d_last: Array | None = None  # [1, 1, H]: the head's normed output at its last entry

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

    def _mfn(self, dec: Decoder, T: int, n_last: int) -> ta.Callable[..., tuple[Array, ...]]:
        """The head's captured T-entry step for a round whose last entry is at position n_last - 1."""

        key = (T, dec.bucket(n_last))
        if key not in self._mfns:
            self._mfns[key] = self._ops.capture(self._mtp.step_fn(T, self._draft_vocab, key[1]))
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
            mlogits, d, mkv = self._mtp.prefill(
                toks,
                hidden,
                start,
                self._draft_vocab,
                state,
                last_only=True,
                reserve=self._decoder(gen).capacity,  # what `_sync_capacity` pads it to: filled in place instead
            )
            self._mflat = list(mkv)

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
        k drafts on the device: d_1 from the head's last refreshed entry, d_2..d_k by recursion at positions n, n+1, ...
        Nothing comes to the host.
        """

        ops = self._ops
        dec = self._decoder(gen)
        self._sync_capacity(dec)

        k = self._k
        n = dec.seq_len
        i32 = ops.dtype('i32')
        f32 = ops.dtype('f32')
        V = self._model.cfg.vocab_size

        darr: list[Array] = []
        qrows: list[Array] = []
        qds: list[Array] = []

        ml = check.not_none(self._mlogits_last)  # [1, V or draft_vocab]
        hid = self._d_last
        first = self._processor.rows(gen, None, 1)

        for j in range(k):
            q = self._sampler.probs(first.apply(ml) if j == 0 else ml)
            d = ops.cast(self._sampler.draw(q), i32)  # [1]

            darr.append(d)
            qds.append(Sampler.gather(ops, q, d))

            if q.shape[1] < V:  # drafting over a vocabulary prefix: zero mass elsewhere
                q = ops.concat([q, ops.zeros((1, V - q.shape[1]), f32)], -1)
            qrows.append(q)

            if j < k - 1:
                ml, hid, *mkv = self._mfn(dec, 1, n + j)(
                    ops.reshape(d, (1, 1)),
                    hid,
                    ops.scalar(n + j),
                    *dec.tables(),
                    *self._mflat,
                )
                self._mflat = list(mkv)
                ml = ml[:, -1]

        return Drafts(
            tokens=ops.concat(darr, 0),
            q=ops.concat(qrows, 0),
            q_d=ops.concat(qds, 0),
        )

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
