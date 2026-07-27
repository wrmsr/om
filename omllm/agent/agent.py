import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .. import llm
from .backends import BackendManager
from .contexts import Context
from .messages import Message


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class State:
    context: Context = Context()

    model: llm.Model | None = None


class Agent:
    def __init__(
            self,
            *,
            backend_manager: BackendManager,
    ) -> None:
        super().__init__()

        self._backend_manager = backend_manager

        self._state = State()

    def prompt(
            self,
            input: str | Message | ta.Sequence[Message],  # noqa
    ) -> None:
        raise NotImplementedError
