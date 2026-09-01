import pytest

from omcore import dataclasses as dc
from omcore.secrets.tests.harness import HarnessSecrets
from omcore.testing.pytest.inject import Harness

from ... import llm
from ..agent import Agent
from ..backends import DictBackendManager
from ..dummy.weather import GetWeatherTool
from ..turns.runner import TurnLoopRunner
from ..types.tools import ToolSet
from .models import ANTHROPIC
from .models import GOOGLE
from .models import OPENAI
from .models import ModelForTest


##


async def _test_agent(
        harness: Harness,
        model: ModelForTest,
) -> None:
    svc = model.stream_backend_cls(
        llm.default_model_catalog()[model.model_key],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip(model.api_key_name),
    )

    agent = Agent(
        turn_runner=TurnLoopRunner(
            backends=DictBackendManager({llm.ImmediateBackend: {None: svc}}),  # type: ignore
        ),
    )

    await agent.prompt(
        llm.UserMessage('Hi there!'),
    )


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
async def test_agent_openai(harness):
    await _test_agent(harness, OPENAI)


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
async def test_agent_anthropic(harness):
    await _test_agent(harness, ANTHROPIC)


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
@pytest.mark.xdist_group('google-online')
async def test_agent_google(harness):
    await _test_agent(harness, GOOGLE)


##


async def _test_agent_with_tool(harness: Harness, model: ModelForTest) -> None:
    svc = model.stream_backend_cls(
        llm.default_model_catalog()[model.model_key],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip(model.api_key_name),
    )

    agent = Agent(
        turn_runner=TurnLoopRunner(
            backends=DictBackendManager({llm.ImmediateBackend: {None: svc}}),  # type: ignore
        ),
    )

    await agent.update_state(
        lambda state: dc.replace(
            state,
            context=dc.replace(
                state.context,
                tools=ToolSet([
                    GetWeatherTool().tool(),
                ]),
            ),
        ),
    )

    await agent.prompt(
        llm.UserMessage('Hi there!'),
    )


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
async def test_agent_with_tool_openai(harness):
    await _test_agent_with_tool(harness, OPENAI)


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
async def test_agent_with_tool_anthropic(harness):
    await _test_agent_with_tool(harness, ANTHROPIC)


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
@pytest.mark.xdist_group('google-online')
async def test_agent_with_tool_google(harness):
    await _test_agent_with_tool(harness, GOOGLE)
