import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .lifecycle import ContextBudget
from .lifecycle import ContextProjection
from .lifecycle import UsageLedger
from .messages import Message
from .tools import ToolSet


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class Context:
    system_prompt: str | None = None

    messages: ta.Sequence[Message] | None = None

    tools: ToolSet | None = None

    usage: UsageLedger | None = None

    context_budget: ContextBudget | None = None

    projection: ContextProjection | None = None
