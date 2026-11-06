import uuid

import pytest

from ..... import agent as agn
from ..... import llm
from ....config import UiConfig
from ...feed import events as fe
from ...feed.feed import Feed
from ...texts import WebTextRenderer
from ..agents import AgentEventFeeder
from ..agents import AgentEventFeederLimits
from ..agents import clip_text


##


def _context(call_id: str, name: str, **args) -> agn.ToolContext:
    return agn.ToolContext(args=args, llm_tool_call=llm.ToolCall(call_id, name, args))


def _events(feed: Feed) -> list[fe.FeedEvent]:
    return [e.event for e in feed.entries_after(0)]


def test_clip_text():
    assert clip_text('abc', 3) == 'abc'
    assert clip_text('abcdefgh', 4) == 'ab\n... (4 characters not shown) ...\ngh'


@pytest.mark.asyncs('asyncio')
async def test_subagent_calls_nest_under_the_spawning_call():
    feed = Feed()
    feeder = AgentEventFeeder(feed=feed, renderer=WebTextRenderer(), config=UiConfig())

    parent = _context('p1', 'subagent', task='look')
    child = _context('c1', 'ls', dir_path='/')
    run_id = agn.SubagentRunId(uuid.UUID(int=1))

    def progress(ev: agn.Event) -> agn.ToolExecutionUpdateEvent:
        return agn.ToolExecutionUpdateEvent(
            tool=None,
            context=parent,
            update=agn.SubagentEventToolProgressUpdate(run_id=run_id, profile='explore', event=ev),
        )

    for ev in [
        agn.ToolExecutionStartEvent(tool=None, context=parent),
        progress(agn.ToolExecutionStartEvent(tool=None, context=child)),
        progress(agn.TurnStartEvent()),
        progress(agn.ToolExecutionEndEvent(tool=None, context=child, result=agn.ToolResult(
            content=llm.TextContent('a\nb'),
        ))),
    ]:
        await feeder.on_agent_event(ev)

    assert _events(feed) == [
        fe.ToolStartFeedEvent(key='p1', name='subagent', args={'task': 'look'}),
        fe.ToolStartFeedEvent(
            key='c1',
            name='ls',
            args={'dir_path': '/'},
            parent='p1',
            via=f'explore {run_id.v}',
        ),
        fe.ToolEndFeedEvent(key='c1', ok=True, result='a\nb'),
    ]


@pytest.mark.asyncs('asyncio')
async def test_tool_output_is_capped():
    feed = Feed()
    feeder = AgentEventFeeder(
        feed=feed,
        renderer=WebTextRenderer(),
        config=UiConfig(),
        limits=AgentEventFeederLimits(max_output_chars=10),
    )

    ctx = _context('b1', 'bash', command='yes')
    for text in ['12345', '67890', 'abcde', 'fghij']:
        await feeder.on_agent_event(agn.ToolExecutionUpdateEvent(
            tool=None,
            context=ctx,
            update=agn.OutputToolProgressUpdate(text),
        ))

    assert [e.text for e in _events(feed) if isinstance(e, fe.ToolOutputFeedEvent)] == [
        '12345',
        '67890',
        '\n... (further output not shown) ...\n',
    ]


@pytest.mark.asyncs('asyncio')
async def test_immediate_text_comes_at_turn_end():
    feed = Feed()
    feeder = AgentEventFeeder(feed=feed, renderer=WebTextRenderer(), config=UiConfig(immediate=True))

    await feeder.on_agent_event(agn.AgentStartEvent())
    await feeder.on_agent_event(agn.LlmAiStreamEvent(llm.TextDeltaAiStreamEvent('ignored', content_index=0)))
    await feeder.on_agent_event(agn.TurnEndEvent(message=llm.AiMessage([llm.TextContent('all at once')])))

    assert _events(feed) == [
        fe.RunStartFeedEvent(),
        fe.AiTextFeedEvent(text='all at once'),
    ]
