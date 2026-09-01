import asyncio

import pytest

from omcore.secrets.tests.harness import HarnessSecrets
from omcore.testing.pytest.inject import Harness

from .... import llm
from ...dummy.weather import GetWeatherTool
from ...tests.models import ANTHROPIC
from ...tests.models import GOOGLE
from ...tests.models import OPENAI
from ...tests.models import ModelForTest
from ...types.contexts import Context
from ...types.events import AgentEndEvent
from ...types.events import AgentEndReason
from ...types.events import Event
from ...types.tools import ToolSet
from ..loop import TurnLoop


##


class _FailingBackend(llm.ImmediateBackend):
    def __init__(self, error: Exception) -> None:
        super().__init__()

        self._error = error
        self._model = llm.Model(key=llm.ModelKey('test', 'failure'), backend='test')

    @property
    def model(self) -> llm.Model:
        return self._model

    async def immediate(self, context, options=None):
        raise self._error


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


@pytest.mark.asyncs('asyncio')
async def test_loop_publishes_failed_terminal_event():
    error = RuntimeError('boom')
    events: list[Event] = []
    loop = TurnLoop(
        new_messages=[llm.UserMessage('hi')],
        subscriber=events.append,
        llm_backend=_FailingBackend(error),
    )

    with pytest.raises(RuntimeError, match='boom'):
        await loop.run()

    ends = [event for event in events if isinstance(event, AgentEndEvent)]
    assert len(ends) == 1
    end = ends[0]
    assert end.reason is AgentEndReason.FAILED
    assert end.error is error


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

    ends = [event for event in events if isinstance(event, AgentEndEvent)]
    assert len(ends) == 1
    end = ends[0]
    assert end.reason is AgentEndReason.CANCELLED
    assert isinstance(end.error, asyncio.CancelledError)


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
