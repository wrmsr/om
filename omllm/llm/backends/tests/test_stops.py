"""Every backend's stop reason translation: what it knows, and that what it does not know is carried, not raised."""
from ..anthropic.messages.responses import translate_stop_reason as anthropic_stop_reason
from ..google.generative.responses import translate_stop_reason as google_stop_reason
from ..openai.completions.responses import translate_stop_reason as completions_stop_reason
from ..openai.responses.responses import translate_stop_reason as responses_stop_reason


def test_anthropic():
    assert anthropic_stop_reason('end_turn') == 'stop'
    assert anthropic_stop_reason('stop_sequence') == 'stop'
    assert anthropic_stop_reason('max_tokens') == 'length'
    assert anthropic_stop_reason('model_context_window_exceeded') == 'context_length'
    assert anthropic_stop_reason('tool_use') == 'tool_use'
    assert anthropic_stop_reason('refusal') == 'error'

    assert anthropic_stop_reason('pause_turn') == 'other'
    assert anthropic_stop_reason('something_new') == 'other'


def test_openai_completions():
    assert completions_stop_reason('stop') == 'stop'
    assert completions_stop_reason('length') == 'length'
    assert completions_stop_reason('tool_calls') == 'tool_use'
    assert completions_stop_reason('function_call') == 'tool_use'
    assert completions_stop_reason('content_filter') == 'error'
    assert completions_stop_reason('error') == 'error'

    assert completions_stop_reason('something_new') == 'other'


def test_openai_responses():
    assert responses_stop_reason('completed') == 'stop'
    assert responses_stop_reason('completed', has_tool_calls=True) == 'tool_use'
    assert responses_stop_reason('incomplete', incomplete_reason='max_output_tokens') == 'length'
    assert responses_stop_reason('incomplete', incomplete_reason='content_filter') == 'error'
    assert responses_stop_reason('cancelled') == 'error'

    assert responses_stop_reason('something_new') == 'other'


def test_google():
    assert google_stop_reason('STOP') == 'stop'
    assert google_stop_reason('MAX_TOKENS') == 'length'
    assert google_stop_reason('SAFETY') == 'error'
    assert google_stop_reason('MALFORMED_FUNCTION_CALL') == 'error'

    assert google_stop_reason('SOMETHING_NEW') == 'other'
