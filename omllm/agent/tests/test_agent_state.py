"""
The agent's contract around a run: one at a time, a result for every outcome, and state that reflects what happened.
"""
import asyncio

import pytest

from omcore.asyncs.asynclite import all as asl

from ... import llm
from ...core.asyncs.asyncio import AsyncioGroupRunner
from ..agent import Agent
from ..backends import DictBackendManager
from ..turns.runner import TurnLoopRunner
from ..types.errors import AgentBusyError
from ..types.events import AgentEndEvent
from ..types.events import StateUpdateEvent
from ..types.messages import InfoAgentMessage
from ..types.turns import AgentEndReason
from .scripted import scripted_backend
from .scripted import text_message


##


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


def _agent(backend):
    return Agent(
        turn_runner=TurnLoopRunner(
            cancellation=asl.asyncio.Cancellation(),
            group_runner=AsyncioGroupRunner(),
            backends=DictBackendManager({llm.ImmediateBackend: {None: backend}}),  # type: ignore[type-abstract]
        ),
    )


def _message_types(agent):
    return [type(m) for m in agent.state.context.messages or []]


@pytest.mark.asyncs('asyncio')
async def test_prompt_returns_result_and_applies_state():
    agent = _agent(scripted_backend(text_message('hello'), text_message('again')))

    result = await agent.prompt('hi')

    assert result.reason is AgentEndReason.COMPLETED
    assert _message_types(agent) == [llm.UserMessage, llm.AiMessage]
    assert not agent.is_running

    # The next prompt builds on the last.
    await agent.prompt('more')

    assert _message_types(agent) == [llm.UserMessage, llm.AiMessage, llm.UserMessage, llm.AiMessage]


@pytest.mark.asyncs('asyncio')
async def test_failed_prompt_returns_rather_than_raises_and_applies_state():
    error = RuntimeError('boom')
    agent = _agent(scripted_backend(error))

    result = await agent.prompt('hi')

    assert result.reason is AgentEndReason.FAILED
    assert result.error is error
    assert _message_types(agent) == [llm.UserMessage, InfoAgentMessage]
    assert not agent.is_running


@pytest.mark.asyncs('asyncio')
async def test_cancelled_prompt_raises_and_still_applies_state():
    backend = _BlockingBackend()
    agent = _agent(backend)
    updates = []
    agent.subscribe(lambda e: updates.append(e) if isinstance(e, StateUpdateEvent) else None)

    task = asyncio.create_task(agent.prompt('hi'))
    await backend.started.wait()
    assert agent.is_running

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert not agent.is_running
    assert _message_types(agent) == [llm.UserMessage, InfoAgentMessage]
    assert agent.state.context.messages[-1].info == 'Turn cancelled.'
    assert len(updates) == 1


@pytest.mark.asyncs('asyncio')
async def test_state_is_applied_when_a_cancel_lands_in_a_later_subscriber():
    class StallingSubscriber:
        def __init__(self):
            self.stalled = asyncio.Event()
            self.release = asyncio.Event()
            self.ended = False

        async def __call__(self, ev):
            if isinstance(ev, AgentEndEvent):
                self.stalled.set()
                await self.release.wait()
                self.ended = True

    stalling = StallingSubscriber()
    agent = _agent(scripted_backend(text_message('hello')))
    agent.subscribe(stalling)

    task = asyncio.create_task(agent.prompt('hi'))
    await stalling.stalled.wait()
    task.cancel()

    # The terminal publish is shielded: the cancellation waits for the subscriber rather than being thrown into it.
    await asyncio.sleep(0)
    assert not task.done()
    stalling.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task

    # The run itself completed; the cancellation only landed during its terminal publish, which still ran to its end.
    # The completed transcript is what gets applied.
    assert stalling.ended
    assert _message_types(agent) == [llm.UserMessage, llm.AiMessage]
    assert not agent.is_running


@pytest.mark.asyncs('asyncio')
async def test_overlapping_prompt_is_refused():
    backend = _BlockingBackend()
    agent = _agent(backend)

    task = asyncio.create_task(agent.prompt('first'))
    await backend.started.wait()

    with pytest.raises(AgentBusyError):
        await agent.prompt('second')

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert not agent.is_running
    # The refused prompt left no trace.
    assert _message_types(agent) == [llm.UserMessage, InfoAgentMessage]
