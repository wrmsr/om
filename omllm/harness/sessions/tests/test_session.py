"""Session storage follows the agent's state: every run's messages are stored, however the run ended."""
import asyncio

import pytest

from .... import agent as agn
from .... import llm
from ....agent.tests.scripted import scripted_backend
from ....agent.tests.scripted import text_message
from ....core import ui
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


def _session(backend):
    agent = agn.Agent(
        turn_runner=agn.TurnLoopRunner(
            backends=agn.DictBackendManager({llm.ImmediateBackend: {None: backend}}),  # type: ignore[type-abstract]
        ),
    )
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
    session, storage = _session(scripted_backend(text_message('hello')))

    await session.prompt('hi')

    assert _stored_types(storage) == [llm.UserMessage, llm.AiMessage]


@pytest.mark.asyncs('asyncio')
async def test_failed_run_is_stored():
    session, storage = _session(scripted_backend(RuntimeError('boom')))

    await session.prompt('hi')

    assert _stored_types(storage) == [llm.UserMessage, agn.InfoAgentMessage]
    assert 'boom' in storage.entries[-1].message.info


@pytest.mark.asyncs('asyncio')
async def test_cancelled_run_is_stored():
    backend = _BlockingBackend()
    session, storage = _session(backend)

    task = asyncio.create_task(session.prompt('hi'))
    await backend.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert _stored_types(storage) == [llm.UserMessage, agn.InfoAgentMessage]
