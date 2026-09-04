"""
End to end through the real agent, runner, and tools: the model misuses tools, the backend falters, the user interrupts,
and in every case the run recovers or leaves a transcript the next one can build on.
"""
import os.path
import tempfile

import pytest

from omcore import dataclasses as dc
from omcore.asyncs.asynclite import all as asl

from ... import llm
from ...core import processes
from ...core.asyncs.asyncio import AsyncioGroupRunner
from ..agent import Agent
from ..backends import DictBackendManager
from ..exec.ops import ProcessesExecOps
from ..exec.tools.bash import BashTool
from ..permissions.deciders import StaticPermissionDecider
from ..permissions.types import PermissionState
from ..turns.runner import TurnLoopRunner
from ..types.contexts import Context
from ..types.events import AgentEndEvent
from ..types.messages import InfoAgentMessage
from ..types.tools import ToolEnvironment
from ..types.tools import ToolSet
from ..types.turns import AgentEndReason
from ..types.turns import LlmRetryConfig
from ..types.turns import TurnConfig
from .scripted import scripted_backend
from .scripted import text_message
from .scripted import tool_call_message
from .sleeps import RecordingSleeps
from .tools import EchoTool


##


def _bash_tool():
    return BashTool(
        permissions=StaticPermissionDecider(PermissionState.ALLOW),
        exec=ProcessesExecOps(),
    )


async def _agent(backend, tools, *, cwd, scope, sleeps=None, turn_config=None):
    agent = Agent(
        turn_runner=TurnLoopRunner(
            cancellation=asl.asyncio.Cancellation(),
            group_runner=AsyncioGroupRunner(),
            backends=DictBackendManager({llm.ImmediateBackend: {None: backend}}),  # type: ignore[type-abstract]
            sleeps=sleeps,
        ),
    )

    await agent.update_state(lambda s: dc.replace(
        s,
        context=Context(tools=ToolSet(list(tools))),
        tool_env=ToolEnvironment(cwd=cwd, processes=scope),
        turn_config=turn_config,
    ))

    return agent


def _tool_results(msgs):
    return [m for m in msgs if isinstance(m, llm.ToolResultMessage)]


@pytest.mark.asyncs('asyncio')
async def test_agent_recovers_from_misused_tools():
    seen_by_model = []

    def expect(inv):
        seen_by_model.extend(_tool_results(inv.context.messages))

    backend = scripted_backend(
        tool_call_message(llm.ToolCall('t1', 'frobnicate', {})),
        tool_call_message(llm.ToolCall('t2', 'echo', {'text': 'hi', 'loudly': True})),
        tool_call_message(llm.ToolCall('t3', 'bash', {'command': 'echo recovered'})),
        llm.BackendScriptTurn(text_message('done'), expect=expect),
    )

    with tempfile.TemporaryDirectory() as td:
        async with processes.AsyncioProcessManager() as m:
            agent = await _agent(backend, [EchoTool().tool(), _bash_tool().tool()], cwd=td, scope=m.root)

            result = await agent.prompt('please')

    assert result.reason is AgentEndReason.COMPLETED
    assert backend.invocations == 4

    unknown, bad_args, ran = _tool_results(result.new_messages)
    assert unknown.is_error and 'Unknown tool' in unknown.content[0].text
    assert bad_args.is_error and 'Unexpected arguments' in bad_args.content[0].text
    assert not ran.is_error and 'recovered' in ran.content[0].text

    # The model's final call saw all three results, flagged as they were.
    assert [tr.is_error for tr in seen_by_model] == [True, True, False]

    # And the agent's state carries the whole exchange forward.
    assert _tool_results(agent.state.context.messages) == [unknown, bad_args, ran]


@pytest.mark.asyncs('asyncio')
async def test_agent_keeps_tool_side_effects_when_the_backend_then_fails():
    backend = scripted_backend(
        tool_call_message(llm.ToolCall('t1', 'bash', {'command': 'echo written > out.txt'})),
        llm.BackendError('bad request'),
    )

    with tempfile.TemporaryDirectory() as td:
        async with processes.AsyncioProcessManager() as m:
            agent = await _agent(backend, [_bash_tool().tool()], cwd=td, scope=m.root)

            result = await agent.prompt('write it')

            with open(os.path.join(td, 'out.txt')) as f:  # noqa: ASYNC230
                assert f.read().strip() == 'written'

    assert result.reason is AgentEndReason.FAILED
    assert isinstance(result.error, llm.BackendError)

    # The file was written, and the state says so: the call, its result, and the failure after it.
    msgs = agent.state.context.messages
    assert [type(m) for m in msgs] == [llm.UserMessage, llm.AiMessage, llm.ToolResultMessage, InfoAgentMessage]
    assert not msgs[2].is_error
    assert 'bad request' in msgs[3].info


@pytest.mark.asyncs('asyncio')
async def test_agent_retries_a_transient_backend_failure():
    backend = scripted_backend(
        llm.TransientBackendError('overloaded', retry_after_s=2.),
        tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'hi'})),
        llm.TransientBackendError('overloaded again'),
        text_message('done'),
    )
    sleeps = RecordingSleeps()
    ends = []

    with tempfile.TemporaryDirectory() as td:
        async with processes.AsyncioProcessManager() as m:
            echo = EchoTool()
            agent = await _agent(
                backend,
                [echo.tool()],
                cwd=td,
                scope=m.root,
                sleeps=sleeps,
                turn_config=TurnConfig(llm_retry=LlmRetryConfig(initial_delay_s=.5)),
            )
            agent.subscribe(lambda e: ends.append(e) if isinstance(e, AgentEndEvent) else None)

            result = await agent.prompt('go')

    assert result.reason is AgentEndReason.COMPLETED
    assert backend.invocations == 4
    assert echo.calls == ['hi']
    assert sleeps.delays == [2., .5]
    assert [e.reason for e in ends] == [AgentEndReason.COMPLETED]
