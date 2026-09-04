"""A message's tool calls run as one group: concurrently, cancelled together, and in call order on the transcript."""
import asyncio

import pytest

from omcore import check
from omcore.asyncs.asynclite import all as asl

from .... import llm
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ...tests.scripted import scripted_backend
from ...tests.scripted import text_message
from ...tests.scripted import tool_call_message
from ...tests.tools import bare_tool
from ...types.contexts import Context
from ...types.events import AgentEndEvent
from ...types.events import MessageAddedEvent
from ...types.events import ToolExecutionEndEvent
from ...types.events import ToolExecutionStartEvent
from ...types.messages import InfoAgentMessage
from ...types.tools import ToolResult
from ...types.tools import ToolSet
from ...types.turns import AgentEndReason
from ...types.turns import TurnConfig
from ..loop import TurnLoop


##


class _GatedTool:
    """An executor which waits to be released, recording what it sees on the way out."""

    def __init__(self, name: str) -> None:
        super().__init__()

        self.name = name
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.seen: list = []

    async def __call__(self, ctx):
        self.started.set()
        try:
            await self.release.wait()
        except asyncio.CancelledError:
            self.seen.append(('cancelled', check.not_none(asyncio.current_task()).cancelling() > 0))
            raise
        self.seen.append('done')
        return ToolResult(content=llm.TextContent(f'ran {self.name}'))

    def tool(self):
        return bare_tool(self.name, self)


async def _unused_executor(ctx):
    raise AssertionError


def _calls(*names):
    return tool_call_message(*[llm.ToolCall(f't{i + 1}', n, {}) for i, n in enumerate(names)])


def _loop(backend, tools, *, config=None, subscriber=None):
    return TurnLoop(
        new_messages=[llm.UserMessage('go')],
        config=config,
        context=Context(tools=ToolSet(list(tools))),
        subscriber=subscriber,
        llm_backend=backend,
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
    )


def _tool_results(msgs):
    return [m for m in msgs if isinstance(m, llm.ToolResultMessage)]


async def _settle(until, *, max_steps=20):
    for _ in range(max_steps):
        if until():
            return
        await asyncio.sleep(0)
    raise AssertionError


##


@pytest.mark.asyncs('asyncio')
async def test_calls_run_concurrently_and_results_keep_call_order():
    a, b = _GatedTool('a'), _GatedTool('b')
    events: list = []
    loop = _loop(
        scripted_backend(_calls('a', 'b'), text_message('done')),
        [a.tool(), b.tool()],
        subscriber=events.append,
    )

    task = asyncio.create_task(loop.run())

    # Both are running before either has finished.
    await a.started.wait()
    await b.started.wait()

    b.release.set()
    await _settle(lambda: b.seen == ['done'])
    a.release.set()
    result = await task

    assert result.reason is AgentEndReason.COMPLETED
    assert [m.tool_call_id for m in _tool_results(result.new_messages)] == ['t1', 't2']

    # The executions ended in the order they finished; the transcript kept the model's order.
    ends = [check.not_none(e.context.llm_tool_call).id for e in events if isinstance(e, ToolExecutionEndEvent)]
    assert ends == ['t2', 't1']
    added = [e for e in events if isinstance(e, MessageAddedEvent)]
    assert [e.index for e in added] == list(range(len(added)))
    assert [m.tool_call_id for m in _tool_results([e.message for e in added])] == ['t1', 't2']


@pytest.mark.asyncs('asyncio')
async def test_cancellation_reaches_every_call_before_the_terminal_event():
    a, b = _GatedTool('a'), _GatedTool('b')
    at_end: list = []

    def subscriber(ev):
        if isinstance(ev, AgentEndEvent):
            at_end.append((ev, list(a.seen), list(b.seen)))

    loop = _loop(scripted_backend(_calls('a', 'b')), [a.tool(), b.tool()], subscriber=subscriber)

    task = asyncio.create_task(loop.run())
    await a.started.wait()
    await b.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Each execution unwound inside its own task, as a cancellation of that task - which is what a parked permission
    # ask judges by - and had done so by the time the run's end was published.
    [(end, a_seen, b_seen)] = at_end
    assert a_seen == [('cancelled', True)]
    assert b_seen == [('cancelled', True)]

    assert end.reason is AgentEndReason.CANCELLED
    msgs = end.new_messages
    assert [type(m) for m in msgs] == [
        llm.UserMessage,
        llm.AiMessage,
        llm.ToolResultMessage,
        llm.ToolResultMessage,
        InfoAgentMessage,
    ]
    assert [m.tool_call_id for m in _tool_results(msgs)] == ['t1', 't2']
    assert all(m.is_error and 'cancelled' in m.content[0].text for m in _tool_results(msgs))


@pytest.mark.asyncs('asyncio')
async def test_completed_calls_keep_their_results_when_the_batch_is_cancelled():
    a, b = _GatedTool('a'), _GatedTool('b')
    events: list = []
    loop = _loop(scripted_backend(_calls('a', 'b')), [a.tool(), b.tool()], subscriber=events.append)

    task = asyncio.create_task(loop.run())
    await a.started.wait()
    await b.started.wait()
    a.release.set()
    await _settle(lambda: a.seen == ['done'])
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    [end] = [e for e in events if isinstance(e, AgentEndEvent)]
    msgs = end.new_messages
    assert [type(m) for m in msgs] == [
        llm.UserMessage,
        llm.AiMessage,
        llm.ToolResultMessage,
        llm.ToolResultMessage,
        InfoAgentMessage,
    ]

    # The call which completed kept its real result; only the one cut short was repaired.
    ra, rb = _tool_results(msgs)
    assert ra.tool_call_id == 't1' and not ra.is_error and ra.content[0].text == 'ran a'
    assert rb.tool_call_id == 't2' and rb.is_error and 'cancelled' in rb.content[0].text

    # That result landed on the way out, unannounced: it reaches subscribers only through the terminal event.
    announced = [e.message for e in events if isinstance(e, MessageAddedEvent)]
    assert [type(m) for m in announced] == [llm.UserMessage, llm.AiMessage]
    assert tuple(msgs[:2]) == tuple(announced)


@pytest.mark.asyncs('asyncio')
async def test_a_cancellation_from_under_one_call_leaves_the_others_running():
    fut = asyncio.get_running_loop().create_future()
    b = _GatedTool('b')

    async def stray(ctx):
        return await fut

    loop = _loop(
        scripted_backend(_calls('stray', 'b'), text_message('done')),
        [bare_tool('stray', stray), b.tool()],
    )

    task = asyncio.create_task(loop.run())
    await b.started.wait()
    fut.cancel()
    await asyncio.sleep(0)
    b.release.set()
    result = await task

    assert result.reason is AgentEndReason.COMPLETED
    rs, rb = _tool_results(result.new_messages)
    assert rs.is_error and 'interrupted' in rs.content[0].text
    assert not rb.is_error
    assert b.seen == ['done']


@pytest.mark.asyncs('asyncio')
async def test_a_failure_in_one_call_cancels_the_rest_and_fails_the_run():
    a = _GatedTool('a')
    events: list = []

    def subscriber(ev):
        # An executor's own exceptions are results; a subscriber raising out of an execution is a real failure.
        if isinstance(ev, ToolExecutionStartEvent) and ev.tool_name == 'boom':
            raise RuntimeError('subscriber boom')
        events.append(ev)

    loop = _loop(
        scripted_backend(_calls('a', 'boom')),
        [a.tool(), bare_tool('boom', _unused_executor)],
        subscriber=subscriber,
    )

    result = await loop.run()

    assert result.reason is AgentEndReason.FAILED
    assert isinstance(result.error, ExceptionGroup)
    assert [type(e) for e in result.error.exceptions] == [RuntimeError]

    # The other call was cancelled along with the batch, before the run ended.
    assert a.seen == [('cancelled', True)]
    [end] = [e for e in events if isinstance(e, AgentEndEvent)]
    assert end.reason is AgentEndReason.FAILED
    assert all(m.is_error and 'failed' in m.content[0].text for m in _tool_results(end.new_messages))


@pytest.mark.asyncs('asyncio')
async def test_steering_skips_pending_runs_calls_one_at_a_time():
    a, b = _GatedTool('a'), _GatedTool('b')
    loop = _loop(
        scripted_backend(_calls('a', 'b'), text_message('done')),
        [a.tool(), b.tool()],
        config=TurnConfig(steering_skips_pending_tool_calls=True),
    )

    task = asyncio.create_task(loop.run())
    await a.started.wait()
    for _ in range(5):
        await asyncio.sleep(0)
    assert not b.started.is_set()

    a.release.set()
    await b.started.wait()
    b.release.set()
    result = await task

    assert result.reason is AgentEndReason.COMPLETED
    assert [(m.tool_call_id, m.is_error) for m in _tool_results(result.new_messages)] == [('t1', False), ('t2', False)]


@pytest.mark.asyncs('asyncio')
async def test_completed_calls_keep_their_results_when_the_batch_fails():
    a, b = _GatedTool('a'), _GatedTool('b')
    go = asyncio.Event()
    events: list = []

    def subscriber(ev):
        # An executor's own exceptions are results; the failure here is a subscriber raising as the call ends.
        if isinstance(ev, ToolExecutionEndEvent) and ev.tool_name == 'boom':
            raise RuntimeError('subscriber boom')
        events.append(ev)

    async def boom(ctx):
        await go.wait()
        return ToolResult(content=llm.TextContent('ran boom'))

    loop = _loop(
        scripted_backend(_calls('a', 'b', 'boom')),
        [a.tool(), b.tool(), bare_tool('boom', boom)],
        subscriber=subscriber,
    )

    task = asyncio.create_task(loop.run())
    await a.started.wait()
    await b.started.wait()
    a.release.set()
    await _settle(lambda: a.seen == ['done'])
    go.set()
    result = await task

    assert result.reason is AgentEndReason.FAILED

    # The call which completed before the failure kept its real result; the rest were repaired.
    ra, rb, rboom = _tool_results(result.new_messages)
    assert ra.tool_call_id == 't1' and not ra.is_error and ra.content[0].text == 'ran a'
    assert rb.tool_call_id == 't2' and rb.is_error and 'failed' in rb.content[0].text
    assert rboom.tool_call_id == 't3' and rboom.is_error and 'failed' in rboom.content[0].text
    assert b.seen == [('cancelled', True)]
