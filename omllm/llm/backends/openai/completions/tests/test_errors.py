import pytest

from ....base.http import HttpErrorDetails
from ...errors import is_openai_context_overflow_error


##


@pytest.mark.parametrize('error', [
    HttpErrorDetails(http_status=400, code='context_length_exceeded'),
    HttpErrorDetails(http_status=400, code='PROMPT_TOO_LONG'),
    HttpErrorDetails(http_status=400, error_type='context_window_exceeded'),
])
@pytest.mark.parametrize('provider', ['openai', 'groq', 'cerebras', 'openrouter'])
def test_structured_openai_compatible_overflow_codes(provider, error):
    assert is_openai_context_overflow_error(error, provider=provider)


def test_openrouter_quantified_router_message():
    error = HttpErrorDetails(
        http_status=400,
        code=400,
        message=(
            "This endpoint's maximum context length is 131072 tokens. However, you requested about 135349 tokens "
            '(60662 of text input, 10687 of tool input, 64000 in the output). Please reduce the length of either one, '
            'or use the context-compression plugin.'
        ),
    )

    assert is_openai_context_overflow_error(error, provider='openrouter')


@pytest.mark.parametrize(('provider', 'message'), [
    # The OpenRouter fallback must not leak to another backend merely because it uses the OpenAI request shape.
    (
        'openai',
        "This endpoint's maximum context length is 100 tokens. However, you requested 101 tokens.",
    ),
    # Suggestive prose without the router's quantified sentence is not a protocol contract.
    ('openrouter', 'Request too large for model: maximum context length exceeded.'),
    # A broad validation type identifies neither context pressure nor a recoverable request.
    ('openrouter', 'invalid request'),
])
def test_unstructured_openai_compatible_errors_fail_closed(provider, message):
    error = HttpErrorDetails(
        http_status=400,
        code=400,
        error_type='invalid_request_error',
        message=message,
    )

    assert not is_openai_context_overflow_error(error, provider=provider)
