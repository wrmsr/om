import pytest

from ..... import agent as agn
from ..... import llm
from ...config import Config
from ..app import MinituiChatApp
from ..output import AgentEventRenderer
from ..output import MinituiTextDisplayer
from .utils import commit_texts
from .utils import frame_lines
from .utils import make_app


##


def test_usage_count_format_promotes_rounded_units():
    assert MinituiChatApp.Usage.render_int(999_999) == '1m'
    assert MinituiChatApp.Usage.render_int(999_499) == '999k'
    assert MinituiChatApp.Usage.render_int(1_234_567) == '1.23m'


@pytest.mark.asyncs('asyncio')
async def test_turn_usage_renders_session_traffic_and_context_occupancy():
    app, _ = make_app()
    renderer = AgentEventRenderer(app=app, text_displayer=MinituiTextDisplayer(app=app), config=Config())

    await renderer.on_agent_event(agn.AgentStartEvent())
    await renderer.on_agent_event(agn.TurnEndEvent(
        message=llm.AiMessage([], token_usage=llm.TokenUsage(input=15_000, output=100)),
        usage=agn.UsageLedger(
            input=15_000,
            output=100,
            reasoning=20,
            cache_read=12_000,
            cache_write=2_000,
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
    assert '15k/84k' in status


@pytest.mark.asyncs('asyncio')
async def test_context_preparation_shows_estimated_pressure_and_reduction():
    app, driver = make_app()
    renderer = AgentEventRenderer(app=app, text_displayer=MinituiTextDisplayer(app=app), config=Config())

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
