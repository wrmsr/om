"""
The loop has its tool invoker carry out every call it executes, and makes of whatever comes back the call's result.
"""
import asyncio
import contextvars

import pytest

from omcore import check
from omcore.asyncs.asynclite import all as asl

from .... import llm
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ...backends import DictBackendManager
from ...tests.scripted import scripted_backend
from ...tests.scripted import text_message
from ...tests.scripted import tool_call_message
from ...tests.tools import EchoTool
from ...tests.tools import bare_tool
from ...tools.invokers import DirectToolInvoker
from ...types.contexts import Context
from ...types.errors import UnknownToolError
from ...types.events import ToolExecutionEndEvent
from ...types.events import ToolExecutionStartEvent
from ...types.states import State
from ...types.tools import ToolInvoker
from ...types.tools import ToolResult
from ...types.tools import ToolSet
from ...types.turns import AgentEndReason
from ...types.turns import TurnParams
from ..loop import TurnLoop
from ..runner import TurnLoopRunner


##


_SURROUNDING_INVOCATION: contextvars.ContextVar = contextvars.ContextVar(f'{__name__}._SURROUNDING_INVOCATION')


class _SurroundingToolInvoker(ToolInvoker):
    """Records each invocation, and surrounds the execution with something it can see: a scope, in miniature."""

    def __init__(self) -> None:
        super().__init__()

        self.invocations: list = []

    async def invoke_tool(self, tool, ctx):
        self.invocations.append((tool, ctx))

        tok = _SURROUNDING_INVOCATION.set(ctx)
        try:
            return await DirectToolInvoker().invoke_tool(tool, ctx)
        finally:
            _SURROUNDING_INVOCATION.reset(tok)


class _RaisingToolInvoker(ToolInvoker):
    async def invoke_tool(self, tool, ctx):
        raise ValueError(f'no invoking {tool.name}')


def _loop(backend, tools, *, tool_invoker=None, subscriber=None):
    return TurnLoop(
        new_messages=[llm.UserMessage('go')],
        context=Context(tools=ToolSet(list(tools))),
        subscriber=subscriber,
        llm_backend=backend,
        tool_invoker=tool_invoker,
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
    )


def _tool_results(msgs):
    return {m.tool_call_id: m for m in msgs if isinstance(m, llm.ToolResultMessage)}


##


@pytest.mark.asyncs('asyncio')
async def test_executed_calls_are_carried_out_by_the_invoker():
    echo = EchoTool()
    echo_tool = echo.tool()
    invoker = _SurroundingToolInvoker()
    events: list = []

    result = await _loop(
        scripted_backend(
            tool_call_message(
                llm.ToolCall('t1', 'echo', {'text': 'a'}),
                llm.ToolCall('t2', 'frobnicate', {}),
                llm.ToolCall('t3', 'echo', {'text': 'b'}),
            ),
            text_message('ok'),
        ),
        [echo_tool],
        tool_invoker=invoker,
        subscriber=events.append,
    ).run()

    assert result.reason is AgentEndReason.COMPLETED
    assert sorted(echo.calls) == ['a', 'b']

    # Each call executed was invoked with the tool it named and the context its execution events carry. A call naming
    # no tool has nothing to invoke, and is the loop's own error result.
    starts = {check.not_none(e.context.llm_tool_call).id: e for e in events if isinstance(e, ToolExecutionStartEvent)}
    invoked = {check.not_none(ctx.llm_tool_call).id: (tool, ctx) for tool, ctx in invoker.invocations}
    assert sorted(invoked) == ['t1', 't3']
    for id, (tool, ctx) in invoked.items():  # noqa
        assert tool is echo_tool
        assert ctx is starts[id].context

    results = _tool_results(result.new_messages)
    assert not results['t1'].is_error and results['t1'].content[0].text == 'a'
    assert results['t2'].is_error
    assert not results['t3'].is_error and results['t3'].content[0].text == 'b'
    [unknown_end] = [e for e in events if isinstance(e, ToolExecutionEndEvent) and e.tool is None]
    assert isinstance(unknown_end.result.error, UnknownToolError)


@pytest.mark.asyncs('asyncio')
async def test_each_execution_runs_inside_its_own_invocation():
    both = asyncio.Event()
    entered: list = []
    seen: list = []

    async def executor(ctx):
        entered.append(ctx)
        if len(entered) == 2:
            both.set()

        # Both executions are parked here at once, each in a task of its own, so each sees its own invocation's
        # surroundings and not the other's.
        await both.wait()

        seen.append(_SURROUNDING_INVOCATION.get(None) is ctx)
        return ToolResult(content=llm.TextContent('ran'))

    invoker = _SurroundingToolInvoker()

    result = await _loop(
        scripted_backend(
            tool_call_message(llm.ToolCall('t1', 'probe', {}), llm.ToolCall('t2', 'probe', {})),
            text_message('ok'),
        ),
        [bare_tool('probe', executor)],
        tool_invoker=invoker,
    ).run()

    assert result.reason is AgentEndReason.COMPLETED
    assert seen == [True, True]
    assert len(invoker.invocations) == 2

    # And nothing of them outlives them.
    assert _SURROUNDING_INVOCATION.get(None) is None


@pytest.mark.asyncs('asyncio')
async def test_whatever_the_invoker_raises_is_an_error_result():
    echo = EchoTool()
    events: list = []

    result = await _loop(
        scripted_backend(
            tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'a'})),
            text_message('ok'),
        ),
        [echo.tool()],
        tool_invoker=_RaisingToolInvoker(),
        subscriber=events.append,
    ).run()

    assert result.reason is AgentEndReason.COMPLETED
    assert not echo.calls

    [tr] = _tool_results(result.new_messages).values()
    assert tr.is_error
    assert 'no invoking echo' in tr.content[0].text

    [end] = [e for e in events if isinstance(e, ToolExecutionEndEvent)]
    assert isinstance(end.result.error, ValueError)


@pytest.mark.asyncs('asyncio')
async def test_the_runner_hands_its_invoker_to_every_turn():
    echo = EchoTool()
    invoker = _SurroundingToolInvoker()

    runner = TurnLoopRunner(
        backends=DictBackendManager.of(scripted_backend(
            tool_call_message(llm.ToolCall('t1', 'echo', {'text': 'a'})),
            text_message('one'),
            tool_call_message(llm.ToolCall('t2', 'echo', {'text': 'b'})),
            text_message('two'),
        )),
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
        tool_invoker=invoker,
    )

    state = State(context=Context(tools=ToolSet([echo.tool()])))
    for text in ['first', 'second']:
        result = await runner.run_turn(TurnParams(
            in_state=state,
            new_messages=[llm.UserMessage(text)],
        ))
        assert result.reason is AgentEndReason.COMPLETED
        state = State(context=result.context)

    assert [check.not_none(ctx.llm_tool_call).id for _, ctx in invoker.invocations] == ['t1', 't2']
    assert echo.calls == ['a', 'b']
