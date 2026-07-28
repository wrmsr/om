import pytest

from omcore.secrets.tests.harness import HarnessSecrets
from omcore.testing.pytest.inject import Harness

from .... import llm
from ...dummy.weather import weather_tool
from ...tests.models import ANTHROPIC
from ...tests.models import GOOGLE
from ...tests.models import OPENAI
from ...tests.models import ModelForTest
from ...types.contexts import Context
from ...types.tools import ToolSet
from ..loop import TurnLoop


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
        llm_backend=svc,
        context=Context(
            messages=[
                llm.UserMessage('Hi there!'),
            ],
        ),
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
async def test_loop_google(harness):
    await _test_loop(harness, GOOGLE)


##


async def _test_loop_with_tool(harness: Harness, model: ModelForTest) -> None:
    svc = model.stream_backend_cls(
        llm.default_model_catalog()[model.model_key],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip(model.api_key_name),
    )

    loop = TurnLoop(
        llm_backend=svc,
        context=Context(
            messages=[
                llm.UserMessage('What is the weather in Edinburgh, Scotland?'),
            ],
            tools=ToolSet([
                weather_tool(),
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
async def test_loop_with_tool_google(harness):
    await _test_loop_with_tool(harness, GOOGLE)
