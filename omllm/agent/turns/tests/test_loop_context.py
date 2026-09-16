import pytest

from omcore import check
from omcore.asyncs.asynclite import all as asl

from .... import llm
from ....core.asyncs.asyncio import AsyncioGroupRunner
from ...tests.tools import bare_tool
from ...types.context_lifecycle import ContextLifecycleConfig
from ...types.contexts import Context
from ...types.events import ContextReductionEvent
from ...types.events import LlmRetryEvent
from ...types.tools import ToolResult
from ...types.tools import ToolSet
from ...types.turns import AgentEndReason
from ...types.turns import TurnConfig
from ..loop import TurnLoop


##


def _model() -> llm.Model:
    return llm.Model(
        key=llm.ModelKey('test', 'context'),
        backend='scripted',
        limits=llm.ModelLimits(context=100_000, input=99_000, output=1_000),
    )


def _context_with_prunable_result(text: str = 'x' * 3_000) -> Context:
    return Context(messages=[
        llm.UserMessage('old request'),
        llm.AiMessage([llm.ToolCall('t1', 'read', {})]),
        llm.ToolResultMessage(
            tool_call_id='t1',
            tool_name='read',
            content=(llm.TextContent(text),),
        ),
    ])


def _config() -> TurnConfig:
    return TurnConfig(context_lifecycle=ContextLifecycleConfig(
        max_tool_result_chars=None,
        prune_min_chars=100,
        max_overflow_retries=1,
    ))


def _backend(*turns, stream=False, gate=None, model=None):
    script_turns = [
        turn if isinstance(turn, llm.BackendScriptTurn) else llm.BackendScriptTurn(
            error=turn,
        ) if isinstance(turn, BaseException) else llm.BackendScriptTurn(turn)
        for turn in turns
    ]
    script = llm.BackendScript(script_turns, gate=gate)
    cls = llm.ScriptedStreamBackend if stream else llm.ScriptedImmediateBackend
    return cls(model if model is not None else _model(), script)


async def _run(backend, *, context=None, events=None):
    return await TurnLoop(
        new_messages=[llm.UserMessage('continue')],
        config=_config(),
        context=context,
        subscriber=events.append if events is not None else None,
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
        llm_backend=backend,
    ).run()


@pytest.mark.asyncs('asyncio')
async def test_context_overflow_prunes_and_retries_once_without_touching_history():
    seen = []

    def expect(invocation):
        seen.append(invocation.context)

    backend = _backend(
        llm.ContextOverflowBackendError('too long'),
        llm.BackendScriptTurn(
            llm.AiMessage([llm.TextContent('done')], stop_reason='stop'),
            expect=expect,
        ),
    )
    original = _context_with_prunable_result()
    original_text = check.isinstance((original.messages or [])[2], llm.ToolResultMessage).content[0].text
    events: list = []

    result = await _run(backend, context=original, events=events)

    assert result.reason is AgentEndReason.COMPLETED
    assert backend.invocations == 2
    assert not [event for event in events if isinstance(event, LlmRetryEvent)]
    [reduction] = [event.reduction for event in events if isinstance(event, ContextReductionEvent)]
    assert reduction.reason == 'overflow'
    assert reduction.tool_result_indices == (2,)

    [retried_context] = seen
    retried_result = check.isinstance((retried_context.messages or [])[2], llm.ToolResultMessage)
    assert 'Earlier read result pruned' in retried_result.content[0].text

    # The complete tool output remains in the agent context and can be persisted or inspected later.
    durable_result = check.isinstance((result.context.messages or [])[2], llm.ToolResultMessage)
    assert durable_result.content[0].text == original_text


@pytest.mark.asyncs('asyncio')
async def test_context_overflow_without_reducible_material_is_not_retried():
    error = llm.ContextOverflowBackendError('too long')
    backend = _backend(error, llm.AiMessage([llm.TextContent('never')], stop_reason='stop'))

    result = await _run(backend, context=Context())

    assert result.reason is AgentEndReason.FAILED
    assert result.error is error
    assert backend.invocations == 1


@pytest.mark.asyncs('asyncio')
async def test_context_overflow_recovery_is_bounded():
    last = llm.ContextOverflowBackendError('still too long')
    backend = _backend(
        llm.ContextOverflowBackendError('too long'),
        last,
        llm.AiMessage([llm.TextContent('never')], stop_reason='stop'),
    )

    result = await _run(backend, context=_context_with_prunable_result())

    assert result.reason is AgentEndReason.FAILED
    assert result.error is last
    assert backend.invocations == 2


@pytest.mark.asyncs('asyncio')
async def test_context_overflow_after_stream_content_is_not_retried():
    async def gate(point):
        if point.invocation_index == 0 and point.emission_index == 2:
            raise llm.ContextOverflowBackendError('too late')

    backend = _backend(
        llm.AiMessage([llm.TextContent('first')], stop_reason='stop'),
        llm.AiMessage([llm.TextContent('never')], stop_reason='stop'),
        stream=True,
        gate=gate,
    )

    result = await _run(backend, context=_context_with_prunable_result())

    assert result.reason is AgentEndReason.FAILED
    assert isinstance(result.error, llm.ContextOverflowBackendError)
    assert backend.invocations == 1
    assert not result.context.projection.tool_results


@pytest.mark.asyncs('asyncio')
async def test_tool_output_is_bounded_before_the_post_tool_llm_call():
    full_text = 'z' * 50_000
    seen = []

    async def execute(ctx):
        return ToolResult(content=llm.TextContent(full_text))

    def expect(invocation):
        seen.append(invocation.context)

    model = llm.Model(
        key=llm.ModelKey('test', 'small'),
        backend='scripted',
        limits=llm.ModelLimits(context=10_000, input=9_000, output=1_000),
    )
    backend = _backend(
        llm.AiMessage([llm.ToolCall('t1', 'read', {})], stop_reason='tool_use'),
        llm.BackendScriptTurn(
            llm.AiMessage([llm.TextContent('done')], stop_reason='stop'),
            expect=expect,
        ),
        model=model,
    )
    events: list = []

    result = await TurnLoop(
        new_messages=[llm.UserMessage('read')],
        config=TurnConfig(),
        context=Context(tools=ToolSet([bare_tool('read', execute)])),
        subscriber=events.append,
        cancellation=asl.asyncio.Cancellation(),
        group_runner=AsyncioGroupRunner(),
        llm_backend=backend,
    ).run()

    assert result.reason is AgentEndReason.COMPLETED
    [second_context] = seen
    projected_result = check.isinstance((second_context.messages or [])[2], llm.ToolResultMessage)
    assert len(projected_result.content[0].text) == 30_000

    durable_result = check.isinstance((result.context.messages or [])[2], llm.ToolResultMessage)
    assert durable_result.content[0].text == full_text
    assert any(
        isinstance(event, ContextReductionEvent) and event.reduction.reason == 'tool_output_limit'
        for event in events
    )
