"""How the loop ends: every stop reason, and the turn limit."""
import pytest

from .... import llm
from ...tests.scripted import scripted_backend
from ...tests.scripted import text_message
from ...tests.scripted import tool_call_message
from ...tests.tools import EchoTool
from ...types.contexts import Context
from ...types.errors import ErrorStopReasonError
from ...types.events import ToolExecutionEndEvent
from ...types.events import TurnEndEvent
from ...types.messages import InfoAgentMessage
from ...types.tools import ToolSet
from ...types.turns import AgentEndReason
from ...types.turns import TurnConfig
from ..loop import TurnLoop


##


def _tool_results(result):
    return [m for m in result.new_messages if isinstance(m, llm.ToolResultMessage)]


async def _run(backend, tools, *, config=None, events=None):
    loop = TurnLoop(
        new_messages=[llm.UserMessage('go')],
        config=config,
        context=Context(tools=ToolSet(list(tools))),
        subscriber=events.append if events is not None else None,
        llm_backend=backend,
    )
    return await loop.run()


@pytest.mark.asyncs('asyncio')
async def test_error_stop_reason_fails_the_run_and_keeps_the_message():
    refusal = text_message('I will not.', stop_reason='error')
    events: list = []

    result = await _run(scripted_backend(refusal), [], events=events)

    assert result.reason is AgentEndReason.FAILED
    assert isinstance(result.error, ErrorStopReasonError)
    assert result.error.message == refusal

    # The refusal stays in the transcript with the failure noted after it, and the turn was still closed.
    assert [type(m) for m in result.new_messages] == [llm.UserMessage, llm.AiMessage, InfoAgentMessage]
    assert len([e for e in events if isinstance(e, TurnEndEvent)]) == 1


@pytest.mark.asyncs('asyncio')
async def test_length_stop_reason_ends_the_run_without_executing_calls():
    echo = EchoTool()
    events: list = []

    result = await _run(
        scripted_backend(tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'trunc'}), stop_reason='length')),
        [echo.tool()],
        events=events,
    )

    assert result.reason is AgentEndReason.LENGTH
    assert result.error is None
    assert echo.calls == []
    assert not [e for e in events if isinstance(e, ToolExecutionEndEvent)]

    # The untrusted call gets a result saying it was never run, so the transcript stays well-formed.
    [tr] = _tool_results(result)
    assert tr.tool_call_id == 't1'
    assert tr.is_error
    assert 'token limit' in tr.content[0].text


@pytest.mark.asyncs('asyncio')
async def test_length_stop_reason_without_calls():
    result = await _run(scripted_backend(text_message('half a thou', stop_reason='length')), [])

    assert result.reason is AgentEndReason.LENGTH
    assert [type(m) for m in result.new_messages] == [llm.UserMessage, llm.AiMessage]


@pytest.mark.parametrize('stop_reason', ['stop', None, 'tool_use'])
@pytest.mark.asyncs('asyncio')
async def test_tool_calls_are_executed_on_presence_not_stop_reason(stop_reason):
    echo = EchoTool()
    backend = scripted_backend(
        tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'hi'}), stop_reason=stop_reason),
        text_message('ok'),
    )

    result = await _run(backend, [echo.tool()])

    assert result.reason is AgentEndReason.COMPLETED
    assert echo.calls == ['hi']
    assert backend.invocations == 2


@pytest.mark.asyncs('asyncio')
async def test_tool_use_stop_reason_without_calls_completes():
    result = await _run(scripted_backend(text_message('done', stop_reason='tool_use')), [])

    assert result.reason is AgentEndReason.COMPLETED


@pytest.mark.asyncs('asyncio')
async def test_max_turns_leaves_pending_calls_unexecuted():
    echo = EchoTool()
    backend = scripted_backend(
        tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'one'})),
        tool_call_message(llm.ToolCall('t2', 'echo', {'text': 'two'})),
        text_message('never reached'),
    )

    result = await _run(backend, [echo.tool()], config=TurnConfig(max_turns=2))

    assert result.reason is AgentEndReason.MAX_TURNS
    assert result.error is None
    assert backend.invocations == 2
    assert echo.calls == ['one']

    done, pending = _tool_results(result)
    assert not done.is_error
    assert pending.tool_call_id == 't2'
    assert pending.is_error
    assert 'turn limit' in pending.content[0].text


@pytest.mark.asyncs('asyncio')
async def test_max_turns_is_not_reached_by_a_completing_run():
    echo = EchoTool()
    backend = scripted_backend(
        tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'one'})),
        text_message('done'),
    )

    result = await _run(backend, [echo.tool()], config=TurnConfig(max_turns=2))

    assert result.reason is AgentEndReason.COMPLETED
    assert echo.calls == ['one']
