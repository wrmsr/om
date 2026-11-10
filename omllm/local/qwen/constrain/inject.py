from omcore import inject as inj

from ..core.model import Qwen35
from ..decode.inject import GENERATION_SCOPE
from ..decode.inject import logit_processors
from ..decode.processors import LogitProcessor
from ..decode.processors import NullLogitProcessor
from ..decode.runners import GenerationParams
from ..ops.base import Ops
from .processors import GrammarProcessor


##


def _grammar(params: GenerationParams, ops: Ops, model: Qwen35) -> LogitProcessor:
    if params.constraint is None:
        return NullLogitProcessor()
    return GrammarProcessor(ops, vocab_size=model.cfg.vocab_size, constraint=params.constraint)


def bind_constrain() -> inj.Elements:
    """A request's grammar (tool calls, JSON mode), when it brings one, as one of its logit processors."""

    return logit_processors().bind_item(to_fn=_grammar, in_=GENERATION_SCOPE)
