import abc
import typing as ta

from omcore import lang

from ..ops.base import Array
from ..ops.base import Ops
from .generation import Generation
from .rounds import Drafts
from .rounds import Round
from .state import Snapshot


if ta.TYPE_CHECKING:
    import numpy as np
else:
    np = lang.proxy_import('numpy')


##


class DraftSource(lang.Abstract):
    """
    Proposes tokens for the target to verify. The MTP head is one (spec/mtp.py); prompt lookup and grammar-forced runs
    would be others; `NullDraftSource` makes the token source plain decode. Sources combine by wrapping: a source that
    has nothing to say this round may ask the one it wraps.
    """

    @property
    @abc.abstractmethod
    def max_drafts(self) -> int:
        """The most drafts `propose` returns: what the token source reserves decode capacity for."""

        raise NotImplementedError

    @abc.abstractmethod
    def accepts(self, resume: Snapshot) -> bool:
        """Whether a stored state can be resumed from (its draft part may be missing something this source needs)."""

        raise NotImplementedError

    @abc.abstractmethod
    def start(
            self,
            gen: Generation,
            *,
            hidden: Array,
            start: int,
            tokens: ta.Sequence[int],
            state: tuple[Array, ...] | None,
    ) -> None:
        """
        Bring up over the prompt: `hidden` [1, R, H] is the target's final-normed hidden states at positions
        start..start+R-1 and `tokens` the token at each following position (the last one the pending token); `state` is
        this source's exported state from a resumed snapshot (covering what precedes `start`), or None.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def propose(self, gen: Generation) -> Drafts | None:
        """Up to `max_drafts` drafts following the pending token, or None for none this round."""

        raise NotImplementedError

    @abc.abstractmethod
    def on_commit(self, gen: Generation, rnd: Round, n: int) -> None:
        """After the target committed the first n tokens of a round: the round carries the verify step's outputs."""

        raise NotImplementedError

    @abc.abstractmethod
    def export(self, gen: Generation) -> tuple[Array, ...] | None:
        """This source's state for a stored snapshot of the committed position, or None if it has none."""

        raise NotImplementedError


class NullDraftSource(DraftSource):
    """No drafts: the token source decodes one token per round."""

    @property
    def max_drafts(self) -> int:
        return 0

    def accepts(self, resume: Snapshot) -> bool:
        return True

    def start(
            self,
            gen: Generation,
            *,
            hidden: Array,
            start: int,
            tokens: ta.Sequence[int],
            state: tuple[Array, ...] | None,
    ) -> None:
        pass

    def propose(self, gen: Generation) -> Drafts | None:
        return None

    def on_commit(self, gen: Generation, rnd: Round, n: int) -> None:
        pass

    def export(self, gen: Generation) -> tuple[Array, ...] | None:
        return None


def point_drafts(ops: Ops, vocab_size: int, tokens: ta.Sequence[int]) -> Drafts:
    """
    Drafts proposed with certainty (one-hot q): the rejection step then accepts each exactly as often as the target
    would have produced it, so any such proposal leaves the output distribution unchanged.
    """

    f32 = ops.dtype('f32')
    arr = ops.array(np.asarray(tokens, dtype=np.int32))
    return Drafts(
        tokens=arr,
        q=ops.cast(ops.arange(vocab_size)[None, :] == arr[:, None], f32),
        q_d=ops.zeros((len(tokens),), f32) + 1,
    )
