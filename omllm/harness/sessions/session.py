import typing as ta
import uuid

from omcore import check
from omcore import dataclasses as dc

from ... import agent as agn
from ...core.eventbus import EventPublisher
from ..commands.manager import CommandsManager
from .entries import ContextProjectionSessionEntry
from .entries import MessageSessionEntry
from .events import AgentSessionEvent
from .events import SessionEvent
from .storage.types import SessionStorage
from .types import SessionId


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
            id: SessionId | None = None,  # noqa
    ) -> None:
        super().__init__()

        self._agent = agent
        self._storage = storage
        self._commands_manager = commands_manager
        self._id = check.isinstance(id, SessionId) if id is not None else SessionId(uuid.uuid7())

        # How much of the run in progress has been stored: messages are stored as they are announced, and the run's
        # terminal event then covers whatever it did not announce.
        self._num_run_stored = 0

        # The projection last stored, against which a changed one is told: a run announces its reductions as they
        # happen, and the state carries whatever else changes it - a compaction on request.
        self._stored_projection: agn.ContextProjection | None = None

        agent.subscribe(self._on_agent_event)

    @property
    def id(self) -> SessionId:
        return self._id

    async def resume(self) -> ta.Sequence[agn.Message]:
        check.state(not self._agent.is_running)
        check.state(not self._agent.state.context.messages, 'Cannot resume into a non-empty agent transcript')
        check.state(not self._agent.state.context.projection, 'Cannot resume into a projected agent transcript')

        entries = await self._storage.get_entries()

        messages: list[agn.Message] = []
        projection: agn.ContextProjection | None = None
        for entry in entries:
            if isinstance(entry, MessageSessionEntry):
                messages.append(entry.message)

            elif isinstance(entry, ContextProjectionSessionEntry):
                check.state(entry.projection.first_kept_message_index <= len(messages))
                projection = entry.projection

            else:
                raise TypeError(entry)

        repair_messages: list[agn.Message] = [
            *agn.build_unanswered_tool_call_results(messages, 'the session was interrupted'),
        ]
        if repair_messages:
            repair_messages.append(agn.InfoAgentMessage('Session resumed after an interruption.'))
            await self._storage.add_entry(*[
                MessageSessionEntry(message)
                for message in repair_messages
            ])
            messages.extend(repair_messages)

        # Ahead of the state update, whose announcement would otherwise store the projection over again.
        self._stored_projection = projection

        await self._agent.update_state(
            lambda state: dc.replace(
                state,
                context=dc.replace(
                    state.context,
                    messages=tuple(messages),
                    projection=projection,
                ),
            ),
        )

        return tuple(messages)

    async def _store_projection(self, projection: agn.ContextProjection | None) -> None:
        if (projection or agn.ContextProjection.ZERO) == (self._stored_projection or agn.ContextProjection.ZERO):
            return

        await self._storage.add_entry(ContextProjectionSessionEntry(projection or agn.ContextProjection.ZERO))
        self._stored_projection = projection

    async def _on_agent_event(self, agn_event: agn.Event) -> None:
        await self._publish(AgentSessionEvent(agn_event))

        if isinstance(agn_event, agn.AgentStartEvent):
            self._num_run_stored = 0

        elif isinstance(agn_event, agn.MessageAddedEvent):
            await self._storage.add_entry(MessageSessionEntry(agn_event.message))
            self._num_run_stored = max(self._num_run_stored, agn_event.index + 1)

        elif isinstance(agn_event, agn.ContextReductionEvent):
            # Stored as it happens rather than at the run's end: a compaction cost a model call, which a run cut short
            # is not to pay again. Every message it indexes has been announced, and so stored, ahead of it.
            await self._store_projection(agn_event.projection)

        elif isinstance(agn_event, agn.AgentEndEvent):
            # Every outcome is stored, not only completion: the loop keeps the transcript up to a failure or
            # cancellation, repaired so it can be built on, and the agent applies it to its state - the store has to
            # match what the next prompt will see. The tail here is the repair messages an interrupted run adds without
            # announcing.
            await self._storage.add_entry(*[
                MessageSessionEntry(m)
                for m in agn_event.new_messages[self._num_run_stored:]
            ])
            self._num_run_stored = 0

        elif isinstance(agn_event, agn.StateUpdateEvent):
            await self._store_projection(agn_event.new_state.context.projection)

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
