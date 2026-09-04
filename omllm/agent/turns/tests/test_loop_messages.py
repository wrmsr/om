"""Messages are announced as they land; what an interrupted run appends on its way out rides the terminal event."""
import asyncio

import pytest

from omcore.asyncs.asynclite import all as asl

from .... import llm
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ...tests.scripted import scripted_backend
from ...tests.scripted import text_message
from ...tests.scripted import tool_call_message
from ...tests.tools import EchoTool
from ...tests.tools import bare_tool
from ...types.contexts import Context
from ...types.events import AgentEndEvent
from ...types.events import MessageAddedEvent
from ...types.messages import InfoAgentMessage
from ...types.tools import ToolSet
from ..loop import TurnLoop


##


def _added(events):
    return [e for e in events if isinstance(e, MessageAddedEvent)]


class _BlockingExecutor:
    def __init__(self) -> None:
        super().__init__()

        self.started = asyncio.Event()
        self._never = asyncio.Event()

    async def __call__(self, ctx):
        self.started.set()
        await self._never.wait()
        raise AssertionError


@pytest.mark.asyncs('asyncio')
async def test_messages_are_announced_in_order_with_indices():
    echo = EchoTool()
    events: list = []
    loop = TurnLoop(
        new_messages=[llm.UserMessage('go')],
        context=Context(tools=ToolSet([echo.tool()])),
        subscriber=events.append,
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
        llm_backend=scripted_backend(
            tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'hi'})),
            text_message('done'),
        ),
    )

    result = await loop.run()

    added = _added(events)
    assert [e.index for e in added] == [0, 1, 2, 3]
    assert [e.message for e in added] == list(result.new_messages)
    assert [type(e.message) for e in added] == [
        llm.UserMessage,
        llm.AiMessage,
        llm.ToolResultMessage,
        llm.AiMessage,
    ]

    # All of them ahead of the terminal event.
    [end] = [e for e in events if isinstance(e, AgentEndEvent)]
    assert events.index(added[-1]) < events.index(end)


@pytest.mark.asyncs('asyncio')
async def test_repair_messages_are_not_announced_but_carried():
    executor = _BlockingExecutor()
    events: list = []
    loop = TurnLoop(
        new_messages=[llm.UserMessage('go')],
        context=Context(tools=ToolSet([bare_tool('block', executor)])),
        subscriber=events.append,
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
        llm_backend=scripted_backend(tool_call_message(llm.ToolCall('t1', 'block', {}))),
    )

    task = asyncio.create_task(loop.run())
    await executor.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    added = _added(events)
    assert [type(e.message) for e in added] == [llm.UserMessage, llm.AiMessage]

    [end] = [e for e in events if isinstance(e, AgentEndEvent)]
    assert list(end.new_messages[:2]) == [e.message for e in added]
    assert [type(m) for m in end.new_messages[2:]] == [llm.ToolResultMessage, InfoAgentMessage]
