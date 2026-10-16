"""
The hand-built runner, end to end through the tool: a parent agent spawning a child, each on its own scripted model.
"""
import asyncio
import tempfile

import pytest

from omcore import check

from .... import llm
from ....core import processes
from ...sessions.session import Session
from ...sessions.storage.inmemory import InMemorySessionStorage
from ...systemprompt.types import SystemPromptContributors
from ...systemprompt.types import SystemPromptPart
from ...systemprompt.types import SystemPromptPriority
from ...tests.scripted import text_message
from ...tests.scripted import tool_call_message
from ...tests.tools import EchoTool
from ...types.events import AgentEndEvent
from ...types.events import AgentStartEvent
from ...types.events import MessageAddedEvent
from ...types.events import ToolExecutionEndEvent
from ...types.events import ToolExecutionStartEvent
from ...types.tools import ToolEnvironment
from ...types.turns import AgentEndReason
from ..errors import UnknownSubagentToolsError
from ..profiles import GENERAL_SUBAGENT_PROFILE
from ..profiles import SubagentProfile
from ..profiles import SubagentProfiles
from ..profiles import explore_subagent_profile
from ..systemprompt import SUBAGENT_SYSTEM_PROMPT
from ..tools.details import SubagentToolResultDetails
from ..tools.subagent import SubagentTool
from .support import EnvRecordingTool
from .support import GatedTool
from .support import ai_text
from .support import child_runner
from .support import parent_agent
from .support import relayed_events
from .support import relayed_updates
from .support import subagent_call
from .support import subagent_tool
from .support import tool_results


##


def _echo_call(id, text):  # noqa
    return llm.ToolCall(id, 'echo', {'text': text})


@pytest.mark.asyncs('asyncio')
async def test_subagent_result_is_the_childs_final_text():
    echo = EchoTool()
    runner = child_runner(
        tool_call_message(_echo_call('c1', 'x')),
        text_message('child says hi'),
        tools=[echo.tool()],
    )
    agent = await parent_agent(
        tool_call_message(subagent_call('p1', 'go', description='a task')),
        text_message('parent done'),
        tools=[subagent_tool(runner).tool()],
    )

    events: list = []
    agent.subscribe(events.append)

    result = await agent.prompt('hi')

    assert result.reason is AgentEndReason.COMPLETED
    assert echo.calls == ['x']

    [tr] = tool_results(result.new_messages)
    assert not tr.is_error
    assert tr.content[0].text == 'child says hi'
    assert ai_text(result.new_messages[-1]) == 'parent done'

    [end] = [e for e in events if isinstance(e, ToolExecutionEndEvent)]
    details = check.isinstance(end.result.details, SubagentToolResultDetails)
    assert details.profile == 'general'
    assert details.reason is AgentEndReason.COMPLETED
    assert details.num_turns == 2
    assert [type(m) for m in details.messages] == [
        llm.UserMessage,
        llm.AiMessage,
        llm.ToolResultMessage,
        llm.AiMessage,
    ]
    assert check.isinstance(details.messages[0], llm.UserMessage).content == 'go'


@pytest.mark.asyncs('asyncio')
async def test_child_events_are_relayed_as_progress_and_never_published_raw():
    runner = child_runner(
        tool_call_message(_echo_call('c1', 'x')),
        text_message('child says hi'),
        tools=[EchoTool().tool()],
    )
    agent = await parent_agent(
        tool_call_message(subagent_call('p1', 'go')),
        text_message('parent done'),
        tools=[subagent_tool(runner).tool()],
    )

    # A session on the parent sees only the parent's run.
    storage = InMemorySessionStorage()
    Session(agent=agent, storage=storage)

    events: list = []
    agent.subscribe(events.append)

    await agent.prompt('hi')

    # The parent's bus carries exactly one run.
    assert len([e for e in events if isinstance(e, AgentStartEvent)]) == 1
    assert len([e for e in events if isinstance(e, AgentEndEvent)]) == 1
    assert [e.message.__class__ for e in events if isinstance(e, MessageAddedEvent)] == [
        llm.UserMessage,
        llm.AiMessage,
        llm.ToolResultMessage,
        llm.AiMessage,
    ]
    assert len(await storage.get_entries()) == 4

    # The child's whole run came through as progress of the spawning call, every update tagged with the run.
    updates = relayed_updates(events)
    assert {u.profile for u in updates} == {'general'}
    assert len({u.run_id for u in updates}) == 1

    child_events = relayed_events(events)
    assert isinstance(child_events[0], AgentStartEvent)
    assert isinstance(child_events[-1], AgentEndEvent)
    assert [e.tool_name for e in child_events if isinstance(e, ToolExecutionStartEvent)] == ['echo']
    assert check.isinstance(child_events[-1], AgentEndEvent).reason is AgentEndReason.COMPLETED

    [end] = [e for e in events if isinstance(e, ToolExecutionEndEvent)]
    assert check.isinstance(end.result.details, SubagentToolResultDetails).run_id == updates[0].run_id


@pytest.mark.asyncs('asyncio')
async def test_child_works_in_a_process_scope_of_its_own_under_the_parents():
    recording = EnvRecordingTool('rec')
    runner = child_runner(
        tool_call_message(llm.ToolCall('c1', 'rec', {})),
        text_message('child done'),
        tools=[recording.tool()],
    )

    with tempfile.TemporaryDirectory() as td:
        async with processes.AsyncioProcessManager() as m:
            agent = await parent_agent(
                tool_call_message(subagent_call('p1', 'go')),
                text_message('parent done'),
                tools=[subagent_tool(runner).tool()],
                env=ToolEnvironment(cwd=td, processes=m.root),
            )

            await agent.prompt('hi')

            [env] = [check.not_none(e) for e in recording.envs]
            scope = check.not_none(env.processes)
            assert env.cwd == td
            assert scope.parent is m.root
            assert scope.name.startswith('subagent-')
            assert scope.closed
            assert not m.root.children


@pytest.mark.asyncs('asyncio')
async def test_failed_child_is_an_error_result_for_the_parent():
    runner = child_runner(RuntimeError('boom'))
    agent = await parent_agent(
        tool_call_message(subagent_call('p1', 'go')),
        text_message('parent recovers'),
        tools=[subagent_tool(runner).tool()],
    )

    events: list = []
    agent.subscribe(events.append)

    result = await agent.prompt('hi')

    assert result.reason is AgentEndReason.COMPLETED
    [tr] = tool_results(result.new_messages)
    assert tr.is_error
    assert 'The subagent failed' in tr.content[0].text
    assert 'boom' in tr.content[0].text

    [end] = [e for e in events if isinstance(e, ToolExecutionEndEvent)]
    assert isinstance(end.result.error, RuntimeError)
    assert check.isinstance(end.result.details, SubagentToolResultDetails).reason is AgentEndReason.FAILED
    assert check.isinstance(relayed_events(events)[-1], AgentEndEvent).reason is AgentEndReason.FAILED


@pytest.mark.asyncs('asyncio')
async def test_turn_limited_child_returns_what_it_had_with_a_note():
    echo = EchoTool()
    profiles = SubagentProfiles([SubagentProfile(name='brief', description='one turn', max_turns=1)])
    runner = child_runner(
        tool_call_message(_echo_call('c1', 'x')),
        tools=[echo.tool()],
        profiles=profiles,
    )
    agent = await parent_agent(
        tool_call_message(subagent_call('p1', 'go')),
        text_message('parent done'),
        tools=[subagent_tool(runner, profiles=profiles).tool()],
    )

    events: list = []
    agent.subscribe(events.append)

    result = await agent.prompt('hi')

    assert echo.calls == []
    [tr] = tool_results(result.new_messages)
    assert not tr.is_error
    assert 'turn limit' in tr.content[0].text

    [end] = [e for e in events if isinstance(e, ToolExecutionEndEvent)]
    details = check.isinstance(end.result.details, SubagentToolResultDetails)
    assert details.reason is AgentEndReason.MAX_TURNS
    assert details.num_turns == 1


@pytest.mark.asyncs('asyncio')
async def test_parent_cancellation_unwinds_the_child():
    gated = GatedTool('gate')
    runner = child_runner(
        tool_call_message(llm.ToolCall('c1', 'gate', {})),
        text_message('never'),
        tools=[gated.tool()],
    )

    async with processes.AsyncioProcessManager() as m:
        agent = await parent_agent(
            tool_call_message(subagent_call('p1', 'go')),
            text_message('never'),
            tools=[subagent_tool(runner).tool()],
            env=ToolEnvironment(cwd='/', processes=m.root),
        )

        events: list = []
        agent.subscribe(events.append)

        task = asyncio.create_task(agent.prompt('hi'))
        await gated.started.wait()
        assert len(m.root.children) == 1

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        # The child's execution unwound as a cancellation of its own task, its run ended as cancelled and said so
        # through the relay, and its process scope went with it. Then the parent's run ended the same way.
        assert gated.seen == [('cancelled', True)]
        assert check.isinstance(relayed_events(events)[-1], AgentEndEvent).reason is AgentEndReason.CANCELLED
        assert not m.root.children

        [end] = [e for e in events if isinstance(e, AgentEndEvent)]
        assert end.reason is AgentEndReason.CANCELLED
        [tr] = tool_results(end.new_messages)
        assert tr.is_error and 'cancelled' in tr.content[0].text


@pytest.mark.asyncs('asyncio')
async def test_child_gets_the_profiles_tools_and_prompt_and_nothing_of_the_parents():
    seen: list = []

    def expect(inv):
        seen.append(inv.context)

    echo = EchoTool()
    other = EnvRecordingTool('other')
    profiles = SubagentProfiles([explore_subagent_profile(['echo'])])

    class _Extra:
        def get_system_prompt_parts(self):
            return [SystemPromptPart(SystemPromptPriority.DEFAULT, 'Working in /tmp/somewhere')]

    runner = child_runner(
        llm.BackendScriptTurn(text_message('child done'), expect=expect),
        tools=[echo.tool(), other.tool()],
        profiles=profiles,
        system_prompt_contributors=SystemPromptContributors([_Extra()]),  # type: ignore[list-item]
    )
    agent = await parent_agent(
        tool_call_message(subagent_call('p1', 'find things', profile='explore')),
        text_message('parent done'),
        tools=[subagent_tool(runner, profiles=profiles).tool()],
    )

    await agent.prompt('a long conversation the child must not see')

    [ctx] = seen
    assert [t.name for t in ctx.tools] == ['echo']
    assert [m.content for m in ctx.messages if isinstance(m, llm.UserMessage)] == ['find things']

    system_prompt = check.not_none(ctx.system_prompt)
    assert system_prompt.startswith(SUBAGENT_SYSTEM_PROMPT)
    assert check.not_none(profiles['explore'].system_prompt) in system_prompt
    assert system_prompt.endswith('Working in /tmp/somewhere')


def test_runner_checks_profiles_against_its_pool_up_front():
    with pytest.raises(UnknownSubagentToolsError):
        child_runner(
            tools=[EchoTool().tool()],
            profiles=SubagentProfiles([GENERAL_SUBAGENT_PROFILE, explore_subagent_profile(['ls'])]),
        )


@pytest.mark.asyncs('asyncio')
async def test_two_subagents_in_one_message_run_concurrently():
    a, b = GatedTool('a'), GatedTool('b')

    # The children share one scripted model, which answers in invocation order: the two first calls land before either
    # child is released, one per child, and then the two second calls.
    runner = child_runner(
        tool_call_message(llm.ToolCall('c1', 'a', {})),
        tool_call_message(llm.ToolCall('c2', 'b', {})),
        text_message('first done'),
        text_message('second done'),
        tools=[a.tool(), b.tool()],
    )
    agent = await parent_agent(
        tool_call_message(subagent_call('p1', 'run a'), subagent_call('p2', 'run b')),
        text_message('parent done'),
        tools=[subagent_tool(runner).tool()],
    )

    events: list = []
    agent.subscribe(events.append)

    task = asyncio.create_task(agent.prompt('hi'))

    # Both are parked at once before either is released.
    await a.started.wait()
    await b.started.wait()
    b.release.set()
    a.release.set()

    result = await task

    assert result.reason is AgentEndReason.COMPLETED
    assert sorted(tr.content[0].text for tr in tool_results(result.new_messages)) == ['first done', 'second done']

    # Two runs, each relayed under its own id, and neither offered the subagent tool itself.
    assert len({u.run_id for u in relayed_updates(events)}) == 2
    started = [e for e in relayed_events(events) if isinstance(e, ToolExecutionStartEvent)]
    assert sorted(e.tool_name for e in started) == ['a', 'b']
    assert SubagentTool.name not in {e.tool_name for e in started}
