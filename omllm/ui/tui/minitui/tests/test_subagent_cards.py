"""A subagent's tool calls are cards of their own, beside the call which spawned it, named under its profile."""
import uuid

from omcore import lang

from ..... import agent as agn
from ..... import llm
from ...config import Config
from ..output import AgentEventRenderer
from ..output import MinituiTextDisplayer
from .utils import commit_texts
from .utils import frame_lines
from .utils import make_app


##


def _context(call: llm.ToolCall) -> agn.ToolContext:
    return agn.ToolContext(args=call.args, llm_tool_call=call)


def _wrap(parent: agn.ToolContext, run_id: agn.SubagentRunId, event: agn.Event) -> agn.ToolExecutionUpdateEvent:
    return agn.ToolExecutionUpdateEvent(
        tool=None,
        context=parent,
        update=agn.SubagentEventToolProgressUpdate(run_id=run_id, profile='explore', event=event),
    )


def test_subagent_tool_calls_are_prefixed_sibling_cards():
    app, driver = make_app()
    renderer = AgentEventRenderer(app=app, text_displayer=MinituiTextDisplayer(app=app), config=Config())

    def feed(*events):
        for ev in events:
            lang.sync_await(renderer.on_agent_event(ev))

    run_id = agn.SubagentRunId(uuid.uuid7())
    parent = _context(llm.ToolCall('p1', 'subagent', {'prompt': 'look around', 'profile': 'explore'}))
    child = _context(llm.ToolCall('c1', 'ls', {'dir_path': '/x'}))

    feed(agn.AgentStartEvent())
    driver.commits.clear()

    feed(
        agn.ToolExecutionStartEvent(tool=None, context=parent),
        _wrap(parent, run_id, agn.ToolExecutionStartEvent(tool=None, context=child)),
    )

    running = [line for line in frame_lines(app) if 'running...' in line]
    assert len(running) == 2
    assert 'subagent  running...' in running[0]
    assert 'explore/ls  running...' in running[1]

    feed(
        _wrap(parent, run_id, agn.ToolExecutionUpdateEvent(
            tool=None,
            context=child,
            update=agn.OutputToolProgressUpdate('a.txt\n'),
        )),
        _wrap(parent, run_id, agn.ToolExecutionEndEvent(
            tool=None,
            context=child,
            result=agn.ToolResult(content=llm.TextContent('a.txt')),
        )),
    )

    lines = frame_lines(app)
    assert any('subagent  running...' in line for line in lines)
    assert any('explore/ls  done' in line for line in lines)

    # The child's card finished but the subagent's did not: nothing commits yet, in start order.
    driver.fire_after(.8)
    assert driver.commits == []

    feed(
        agn.ToolExecutionEndEvent(
            tool=None,
            context=parent,
            result=agn.ToolResult(
                content=llm.TextContent('one file: a.txt'),
                details=agn.SubagentToolResultDetails(
                    run_id=run_id,
                    profile='explore',
                    reason=agn.AgentEndReason.COMPLETED,
                    num_turns=2,
                    usage=agn.UsageLedger(input=1200, output=34),
                ),
            ),
        ),
    )
    driver.fire_after(.8)

    committed = commit_texts(driver)
    assert len(committed) == 2
    assert 'subagent  done' in committed[0]
    assert 'explore/ls  done' in committed[1]

    # The card's detail is the subagent's facts over its final word, run id and all.
    app.tool_started('p2', 'subagent', ())
    app.tool_finished(
        'p2',
        'subagent',
        ok=True,
        detail_rows=renderer._result_rows(agn.ToolResult(  # noqa: SLF001
            content=llm.TextContent('one file: a.txt'),
            details=agn.SubagentToolResultDetails(
                run_id=run_id,
                profile='explore',
                reason=agn.AgentEndReason.MAX_TURNS,
                num_turns=30,
            ),
        )),
        expand=True,
    )
    text = '\n'.join(frame_lines(app))
    assert f'run {run_id.v}; profile explore; 30 turns; max_turns' in text
    assert 'one file: a.txt' in text

    feed(agn.AgentEndEvent(context=agn.Context()))
    assert not app.is_busy
