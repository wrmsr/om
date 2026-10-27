"""
Tool calls through the tui's injector: each one invoked in an opening of the agent's tool invocation scope, seeded with
the tool and its context, nested in the turn's.
"""
import asyncio
import os.path
import tempfile

import pytest

from omcore import check
from omcore import inject as inj

from .... import agent as agn
from .... import llm
from ....agent.tests.scripted import text_message
from ....agent.tests.scripted import tool_call_message
from ..config import Config
from ..inject import TOOL_INVOCATION_SCOPE
from ..inject import agent_tools
from .headless import bind_headless_tui
from .headless import bind_scripted_backend
from .headless import headless_tui


##


class _ScopeProbe:
    """
    A bare tool whose executions park until both of a pair are running, then look their invocation scope up as anything
    provided in it would: through the injector, from the execution's own task.
    """

    def __init__(self) -> None:
        super().__init__()

        self.injector: inj.AsyncInjector | None = None

        self._entered = 0
        self._both = asyncio.Event()

        self.seen: list = []

    async def __call__(self, ctx):
        self._entered += 1
        if self._entered == 2:
            self._both.set()
        await self._both.wait()

        injector = check.not_none(self.injector)
        self.seen.append(dict(
            ctx=ctx,
            scoped_ctx=await injector[agn.ToolContext],
            scoped_tool=await injector[agn.Tool],
            scoped_invoker=await injector[agn.DirectToolInvoker],
            turn_params=await injector[agn.TurnParams],
        ))

        return agn.ToolResult(content=llm.TextContent('probed'))

    def tool(self):
        return agn.Tool(
            llm_tool=llm.Tool(name='probe'),
            executor=self,
        )


def _bind_recording_direct_tool_invoker(provided):
    """An override: the invoker bound in the scope, provided as before, noting what each opening provided it from."""

    def provide(tool: agn.Tool, ctx: agn.ToolContext, params: agn.TurnParams) -> agn.DirectToolInvoker:
        invoker = agn.DirectToolInvoker()
        provided.append(dict(
            tool=tool,
            ctx=ctx,
            turn_params=params,
            invoker=invoker,
        ))
        return invoker

    return inj.bind(agn.DirectToolInvoker, in_=TOOL_INVOCATION_SCOPE, to_fn=provide)


def _tool_results(messages):
    return [m for m in messages if isinstance(m, llm.ToolResultMessage)]


##


@pytest.mark.asyncs('asyncio')
async def test_each_tool_call_is_invoked_in_an_opening_of_its_own():
    probe = _ScopeProbe()
    provided: list = []

    async with headless_tui(
            inj.override(
                bind_headless_tui(Config(
                    model='scripted',
                    immediate=True,
                    in_memory=True,
                )),
                bind_scripted_backend(
                    tool_call_message(llm.ToolCall('t1', 'probe', {}), llm.ToolCall('t2', 'probe', {})),
                    text_message('done'),
                ),
                _bind_recording_direct_tool_invoker(provided),
            ),
            agent_tools().bind_item(to_const=probe.tool()),
    ) as tui:
        probe.injector = tui.injector
        probe_tool = check.not_none(tui.agent.state.context.tools)['probe']

        result = await tui.agent.prompt('go')

        assert result.reason is agn.AgentEndReason.COMPLETED
        assert [tr.content[0].text for tr in _tool_results(result.new_messages)] == ['probed', 'probed']

        # The two calls ran at once, each in an opening of its own, seeded with its own tool and context.
        assert len(probe.seen) == 2
        assert {check.not_none(s['ctx'].llm_tool_call).id for s in probe.seen} == {'t1', 't2'}
        for s in probe.seen:
            assert s['scoped_ctx'] is s['ctx']
            assert s['scoped_tool'] is probe_tool

        # What is bound in the scope is built once per opening, from that opening's seeds and the turn's, and is what
        # the invocation was carried out by.
        assert len(provided) == 2
        by_id = {check.not_none(p['ctx'].llm_tool_call).id: p for p in provided}
        for s in probe.seen:
            p = by_id[check.not_none(s['ctx'].llm_tool_call).id]
            assert p['ctx'] is s['ctx']
            assert p['tool'] is probe_tool
            assert p['invoker'] is s['scoped_invoker']
        assert provided[0]['invoker'] is not provided[1]['invoker']

        # The calls' openings are nested in the turn's, which both see.
        [turn_params] = {id(s['turn_params']): s['turn_params'] for s in probe.seen}.values()
        assert turn_params is provided[0]['turn_params'] is provided[1]['turn_params']
        assert list(turn_params.new_messages) == [llm.UserMessage('go')]

        # And none of it is open once the calls are done.
        with pytest.raises(inj.ScopeNotOpenError):
            await tui.injector[agn.ToolContext]


@pytest.mark.asyncs('asyncio')
async def test_a_subagents_tool_calls_are_invoked_in_a_scope_of_its_own():
    with tempfile.TemporaryDirectory() as td:
        td = os.path.abspath(os.path.realpath(td))

        with open(os.path.join(td, 'note.txt'), 'w') as f:  # noqa: ASYNC230
            f.write('hello\n')

        provided: list = []

        async with headless_tui(inj.override(
                bind_headless_tui(Config(
                    model='scripted',
                    immediate=True,
                    in_memory=True,
                    fs=True,
                    subagents=True,
                    cwd=td,
                    autoexec=[
                        '/permissions add allow subagent {}',
                        f'/permissions add allow glob_fs \'{{"glob":"{td}/**","modes":["r"]}}\'',
                    ],
                )),
                bind_scripted_backend(
                    tool_call_message(llm.ToolCall('p1', 'subagent', {'prompt': 'look', 'profile': 'explore'})),
                    tool_call_message(llm.ToolCall('c1', 'ls', {'dir_path': td})),
                    text_message('one file: note.txt'),
                    text_message('parent done'),
                ),
                _bind_recording_direct_tool_invoker(provided),
        )) as tui:
            events: list = []
            tui.agent.subscribe(events.append)

            result = await tui.agent.prompt('go')

            assert result.reason is agn.AgentEndReason.COMPLETED
            [tr] = _tool_results(result.new_messages)
            assert not tr.is_error
            assert tr.content[0].text == 'one file: note.txt'

            # The child's call ran, from inside the parent's subagent call's opening, in an opening of the child's own
            # scope: the root's saw the parent's call alone.
            child_ends = [
                u.event
                for e in events
                if isinstance(e, agn.ToolExecutionUpdateEvent)
                if isinstance(u := e.update, agn.SubagentEventToolProgressUpdate)
                if isinstance(u.event, agn.ToolExecutionEndEvent)
            ]
            assert [e.tool_name for e in child_ends] == ['ls']
            assert child_ends[0].result.error is None

            assert [check.not_none(p['ctx'].llm_tool_call).id for p in provided] == ['p1']
