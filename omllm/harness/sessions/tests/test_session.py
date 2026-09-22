"""Session storage follows the agent's transcript: stored as it lands, whole, once, however the run ends."""
import asyncio

import pytest

from omcore import dataclasses as dc
from omcore.asyncs.asynclite import all as asl

from .... import agent as agn
from .... import llm
from ....agent.tests.scripted import scripted_backend
from ....agent.tests.scripted import text_message
from ....agent.tests.scripted import tool_call_message
from ....agent.tests.tools import EchoTool
from ....agent.tests.tools import bare_tool
from ....core import ui
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ...commands.base import Commands
from ...commands.manager import CommandsManager
from ..entries import ContextProjectionSessionEntry
from ..entries import MessageSessionEntry
from ..session import Session
from ..storage.types import SessionStorage


##


class _RecordingStorage(SessionStorage):
    def __init__(self, entries=()):
        super().__init__()

        self.entries = list(entries)

    async def get_entries(self):
        return tuple(self.entries)

    async def add_entry(self, *entries):
        self.entries.extend(entries)


class _BlockingBackend(llm.ImmediateBackend):
    def __init__(self) -> None:
        super().__init__()

        self._model = llm.Model(key=llm.ModelKey('test', 'blocking'), backend='test')
        self.started = asyncio.Event()
        self._never = asyncio.Event()

    @property
    def model(self) -> llm.Model:
        return self._model

    async def immediate(self, context, options=None):
        self.started.set()
        await self._never.wait()
        raise AssertionError


class _BlockingExecutor:
    def __init__(self) -> None:
        super().__init__()

        self.started = asyncio.Event()
        self._never = asyncio.Event()

    async def __call__(self, ctx):
        self.started.set()
        await self._never.wait()
        raise AssertionError


def _agent(backend, context_lifecycle_manager=None):
    return agn.Agent(
        turn_runner=agn.TurnLoopRunner(
            cancellation=asl.asyncio.Cancellation(),
            group_runner=AsyncioGroupRunner(),
            backends=agn.DictBackendManager({llm.ImmediateBackend: {None: backend}}),  # type: ignore[type-abstract]
            context_lifecycle_manager=context_lifecycle_manager,
        ),
    )


def _commands_manager():
    return CommandsManager(commands=Commands([]), text_displayer=ui.NopTextDisplayer())


async def _session(backend, tools=(), storage=None, agent=None):
    if agent is None:
        agent = _agent(backend)
    if tools:
        await agent.update_state(lambda s: dc.replace(s, context=agn.Context(tools=agn.ToolSet(list(tools)))))

    if storage is None:
        storage = _RecordingStorage()
    session = Session(
        agent=agent,
        storage=storage,
        commands_manager=_commands_manager(),
    )
    return session, storage


def _stored_types(storage):
    assert all(isinstance(e, MessageSessionEntry) for e in storage.entries)
    return [type(e.message) for e in storage.entries]


@pytest.mark.asyncs('asyncio')
async def test_resume_restores_and_repairs_transcript():
    tool_calls = tool_call_message(
        llm.ToolCall('t1', 'finished', {}),
        llm.ToolCall('t2', 'interrupted', {}),
    )
    storage = _RecordingStorage([
        MessageSessionEntry(llm.UserMessage('hi')),
        MessageSessionEntry(tool_calls),
        MessageSessionEntry(llm.ToolResultMessage(
            tool_call_id='t1',
            tool_name='finished',
            content=(llm.TextContent('done'),),
        )),
    ])

    def expect(inv):
        assert [type(message) for message in inv.context.messages or ()] == [
            llm.UserMessage,
            llm.AiMessage,
            llm.ToolResultMessage,
            llm.ToolResultMessage,
            llm.UserMessage,
        ]

    session, _ = await _session(
        scripted_backend(llm.BackendScriptTurn(text_message('continued'), expect=expect)),
        storage=storage,
    )

    messages = await session.resume()

    assert [type(message) for message in messages] == [
        llm.UserMessage,
        llm.AiMessage,
        llm.ToolResultMessage,
        llm.ToolResultMessage,
        agn.InfoAgentMessage,
    ]
    repair_result = messages[-2]
    assert isinstance(repair_result, llm.ToolResultMessage)
    assert repair_result.tool_call_id == 't2'
    assert repair_result.is_error
    assert 'interrupted' in repair_result.content[0].text
    assert len(storage.entries) == 5

    resumed_again, _ = await _session(scripted_backend(text_message('unused')), storage=storage)
    assert len(await resumed_again.resume()) == 5
    assert len(storage.entries) == 5

    await session.prompt('continue')

    assert len(storage.entries) == 7


@pytest.mark.asyncs('asyncio')
async def test_completed_run_is_stored():
    session, storage = await _session(scripted_backend(text_message('hello')))

    await session.prompt('hi')

    assert _stored_types(storage) == [llm.UserMessage, llm.AiMessage]


@pytest.mark.asyncs('asyncio')
async def test_messages_are_stored_as_they_land_once_each():
    echo = EchoTool()
    session, storage = await _session(
        scripted_backend(
            tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'x'})),
            text_message('ok'),
        ),
        [echo.tool()],
    )

    await session.prompt('hi')

    assert _stored_types(storage) == [llm.UserMessage, llm.AiMessage, llm.ToolResultMessage, llm.AiMessage]

    # A second run starts its own count.
    await session.prompt('again')

    assert len(storage.entries) == 6


@pytest.mark.asyncs('asyncio')
async def test_failed_run_is_stored():
    session, storage = await _session(scripted_backend(RuntimeError('boom')))

    await session.prompt('hi')

    assert _stored_types(storage) == [llm.UserMessage, agn.InfoAgentMessage]
    assert 'boom' in storage.entries[-1].message.info


@pytest.mark.asyncs('asyncio')
async def test_cancelled_run_is_stored():
    backend = _BlockingBackend()
    session, storage = await _session(backend)

    task = asyncio.create_task(session.prompt('hi'))
    await backend.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert _stored_types(storage) == [llm.UserMessage, agn.InfoAgentMessage]


@pytest.mark.asyncs('asyncio')
async def test_cancelled_mid_tool_stores_the_repair_tail_once():
    executor = _BlockingExecutor()
    session, storage = await _session(
        scripted_backend(tool_call_message(llm.ToolCall('t1', 'block', {}))),
        [bare_tool('block', executor)],
    )

    task = asyncio.create_task(session.prompt('hi'))
    await executor.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # The announced messages, then the unannounced repair tail, with nothing stored twice.
    assert _stored_types(storage) == [
        llm.UserMessage,
        llm.AiMessage,
        llm.ToolResultMessage,
        agn.InfoAgentMessage,
    ]
    assert storage.entries[2].message.is_error


##


class _FixedCompactor(agn.ContextCompactor):
    """Summarizes everything but the newest message, without a model."""

    async def compact(self, context, *, backend, target_tokens, reason, instructions=None):
        return agn.ContextProjection(
            summary='Summarized.',
            first_kept_message_index=len(context.messages or ()) - 1,
        )


def _pressed_backend(*turns):
    # A model so small that every call is over its threshold, so every call compacts.
    return llm.ScriptedImmediateBackend(
        llm.Model(
            key=llm.ModelKey('test', 'tiny'),
            backend='test',
            limits=llm.ModelLimits(context=100, input=90, output=10),
        ),
        llm.BackendScript([llm.BackendScriptTurn(t) for t in turns]),
    )


def _entry_types(storage):
    return [type(e) for e in storage.entries]


@pytest.mark.asyncs('asyncio')
async def test_a_runs_reduction_is_stored_as_it_happens_and_restored_on_resume():
    manager = agn.StandardContextLifecycleManager(compactor=_FixedCompactor())
    session, storage = await _session(
        backend := _pressed_backend(text_message('hello')),
        agent=_agent(backend, manager),
    )

    await session.prompt('hi')

    # The reduction landed between the prompt and the answer, and so does its entry.
    assert _entry_types(storage) == [MessageSessionEntry, ContextProjectionSessionEntry, MessageSessionEntry]
    projection = storage.entries[1].projection
    assert projection.summary == 'Summarized.'
    assert projection.first_kept_message_index == 0

    # Resumed, the projection stands over the messages, and is not stored over again.
    agent = _agent(backend := _pressed_backend(text_message('again')), manager)
    resumed, _ = await _session(backend, storage=storage, agent=agent)
    assert len(await resumed.resume()) == 2
    assert agent.state.context.projection == projection
    assert len(storage.entries) == 3

    # The next run's reduction lands the same way, after what came before.
    await resumed.prompt('more')

    assert _entry_types(storage) == [
        MessageSessionEntry,
        ContextProjectionSessionEntry,
        MessageSessionEntry,
        MessageSessionEntry,
        ContextProjectionSessionEntry,
        MessageSessionEntry,
    ]
    assert storage.entries[4].projection.first_kept_message_index == 2
    assert agent.state.context.projection == storage.entries[4].projection


@pytest.mark.asyncs('asyncio')
async def test_a_projection_arriving_by_state_update_is_stored_once():
    agent = _agent(backend := scripted_backend(text_message('hello')))
    session, storage = await _session(backend, agent=agent)

    await session.prompt('hi')
    assert _entry_types(storage) == [MessageSessionEntry, MessageSessionEntry]

    # What a compaction on request does to the state.
    projection = agn.ContextProjection(summary='By hand.', first_kept_message_index=2)
    await agent.update_state(lambda s: dc.replace(s, context=dc.replace(s.context, projection=projection)))

    assert _entry_types(storage) == [MessageSessionEntry, MessageSessionEntry, ContextProjectionSessionEntry]
    assert storage.entries[2].projection == projection

    # A state update leaving it as it is stores nothing.
    await agent.update_state(lambda s: s)
    assert len(storage.entries) == 3

    # A resumed session takes the projection with the messages.
    resumed_agent = _agent(scripted_backend(text_message('unused')))
    resumed, _ = await _session(None, storage=storage, agent=resumed_agent)
    await resumed.resume()
    assert resumed_agent.state.context.projection == projection
    assert len(storage.entries) == 3
