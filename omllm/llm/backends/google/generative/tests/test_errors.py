import pytest

from ....base.http import HttpErrorDetails
from ..errors import is_google_context_overflow_error


##


def test_google_quantified_input_token_overflow():
    assert is_google_context_overflow_error(HttpErrorDetails(
        http_status=400,
        code=400,
        provider_status='INVALID_ARGUMENT',
        message='The input token count (123,456) exceeds the maximum number of tokens allowed (100,000).',
    ))


@pytest.mark.parametrize('error', [
    # INVALID_ARGUMENT covers every malformed request, so the status alone conveys no overflow semantics.
    HttpErrorDetails(
        http_status=400,
        code=400,
        provider_status='INVALID_ARGUMENT',
        message='Request contains an invalid argument.',
    ),
    # Even token-related validation is not necessarily about the reducible input context.
    HttpErrorDetails(
        http_status=400,
        code=400,
        provider_status='INVALID_ARGUMENT',
        message='maxOutputTokens exceeds the maximum number of tokens allowed.',
    ),
    # Matching wording under a different provider status is not the documented GenerateContent overflow envelope.
    HttpErrorDetails(
        http_status=400,
        code=400,
        provider_status='FAILED_PRECONDITION',
        message='The input token count (123) exceeds the maximum number of tokens allowed (100).',
    ),
])
def test_unrelated_google_validation_errors_fail_closed(error):
    assert not is_google_context_overflow_error(error)
