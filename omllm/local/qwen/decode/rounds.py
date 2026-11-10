import typing as ta

from omcore import dataclasses as dc

from ..ops.base import Array


##


@dc.dataclass(frozen=True)
class Verified:
    """
    What one target step over T tokens returned: logits [1, T, V] float32, the final-normed hidden states [1, T, H],
    and the decoder's state after the step -- `stacked` when it holds the state after every token, so a commit can keep
    any prefix. Only the decoder that produced it reads `states`.
    """

    logits: Array
    hidden: Array
    states: ta.Any
    stacked: bool


@dc.dataclass(frozen=True)
class Drafts:
    """
    n proposed tokens and the distributions they were drawn from, on the device: tokens [n] int32, q [n, V] float32
    (rows of zeros past a restricted draft vocabulary; one-hot for a draft that is certain), q_d [n] = q[i, tokens[i]].
    """

    tokens: Array
    q: Array
    q_d: Array

    @property
    def n(self) -> int:
        return int(self.tokens.shape[0])


@dc.dataclass(frozen=True)
class Round:
    """
    One round's accepted tokens, not yet committed: [pending, d_1..d_m] -- the pending token always, then the drafts the
    target accepted. `next_tok` / `next_arr` is what follows if all of them are kept (the correction at the first
    rejection, or the bonus draw after the last draft).
    """

    tokens: tuple[int, ...]
    verified: Verified
    drafts: Drafts | None
    accepted: int
    next_tok: int
    next_arr: Array
