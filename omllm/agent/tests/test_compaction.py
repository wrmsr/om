"""Compaction on request: the agent held for it, its state updated with the result, and what changed reported."""
import asyncio

import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore.asyncs.asynclite import all as asl

from ... import llm
from ...core.asyncs.asyncio import AsyncioGroupRunner
from ..agent import Agent
from ..backends import DictBackendManager
from ..compaction import ContextCompactionRunner
from ..lifecycle.compactors import ContextCompactor
from ..lifecycle.managers import StandardContextLifecycleManager
from ..lifecycle.summarizing import SummarizingContextCompactor
from ..turns.runner import TurnLoopRunner
from ..types.contexts import Context
from ..types.errors import AgentBusyError
from ..types.errors import NoContextCompactorError
from ..types.events import StateUpdateEvent
from ..types.lifecycle import ContextProjection
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


def _backends(backend):
    return DictBackendManager({llm.ImmediateBackend: {None: backend}})  # type: ignore[type-abstract]


async def _agent(backend, *messages):
    agent = Agent(
        turn_runner=TurnLoopRunner(
            cancellation=asl.asyncio.Cancellation(),
            group_runner=AsyncioGroupRunner(),
            backends=_backends(backend),
        ),
    )
    if messages:
        await agent.update_state(lambda s: dc.replace(s, context=Context(messages=list(messages))))
    return agent


def _runner(backend, compactor=None):
    return ContextCompactionRunner(
        backends=_backends(backend),
        context_lifecycle_manager=StandardContextLifecycleManager(compactor=compactor),
    )


def _summarizer():
    return SummarizingContextCompactor(config=SummarizingContextCompactor.Config(
        keep_recent_tokens=100,
        max_summary_tokens=50,
    ))


_MESSAGES = (
    llm.UserMessage('x' * 2_000),
    llm.AiMessage([llm.TextContent('ok')]),
    llm.UserMessage('y' * 2_000),
    llm.AiMessage([llm.TextContent('ok')]),
)


@pytest.mark.asyncs('asyncio')
async def test_compaction_on_request_updates_the_state_and_reports_what_changed():
    seen: list = []

    def expect(invocation):
        seen.append(invocation.context)

    backend = scripted_backend(llm.BackendScriptTurn(text_message('Summary.'), expect=expect))
    agent = await _agent(backend, *_MESSAGES)
    updates: list = []
    agent.subscribe(lambda e: updates.append(e) if isinstance(e, StateUpdateEvent) else None)

    reduction = await _runner(backend, _summarizer()).run_compaction(agent, instructions='Keep the names.')

    assert reduction is not None
    assert reduction.reason == 'manual'
    assert reduction.compacted
    assert backend.invocations == 1
    assert not agent.is_running

    projection = check.not_none(agent.state.context.projection)
    assert projection.summary == 'Summary.'
    assert projection.first_kept_message_index == 3
    assert tuple(agent.state.context.messages or ()) == _MESSAGES

    [update] = updates
    assert update.new_state.context.projection == projection

    [request] = seen
    request_text = check.isinstance(check.isinstance((request.messages or [])[0], llm.UserMessage).content, str)
    assert 'Keep the names.' in request_text

    # Once more, and there is nothing ahead of the kept tail to summarize.
    assert await _runner(backend, _summarizer()).run_compaction(agent) is None
    assert backend.invocations == 1


class _HoldingCompactor(ContextCompactor):
    """Sees for itself that the agent is held while it works."""

    def __init__(self, agent: Agent) -> None:
        super().__init__()

        self._agent = agent

        self.was_running: bool | None = None

    async def compact(self, context, *, backend, target_tokens, reason, instructions=None):
        self.was_running = self._agent.is_running

        with pytest.raises(AgentBusyError):
            await self._agent.prompt('not now')

        return ContextProjection(summary='Held.', first_kept_message_index=1)


@pytest.mark.asyncs('asyncio')
async def test_the_agent_is_held_against_prompts_for_the_duration():
    backend = scripted_backend(text_message('never'))
    agent = await _agent(backend, *_MESSAGES)
    compactor = _HoldingCompactor(agent)

    reduction = await _runner(backend, compactor).run_compaction(agent)

    assert reduction is not None
    assert compactor.was_running
    assert not agent.is_running
    assert check.not_none(agent.state.context.projection).summary == 'Held.'
    assert backend.invocations == 0


@pytest.mark.asyncs('asyncio')
async def test_compaction_during_a_run_is_refused():
    backend = _BlockingBackend()
    agent = await _agent(backend)

    task = asyncio.create_task(agent.prompt('first'))
    await backend.started.wait()

    with pytest.raises(AgentBusyError):
        await _runner(backend, _summarizer()).run_compaction(agent)

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert not agent.is_running


@pytest.mark.asyncs('asyncio')
async def test_without_a_compactor_there_is_nothing_to_run():
    backend = scripted_backend(text_message('never'))
    agent = await _agent(backend, *_MESSAGES)

    with pytest.raises(NoContextCompactorError):
        await _runner(backend).run_compaction(agent)

    assert not agent.is_running
    assert agent.state.context.projection is None
