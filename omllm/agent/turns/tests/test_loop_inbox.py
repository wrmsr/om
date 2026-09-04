"""Steering and follow-ups: taken at the loop's own pace, never mid-call."""
import pytest

from omcore import check

from .... import llm
from ...tests.scripted import scripted_backend
from ...tests.scripted import text_message
from ...tests.scripted import tool_call_message
from ...tests.tools import bare_tool
from ...types.contexts import Context
from ...types.tools import ToolResult
from ...types.tools import ToolSet
from ...types.turns import AgentEndReason
from ...types.turns import TurnConfig
from ..inboxes import ListTurnInbox
from ..loop import TurnLoop


##


def _tool_results(result):
    return [m for m in result.new_messages if isinstance(m, llm.ToolResultMessage)]


def _interjecting_tool(inbox, text, *, on='1'):
    """A tool during whose execution the user interjects - once, on the call with the given argument."""

    async def executor(ctx):
        if ctx.args['n'] == on:
            inbox.add_steering(llm.UserMessage(text))
        return ToolResult(content=llm.TextContent(f'ran {ctx.args["n"]}'))

    return bare_tool('act', executor)


def _calls(*ns):
    return tool_call_message(*[llm.ToolCall(f't{n}', 'act', {'n': n}) for n in ns])


async def _run(backend, tools, inbox, *, config=None):
    loop = TurnLoop(
        new_messages=[llm.UserMessage('go')],
        config=config,
        context=Context(tools=ToolSet(list(tools))),
        llm_backend=backend,
        inbox=inbox,
    )
    return await loop.run()


@pytest.mark.asyncs('asyncio')
async def test_steering_is_delivered_after_the_batch_by_default():
    inbox = ListTurnInbox()
    seen: list = []

    def expect(inv):
        seen.append(inv.context.messages)

    backend = scripted_backend(
        _calls('1', '2'),
        llm.BackendScriptTurn(text_message('done'), expect=expect),
    )

    result = await _run(backend, [_interjecting_tool(inbox, 'wait!')], inbox)

    assert result.reason is AgentEndReason.COMPLETED
    assert [tr.is_error for tr in _tool_results(result)] == [False, False]

    # The model's next call saw the whole batch's results, then the steering.
    [msgs] = seen
    assert [type(m) for m in msgs] == [
        llm.UserMessage,
        llm.AiMessage,
        llm.ToolResultMessage,
        llm.ToolResultMessage,
        llm.UserMessage,
    ]
    assert msgs[-1].content == 'wait!'
    assert not inbox.has_steering()


@pytest.mark.asyncs('asyncio')
async def test_steering_can_cut_the_batch_short():
    inbox = ListTurnInbox()
    backend = scripted_backend(
        _calls('1', '2', '3'),
        text_message('done'),
    )

    result = await _run(
        backend,
        [_interjecting_tool(inbox, 'wait!')],
        inbox,
        config=TurnConfig(steering_skips_pending_tool_calls=True),
    )

    assert result.reason is AgentEndReason.COMPLETED

    ran, skipped_a, skipped_b = _tool_results(result)
    assert not ran.is_error
    assert skipped_a.is_error and 'interjected' in skipped_a.content[0].text
    assert skipped_b.is_error and skipped_b.tool_call_id == 't3'

    # The steering follows the batch's results, ahead of the model's next message.
    msgs = list(result.new_messages)
    assert [type(m) for m in msgs[5:]] == [llm.UserMessage, llm.AiMessage]
    assert msgs[5].content == 'wait!'


@pytest.mark.asyncs('asyncio')
async def test_steering_pending_at_the_start_is_delivered_first():
    inbox = ListTurnInbox()
    inbox.add_steering(llm.UserMessage('by the way'))
    seen: list = []

    def expect(inv):
        seen.append(inv.context.messages)

    result = await _run(scripted_backend(llm.BackendScriptTurn(text_message('ok'), expect=expect)), [], inbox)

    assert result.reason is AgentEndReason.COMPLETED
    [msgs] = seen
    assert [m.content for m in msgs if isinstance(m, llm.UserMessage)] == ['go\n\nby the way']
    assert [type(m) for m in result.new_messages] == [llm.UserMessage, llm.UserMessage, llm.AiMessage]


@pytest.mark.asyncs('asyncio')
async def test_follow_up_extends_a_completed_run():
    inbox = ListTurnInbox()
    inbox.add_follow_ups(llm.UserMessage('and then?'))
    backend = scripted_backend(text_message('first'), text_message('second'))

    result = await _run(backend, [], inbox)

    assert result.reason is AgentEndReason.COMPLETED
    assert backend.invocations == 2
    msgs = list(result.new_messages)
    assert [type(m) for m in msgs] == [llm.UserMessage, llm.AiMessage, llm.UserMessage, llm.AiMessage]
    assert msgs[2].content == 'and then?'


@pytest.mark.asyncs('asyncio')
async def test_follow_up_waits_when_the_turn_limit_is_reached():
    inbox = ListTurnInbox()
    inbox.add_follow_ups(llm.UserMessage('and then?'))
    backend = scripted_backend(text_message('first'), text_message('never'))

    result = await _run(backend, [], inbox, config=TurnConfig(max_turns=1))

    assert result.reason is AgentEndReason.COMPLETED
    assert backend.invocations == 1
    assert [check.isinstance(m, llm.UserMessage).content for m in inbox.take_follow_ups()] == ['and then?']


@pytest.mark.asyncs('asyncio')
async def test_leftovers_wait_when_the_run_ends_short():
    inbox = ListTurnInbox()
    inbox.add_follow_ups(llm.UserMessage('and then?'))

    result = await _run(scripted_backend(text_message('half', stop_reason='length')), [], inbox)

    assert result.reason is AgentEndReason.LENGTH
    assert [check.isinstance(m, llm.UserMessage).content for m in inbox.take_follow_ups()] == ['and then?']
