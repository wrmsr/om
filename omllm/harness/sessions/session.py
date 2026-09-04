import typing as ta

from ... import agent as agn
from ...core.eventbus import EventPublisher
from ..commands.manager import CommandsManager
from .entries import MessageSessionEntry
from .events import AgentSessionEvent
from .events import SessionEvent
from .storage import SessionStorage


##


class Session(
    EventPublisher[SessionEvent],
):
    def __init__(
            self,
            *,
            agent: agn.Agent,
            storage: SessionStorage,
            commands_manager: CommandsManager,
    ) -> None:
        super().__init__()

        self._agent = agent
        self._storage = storage
        self._commands_manager = commands_manager

        # How much of the run in progress has been stored: messages are stored as they are announced, and the run's
        # terminal event then covers whatever it did not announce.
        self._num_run_stored = 0

        agent.subscribe(self._on_agent_event)

    async def _on_agent_event(self, agn_event: agn.Event) -> None:
        await self._publish(AgentSessionEvent(agn_event))

        if isinstance(agn_event, agn.AgentStartEvent):
            self._num_run_stored = 0

        elif isinstance(agn_event, agn.MessageAddedEvent):
            await self._storage.add_entry(MessageSessionEntry(agn_event.message))
            self._num_run_stored = max(self._num_run_stored, agn_event.index + 1)

        elif isinstance(agn_event, agn.AgentEndEvent):
            # Every outcome is stored, not only completion: the loop keeps the transcript up to a failure or
            # cancellation, repaired so it can be built on, and the agent applies it to its state - the store has to
            # match what the next prompt will see. The tail here is the repair messages an interrupted run adds
            # without announcing.
            await self._storage.add_entry(*[
                MessageSessionEntry(m)
                for m in agn_event.new_messages[self._num_run_stored:]
            ])
            self._num_run_stored = 0

    async def prompt(
            self,
            input: str,  # noqa
    ) -> None:
        if not input:
            return

        if input.startswith('/'):
            await self._commands_manager.run_command_text(input[1:])
            return

        await self._agent.prompt(input)

    def steer(
            self,
            input: str | agn.Message | ta.Sequence[agn.Message],  # noqa
    ) -> None:
        """
        Queues input for the run in progress. Nothing in the ui routes here yet: a `/steer` command is to, which needs
        the ui to dispatch commands while a turn runs rather than queue them behind it.
        """

        self._agent.steer(input)
