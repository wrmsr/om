# ruff: noqa: N803 N806
"""
Logit processors: what adjusts the target's next-token distributions before the Sampler's warping -- grammar masks,
presence / frequency penalties, biases.

A processor's contribution is a mask (allowed ids) and/or an additive bias, and contributions combine by AND and +.
That makes them commutative: the processors of a generation are an unordered set (a multibinding, when assembled by
the injector), and no ordering between them is needed or expressible. Anything whose effect depends on order --
temperature, top-k, top-p, min-p -- is the Sampler's fixed pipeline, not a processor.

`rows` is pure (it may be asked twice for the same position: a draft source asks for the next row as an acceptance
heuristic, the token source then for every verify row); `after` advances on the tokens that condition later rows.
"""
import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..ops.base import Array
from ..ops.base import Ops
from .generation import Generation


##


@dc.dataclass(frozen=True)
class Contribution:
    """[R, V] rows: mask is 1 for allowed ids and 0 for the rest, bias is added to the logits. Either may be None."""

    mask: Array | None = None
    bias: Array | None = None

    @property
    def empty(self) -> bool:
        return self.mask is None and self.bias is None

    def combine(self, ops: Ops, other: Contribution) -> Contribution:
        return Contribution(
            mask=self.mask if other.mask is None else other.mask if self.mask is None else self.mask * other.mask,
            bias=self.bias if other.bias is None else other.bias if self.bias is None else self.bias + other.bias,
        )

    def apply(self, logits: Array) -> Array:
        """
        logits [R, W] with W <= V: a draft head restricted to a vocabulary prefix sees the first W columns, which is
        exactly its tokens' contribution.
        """

        W = logits.shape[-1]
        if self.bias is not None:
            logits = logits + self.bias[:, :W]
        if self.mask is not None:
            logits = logits + (1 - self.mask[:, :W]) * -1e30
        return logits


class LogitProcessor(lang.Abstract):
    @abc.abstractmethod
    def rows(self, gen: Generation, drafts: Array | None, n_rows: int) -> Contribution:
        """
        The contribution for the next `n_rows` positions: row 0 is the position after the pending token, row i the one
        after the pending token and drafts[:i]. `drafts` is the [n_rows - 1] int32 device array (None for one row); a
        processor that needs it on the host reads it itself, so that host sync exists only when such a processor is
        present.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def after(self, gen: Generation, tokens: ta.Sequence[int], arr: Array) -> None:
        """Advance over tokens that will be emitted (host ids and the same as an int32 device array)."""

        raise NotImplementedError


class NullLogitProcessor(LogitProcessor):
    """Contributes nothing: what a per-request processor slot holds when the request does not need it."""

    def rows(self, gen: Generation, drafts: Array | None, n_rows: int) -> Contribution:
        return Contribution()

    def after(self, gen: Generation, tokens: ta.Sequence[int], arr: Array) -> None:
        pass


class CompositeLogitProcessor(LogitProcessor):
    def __init__(self, ops: Ops, processors: ta.Iterable[LogitProcessor] = ()) -> None:
        super().__init__()

        self._ops = ops
        self._processors = list(processors)

    def rows(self, gen: Generation, drafts: Array | None, n_rows: int) -> Contribution:
        out = Contribution()
        for p in self._processors:
            out = out.combine(self._ops, p.rows(gen, drafts, n_rows))
        return out

    def after(self, gen: Generation, tokens: ta.Sequence[int], arr: Array) -> None:
        for p in self._processors:
            p.after(gen, tokens, arr)


class PenaltyProcessor(LogitProcessor):
    """
    Presence and frequency penalties over the generated tokens: the bias is -(presence * [count > 0] + frequency *
    count), from a device histogram. Exact under speculation: verify row i counts the drafts before it too, so each row
    is the penalised distribution given its own prefix.
    """

    def __init__(
            self,
            ops: Ops,
            *,
            vocab_size: int,
            presence: float = 0.,
            frequency: float = 0.,
    ) -> None:
        super().__init__()

        self._ops = ops
        self._vocab_size = vocab_size
        self._presence = presence
        self._frequency = frequency

        self._counts: Array | None = None  # [V] float32, allocated on first use

    def _get_counts(self) -> Array:
        if self._counts is None:
            self._counts = self._ops.zeros((self._vocab_size,), self._ops.dtype('f32'))
        return self._counts

    def rows(self, gen: Generation, drafts: Array | None, n_rows: int) -> Contribution:
        ops = self._ops
        f32 = ops.dtype('f32')
        counts = self._get_counts()[None, :]  # [1, V]

        if n_rows > 1:
            drafts = ta.cast(Array, drafts)
            oh = ops.cast(ops.arange(self._vocab_size)[None, :] == drafts[:n_rows - 1, None], f32)  # [n-1, V]
            counts = ops.concat([counts, counts + ops.cumsum(oh, 0)], 0)  # row i: + the drafts before it

        bias = -(self._presence * ops.cast(counts > 0, f32) + self._frequency * counts)
        return Contribution(bias=bias)

    def after(self, gen: Generation, tokens: ta.Sequence[int], arr: Array) -> None:
        ops = self._ops
        counts = self._get_counts()
        self._counts = ops.index_add(counts, arr, ops.zeros(arr.shape, counts.dtype) + 1)
