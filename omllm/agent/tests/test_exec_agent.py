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
from ..types.tools import ToolEnvironment
from ..types.tools import ToolSet
from ..types.turns import AgentEndReason


def _scripted_backend():
    model = llm.Model(key=llm.ModelKey('scripted', 'test'), backend='scripted')
    script = llm.BackendScript([
        llm.BackendScriptTurn(llm.AiMessage(
            [llm.ToolCall(id='t1', name='bash', args={'command': 'echo integration-ok; echo warn >&2; exit 5'})],
            stop_reason='tool_use',
        )),
        llm.BackendScriptTurn(llm.AiMessage(
            [llm.TextContent('all done')],
            stop_reason='stop',
        )),
    ])
    return llm.ScriptedImmediateBackend(model, script)


async def _run_agent(td, m):
    backend = _scripted_backend()
    agent = Agent(
        turn_runner=TurnLoopRunner(
            cancellation=asl.asyncio.Cancellation(),
            group_runner=AsyncioGroupRunner(),
            backends=DictBackendManager({llm.ImmediateBackend: {None: backend}}),  # type: ignore[type-abstract]
        ),
    )

    bash = BashTool(
        permissions=StaticPermissionDecider(PermissionState.ALLOW),
        exec=ProcessesExecOps(),
    )

    await agent.update_state(lambda s: dc.replace(
        s,
        context=Context(tools=ToolSet([bash.tool()])),
        tool_env=ToolEnvironment(cwd=td, processes=m.root),
    ))

    ended: list = []
    agent.subscribe(lambda e: ended.append(e) if isinstance(e, AgentEndEvent) else None)

    await agent.prompt('please run the echo')
    assert ended[-1].reason is AgentEndReason.COMPLETED
    return ended[-1].new_messages


@pytest.mark.asyncs('asyncio')
async def test_agent_runs_bash_tool_through_procs():
    with tempfile.TemporaryDirectory() as td:
        async with processes.AsyncioProcessManager() as m:
            new_messages = await _run_agent(td, m)

            tool_results = [msg for msg in new_messages if isinstance(msg, llm.ToolResultMessage)]
            assert len(tool_results) == 1
            assert tool_results[0].tool_name == 'bash'

            # real subprocess output flowed back into the conversation, with stderr + exit-code framing.
            text = tool_results[0].content[0].text
            assert 'integration-ok' in text
            assert 'warn' in text
            assert 'exit code 5' in text

            # the final assistant turn is present, and nothing leaked.
            ai_texts = [
                c.text
                for msg in new_messages if isinstance(msg, llm.AiMessage)
                for c in msg.content if isinstance(c, llm.TextContent)
            ]
            assert 'all done' in ai_texts
            assert not m.processes
