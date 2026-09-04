"""The bash tool end to end through the loop: streamed output, and the structured details on the result."""
import tempfile

import pytest

from omcore import check
from omcore.asyncs.asynclite import all as asl

from ..... import llm
from .....core import processes
from .....core.asyncs.asyncio import AsyncioGroupRunner
from ....permissions.deciders import StaticPermissionDecider
from ....permissions.types import PermissionState
from ....tests.scripted import scripted_backend
from ....tests.scripted import text_message
from ....tests.scripted import tool_call_message
from ....turns.loop import TurnLoop
from ....types.contexts import Context
from ....types.events import ToolExecutionEndEvent
from ....types.events import ToolExecutionUpdateEvent
from ....types.progress import OutputToolProgressUpdate
from ....types.tools import ToolEnvironment
from ....types.tools import ToolSet
from ....types.turns import AgentEndReason
from ...ops import ProcessesExecOps
from ..bash import BashTool
from ..details import ExecToolResultDetails


##


async def _run(command, *, timeout_s=None):
    events: list = []
    args = {'command': command, **({'timeout_s': timeout_s} if timeout_s is not None else {})}

    with tempfile.TemporaryDirectory() as td:
        async with processes.AsyncioProcessManager() as m:
            tool = BashTool(
                permissions=StaticPermissionDecider(PermissionState.ALLOW),
                exec=ProcessesExecOps(),
            )

            loop = TurnLoop(
                new_messages=[llm.UserMessage('go')],
                context=Context(tools=ToolSet([tool.tool()])),
                subscriber=events.append,
                cancellation=asl.asyncio.Cancellation(),
                group_runner=AsyncioGroupRunner(),
                llm_backend=scripted_backend(
                    tool_call_message(llm.ToolCall('t1', 'bash', args)),
                    text_message('done'),
                ),
                tool_env=ToolEnvironment(cwd=td, processes=m.root),
            )

            result = await loop.run()

    return result, events


def _end_details(events):
    [end] = [e for e in events if isinstance(e, ToolExecutionEndEvent)]
    assert end.result.error is None
    return end.result.details


@pytest.mark.asyncs('asyncio')
async def test_bash_streams_output_and_reports_details():
    result, events = await _run('echo out-one; echo err-two >&2; echo out-three')

    assert result.reason is AgentEndReason.COMPLETED

    updates = [
        check.isinstance(e.update, OutputToolProgressUpdate)
        for e in events
        if isinstance(e, ToolExecutionUpdateEvent)
    ]
    assert updates
    stdout = ''.join(u.text for u in updates if u.stream == 'stdout')
    stderr = ''.join(u.text for u in updates if u.stream == 'stderr')
    assert 'out-one' in stdout and 'out-three' in stdout
    assert 'err-two' in stderr

    details = _end_details(events)
    assert isinstance(details, ExecToolResultDetails)
    assert details.rc == 0
    assert 'out-one' in details.stdout
    assert 'err-two' in details.stderr
    assert not details.timed_out

    # The model-facing text is as before.
    [tr] = [m for m in result.new_messages if isinstance(m, llm.ToolResultMessage)]
    assert 'out-one' in tr.content[0].text and 'err-two' in tr.content[0].text


@pytest.mark.asyncs('asyncio')
async def test_bash_times_out_while_streaming():
    result, events = await _run('echo started; sleep 30', timeout_s=.3)

    assert result.reason is AgentEndReason.COMPLETED

    details = _end_details(events)
    assert isinstance(details, ExecToolResultDetails)
    assert details.timed_out
    assert 'started' in details.stdout

    [tr] = [m for m in result.new_messages if isinstance(m, llm.ToolResultMessage)]
    assert 'timed out' in tr.content[0].text
