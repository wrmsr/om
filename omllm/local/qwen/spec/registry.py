"""Which draft source drafts with a model's draft head: by the type of the head (core/draftheads.py)."""
import typing as ta

from ..core.dspark.drafter import DsparkDrafter
from ..core.model import Qwen35
from ..core.mtp import MtpHead
from ..decode.drafts import DraftSource
from ..decode.processors import LogitProcessor
from ..decode.sampling import Sampler
from .dspark import DsparkDraftSource
from .mtp import MtpDraftSource


##


def head_draft_source(
        model: Qwen35,
        *,
        sampler: Sampler,
        processor: LogitProcessor,
        k: int | ta.Sequence[int],
        draft_vocab: int = 0,
        confidence: float | None = None,
) -> DraftSource:
    """
    The draft source over the model's own draft head, for `k` drafts a round (several: the counts a round may stop
    at; for a DSpark drafter one number is every count up to it). What else a head's source takes is its own:
    `draft_vocab` and `confidence` are the MTP head's, and a head that has no use for one refuses it rather than
    ignore it.
    """

    head = model.mtp

    if isinstance(head, MtpHead):
        return MtpDraftSource(
            model=model,
            sampler=sampler,
            processor=processor,
            k=k,
            draft_vocab=draft_vocab,
            confidence=confidence,
        )

    if isinstance(head, DsparkDrafter):
        if draft_vocab or confidence is not None:
            raise ValueError('a DSpark drafter takes no draft vocabulary or confidence')
        return DsparkDraftSource(
            model=model,
            sampler=sampler,
            k=k,
        )

    if head is None:
        raise ValueError('no draft head loaded')
    raise TypeError(f'no draft source for a {type(head).__name__}')
