import typing as ta

from omcore import dataclasses as dc

from ..ops.base import Array


if ta.TYPE_CHECKING:
    from .decoder import TargetDecoder


##


class Generation:
    """
    The state one generation's collaborators share by reference -- the token source, its draft source, the logit
    processors, the terminator, the observers -- rather than by argument lists: the prompt, the tokens emitted so far,
    the target's decoder, and the pending token (sampled, certain to be emitted next, not yet fed to the model). It is
    the per-request state and nothing else; collaborators keep their own state themselves.
    """

    def __init__(
            self,
            *,
            prompt: ta.Sequence[int],
            capacity: int,
    ) -> None:
        super().__init__()

        self.prompt: tuple[int, ...] = tuple(int(t) for t in prompt)
        self.capacity = capacity

        self.tokens: list[int] = []  # emitted (committed) generated tokens
        self.decoder: TargetDecoder | None = None  # set by the token source when it starts
        self.reused = 0  # prompt tokens resumed from a stored state rather than prefilled

        self.pending: int | None = None
        self.pending_arr: Array | None = None  # [1] int32 on the device

    @property
    def ids(self) -> list[int]:
        """Every token the state has committed: prompt + emitted."""

        return [*self.prompt, *self.tokens]

    def require_decoder(self) -> TargetDecoder:
        if self.decoder is None:
            raise RuntimeError('the token source has not started')
        return self.decoder


@dc.dataclass(frozen=True)
class Generated:
    """What a generation produced, and what it cost: returned by the loop instead of side channels on the model."""

    tokens: ta.Sequence[int]
    prompt_tokens: int
    reused: int  # prompt tokens resumed from a stored state

    rounds: int = 0
    drafted: int = 0  # draft tokens proposed over all rounds
    accepted: int = 0  # of which accepted by the target

    @property
    def tokens_per_round(self) -> float:
        return len(self.tokens) / max(1, self.rounds)
