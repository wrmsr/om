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

        agent.subscribe(self._on_agent_event)

    async def _on_agent_event(self, agn_event: agn.Event) -> None:
        await self._publish(AgentSessionEvent(agn_event))

        if isinstance(agn_event, agn.AgentEndEvent):
            await self._storage.add_entry(*[
                MessageSessionEntry(m)
                for m in agn_event.new_messages or []
            ])

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
