import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .contexts import Context
from .messages import Message


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class State:
    context: Context = Context()


class Agent:
    def __init__(
            self,
    ) -> None:
        super().__init__()

        self._state = State()

    def prompt(
            self,
            input: str | Message | ta.Sequence[Message],  # noqa
    ) -> None:
        raise NotImplementedError
