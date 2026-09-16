import pytest

from omcore import check

from .... import llm
from ...projection.builders import StandardLlmContextBuilder
from ...types.context_lifecycle import ContextLifecycleConfig
from ...types.context_lifecycle import ContextProjection
from ...types.context_lifecycle import ContextReductionReason
from ...types.contexts import Context
from ..compactors import ContextCompactor
from ..managers import StandardContextLifecycleManager


##


def _tool_group(call_id: str, name: str, text: str, *, error: bool = False):
    return [
        llm.AiMessage([llm.ToolCall(call_id, name, {})]),
        llm.ToolResultMessage(
            tool_call_id=call_id,
            tool_name=name,
            content=(llm.TextContent(text),),
            is_error=error,
        ),
    ]


@pytest.mark.asyncs('asyncio')
async def test_individual_tool_output_is_bounded_only_in_the_projection():
    full_text = 'x' * 1_000
    group = _tool_group('t1', 'read', full_text)
    result_message = group[1]
    context = Context(messages=[llm.UserMessage('go'), *group])

    result = await StandardContextLifecycleManager().prepare(
        context,
        builder=StandardLlmContextBuilder(),
        model=llm.Model(key=llm.ModelKey('test', 'unlimited'), backend='test'),
        options=None,
        config=ContextLifecycleConfig(max_tool_result_chars=100),
    )

    assert result.reduction is not None
    assert result.reduction.reason == 'tool_output_limit'
    assert result.reduction.tool_result_indices == (2,)
    assert result.context.messages is not None and result.context.messages[2] is result_message
    assert check.isinstance(result.context.messages[2], llm.ToolResultMessage).content[0].text == full_text
    projected = check.isinstance((result.llm_context.messages or [])[2], llm.ToolResultMessage)
    assert len(projected.content[0].text) == 100


@pytest.mark.asyncs('asyncio')
async def test_threshold_prunes_an_old_result_but_keeps_the_recent_tail():
    old_text = 'o' * 4_000
    recent_text = 'r' * 4_000
    context = Context(messages=[
        llm.UserMessage('old'),
        *_tool_group('t1', 'read', old_text),
        llm.UserMessage('recent'),
        *_tool_group('t2', 'read', recent_text),
    ])
    model = llm.Model(
        key=llm.ModelKey('test', 'small'),
        backend='test',
        limits=llm.ModelLimits(context=2_200, input=1_900, output=100),
    )

    result = await StandardContextLifecycleManager().prepare(
        context,
        builder=StandardLlmContextBuilder(),
        model=model,
        options=None,
        config=ContextLifecycleConfig(
            max_tool_result_chars=None,
            keep_recent_tokens=1_000,
            prune_headroom_tokens=100,
            safety_margin_tokens=0,
        ),
    )

    assert result.reduction is not None
    assert result.reduction.reason == 'threshold'
    assert result.reduction.tool_result_indices == (2,)
    assert result.context.context_budget is not None
    assert result.context.context_budget.estimated_input is not None
    assert result.context.context_budget.estimated_input <= 1_800

    projected = result.llm_context.messages or []
    assert 'Earlier read result pruned' in check.isinstance(projected[2], llm.ToolResultMessage).content[0].text
    assert check.isinstance(projected[5], llm.ToolResultMessage).content[0].text == recent_text

    # Both original results remain byte-for-byte intact in the transcript.
    assert check.isinstance((context.messages or [])[2], llm.ToolResultMessage).content[0].text == old_text
    assert check.isinstance((context.messages or [])[5], llm.ToolResultMessage).content[0].text == recent_text


@pytest.mark.asyncs('asyncio')
async def test_forced_recovery_does_not_prune_errors_or_mutating_tool_results():
    context = Context(messages=[
        llm.UserMessage('go'),
        *_tool_group('t1', 'read', 'failed' * 1_000, error=True),
        *_tool_group('t2', 'write', 'written' * 1_000),
    ])

    result = await StandardContextLifecycleManager().recover_overflow(
        context,
        builder=StandardLlmContextBuilder(),
        model=llm.Model(key=llm.ModelKey('test', 'unknown'), backend='test'),
        options=None,
        config=ContextLifecycleConfig(max_tool_result_chars=None),
    )

    assert result.reduction is None
    assert result.context.projection == ContextProjection()


class _RecordingCompactor(ContextCompactor):
    def __init__(self) -> None:
        super().__init__()

        self.calls: list[tuple[Context, int, ContextReductionReason]] = []

    async def compact(self, context, *, target_tokens, reason):
        self.calls.append((context, target_tokens, reason))
        return ContextProjection(summary='The old material was summarized.', first_kept_message_index=1)


@pytest.mark.asyncs('asyncio')
async def test_compactor_seam_runs_after_deterministic_reduction_is_insufficient():
    compactor = _RecordingCompactor()
    context = Context(messages=[
        llm.UserMessage('x' * 5_000),
        llm.UserMessage('keep me'),
    ])
    model = llm.Model(
        key=llm.ModelKey('test', 'small'),
        backend='test',
        limits=llm.ModelLimits(context=1_000, input=900, output=100),
    )

    result = await StandardContextLifecycleManager(compactor=compactor).prepare(
        context,
        builder=StandardLlmContextBuilder(),
        model=model,
        options=None,
        config=ContextLifecycleConfig(
            max_tool_result_chars=None,
            prune_tool_results=False,
            safety_margin_tokens=0,
            prune_headroom_tokens=100,
        ),
    )

    assert len(compactor.calls) == 1
    assert result.reduction is not None and result.reduction.compacted
    assert result.context.projection.summary == 'The old material was summarized.'
    assert result.context.messages == context.messages
    kept = check.isinstance((result.llm_context.messages or [])[0], llm.UserMessage)
    assert 'keep me' in check.isinstance(kept.content, str)
