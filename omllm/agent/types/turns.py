import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ... import llm
from .contexts import Context
from .messages import Message


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class TurnConfig:
    llm_options: llm.Options | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class TurnResult:
    config: TurnConfig
    context: Context

    new_messages: ta.Sequence[Message] | None = None
