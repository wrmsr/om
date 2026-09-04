import typing as ta

from omcore import check
from omcore import dataclasses as dc

from .. import llm
from ..core.eventbus import EventPublisher
from .turns.inboxes import ListTurnInbox
from .types.contexts import Context
from .types.errors import AgentBusyError
from .types.events import AgentEndEvent
from .types.events import Event
from .types.events import StateUpdateEvent
from .types.messages import MESSAGE_TYPES
from .types.messages import Message
from .types.states import State
from .types.turns import TurnConfig
from .types.turns import TurnParams
from .types.turns import TurnResult
from .types.turns import TurnRunner


##


class _TerminalEventCapture:
    """Forwards a run's events to the agent's bus, keeping hold of the terminal one for the exceptional exit path."""

    def __init__(self, publish: ta.Callable[[Event], ta.Awaitable[None]]) -> None:
        super().__init__()

        self._publish = publish

        self.end_event: AgentEndEvent | None = None

    async def __call__(self, event: Event) -> None:
        # Recorded ahead of forwarding, so a cancellation thrown into a later subscriber still leaves it recorded.
        if isinstance(event, AgentEndEvent):
            self.end_event = event

        await self._publish(event)


##


class Agent(
    EventPublisher[Event],
):
    """
    Holds the conversation state and runs prompts against it, one at a time: a `prompt` submitted while another is
    running raises AgentBusyError rather than interleaving on the state. Input for a run already in progress goes
    through `steer` and `follow_up` instead. Belongs to one event loop, and is not thread-safe.
    """

    def __init__(
            self,
            *,
            turn_runner: TurnRunner,
    ) -> None:
        super().__init__()

        self._turn_runner = turn_runner

        self._state = State()

        self._running = False

        self._inbox = ListTurnInbox()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def state(self) -> State:
        return self._state

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

    #

    async def _apply_turn(self, *, config: TurnConfig | None = None, context: Context) -> None:
        def fn(old_state: State) -> State:
            new_state = dc.replace(old_state, context=context)
            if config is not None:
                new_state = dc.replace(new_state, turn_config=config)
            return new_state

        await self.update_state(fn)

    @staticmethod
    def _coerce_messages(
            input: str | Message | ta.Sequence[Message],  # noqa
    ) -> list[Message]:
        if isinstance(input, str):
            return [llm.UserMessage(input)]
        elif isinstance(input, MESSAGE_TYPES):
            return [input]
        else:
            return [check.isinstance(m, MESSAGE_TYPES) for m in check.isinstance(input, ta.Sequence)]

    #

    def steer(
            self,
            input: str | Message | ta.Sequence[Message],  # noqa
    ) -> None:
        """
        Queues messages for the run in progress, delivered at the start of its next turn - after the current tool
        batch, unless the turn config says to cut it short. With no run in progress they are delivered at the start
        of the next prompt.
        """

        self._inbox.add_steering(*self._coerce_messages(input))

    def follow_up(
            self,
            input: str | Message | ta.Sequence[Message],  # noqa
    ) -> None:
        """
        Queues messages to be delivered only once the model would otherwise have ended the run, which then continues.
        With no run in progress they wait for the next prompt to reach that point.
        """

        self._inbox.add_follow_ups(*self._coerce_messages(input))

    #

    async def _prompt(self, new_messages: ta.Sequence[Message]) -> TurnResult:
        in_state = self._state

        capture = _TerminalEventCapture(self._publish)

        try:
            result = await self._turn_runner.run_turn(TurnParams(
                in_state=in_state,
                new_messages=new_messages,
                subscriber=capture,
                inbox=self._inbox,
            ))

        except BaseException:
            # The run raised - a cancellation, in practice - possibly after getting as far as its terminal event. That
            # event carries the transcript as the loop left it, repaired, and it is applied here so the next prompt
            # builds on what actually happened rather than on the state from before this one. The state assignment
            # itself is synchronous; only the StateUpdateEvent publish can be lost to a second cancellation.
            if (end := capture.end_event) is not None:
                await self._apply_turn(context=end.context)

            raise

        else:
            await self._apply_turn(config=result.config, context=result.context)

            return result

    async def prompt(
            self,
            input: str | Message | ta.Sequence[Message],  # noqa
    ) -> TurnResult:
        """
        Runs one prompt to its end and returns its result. Every outcome the loop decides - completion, truncation, the
        turn limit, a failure - comes back as a result, its reason and any error on it; the state reflects the run
        either way. Only the caller's own cancellation raises out.
        """

        if self._running:
            raise AgentBusyError

        new_messages = self._coerce_messages(input)

        self._running = True
        try:
            return await self._prompt(new_messages)
        finally:
            self._running = False
