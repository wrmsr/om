"""The loop's handling of tool calls which cannot be executed as asked: every one is an error result the model sees."""
import pytest

from .... import llm
from ...tests.scripted import scripted_backend
from ...tests.scripted import text_message
from ...tests.scripted import tool_call_message
from ...tests.tools import EchoTool
from ...tests.tools import RaisingTool
from ...tests.tools import bare_tool
from ...tools.reflect import reflect_tool_fn
from ...types.contexts import Context
from ...types.errors import UnknownToolError
from ...types.events import ToolExecutionEndEvent
from ...types.events import ToolExecutionStartEvent
from ...types.tools import ToolDescription
from ...types.tools import ToolSet
from ...types.turns import AgentEndReason
from ..loop import TurnLoop


##


def _tool_results(result):
    return [m for m in result.new_messages if isinstance(m, llm.ToolResultMessage)]


async def _run(backend, tools, events=None):
    loop = TurnLoop(
        new_messages=[llm.UserMessage('go')],
        context=Context(tools=ToolSet(list(tools))),
        subscriber=events.append if events is not None else None,
        llm_backend=backend,
    )
    return await loop.run()


@pytest.mark.asyncs('asyncio')
async def test_unknown_tool_is_an_error_result_for_the_model():
    seen = []

    def expect(inv):
        # The model's second call sees the error result of its first.
        seen.append(inv.context.messages[-1])

    backend = scripted_backend(
        tool_call_message(llm.ToolCall('t1', 'frobnicate', {'x': 1})),
        llm.BackendScriptTurn(text_message('ok'), expect=expect),
    )
    events: list = []

    result = await _run(backend, [EchoTool().tool()], events)

    assert result.reason is AgentEndReason.COMPLETED
    assert backend.invocations == 2

    [tr] = _tool_results(result)
    assert tr.tool_call_id == 't1'
    assert tr.tool_name == 'frobnicate'
    assert tr.is_error
    assert 'Unknown tool' in tr.content[0].text
    assert seen == [tr]

    # The call is still surfaced as an execution, with no tool to name but the name the model used.
    [start] = [e for e in events if isinstance(e, ToolExecutionStartEvent)]
    [end] = [e for e in events if isinstance(e, ToolExecutionEndEvent)]
    assert start.tool is None
    assert start.tool_name == 'frobnicate'
    assert isinstance(end.result.error, UnknownToolError)
    assert end.result.error.tool_name == 'frobnicate'


@pytest.mark.asyncs('asyncio')
async def test_bad_arguments_are_an_error_result_for_the_model():
    echo = EchoTool()
    backend = scripted_backend(
        tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'oops', 'loudly': True})),
        tool_call_message(llm.ToolCall('t2', 'echo', {})),
        tool_call_message(llm.ToolCall('t3', 'echo', {'text': 'fine'})),
        text_message('ok'),
    )

    result = await _run(backend, [echo.tool()])

    assert result.reason is AgentEndReason.COMPLETED
    assert echo.calls == ['fine']

    unexpected, missing, fine = _tool_results(result)
    assert unexpected.is_error and 'Unexpected arguments' in unexpected.content[0].text
    assert missing.is_error and 'Missing arguments' in missing.content[0].text
    assert not fine.is_error and fine.content[0].text == 'fine'


@pytest.mark.asyncs('asyncio')
async def test_tool_class_exception_is_an_error_result():
    backend = scripted_backend(
        tool_call_message(llm.ToolCall('t1', 'raiser', {'text': 'kaboom'})),
        text_message('ok'),
    )

    result = await _run(backend, [RaisingTool().tool()])

    assert result.reason is AgentEndReason.COMPLETED
    [tr] = _tool_results(result)
    assert tr.is_error
    assert 'kaboom' in tr.content[0].text


@pytest.mark.asyncs('asyncio')
async def test_bare_executor_exception_is_an_error_result():
    async def executor(ctx):
        raise KeyError('no such thing')

    backend = scripted_backend(
        tool_call_message(llm.ToolCall('t1', 'bare', {})),
        text_message('ok'),
    )
    events: list = []

    result = await _run(backend, [bare_tool('bare', executor)], events)

    assert result.reason is AgentEndReason.COMPLETED
    [tr] = _tool_results(result)
    assert tr.is_error
    assert 'no such thing' in tr.content[0].text

    [end] = [e for e in events if isinstance(e, ToolExecutionEndEvent)]
    assert isinstance(end.result.error, KeyError)


@pytest.mark.asyncs('asyncio')
async def test_reflected_function_exception_is_an_error_result():
    from omcore import dataclasses as dc

    @dc.dataclass(frozen=True)
    class Params:
        n: int

    async def divide(params: Params) -> str:
        return str(1 / params.n)

    tool = reflect_tool_fn(ToolDescription('Divides.', dict(n='The divisor.')), divide)

    backend = scripted_backend(
        tool_call_message(llm.ToolCall('t1', 'divide', {'n': 0})),
        tool_call_message(llm.ToolCall('t2', 'divide', {'n': 2})),
        text_message('ok'),
    )

    result = await _run(backend, [tool])

    assert result.reason is AgentEndReason.COMPLETED
    bad, good = _tool_results(result)
    assert bad.is_error and 'ZeroDivisionError' in bad.content[0].text
    assert not good.is_error and good.content[0].text == '0.5'
