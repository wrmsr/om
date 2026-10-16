"""A real model spawning a subagent on a real model, through the hand-built runner."""
import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore.asyncs.asynclite import all as asl
from omcore.secrets.tests.harness import HarnessSecrets
from omcore.testing.pytest.inject import Harness

from .... import llm
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ...agent import Agent
from ...backends import DictBackendManager
from ...permissions.deciders import StaticPermissionDecider
from ...permissions.types import PermissionState
from ...tests.models import ANTHROPIC
from ...tests.models import GOOGLE
from ...tests.models import OPENAI
from ...tests.models import ModelForTest
from ...tests.tools import EchoTool
from ...turns.runner import TurnLoopRunner
from ...types.contexts import Context
from ...types.events import ToolExecutionEndEvent
from ...types.events import ToolExecutionStartEvent
from ...types.tools import ToolSet
from ...types.turns import AgentEndReason
from ...types.turns import LlmRetryConfig
from ...types.turns import TurnConfig
from ..profiles import GENERAL_SUBAGENT_PROFILE
from ..profiles import SubagentProfiles
from ..runners import AgentSubagentRunner
from ..tools.details import SubagentToolResultDetails
from ..tools.subagent import SubagentTool
from .support import ai_text
from .support import relayed_events
from .support import tool_results


##


_WORD = 'pineapple-42'

_PROMPT = (
    'You must use the subagent tool for this, and must not call any other tool yourself. Spawn one subagent and '
    f'instruct it to call its echo tool with exactly the text "{_WORD}" and then report back the exact text the echo '
    'tool returned. When the subagent returns, reply with only the text it reported, nothing else.'
)


async def _test_subagent(harness: Harness, model: ModelForTest) -> None:
    backend = model.stream_backend_cls(
        llm.provider_model_catalog()[model.model_key],  # noqa
        api_key=harness[HarnessSecrets].get_or_skip(model.api_key_name),
    )

    def turn_runner():
        return TurnLoopRunner(
            cancellation=asl.asyncio.Cancellation(),
            group_runner=AsyncioGroupRunner(),
            backends=DictBackendManager.of(backend),
            sleeps=asl.asyncio.Sleeps(),
        )

    turn_config = TurnConfig(llm_retry=LlmRetryConfig())

    echo = EchoTool()
    profiles = SubagentProfiles([GENERAL_SUBAGENT_PROFILE])
    runner = AgentSubagentRunner(
        turn_runner=turn_runner(),
        tools=ToolSet([echo.tool()]),
        profiles=profiles,
        turn_config=turn_config,
    )
    tool = SubagentTool(
        permissions=StaticPermissionDecider(PermissionState.ALLOW),
        runner=runner,
        profiles=profiles,
    )

    agent = Agent(turn_runner=turn_runner())
    await agent.update_state(lambda s: dc.replace(
        s,
        context=Context(tools=ToolSet([tool.tool()])),
        turn_config=turn_config,
    ))

    events: list = []
    agent.subscribe(events.append)

    result = await agent.prompt(_PROMPT)

    assert result.reason is AgentEndReason.COMPLETED, result.error

    # The parent spawned, the child echoed, and the word made its way back up.
    assert [e.tool_name for e in events if isinstance(e, ToolExecutionStartEvent)] == ['subagent']
    assert echo.calls == [_WORD]
    assert [e.tool_name for e in relayed_events(events) if isinstance(e, ToolExecutionStartEvent)] == ['echo']

    [tr] = tool_results(result.new_messages)
    assert not tr.is_error
    assert _WORD in tr.content[0].text
    assert _WORD in ai_text(result.new_messages[-1])

    [end] = [e for e in events if isinstance(e, ToolExecutionEndEvent)]
    details = check.isinstance(end.result.details, SubagentToolResultDetails)
    assert details.reason is AgentEndReason.COMPLETED
    assert details.num_turns >= 2
    assert check.not_none(details.usage).input > 0


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
@pytest.mark.timeout(300)
async def test_subagent_openai(harness):
    await _test_subagent(harness, OPENAI)


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
@pytest.mark.timeout(300)
async def test_subagent_anthropic(harness):
    await _test_subagent(harness, ANTHROPIC)


@pytest.mark.asyncs('asyncio')
@pytest.mark.online
@pytest.mark.timeout(300)
@pytest.mark.xdist_group('google-online')
async def test_subagent_google(harness):
    await _test_subagent(harness, GOOGLE)
