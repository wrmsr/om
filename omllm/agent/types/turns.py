import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ... import llm
from ...core.eventbus import EventSubscriber
from .contexts import Context
from .messages import Message


if ta.TYPE_CHECKING:
    from .events import Event
    from .states import State


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class TurnConfig:
    llm_options: llm.Options | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class TurnParams:
    in_state: State
    new_messages: ta.Sequence[Message]

    subscriber: EventSubscriber[Event] | None = None


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class TurnResult:
    config: TurnConfig
    context: Context

    new_messages: ta.Sequence[Message] | None = None


##


class TurnRunner(lang.Abstract):
    @abc.abstractmethod
    def run_turn(self, params: TurnParams) -> ta.Awaitable[TurnResult]:
        raise NotImplementedError
