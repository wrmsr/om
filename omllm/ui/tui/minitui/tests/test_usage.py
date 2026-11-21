import pytest

from ..... import agent as agn
from ..... import llm
from ...config import TuiConfig
from ..app import MinituiChatApp
from ..output import AgentEventRenderer
from ..output import MinituiTextDisplayer
from .utils import commit_texts
from .utils import frame_lines
from .utils import make_app


##


def test_usage_count_format_promotes_rounded_units():
    assert MinituiChatApp.Usage.render_int(100_000) == '100k'
    assert MinituiChatApp.Usage.render_int(999_999) == '1m'
    assert MinituiChatApp.Usage.render_int(999_499) == '999k'
    assert MinituiChatApp.Usage.render_int(1_234_567) == '1.23m'


def test_usage_cost_format():
    assert MinituiChatApp.Usage.render_cost(0.) == '$0.00'
    assert MinituiChatApp.Usage.render_cost(.0015) == '$0.0015'
    assert MinituiChatApp.Usage.render_cost(.125) == '$0.12'
    assert MinituiChatApp.Usage.render_cost(1.5) == '$1.50'


@pytest.mark.asyncs('asyncio')
async def test_turn_usage_renders_session_traffic_and_context_occupancy():
    app, _ = make_app()
    renderer = AgentEventRenderer(app=app, text_displayer=MinituiTextDisplayer(app=app), config=TuiConfig())

    await renderer.on_agent_event(agn.AgentStartEvent())
    await renderer.on_agent_event(agn.TurnEndEvent(
        message=llm.AiMessage([], token_usage=llm.TokenUsage(input=15_000, output=100)),
        usage=agn.UsageLedger(
            input=15_000,
            output=100,
            reasoning=20,
            cache_read=12_000,
            cache_write=2_000,
            cost=.042,
        ),
        context_budget=agn.ContextBudget(
            context_limit=100_000,
            input_limit=84_000,
            threshold=82_976,
            output_reserve=16_000,
            observed_input=15_000,
        ),
    ))

    status = frame_lines(app)[-1]
    assert 'i1k c12k w2k o80 r20' in status
    assert '$0.04' in status
    assert '15k/84k' in status


@pytest.mark.asyncs('asyncio')
async def test_context_preparation_shows_estimated_pressure_and_reduction():
    app, driver = make_app()
    renderer = AgentEventRenderer(app=app, text_displayer=MinituiTextDisplayer(app=app), config=TuiConfig())

    await renderer.on_agent_event(agn.AgentStartEvent())
    await renderer.on_agent_event(agn.ContextWindowEvent(agn.ContextBudget(
        context_limit=100_000,
        input_limit=84_000,
        threshold=82_976,
        output_reserve=16_000,
        estimated_input=20_000,
    )))

    assert '~20k/84k' in frame_lines(app)[-1]

    await renderer.on_agent_event(agn.ContextReductionEvent(
        reduction=agn.ContextReduction(
            reason='threshold',
            before_tokens=90_000,
            after_tokens=70_000,
            tool_result_indices=(2, 5),
        ),
        projection=agn.ContextProjection.ZERO,
    ))

    assert any('context threshold: 90k -> 70k tokens' in text for text in commit_texts(driver))


@pytest.mark.asyncs('asyncio')
async def test_state_update_shows_model_and_clears_stale_context_on_switch():
    app, _ = make_app()
    renderer = AgentEventRenderer(app=app, text_displayer=MinituiTextDisplayer(app=app), config=TuiConfig())

    m1 = llm.Model(
        key=llm.ModelKey('anthropic', 'claude-sonnet'),
        backend='anthropic-messages',
        short_ids=llm.ModelShortIds(short_id='sonnet'),
    )
    m2 = llm.Model(
        key=llm.ModelKey('openai', 'gpt-5'),
        backend='openai-responses',
        short_ids=llm.ModelShortIds(short_id='gpt5'),
    )

    s0 = agn.State()
    s1 = agn.State(model=m1)
    await renderer.on_agent_event(agn.StateUpdateEvent(new_state=s1, old_state=s0))
    assert 'sonnet' in frame_lines(app)[-1]

    app.set_context_usage(20_000, 100_000, estimated=False)
    assert '20k/100k' in frame_lines(app)[-1]

    s2 = agn.State(model=m2)
    await renderer.on_agent_event(agn.StateUpdateEvent(new_state=s2, old_state=s1))
    status = frame_lines(app)[-1]
    assert 'gpt5' in status
    assert 'sonnet' not in status
    assert '20k/100k' not in status
