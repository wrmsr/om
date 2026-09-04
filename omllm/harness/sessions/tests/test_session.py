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
from ..entries import MessageSessionEntry
from ..session import Session
from ..storage import SessionStorage


##


class _RecordingStorage(SessionStorage):
    def __init__(self):
        super().__init__()

        self.entries = []

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


async def _session(backend, tools=()):
    agent = agn.Agent(
        turn_runner=agn.TurnLoopRunner(
            cancellation=asl.asyncio.Cancellation(),
            group_runner=AsyncioGroupRunner(),
            backends=agn.DictBackendManager({llm.ImmediateBackend: {None: backend}}),  # type: ignore[type-abstract]
        ),
    )
    if tools:
        await agent.update_state(lambda s: dc.replace(s, context=agn.Context(tools=agn.ToolSet(list(tools)))))

    storage = _RecordingStorage()
    session = Session(
        agent=agent,
        storage=storage,
        commands_manager=CommandsManager(commands=Commands([]), text_displayer=ui.NopTextDisplayer()),
    )
    return session, storage


def _stored_types(storage):
    assert all(isinstance(e, MessageSessionEntry) for e in storage.entries)
    return [type(e.message) for e in storage.entries]


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
