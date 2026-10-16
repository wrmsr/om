"""
The subagent tool through the tui's injector: each spawn an agent scope of its own, as a child of the app's injector.
"""
import os.path
import tempfile

import pytest

from omcore import check
from omcore import inject as inj

from .... import agent as agn
from .... import llm
from ....agent.tests.scripted import text_message
from ....agent.tests.scripted import tool_call_message
from ....core import processes
from ..config import Config
from ..yolo import yolo_autoexec
from ..yolo import yolo_process_config
from .headless import bind_headless_tui
from .headless import bind_scripted_backend
from .headless import headless_tui


##


def _allow_rules(cwd):
    return [
        '/permissions add allow subagent {}',
        f'/permissions add allow glob_fs \'{{"glob":"{cwd}/**","modes":["r"]}}\'',
    ]


def _bind(cwd, *turns, autoexec=None, subagents=True):
    return inj.override(
        bind_headless_tui(Config(
            model='scripted',
            immediate=True,
            in_memory=True,
            fs=True,
            subagents=subagents,
            cwd=cwd,
            autoexec=autoexec if autoexec is not None else _allow_rules(cwd),
        )),
        bind_scripted_backend(*turns),
    )


def _subagent_call(id, prompt, **args):  # noqa
    return llm.ToolCall(id, 'subagent', {'prompt': prompt, **args})


def _tool_results(messages):
    return [m for m in messages if isinstance(m, llm.ToolResultMessage)]


def _relayed(events):
    return [
        e.update
        for e in events
        if isinstance(e, agn.ToolExecutionUpdateEvent) and isinstance(e.update, agn.SubagentEventToolProgressUpdate)
    ]


##


@pytest.mark.asyncs('asyncio')
async def test_subagent_runs_as_an_agent_scope_of_its_own():
    with tempfile.TemporaryDirectory() as td:
        td = os.path.abspath(os.path.realpath(td))

        with open(os.path.join(td, 'note.txt'), 'w') as f:  # noqa: ASYNC230
            f.write('hello\n')

        # One scripted model answers both agents, in invocation order: parent, child, child, parent.
        async with headless_tui(_bind(
                td,
                tool_call_message(_subagent_call('p1', 'what is in the directory?', profile='explore')),
                tool_call_message(llm.ToolCall('c1', 'ls', {'dir_path': td})),
                text_message('one file: note.txt'),
                text_message('parent done'),
        )) as tui:
            assert 'subagent' in check.not_none(tui.agent.state.context.tools).by_name

            events: list = []
            tui.agent.subscribe(events.append)

            result = await tui.agent.prompt('go')

            assert result.reason is agn.AgentEndReason.COMPLETED
            [tr] = _tool_results(result.new_messages)
            assert not tr.is_error
            assert tr.content[0].text == 'one file: note.txt'

            # The child's tool call ran, under the root's permissions, in the child's own tool set.
            updates = _relayed(events)
            assert {u.profile for u in updates} == {'explore'}
            [child_end] = [u.event for u in updates if isinstance(u.event, agn.ToolExecutionEndEvent)]
            assert child_end.tool_name == 'ls'
            assert child_end.result.error is None
            assert 'note.txt' in child_end.result.content.text

            # The parent's session recorded the parent's run alone.
            storage = await tui.injector[agn.InMemorySessionStorage]
            assert [type(e.message) for e in await storage.get_entries()] == [  # type: ignore[attr-defined]
                llm.UserMessage,
                llm.AiMessage,
                llm.ToolResultMessage,
                llm.AiMessage,
            ]

            # The child's process scope is gone with it.
            pm = await tui.injector[processes.ProcessManager]
            assert not pm.root.children

            # And the root's own tool instances were not the child's: the child got instances of its own.
            [child_start] = [u.event for u in updates if isinstance(u.event, agn.ToolExecutionStartEvent)]
            root_ls = check.not_none(tui.agent.state.context.tools)['ls']
            assert check.not_none(child_start.tool) is not root_ls
            assert check.not_none(child_start.tool).name == root_ls.name


@pytest.mark.asyncs('asyncio')
async def test_explore_subagent_has_only_read_tools_and_no_subagent_tool():
    with tempfile.TemporaryDirectory() as td:
        td = os.path.abspath(os.path.realpath(td))

        async with headless_tui(_bind(
                td,
                tool_call_message(_subagent_call('p1', 'write something', profile='explore')),
                tool_call_message(
                    llm.ToolCall('c1', 'write', {'file_path': os.path.join(td, 'x'), 'content': 'x'}),
                    llm.ToolCall('c2', 'subagent', {'prompt': 'nest'}),
                ),
                text_message('could not'),
                text_message('parent done'),
        )) as tui:
            events: list = []
            tui.agent.subscribe(events.append)

            await tui.agent.prompt('go')

            ends = [u.event for u in _relayed(events) if isinstance(u.event, agn.ToolExecutionEndEvent)]
            assert [e.tool_name for e in ends] == ['write', 'subagent']
            assert all(isinstance(e.result.error, agn.UnknownToolError) for e in ends)
            assert not os.path.exists(os.path.join(td, 'x'))


@pytest.mark.asyncs('asyncio')
async def test_general_subagent_has_the_parents_tools_but_not_the_subagent_tool():
    with tempfile.TemporaryDirectory() as td:
        td = os.path.abspath(os.path.realpath(td))

        async with headless_tui(_bind(
                td,
                tool_call_message(_subagent_call('p1', 'nest')),
                tool_call_message(
                    llm.ToolCall('c1', 'subagent', {'prompt': 'nest'}),
                    llm.ToolCall('c2', 'ls', {'dir_path': td}),
                ),
                text_message('done'),
                text_message('parent done'),
        )) as tui:
            events: list = []
            tui.agent.subscribe(events.append)

            await tui.agent.prompt('go')

            updates = _relayed(events)
            assert {u.profile for u in updates} == {'general'}
            ends = {e.tool_name: e for u in updates if isinstance(e := u.event, agn.ToolExecutionEndEvent)}
            assert isinstance(ends['subagent'].result.error, agn.UnknownToolError)
            assert ends['ls'].result.error is None


@pytest.mark.asyncs('asyncio')
async def test_subagents_in_one_message_each_get_a_scope_of_their_own():
    with tempfile.TemporaryDirectory() as td:
        td = os.path.abspath(os.path.realpath(td))

        async with headless_tui(_bind(
                td,
                tool_call_message(_subagent_call('p1', 'one'), _subagent_call('p2', 'two')),
                text_message('first'),
                text_message('second'),
                text_message('parent done'),
        )) as tui:
            events: list = []
            tui.agent.subscribe(events.append)

            result = await tui.agent.prompt('go')

            assert result.reason is agn.AgentEndReason.COMPLETED
            assert sorted(tr.content[0].text for tr in _tool_results(result.new_messages)) == ['first', 'second']
            assert len({u.run_id for u in _relayed(events)}) == 2

            pm = await tui.injector[processes.ProcessManager]
            assert not pm.root.children


@pytest.mark.asyncs('asyncio')
async def test_spawn_is_denied_without_a_rule():
    with tempfile.TemporaryDirectory() as td:
        td = os.path.abspath(os.path.realpath(td))

        async with headless_tui(_bind(
                td,
                tool_call_message(_subagent_call('p1', 'go')),
                text_message('parent done'),
                autoexec=[],
        )) as tui:
            events: list = []
            tui.agent.subscribe(events.append)

            result = await tui.agent.prompt('go')

            [tr] = _tool_results(result.new_messages)
            assert tr.is_error
            assert 'PermissionDeniedError' in tr.content[0].text
            assert not _relayed(events)


@pytest.mark.asyncs('asyncio')
async def test_subagents_are_off_without_the_flag():
    with tempfile.TemporaryDirectory() as td:
        td = os.path.abspath(os.path.realpath(td))

        async with headless_tui(_bind(
                td,
                text_message('hi'),
                subagents=None,
        )) as tui:
            assert 'subagent' not in check.not_none(tui.agent.state.context.tools).by_name


def test_yolo_implies_subagents_and_allows_spawning():
    for config in [Config(yolo=True), Config(diet_yolo=True)]:
        processed = yolo_process_config(config)
        assert processed.subagents is True
        assert '/permissions add allow subagent {}' in yolo_autoexec(processed, '/somewhere')

    assert yolo_process_config(Config()).subagents is None
    assert yolo_autoexec(Config(), '/somewhere') == []
