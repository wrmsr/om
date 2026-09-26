import pytest

from omcore import dataclasses as dc
from omcore import marshal as msh

from ...models.default import default_model_catalog
from ...types.context import Context
from ...types.models import ModelKey
from ...types.options import Options
from ...types.options import ReasoningEffort
from ...types.tools import Tool
from ..anthropic.messages.requests import RequestPreparer as AnthropicRequestPreparer
from ..google.generative.requests import RequestPreparer as GoogleRequestPreparer
from ..openai.completions.requests import RequestPreparer as CompletionsRequestPreparer
from ..openai.responses.requests import RequestPreparer as ResponsesRequestPreparer


##


@pytest.mark.parametrize(('key', 'preparer', 'expected'), [
    (ModelKey('openai', 'gpt-6-luna'), ResponsesRequestPreparer, {'reasoning': {'effort': 'low'}}),
    (ModelKey('openai', 'gpt-5.4-nano'), CompletionsRequestPreparer, {'reasoning_effort': 'low'}),
    (ModelKey('anthropic', 'claude-sonnet-5'), AnthropicRequestPreparer, {
        'output_config': {'effort': 'low'},
        'thinking': {'type': 'adaptive'},
    }),
    (ModelKey('google', 'gemini-3-flash-preview'), GoogleRequestPreparer, {
        'generationConfig': {'thinkingConfig': {'thinkingLevel': 'LOW'}},
    }),
])
def test_effort_request_shapes_and_defaults(key, preparer, expected):
    model = default_model_catalog()[key]
    raw = preparer(model, Context(), Options(reasoning_effort=ReasoningEffort.LOW)).raw_request()
    for field, value in expected.items():
        assert raw[field] == value

    inherited = dc.replace(model, default_options=Options(reasoning_effort=ReasoningEffort.LOW))
    raw = preparer(inherited, Context()).raw_request()
    for field, value in expected.items():
        assert raw[field] == value

    with pytest.raises(ValueError, match='does not support effort'):
        preparer(dc.replace(model, reasoning_efforts=None), Context(), Options(
            reasoning_effort=ReasoningEffort.LOW,
        )).raw_request()


@pytest.mark.parametrize('thinking', [None, False, True])
def test_gemini_effort_and_returned_thoughts_are_independent(thinking):
    model = default_model_catalog()[ModelKey('google', 'gemini-3-flash-preview')]
    raw = GoogleRequestPreparer(model, Context(), Options(
        reasoning_effort=ReasoningEffort.MINIMAL,
        thinking=thinking,
    )).raw_request()
    expected = {'thinkingLevel': 'MINIMAL'}
    if thinking is not None:
        expected['includeThoughts'] = thinking
    assert raw['generationConfig']['thinkingConfig'] == expected

    for effort in [ReasoningEffort.NONE, ReasoningEffort.XHIGH, ReasoningEffort.MAX]:
        with pytest.raises(ValueError, match='does not support effort'):
            GoogleRequestPreparer(model, Context(), Options(reasoning_effort=effort)).raw_request()


def test_openai_effort_preserves_summary_request():
    model = default_model_catalog()[ModelKey('openai', 'gpt-6-luna')]
    raw = ResponsesRequestPreparer(model, Context(), Options(
        reasoning_effort=ReasoningEffort.HIGH,
        thinking=True,
    )).raw_request()
    assert raw['reasoning'] == {'effort': 'high', 'summary': 'auto'}
    assert 'reasoning' not in ResponsesRequestPreparer(model, Context()).raw_request()


def test_completions_rejects_tool_effort_combinations_before_sending():
    model = default_model_catalog()[ModelKey('openai', 'gpt-5.4-nano')]
    context = Context(tools=[Tool(name='act')])
    with pytest.raises(ValueError, match='does not support effort low with tools'):
        CompletionsRequestPreparer(model, context, Options(reasoning_effort=ReasoningEffort.LOW)).raw_request()
    raw = CompletionsRequestPreparer(model, context, Options(reasoning_effort=ReasoningEffort.NONE)).raw_request()
    assert raw['reasoning_effort'] == 'none'
    assert raw['tools']


def test_effort_is_optional_and_roundtrips():
    options = Options(thinking=False, reasoning_effort=ReasoningEffort.NONE)
    assert msh.unmarshal(msh.marshal(options), Options) == options
    assert options.merge(Options(reasoning_effort=ReasoningEffort.LOW)) == Options(
        thinking=False,
        reasoning_effort=ReasoningEffort.LOW,
    )
    with pytest.raises(dc.FieldFnValidationError):
        Options(reasoning_effort='low')  # type: ignore[arg-type]
