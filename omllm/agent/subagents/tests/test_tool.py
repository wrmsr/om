import pytest

from omcore import check

from .... import llm
from ...permissions.deciders import DENY_TOOL_PERMISSION_DECIDER
from ...tests.scripted import text_message
from ...tests.scripted import tool_call_message
from ...tests.tools import EchoTool
from ...types.tools import ToolContext
from ...types.turns import AgentEndReason
from ..profiles import GENERAL_SUBAGENT_PROFILE
from ..profiles import SubagentProfiles
from ..profiles import explore_subagent_profile
from ..tools.subagent import SubagentToolParams
from .support import child_runner
from .support import parent_agent
from .support import subagent_call
from .support import subagent_tool
from .support import tool_results


##


def test_description_lists_the_profiles_and_the_default():
    tool = subagent_tool(
        child_runner(tools=[EchoTool().tool()]),
        profiles=SubagentProfiles([GENERAL_SUBAGENT_PROFILE, explore_subagent_profile(['echo'])]),
    )

    description = tool.description
    assert '- general: ' in description.description
    assert '- explore: ' in description.description
    assert 'Defaults to general' in check.not_none(description.params)['profile']

    llm_tool = tool.llm_tool()
    assert llm_tool.name == 'subagent'
    assert {p.name: p.optional for p in llm_tool.params} == {
        'prompt': False,
        'profile': True,
        'description': True,
    }


def test_summary_names_the_profile_and_prefers_the_description():
    tool = subagent_tool(child_runner())
    ctx = ToolContext(args={})

    assert tool.summarize(ctx, SubagentToolParams('do the thing')) == 'general: do the thing'
    assert tool.summarize(ctx, SubagentToolParams('do the thing', profile='explore', description='the thing')) == (
        'explore: the thing'
    )


@pytest.mark.asyncs('asyncio')
async def test_unknown_profile_is_an_error_result_and_spawns_nothing():
    runner = child_runner(text_message('never'))
    agent = await parent_agent(
        tool_call_message(subagent_call('p1', 'go', profile='nope')),
        text_message('ok'),
        tools=[subagent_tool(runner).tool()],
    )

    result = await agent.prompt('hi')

    assert result.reason is AgentEndReason.COMPLETED
    [tr] = tool_results(result.new_messages)
    assert tr.is_error
    assert 'UnknownSubagentProfileError' in tr.content[0].text
    assert "'nope'" in tr.content[0].text


@pytest.mark.asyncs('asyncio')
async def test_denied_spawn_is_an_error_result():
    runner = child_runner(text_message('never'))
    agent = await parent_agent(
        tool_call_message(subagent_call('p1', 'go')),
        text_message('ok'),
        tools=[subagent_tool(runner, permissions=DENY_TOOL_PERMISSION_DECIDER).tool()],
    )

    result = await agent.prompt('hi')

    [tr] = tool_results(result.new_messages)
    assert tr.is_error
    assert 'PermissionDeniedError' in tr.content[0].text
    assert "profile='general'" in tr.content[0].text

    # Nothing was published for a child, because there was none.
    assert not any(isinstance(m, llm.AiMessage) and 'never' in str(m) for m in result.new_messages)
