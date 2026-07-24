import typing as ta

import pytest

from omcore import check
from omcore.secrets.tests.harness import HarnessSecrets
from omcore.testing.pytest.inject import Harness

from ... import llm
from ..contexts import Context
from ..loop import Loop
from ..tools import Tool
from ..tools import ToolContext
from ..tools import ToolResult


##


class ModelKeyAndSecret(ta.NamedTuple):
    model_key: llm.ModelKey
    api_key_name: str


OPENAI = ModelKeyAndSecret(llm.ModelKey('openai', 'gpt-5.4-mini'), 'openai_api_key')
ANTHROPIC = ModelKeyAndSecret(llm.ModelKey('anthropic', 'claude-sonnet-5'), 'anthropic_api_key')
GOOGLE = ModelKeyAndSecret(llm.ModelKey('google', 'gemini-3-flash-preview'), 'gemini_api_key')


##


async def _test_loop(
        harness: Harness,
        model: ModelKeyAndSecret,
) -> None:
    svc = llm.OpenaiCompletionsStreamBackend(
        llm.default_model_catalog()[model.model_key],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip(model.api_key_name),
    )

    loop = Loop(
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


async def execute_weather_tool(ctx: ToolContext) -> ToolResult:
    location = check.non_empty_str(ctx.args['location'])

    if 'edinburgh' in location.lower():
        return ToolResult(content=llm.TextContent('The weather in Edinburgh, Scotland is sunny.'))

    else:
        return ToolResult(content=llm.TextContent('Invalid location'))


WEATHER_TOOL = Tool(
    llm_tool=llm.Tool(
        name='get_weather',
        description='Get the weather in a given location',
        params=[
            llm.ToolParam(
                name='location',
                description='The city and state, e.g. San Francisco, CA',
                type='string',
            ),
        ],
    ),
    executor=execute_weather_tool,
)


async def _test_loop_with_tool(harness: Harness, model: ModelKeyAndSecret) -> None:
    svc = llm.OpenaiCompletionsStreamBackend(
        llm.default_model_catalog()[model.model_key],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip(model.api_key_name),
    )

    loop = Loop(
        llm_backend=svc,
        context=Context(
            messages=[
                llm.UserMessage('What is the weather in Edinburgh, Scotland?'),
            ],
            tools=[
                WEATHER_TOOL,
            ],
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
