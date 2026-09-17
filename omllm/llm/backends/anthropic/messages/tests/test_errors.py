import pytest

from ....base.http import HttpErrorDetails
from ..errors import is_anthropic_context_overflow_error


##


@pytest.mark.parametrize('message', [
    'prompt is too long: 200680 tokens > 200000 maximum',
    'Prompt is too long',
    (
        'input length and `max_tokens` exceed context limit: '
        '197089 + 21333 > 200000, decrease input length or `max_tokens` and try again'
    ),
    'Request size exceeds model context window',
])
def test_anthropic_context_overflow_messages(message):
    assert is_anthropic_context_overflow_error(HttpErrorDetails(
        http_status=400,
        error_type='invalid_request_error',
        message=message,
    ))


@pytest.mark.parametrize('error', [
    # The same broad error type is used for many schema and conversation-integrity failures.
    HttpErrorDetails(
        http_status=400,
        error_type='invalid_request_error',
        message='messages.2: tool_result block must follow a matching tool_use block',
    ),
    # A phrase embedded in a larger diagnostic is not one of the complete provider messages we support.
    HttpErrorDetails(
        http_status=400,
        error_type='invalid_request_error',
        message='Invalid metadata value: prompt is too long',
    ),
    # Anthropic documents request_too_large for the byte-size limit; pruning tokens is not assumed to repair it.
    HttpErrorDetails(
        http_status=413,
        error_type='request_too_large',
        message='Request exceeds the maximum allowed number of bytes',
    ),
])
def test_unrelated_anthropic_validation_errors_fail_closed(error):
    assert not is_anthropic_context_overflow_error(error)
