# ruff: noqa: N803 N806 N812
import math

from ..ops.base import Array
from ..ops.base import Ops


##


class Sampler:
    """
    The warping of a logits row into a distribution, and draws from it, on the device: temperature -> top-k -> top-p ->
    min-p -> Gumbel-max, all as `Ops` calls on [T, V] float32 logits, so what leaves the device is T token ids.
    temperature <= 0 is greedy (the first maximum) and ignores the rest. Qwen's published presets: thinking t=1.0
    top-p=0.95 top-k=20; non-thinking t=0.7 top-p=0.8 top-k=20 (plus presence 1.5, a logit processor).

    What reaches the logits before the warping -- grammar masks, presence / frequency penalties, biases -- is the logit
    processors' business (decode/processors.py), applied by the token source; the warping is this fixed pipeline.

    `probs` (the whole warped distribution) and `draw` are the reference; `sample` is the optimised path (only the top-k
    candidates are materialised) and must draw from exactly `probs`' distribution -- tests/test_sampler.py pins the two
    together, degenerate cases (greedy, ties) included. top-p and min-p are applied among the top-k candidates (top-k
    must be > 0 for them; with top-k=0 they sort the whole vocabulary). `seed` seeds the backend's generator, so the
    stream differs between backends.
    """

    def __init__(
            self,
            temperature: float = 0.0,
            top_k: int = 0,
            top_p: float = 1.0,
            min_p: float = 0.0,
            seed: int = 0,
    ) -> None:
        super().__init__()

        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.min_p = min_p
        self.seed = seed
        self.ops: Ops | None = None

    @property
    def greedy(self) -> bool:
        return self.temperature <= 0

    def bind(self, ops: Ops) -> None:
        if self.ops is not ops:
            self.ops = ops
            ops.seed(self.seed)

    def _ops(self) -> Ops:
        if self.ops is None:
            raise RuntimeError('bind() first')
        return self.ops

    def sample(self, logits: Array) -> Array:
        """logits [T, V] float32 on the device -> [T] int32 token ids on the device."""

        ops = self._ops()

        T, V = logits.shape

        if self.greedy:
            return ops.argmax(logits, -1)

        k = self.top_k if 0 < self.top_k < V else V
        vals, idx = ops.topk(logits, k)  # [T, k] descending
        z = vals / self.temperature
        p = ops.softmax(z, -1)

        keep = ops.cast(ops.cumsum(p, -1) - p < self.top_p, z.dtype) if self.top_p < 1.0 else None

        if self.min_p > 0:
            km = ops.cast(p >= self.min_p * ops.amax(p, -1, keepdims=True), z.dtype)
            keep = km if keep is None else keep * km

        if keep is not None:
            z = z + (1 - keep) * -1e30

        # Gumbel-max: argmax(z + g), g = -log(-log(u)), is a draw from softmax(z)
        u = ops.random_uniform((T, k))
        g = -ops.log(-ops.log(u * (1 - 2e-7) + 1e-7))
        choice = ops.argmax(z + g, -1)  # [T] index into the k candidates

        oh = ops.cast(ops.arange(k)[None, :] == choice[:, None], ops.dtype('f32'))
        return ops.cast(ops.sum(ops.cast(idx, ops.dtype('f32')) * oh, -1) + 0.5, ops.dtype('i32'))

    def probs(self, logits: Array) -> Array:
        """
        The distribution `sample` draws from, materialised over the whole vocabulary: [T, V] float32 rows that sum to 1,
        zero outside the kept set. Every truncation (top-k, top-p, min-p) is a per-row threshold on the tempered logits,
        so this is a topk on the candidates to find the threshold, then one masked softmax. Greedy is a one-hot row at
        the first maximum. Speculative verify compares the target's and the draft head's versions of this.
        """

        ops = self._ops()

        T, V = logits.shape
        f32 = ops.dtype('f32')

        if self.greedy:
            # one-hot at the first maximum, the token `sample`'s argmax picks. Not spread over ties: bf16 logits tie
            # exactly every few dozen tokens on the 27B, and a draw among tied tokens would make greedy speculative
            # decoding depend on the seed and differ from plain greedy.
            am = ops.argmax(logits, -1)
            return ops.cast(ops.arange(V)[None, :] == am[:, None], f32)

        l = logits / self.temperature

        k = self.top_k if 0 < self.top_k < V else V
        vals, _ = ops.topk(l, k)  # [T, k] descending
        thr = vals[:, k - 1:k]  # the k-th largest: everything below it is out

        if self.top_p < 1.0:
            p = ops.softmax(vals, -1)
            keep = ops.cast(ops.cumsum(p, -1) - p < self.top_p, f32)
            thr_p = -ops.amax(-(vals + (1 - keep) * 1e30), -1, keepdims=True)  # smallest kept value
            thr = ops.amax(ops.stack([thr, thr_p], 0), 0)

        if self.min_p > 0:
            # p >= min_p * p_max <=> z >= z_max + ln min_p
            thr_m = ops.amax(vals, -1, keepdims=True) + math.log(self.min_p)
            thr = ops.amax(ops.stack([thr, thr_m], 0), 0)

        return ops.softmax(l + ops.cast(l < thr, f32) * -1e30, -1)

    def draw(self, probs: Array) -> Array:
        """One token per row of a [T, V] probability matrix (Gumbel-max over log p; zeros never win)."""

        ops = self._ops()

        T, V = probs.shape

        u = ops.random_uniform((T, V))
        g = -ops.log(-ops.log(u * (1 - 2e-7) + 1e-7))
        return ops.argmax(ops.log(probs) + g, -1)

    @staticmethod
    def gather(ops: Ops, probs: Array, toks: Array) -> Array:
        """probs[i, toks[i]] for each row -> [T]."""

        return ops.gather_rows(probs, toks)


def speculative_accept(
        ops: Ops,
        sampler: Sampler,
        p_rows: Array,
        q_rows: Array,
        drafts: Array,
        q_d: Array,
) -> tuple[Array, Array]:
    """
    The rejection-sampling step of speculative decoding (Leviathan et al. / Chen et al.). p_rows: [k+1, V], the target's
    warped distribution at each verified position; q_rows: [k, V], the draft head's at the k drafted positions; drafts:
    [k] tokens that were sampled from q_rows; q_d: [k] their draft probabilities. Draft i is accepted with probability
    min(1, p_i(d_i) / q_i(d_i)). Returns (accept flags [k] int32, corrections [k+1] int32): the token to emit at
    position i if draft i is the first rejected one -- a draw from the residual max(0, p_i - q_i) renormalised -- and,
    at index k, a plain draw from p_k for the case where every draft was accepted. The caller takes the first rejection
    on the host; everything here is one small batch of vocabulary-wide ops, so the round still has a single device->host
    sync. With every distribution one-hot (greedy) this reduces to "accept iff argmax matches", so greedy and sampled
    decoding share the path.
    """

    k = q_rows.shape[0]
    f32 = ops.dtype('f32')

    p_d = Sampler.gather(ops, p_rows[:k], drafts)
    ratio = p_d / (q_d + 1e-30)
    ratio = ratio * (1 - ops.cast(ratio > 1, f32)) + ops.cast(ratio > 1, f32)  # min(1, ratio)
    u = ops.random_uniform((k,))
    accept = ops.cast(u < ratio, ops.dtype('i32'))

    resid = p_rows[:k] - q_rows
    resid = resid * ops.cast(resid > 0, f32) + 1e-12 * p_rows[:k]  # max(0, p - q); the tiny term guards p == q
    resid = resid / ops.sum(resid, -1, keepdims=True)

    corrections = sampler.draw(ops.concat([resid, p_rows[k:k + 1]], 0))  # [k+1]

    return accept, corrections
