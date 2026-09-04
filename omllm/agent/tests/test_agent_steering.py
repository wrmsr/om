"""The agent's side of steering and follow-ups."""
import pytest

from omcore import dataclasses as dc

from ... import llm
from ..agent import Agent
from ..backends import DictBackendManager
from ..turns.runner import TurnLoopRunner
from ..types.contexts import Context
from ..types.tools import ToolResult
from ..types.tools import ToolSet
from ..types.turns import AgentEndReason
from .scripted import scripted_backend
from .scripted import text_message
from .scripted import tool_call_message
from .tools import bare_tool


##


def _agent(backend):
    return Agent(
        turn_runner=TurnLoopRunner(
            backends=DictBackendManager({llm.ImmediateBackend: {None: backend}}),  # type: ignore[type-abstract]
        ),
    )


def _message_types(agent):
    return [type(m) for m in agent.state.context.messages or []]


@pytest.mark.asyncs('asyncio')
async def test_steer_while_idle_lands_at_the_start_of_the_next_prompt():
    seen: list = []

    def expect(inv):
        seen.append(inv.context.messages)

    agent = _agent(scripted_backend(llm.BackendScriptTurn(text_message('ok'), expect=expect)))

    agent.steer('psst')
    result = await agent.prompt('hi')

    assert result.reason is AgentEndReason.COMPLETED
    assert _message_types(agent) == [llm.UserMessage, llm.UserMessage, llm.AiMessage]
    assert agent.state.context.messages[1].content == 'psst'

    # And the model saw the two as one turn.
    [msgs] = seen
    assert [m.content for m in msgs if isinstance(m, llm.UserMessage)] == ['hi\n\npsst']


@pytest.mark.asyncs('asyncio')
async def test_follow_up_during_a_run_continues_it():
    backend = scripted_backend(
        tool_call_message(llm.ToolCall('t1', 'act', {})),
        text_message('done'),
        text_message('done again'),
    )
    agent = _agent(backend)

    async def executor(ctx):
        agent.follow_up('one more thing')
        return ToolResult(content=llm.TextContent('ran'))

    await agent.update_state(lambda s: dc.replace(s, context=Context(tools=ToolSet([bare_tool('act', executor)]))))

    result = await agent.prompt('go')

    assert result.reason is AgentEndReason.COMPLETED
    assert backend.invocations == 3
    assert _message_types(agent) == [
        llm.UserMessage,
        llm.AiMessage,
        llm.ToolResultMessage,
        llm.AiMessage,
        llm.UserMessage,
        llm.AiMessage,
    ]
    assert agent.state.context.messages[4].content == 'one more thing'
