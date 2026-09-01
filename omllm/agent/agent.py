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
from .types.turns import TurnParams
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

        # FIXME: the state update below is skipped whenever `run_turn` raises - including when it raises *after* the
        # turn loop has completed. The loop publishes AgentEndEvent(COMPLETED) from inside `run_turn` (subscribers such
        # as the harness Session store the turn's messages on it), and a runner may still suspend after that: the TUI's
        # ScopedTurnRunner exits an async injector scope, whose `__aexit__` is an await point. A cancellation landing
        # there unwinds through here with the completed result in hand but discarded, leaving the turn stored but never
        # applied to agent state - the next prompt runs without it. A sans-io fix is to capture the terminal event's
        # context from the subscriber path and apply it in a `finally` when `run_turn` raised after completion; that
        # trades this inconsistency for its mirror image when the cancellation instead lands inside the publish, ahead
        # of storage. Neither is right without an atomic terminal publish (see the FIXME in TurnLoop.run), which needs
        # cancellation shielding this layer must not take on. Today the window is nil in practice - the scope exit has
        # nothing to await - so this is left as documentation until the publish is made atomic.
        result = await self._turn_runner.run_turn(TurnParams(
            in_state=in_state,
            new_messages=new_messages,
            subscriber=self._publish,
        ))

        await self.update_state(lambda old_state: dc.replace(
            old_state,  # noqa

            turn_config=result.config,
            context=result.context,
        ))
