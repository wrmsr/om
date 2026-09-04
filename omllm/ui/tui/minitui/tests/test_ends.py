"""How the renderer closes a turn for each way a run can end, and how it shows a call to a tool it cannot name."""
import pytest

from ..... import agent as agn
from ..... import llm
from ...config import Config
from ..output import AgentEventRenderer
from ..output import MinituiTextDisplayer
from .utils import commit_texts
from .utils import frame_lines
from .utils import make_app


##


def _renderer(app):
    return AgentEventRenderer(app=app, text_displayer=MinituiTextDisplayer(app=app), config=Config())


async def _end(reason, error=None):
    app, driver = make_app()
    renderer = _renderer(app)

    await renderer.on_agent_event(agn.AgentStartEvent())
    busy_before = app.is_busy

    await renderer.on_agent_event(agn.AgentEndEvent(context=agn.Context(), reason=reason, error=error))
    busy_after = app.is_busy

    assert busy_before and not busy_after

    return commit_texts(driver)


@pytest.mark.asyncs('asyncio')
async def test_failed_end_shows_the_error():
    committed = await _end(agn.AgentEndReason.FAILED, RuntimeError('boom'))

    assert any('✗ failed' in c for c in committed)
    assert any("error: RuntimeError('boom')" in c for c in committed)


@pytest.mark.asyncs('asyncio')
async def test_cancelled_end_shows_no_error():
    committed = await _end(agn.AgentEndReason.CANCELLED)

    assert any('× cancelled' in c for c in committed)
    assert not any('error:' in c for c in committed)


@pytest.mark.parametrize(('reason', 'note'), [
    (agn.AgentEndReason.LENGTH, 'token limit'),
    (agn.AgentEndReason.MAX_TURNS, 'turn limit'),
])
@pytest.mark.asyncs('asyncio')
async def test_short_ends_close_normally_with_a_note(reason, note):
    committed = await _end(reason)

    assert any(note in c for c in committed)
    assert not any('failed' in c or 'cancelled' in c for c in committed)


@pytest.mark.asyncs('asyncio')
async def test_retry_is_noted():
    app, driver = make_app()
    renderer = _renderer(app)

    await renderer.on_agent_event(agn.AgentStartEvent())
    await renderer.on_agent_event(agn.LlmRetryEvent(attempts=1, delay_s=2., error=llm.TransientBackendError('busy')))

    assert any('retrying in 2s' in c for c in commit_texts(driver))


async def _unused_executor(ctx):
    raise AssertionError


@pytest.mark.asyncs('asyncio')
async def test_progress_shows_live_and_details_shape_the_finished_card():
    app, driver = make_app()
    renderer = _renderer(app)
    tool = agn.Tool(llm_tool=llm.Tool(name='bash'), executor=_unused_executor)
    context = agn.ToolContext(tool=tool, args={'command': 'x'}, llm_tool_call=llm.ToolCall('t1', 'bash', {}))

    await renderer.on_agent_event(agn.AgentStartEvent())
    await renderer.on_agent_event(agn.ToolExecutionStartEvent(tool=tool, context=context))
    await renderer.on_agent_event(agn.ToolExecutionUpdateEvent(
        tool=tool,
        context=context,
        update=agn.OutputToolProgressUpdate('hello from the stream\n'),
    ))

    # Streamed output is in the running card's detail, shown once the card is expanded.
    app._cards['t1'].card.toggle_expanded()  # noqa: SLF001
    assert any('hello from the stream' in line for line in frame_lines(app))

    await renderer.on_agent_event(agn.ToolExecutionEndEvent(
        tool=tool,
        context=context,
        result=agn.ToolResult(
            content=llm.TextContent('hello from the stream\n[exit code 3]'),
            details=agn.ExecToolResultDetails(rc=3, stdout='hello from the stream\n', stderr=''),
        ),
    ))
    await renderer.on_agent_event(agn.AgentEndEvent(context=agn.Context()))
    driver.fire_after(.8)

    committed = commit_texts(driver)
    assert any('exit code 3' in c and 'hello from the stream' in c for c in committed)


@pytest.mark.asyncs('asyncio')
async def test_unknown_tool_call_gets_a_card_named_as_the_model_named_it():
    app, driver = make_app()
    renderer = _renderer(app)
    context = agn.ToolContext(tool=None, args={}, llm_tool_call=llm.ToolCall('t1', 'frobnicate', {}))

    await renderer.on_agent_event(agn.AgentStartEvent())
    await renderer.on_agent_event(agn.ToolExecutionStartEvent(tool=None, context=context))
    assert any('frobnicate' in line for line in frame_lines(app))

    await renderer.on_agent_event(agn.ToolExecutionEndEvent(
        tool=None,
        context=context,
        result=agn.ToolResult(
            content=llm.TextContent("Unknown tool: 'frobnicate'"),
            error=agn.UnknownToolError('frobnicate'),
        ),
    ))
    await renderer.on_agent_event(agn.AgentEndEvent(context=agn.Context()))
    driver.fire_after(.8)

    assert any('frobnicate' in c and 'failed' in c for c in commit_texts(driver))
