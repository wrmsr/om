"""
Cancellation, told apart and contained: the run's own unwinds after a terminal publish which is shielded from it, and
one which is not the run's own is a failure - of the tool call it landed in, or of the run - never a cancellation.
"""
import asyncio

import pytest

from omcore.asyncs.asynclite import all as asl

from .... import llm
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ...tests.scripted import scripted_backend
from ...tests.scripted import text_message
from ...tests.scripted import tool_call_message
from ...tests.tools import bare_tool
from ...types.contexts import Context
from ...types.events import AgentEndEvent
from ...types.events import ToolExecutionEndEvent
from ...types.events import TurnStartEvent
from ...types.messages import InfoAgentMessage
from ...types.tools import ToolSet
from ...types.turns import AgentEndReason
from ...types.turns import TurnConfig
from ..loop import TurnLoop


##


class _BlockingBackend(llm.ImmediateBackend):
    def __init__(self) -> None:
        super().__init__()

        self._model = llm.Model(key=llm.ModelKey('test', 'blocking'), backend='test')
        self.started = asyncio.Event()
        self._never = asyncio.Event()

    @property
    def model(self) -> llm.Model:
        return self._model

    async def immediate(self, context, options=None):
        self.started.set()
        await self._never.wait()
        raise AssertionError


class _StallingEndSubscriber:
    """Suspends inside the AgentEndEvent until released, recording every event it is handed."""

    def __init__(self) -> None:
        super().__init__()

        self.stalled = asyncio.Event()
        self.release = asyncio.Event()
        self.events: list = []

    async def __call__(self, ev) -> None:
        if isinstance(ev, AgentEndEvent):
            self.stalled.set()
            await self.release.wait()
        self.events.append(ev)

    def end_events(self):
        return [e for e in self.events if isinstance(e, AgentEndEvent)]


def _loop(backend, *, tools=(), subscriber=None):
    return TurnLoop(
        new_messages=[llm.UserMessage('go')],
        context=Context(tools=ToolSet(list(tools))),
        subscriber=subscriber,
        llm_backend=backend,
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
    )


##


@pytest.mark.asyncs('asyncio')
async def test_a_cancellation_from_under_a_tool_is_that_calls_error_result():
    fut = asyncio.get_running_loop().create_future()
    started = asyncio.Event()

    async def executor(ctx):
        started.set()
        return await fut

    events: list = []
    loop = _loop(
        scripted_backend(
            tool_call_message(llm.ToolCall('t1', 'wait', {})),
            text_message('done'),
        ),
        tools=[bare_tool('wait', executor)],
        subscriber=events.append,
    )

    task = asyncio.create_task(loop.run())
    await started.wait()
    fut.cancel()
    result = await task

    # The run was not cancelled, and went on to its end: the call got an error result the model could see.
    assert result.reason is AgentEndReason.COMPLETED
    assert not task.cancelled()

    [tr] = [m for m in result.new_messages if isinstance(m, llm.ToolResultMessage)]
    assert tr.is_error
    assert 'interrupted' in tr.content[0].text

    [end] = [e for e in events if isinstance(e, ToolExecutionEndEvent)]
    assert isinstance(end.result.error, asyncio.CancelledError)


@pytest.mark.asyncs('asyncio')
async def test_a_cancellation_from_under_the_run_fails_it():
    fut = asyncio.get_running_loop().create_future()
    started = asyncio.Event()
    events = []

    async def subscriber(ev):
        events.append(ev)
        if isinstance(ev, TurnStartEvent):
            started.set()
            await fut

    loop = _loop(scripted_backend(text_message('never')), subscriber=subscriber)

    task = asyncio.create_task(loop.run())
    await started.wait()
    fut.cancel()
    result = await task

    # A failure, with the cancellation error as its cause - and a result, not a raise: nothing cancelled the task.
    assert result.reason is AgentEndReason.FAILED
    assert isinstance(result.error, asyncio.CancelledError)
    assert not task.cancelled()

    [end] = [e for e in events if isinstance(e, AgentEndEvent)]
    assert end.reason is AgentEndReason.FAILED
    assert [type(m) for m in end.new_messages] == [llm.UserMessage, InfoAgentMessage]


@pytest.mark.asyncs('asyncio')
async def test_terminal_publish_completes_before_a_cancellation_landing_in_it_is_delivered():
    stalling = _StallingEndSubscriber()
    loop = _loop(scripted_backend(text_message('hello')), subscriber=stalling)

    task = asyncio.create_task(loop.run())
    await stalling.stalled.wait()
    task.cancel()

    # The publish is shielded: the cancellation waits, rather than being thrown into the suspended subscriber.
    await asyncio.sleep(0)
    assert not task.done()

    stalling.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task

    # The subscriber saw the run end - as the completed run it was.
    [end] = stalling.end_events()
    assert end.reason is AgentEndReason.COMPLETED
    assert [type(m) for m in end.new_messages] == [llm.UserMessage, llm.AiMessage]


@pytest.mark.asyncs('asyncio')
async def test_a_second_cancellation_landing_in_the_terminal_publish_waits_too():
    backend = _BlockingBackend()
    stalling = _StallingEndSubscriber()
    loop = _loop(backend, subscriber=stalling)

    task = asyncio.create_task(loop.run())
    await backend.started.wait()
    task.cancel()
    await stalling.stalled.wait()

    # The run is already unwinding from the first cancellation; the second lands in its terminal publish.
    task.cancel()
    await asyncio.sleep(0)
    assert not task.done()

    stalling.release.set()
    with pytest.raises(asyncio.CancelledError):
        await task

    [end] = stalling.end_events()
    assert end.reason is AgentEndReason.CANCELLED
    assert [type(m) for m in end.new_messages] == [llm.UserMessage, InfoAgentMessage]


@pytest.mark.asyncs('asyncio')
async def test_cancel_timeout_cuts_a_hung_terminal_publish_short():
    stalling = _StallingEndSubscriber()
    loop = TurnLoop(
        new_messages=[llm.UserMessage('go')],
        config=TurnConfig(cancel_timeout_s=.05),
        subscriber=stalling,
        llm_backend=scripted_backend(text_message('hello')),
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
    )

    # Nothing releases the subscriber: past the bound the publish is cut short, and the run finishes regardless.
    result = await loop.run()

    assert result.reason is AgentEndReason.COMPLETED
    assert stalling.stalled.is_set()
    assert not stalling.end_events()


@pytest.mark.asyncs('asyncio')
async def test_cancel_timeout_bounds_how_long_a_cancellation_waits():
    backend = _BlockingBackend()
    stalling = _StallingEndSubscriber()
    loop = TurnLoop(
        new_messages=[llm.UserMessage('go')],
        config=TurnConfig(cancel_timeout_s=.05),
        subscriber=stalling,
        llm_backend=backend,
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
    )

    task = asyncio.create_task(loop.run())
    await backend.started.wait()
    task.cancel()
    await stalling.stalled.wait()

    # The cancellation is still what comes out, once the bound is up.
    with pytest.raises(asyncio.CancelledError):
        await task
    assert task.cancelled()
    assert not stalling.end_events()
