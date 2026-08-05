import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ... import llm
from .contexts import Context
from .tools import ToolEnvironment
from .turns import TurnConfig


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class State:
    context: Context = Context()

    model: llm.Model | None = None

    turn_config: TurnConfig | None = None

    tool_env: ToolEnvironment | None = None
