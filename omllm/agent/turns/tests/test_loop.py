import asyncio

import pytest

from omcore import check
from omcore.secrets.tests.harness import HarnessSecrets
from omcore.testing.pytest.inject import Harness

from .... import llm
from ...dummy.weather import GetWeatherTool
from ...tests.models import ANTHROPIC
from ...tests.models import GOOGLE
from ...tests.models import OPENAI
from ...tests.models import ModelForTest
from ...tests.scripted import scripted_backend
from ...tests.scripted import text_message
from ...tests.scripted import tool_call_message
from ...tests.tools import bare_tool
from ...types.contexts import Context
from ...types.events import AgentEndEvent
from ...types.events import Event
from ...types.messages import InfoAgentMessage
from ...types.tools import ToolResult
from ...types.tools import ToolSet
from ...types.turns import AgentEndReason
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


class _BlockingExecutor:
    def __init__(self) -> None:
        super().__init__()

        self.started = asyncio.Event()
        self._never = asyncio.Event()

    async def __call__(self, ctx):
        self.started.set()
        await self._never.wait()
        raise AssertionError


def _end_events(events):
    return [e for e in events if isinstance(e, AgentEndEvent)]


@pytest.mark.asyncs('asyncio')
async def test_loop_returns_failed_result_and_publishes_terminal_event():
    error = RuntimeError('boom')
    events: list[Event] = []
    loop = TurnLoop(
        new_messages=[llm.UserMessage('hi')],
        subscriber=events.append,
        llm_backend=scripted_backend(error),
    )

    # A failure is an outcome of the run, not an exception out of it.
    result = await loop.run()

    assert result.reason is AgentEndReason.FAILED
    assert result.error is error

    [end] = _end_events(events)
    assert end.reason is AgentEndReason.FAILED
    assert end.error is error

    # The transcript up to the failure is kept, and the failure noted in it.
    assert [type(m) for m in result.new_messages] == [llm.UserMessage, InfoAgentMessage]
    assert 'boom' in check.isinstance(result.new_messages[-1], InfoAgentMessage).info
    assert end.new_messages == result.new_messages
    assert list(result.context.messages or []) == list(result.new_messages)


@pytest.mark.asyncs('asyncio')
async def test_loop_failure_after_tool_keeps_the_work():
    tool_calls = []

    async def executor(ctx):
        tool_calls.append(ctx.args)
        return ToolResult(content=llm.TextContent('did it'))

    loop = TurnLoop(
        new_messages=[llm.UserMessage('go')],
        context=Context(tools=ToolSet([bare_tool('act', executor)])),
        llm_backend=scripted_backend(
            tool_call_message(llm.ToolCall('t1', 'act', {'n': 1})),
            RuntimeError('boom'),
        ),
    )

    result = await loop.run()

    assert result.reason is AgentEndReason.FAILED
    assert tool_calls == [{'n': 1}]

    # The executed call and its result survive the later failure; nothing dangles.
    types = [type(m) for m in result.new_messages]
    assert types == [llm.UserMessage, llm.AiMessage, llm.ToolResultMessage, InfoAgentMessage]
    assert not check.isinstance(result.new_messages[2], llm.ToolResultMessage).is_error


@pytest.mark.asyncs('asyncio')
async def test_loop_publishes_cancelled_terminal_event():
    backend = _BlockingBackend()
    events: list[Event] = []
    loop = TurnLoop(
        new_messages=[llm.UserMessage('hi')],
        subscriber=events.append,
        llm_backend=backend,
    )

    task = asyncio.create_task(loop.run())
    await backend.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    [end] = _end_events(events)
    assert end.reason is AgentEndReason.CANCELLED
    assert isinstance(end.error, asyncio.CancelledError)

    # Cancelled before any response: the prompt stays, with the cancellation noted after it.
    assert [type(m) for m in end.new_messages] == [llm.UserMessage, InfoAgentMessage]


@pytest.mark.asyncs('asyncio')
async def test_loop_cancelled_mid_tool_repairs_transcript():
    executor = _BlockingExecutor()
    events: list[Event] = []
    loop = TurnLoop(
        new_messages=[llm.UserMessage('go')],
        context=Context(tools=ToolSet([bare_tool('block', executor)])),
        subscriber=events.append,
        llm_backend=scripted_backend(
            tool_call_message(
                llm.ToolCall('t1', 'block', {}),
                llm.ToolCall('t2', 'block', {}),
            ),
        ),
    )

    task = asyncio.create_task(loop.run())
    await executor.started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    [end] = _end_events(events)
    assert end.reason is AgentEndReason.CANCELLED

    # Both the interrupted call and the one never reached get an error result, so the next request is well-formed.
    msgs = end.new_messages
    assert [type(m) for m in msgs] == [
        llm.UserMessage,
        llm.AiMessage,
        llm.ToolResultMessage,
        llm.ToolResultMessage,
        InfoAgentMessage,
    ]
    assert [m.tool_call_id for m in msgs[2:4]] == ['t1', 't2']
    assert all(m.is_error for m in msgs[2:4])
    assert all('cancelled' in m.content[0].text for m in msgs[2:4])
    assert msgs[-1].info == 'Turn cancelled.'


@pytest.mark.asyncs('asyncio')
async def test_loop_does_not_publish_on_base_exception():
    class FooError(BaseException):
        pass

    events: list[Event] = []
    loop = TurnLoop(
        new_messages=[llm.UserMessage('hi')],
        subscriber=events.append,
        llm_backend=scripted_backend(FooError()),
    )

    task = asyncio.create_task(loop.run())
    with pytest.raises(FooError):
        await task

    assert not _end_events(events)


@pytest.mark.asyncs('asyncio')
async def test_loop_completes_with_text():
    events: list[Event] = []
    loop = TurnLoop(
        new_messages=[llm.UserMessage('hi')],
        subscriber=events.append,
        llm_backend=scripted_backend(text_message('hello')),
    )

    result = await loop.run()

    assert result.reason is AgentEndReason.COMPLETED
    assert result.error is None
    assert [type(m) for m in result.new_messages] == [llm.UserMessage, llm.AiMessage]

    [end] = _end_events(events)
    assert end.reason is AgentEndReason.COMPLETED


##


async def _test_loop(
        harness: Harness,
        model: ModelForTest,
) -> None:
    svc = model.stream_backend_cls(
        llm.default_model_catalog()[model.model_key],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip(model.api_key_name),
    )

    loop = TurnLoop(
        new_messages=[
            llm.UserMessage('Hi there!'),
        ],
        llm_backend=svc,
    )

    loop_res = await loop.run()

    print(loop_res)


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
async def test_loop_openai(harness):
    await _test_loop(harness, OPENAI)


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
async def test_loop_anthropic(harness):
    await _test_loop(harness, ANTHROPIC)


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
@pytest.mark.xdist_group('google-online')
async def test_loop_google(harness):
    await _test_loop(harness, GOOGLE)


##


async def _test_loop_with_tool(harness: Harness, model: ModelForTest) -> None:
    svc = model.stream_backend_cls(
        llm.default_model_catalog()[model.model_key],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip(model.api_key_name),
    )

    loop = TurnLoop(
        new_messages=[
            llm.UserMessage('What is the weather in Edinburgh, Scotland?'),
        ],
        llm_backend=svc,
        context=Context(
            tools=ToolSet([
                GetWeatherTool().tool(),
            ]),
        ),
    )

    loop_res = await loop.run()

    print(loop_res)


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
async def test_loop_with_tool_openai(harness):
    await _test_loop_with_tool(harness, OPENAI)


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
async def test_loop_with_tool_anthropic(harness):
    await _test_loop_with_tool(harness, ANTHROPIC)


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
@pytest.mark.xdist_group('google-online')
async def test_loop_with_tool_google(harness):
    await _test_loop_with_tool(harness, GOOGLE)
