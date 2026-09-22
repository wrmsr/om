"""
The summarizing compactor, offline: where it cuts, what it shows the summarizer, and what it hands back. Token figures
are the character estimator's: eight a message, plus a quarter of its text.
"""
import pytest

from omcore import check

from .... import llm
from ...tests.scripted import scripted_backend
from ...tests.scripted import text_message
from ...types.contexts import Context
from ...types.lifecycle import ContextProjection
from ...types.lifecycle import ToolResultProjection
from ...types.messages import InfoAgentMessage
from ..estimators import CharacterContextTokenEstimator
from ..summarizing import DEFAULT_SUMMARY_SYSTEM_PROMPT
from ..summarizing import SummarizingContextCompactor


##


def _tool_group(call_id: str, name: str, text: str):
    return [
        llm.AiMessage([llm.ToolCall(call_id, name, {})]),
        llm.ToolResultMessage(
            tool_call_id=call_id,
            tool_name=name,
            content=(llm.TextContent(text),),
        ),
    ]


def _two_reads():
    # Groups of 9, 121, 9, 121, and 9 tokens: a user turn, a read of 400 characters, and again, then a closing word.
    return [
        llm.UserMessage('a'),
        *_tool_group('t1', 'read', 'x' * 400),
        llm.UserMessage('b'),
        *_tool_group('t2', 'read', 'y' * 400),
        llm.AiMessage([llm.TextContent('done')]),
    ]


def _compactor(**kwargs):
    return SummarizingContextCompactor(config=SummarizingContextCompactor.Config(**kwargs))


def _capturing_backend(*turns):
    seen: list[llm.Context] = []

    def expect(invocation):
        seen.append(invocation.context)

    backend = scripted_backend(*[
        llm.BackendScriptTurn(turn, expect=expect)
        for turn in turns
    ])
    return backend, seen


def _request_text(request: llm.Context) -> str:
    [message] = request.messages or []
    return check.isinstance(check.isinstance(message, llm.UserMessage).content, str)


@pytest.mark.asyncs('asyncio')
async def test_cut_keeps_the_newest_tokens_and_never_splits_a_tool_call_from_its_results():
    backend, seen = _capturing_backend(text_message('Summary.'))
    context = Context(messages=[InfoAgentMessage('note'), *_two_reads()])

    projection = await _compactor(keep_recent_tokens=200, max_summary_tokens=50).compact(
        context,
        backend=backend,
        target_tokens=10_000,
        reason='threshold',
    )

    # Two hundred tokens of tail is the closing word, the second read, and the user turn ahead of it: the first read
    # would not fit, and its call is not to be kept without its result.
    assert projection == ContextProjection(summary='Summary.', first_kept_message_index=4)
    assert backend.invocations == 1

    [request] = seen
    assert request.system_prompt == DEFAULT_SUMMARY_SYSTEM_PROMPT
    assert request.tools is None
    text = _request_text(request)
    assert '## User\n\na' in text
    assert '[Tool call read: {}]' in text
    assert '## Tool result read\n\n' + 'x' * 400 in text
    assert 'y' * 400 not in text
    assert 'done' not in text
    assert 'note' not in text  # Agent messages are shown as they are projected, which by default is not at all.
    assert 'omitted' not in text
    assert 'Additional instructions' not in text


@pytest.mark.asyncs('asyncio')
async def test_repeated_compaction_folds_the_previous_summary_and_keeps_the_tails_tool_result_projections():
    backend, seen = _capturing_backend(text_message('Folded.'))
    context = Context(
        messages=_two_reads(),
        projection=ContextProjection(
            summary='Earlier: constraints.',
            first_kept_message_index=3,
            tool_results=(
                ToolResultProjection(message_index=2, max_chars=0),
                ToolResultProjection(message_index=5, max_chars=100),
            ),
        ),
    )

    projection = await _compactor(keep_recent_tokens=60, max_summary_tokens=50).compact(
        context,
        backend=backend,
        target_tokens=10_000,
        reason='manual',
    )

    # The second read, at its projected hundred characters, fits with the closing word; the user turn does not.
    assert projection == ContextProjection(
        summary='Folded.',
        first_kept_message_index=4,
        tool_results=(ToolResultProjection(message_index=5, max_chars=100),),
    )

    [request] = seen
    text = _request_text(request)
    assert 'summarized earlier' in text
    assert 'Earlier: constraints.' in text
    assert '## User\n\nb' in text
    assert 'x' * 400 not in text
    assert 'y' * 400 not in text


@pytest.mark.asyncs('asyncio')
async def test_nothing_new_to_summarize_is_no_compaction():
    backend, _ = _capturing_backend(text_message('never'))
    compactor = _compactor(keep_recent_tokens=1_000, max_summary_tokens=50)

    # Everything fits in the tail.
    assert await compactor.compact(
        Context(messages=[llm.UserMessage('a'), llm.AiMessage([llm.TextContent('done')])]),
        backend=backend,
        target_tokens=10_000,
        reason='manual',
    ) is None

    # Nothing stands after the last summary.
    assert await compactor.compact(
        Context(
            messages=[llm.UserMessage('a'), llm.AiMessage([llm.TextContent('done')])],
            projection=ContextProjection(summary='s', first_kept_message_index=2),
        ),
        backend=backend,
        target_tokens=0,
        reason='overflow',
    ) is None

    # The newest group is kept whatever the target, and there is nothing ahead of it.
    assert await compactor.compact(
        Context(messages=[llm.UserMessage('a')]),
        backend=backend,
        target_tokens=0,
        reason='overflow',
    ) is None

    assert backend.invocations == 0


@pytest.mark.asyncs('asyncio')
async def test_material_is_trimmed_to_the_summarizer_models_input_budget():
    seen: list[llm.Context] = []

    def expect(invocation):
        seen.append(invocation.context)

    limits = llm.ModelLimits(context=250, output=100)
    backend = llm.ScriptedImmediateBackend(
        llm.Model(key=llm.ModelKey('test', 'summarizer'), backend='test', limits=limits),
        llm.BackendScript([llm.BackendScriptTurn(text_message('Summary.'), expect=expect)]),
    )
    context = Context(messages=[
        llm.UserMessage('a' * 400),
        llm.AiMessage([llm.TextContent('ok')]),
        llm.UserMessage('b' * 400),
        llm.AiMessage([llm.TextContent('ok')]),
        llm.UserMessage('c' * 400),
        llm.AiMessage([llm.TextContent('ok')]),
        llm.UserMessage('now'),
    ])
    compactor = _compactor(
        keep_recent_tokens=0,
        max_summary_tokens=50,
        safety_margin_tokens=0,
        system_prompt='S',
    )

    projection = await compactor.compact(
        context,
        backend=backend,
        target_tokens=10_000,
        reason='manual',
    )

    assert projection == ContextProjection(summary='Summary.', first_kept_message_index=6)

    # Two hundred tokens of budget takes the newest user turn and the words around it, not the one before.
    [request] = seen
    text = _request_text(request)
    assert '[3 earlier messages omitted]' in text
    assert 'c' * 400 in text
    assert 'b' * 400 not in text
    assert CharacterContextTokenEstimator().estimate_context(request) <= limits.input_budget(output_reserve=50)


@pytest.mark.asyncs('asyncio')
async def test_instructions_reach_the_summarizer_and_an_empty_summary_is_no_compaction():
    backend, seen = _capturing_backend(text_message('Summary.'), text_message(''))
    compactor = _compactor(keep_recent_tokens=0, max_summary_tokens=50)
    context = Context(messages=[llm.UserMessage('a'), llm.AiMessage([llm.TextContent('done')])])

    projection = await compactor.compact(
        context,
        backend=backend,
        target_tokens=10_000,
        reason='manual',
        instructions='Keep the file list.',
    )

    assert projection is not None and projection.summary == 'Summary.'
    assert 'Additional instructions for this summary:\n\nKeep the file list.' in _request_text(seen[0])

    assert await compactor.compact(
        context,
        backend=backend,
        target_tokens=10_000,
        reason='manual',
    ) is None
    assert backend.invocations == 2
