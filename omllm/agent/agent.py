import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .. import llm
from ..core.eventbus import EventPublisher
from .backends import BackendManager
from .turns.loop import TurnLoop
from .types.events import Event
from .types.events import StateUpdateEvent
from .types.messages import Message
from .types.states import State


##


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

    async def update_state(self, fn: ta.Callable[[State], State | ta.Awaitable[State]]) -> None:
        old_state = self._state
        out = fn(old_state)
        if isinstance(out, ta.Awaitable):
            out = await out
        new_state = check.isinstance(out, State)

        self._state = new_state

        await self._publish(StateUpdateEvent(
            new_state=new_state,
            old_state=old_state,
        ))

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

        in_state = self._state

        context = dc.replace(
            in_state.context,

            messages=[
                *(self._state.context.messages or []),
                *new_messages,
            ],
        )

        llm_backend = self._backends.get_backend(llm.ImmediateBackend, in_state.model)  # type: ignore[type-abstract]

        loop = TurnLoop(
            config=in_state.turn_config,
            context=context,
            subscriber=self._publish,
            llm_backend=llm_backend,
            tool_env=in_state.tool_env,
        )

        result = await loop.run()

        await self.update_state(lambda old_state: dc.replace(
            old_state,

            turn_config=result.config,
            context=result.context,
        ))
