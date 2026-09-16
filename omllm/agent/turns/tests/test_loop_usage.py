import pytest

from omcore.asyncs.asynclite import all as asl

from .... import llm
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ...types.context_lifecycle import UsageLedger
from ...types.contexts import Context
from ...types.events import TurnEndEvent
from ..loop import TurnLoop


##


@pytest.mark.asyncs('asyncio')
async def test_loop_accumulates_usage_and_publishes_the_context_budget():
    model = llm.Model(
        key=llm.ModelKey('test', 'usage'),
        backend='scripted',
        limits=llm.ModelLimits(context=100_000, input=80_000, output=30_000),
    )
    message = llm.AiMessage(
        [llm.TextContent('done')],
        stop_reason='stop',
        token_usage=llm.TokenUsage(
            input=15_000,
            output=100,
            reasoning=20,
            cache_read=12_000,
            cache_write=2_000,
        ),
    )
    backend = llm.ScriptedImmediateBackend(model, llm.BackendScript([llm.BackendScriptTurn(message)]))
    events: list = []

    result = await TurnLoop(
        new_messages=[llm.UserMessage('go')],
        context=Context(usage=UsageLedger(input=100, output=10)),
        subscriber=events.append,
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
        llm_backend=backend,
    ).run()

    assert result.context.usage == UsageLedger(
        input=15_100,
        output=110,
        reasoning=20,
        cache_read=12_000,
        cache_write=2_000,
    )

    [turn_end] = [event for event in events if isinstance(event, TurnEndEvent)]
    assert turn_end.usage == result.context.usage
    assert turn_end.context_budget is not None
    assert turn_end.context_budget.observed_input == 15_000
    assert turn_end.context_budget.input_limit == 80_000
