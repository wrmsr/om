import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .. import llm
from ..core.eventbus import EventPublisher
from .types.events import Event
from .types.events import StateUpdateEvent
from .types.messages import MESSAGE_TYPES
from .types.messages import Message
from .types.states import State
from .types.turns import TurnRunner


##


class Agent(
    EventPublisher[Event],
):
    def __init__(
            self,
            *,
            turn_runner: TurnRunner,
    ) -> None:
        super().__init__()

        self._turn_runner = turn_runner

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
        elif isinstance(input, MESSAGE_TYPES):
            new_messages = [input]
        else:
            new_messages = [check.isinstance(m, MESSAGE_TYPES) for m in check.isinstance(input, ta.Sequence)]

        in_state = self._state

        result = await self._turn_runner.run_turn(
            in_state,
            new_messages,
            subscriber=self._publish,
        )

        await self.update_state(lambda old_state: dc.replace(
            old_state,

            turn_config=result.config,
            context=result.context,
        ))
