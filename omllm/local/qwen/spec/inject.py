from omcore import dataclasses as dc
from omcore import inject as inj

from ..core.model import Qwen35
from ..decode.drafts import DraftSource
from ..decode.drafts import NullDraftSource
from ..decode.inject import GENERATION_SCOPE
from ..decode.processors import LogitProcessor
from ..decode.sampling import Sampler
from ..ops.base import Ops
from .lookup import LookupDraftSource
from .mtp import MtpDraftSource


##


@dc.dataclass(frozen=True)
class SpecConfig:
    """Speculative decoding with the MTP head: k drafts a round (0 = off), drafted over the first draft_vocab ids."""

    k: int = 0
    draft_vocab: int = 0


def _mtp(
        model: Qwen35,
        sampler: Sampler,
        processor: LogitProcessor,
        config: SpecConfig,
) -> DraftSource:
    return MtpDraftSource(
        model=model,
        sampler=sampler,
        processor=processor,
        k=config.k,
        draft_vocab=config.draft_vocab,
    )


def bind_spec(config: SpecConfig, drafts: inj.WrapperBinderHelper) -> inj.Elements:
    """
    The base of the draft-source chain `drafts` (built by the composition root, which binds DraftSource to its top):
    the MTP head when speculating, else no drafts. Draft sources that fall back to it -- prompt lookup -- are pushed
    on after this.
    """

    return inj.as_elements(
        inj.bind(SpecConfig, to_const=config),
        drafts.push_bind(to_fn=_mtp, in_=GENERATION_SCOPE) if config.k else
        drafts.push_bind(to_ctor=NullDraftSource, in_=GENERATION_SCOPE),
    )


@dc.dataclass(frozen=True)
class LookupConfig:
    """Prompt-lookup drafting: match the last `ngram` tokens against the context; `k` drafts (at least the head's)."""

    ngram: int = 3
    k: int = 3


def _lookup(wrapped: DraftSource, ops: Ops, model: Qwen35, config: LookupConfig) -> DraftSource:
    return LookupDraftSource(
        ops,
        vocab_size=model.cfg.vocab_size,
        wrapped=wrapped,
        ngram=config.ngram,
        k=config.k,
    )


def bind_lookup(config: LookupConfig, drafts: inj.WrapperBinderHelper) -> inj.Elements:
    """Prompt lookup on top of the draft-source chain `drafts`: it drafts when the context repeats, else asks below."""

    return inj.as_elements(
        inj.bind(LookupConfig, to_const=config),
        drafts.push_bind(to_fn=_lookup, in_=GENERATION_SCOPE),
    )
