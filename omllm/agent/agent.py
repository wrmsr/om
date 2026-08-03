import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from .. import llm
from ..core.eventbus import EventPublisher
from .backends import BackendManager
from .turns.loop import TurnLoop
from .types.contexts import Context
from .types.events import Event
from .types.messages import Message
from .types.tools import ToolEnvironment
from .types.turns import TurnConfig


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(default_repr_fn=lang.opt_repr)
class State:
    context: Context = Context()

    model: llm.Model | None = None

    turn_config: TurnConfig | None = None

    tool_env: ToolEnvironment | None = None


class Agent(
    EventPublisher[Event],
):
    def __init__(
            self,
            *,
            backends: BackendManager,
    ) -> None:
        super().__init__()

        self._backends = backends

        self._state = State()

    async def modify_state(self, fn: ta.Callable[[State], State | ta.Awaitable[State]]) -> None:
        out = fn(self._state)
        if isinstance(out, ta.Awaitable):
            out = await out
        self._state = check.isinstance(out, State)

    async def prompt(
            self,
            input: str | Message | ta.Sequence[Message],  # noqa
    ) -> None:
        if isinstance(input, str):
            new_messages: list[Message] = [llm.UserMessage(input)]
        elif isinstance(input, llm.Message):
            new_messages = [input]
        else:
            new_messages = [check.isinstance(m, llm.Message) for m in input]

        context = dc.replace(
            self._state.context,

            messages=[
                *(self._state.context.messages or []),
                *new_messages,
            ],
        )

        llm_backend = self._backends.get_backend(llm.ImmediateBackend, self._state.model)  # type: ignore[type-abstract]

        loop = TurnLoop(
            config=self._state.turn_config,
            context=context,
            subscriber=self._publish,
            llm_backend=llm_backend,
            tool_env=self._state.tool_env,
        )

        result = await loop.run()

        self._state = dc.replace(
            self._state,

            turn_config=result.config,
            context=result.context,
        )
