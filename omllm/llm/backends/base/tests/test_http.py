import email.utils
import time

import pytest

from omcore.http import all as http

from ....types.errors import BackendError
from ....types.errors import ContextOverflowBackendError
from ....types.errors import TransientBackendError
from ..http import HttpErrorDetails
from ..http import parse_http_error_details
from ..http import parse_retry_after_header
from ..http import raise_for_http_status
from ..http import translating_http_client_errors


##


def _response(status, *, headers=None, data=None):
    return http.HttpClientResponse(
        request=http.HttpClientRequest('http://example.invalid/'),
        status=status,
        headers=http.HttpHeaders(headers) if headers is not None else None,
        data=data,
    )


@pytest.mark.parametrize('status', [408, 429, 500, 502, 503, 504, 529])
def test_transient_statuses_raise_transient_errors(status):
    with pytest.raises(TransientBackendError) as ei:
        raise_for_http_status(_response(status))

    assert ei.value.retry_after_s is None
    assert isinstance(ei.value.__cause__, http.StatusHttpClientError)
    assert ei.value.__cause__.response.status == status


@pytest.mark.parametrize('status', [400, 401, 403, 404, 413, 422])
def test_other_statuses_raise_plain_errors_with_the_body(status):
    with pytest.raises(BackendError) as ei:
        raise_for_http_status(_response(status, data=b'{"error": "no such model"}'))

    assert not isinstance(ei.value, TransientBackendError)
    assert 'no such model' in str(ei.value)
    assert f'HTTP {status}' in str(ei.value)


def test_explicit_context_overflow_classifier_raises_typed_error():
    def classify(error: HttpErrorDetails) -> bool:
        return error.code_is('context_length_exceeded')

    with pytest.raises(ContextOverflowBackendError) as ei:
        raise_for_http_status(
            _response(400, data=b'{"error":{"code":"context_length_exceeded","message":"too long"}}'),
            context_overflow_classifier=classify,
        )

    assert not isinstance(ei.value, TransientBackendError)
    assert isinstance(ei.value.__cause__, http.StatusHttpClientError)


@pytest.mark.parametrize('data', [
    b'{"error":{"message":"prompt is too long"}}',
    b'{"error":{"message":"maximum context length"}}',
    b'{"error":{"message":"request too large for model"}}',
])
def test_overflow_sounding_message_has_no_global_meaning(data):
    with pytest.raises(BackendError) as ei:
        raise_for_http_status(_response(400, data=data))

    assert not isinstance(ei.value, ContextOverflowBackendError)


def test_error_details_prefer_the_nested_provider_error():
    details = parse_http_error_details(_response(400, data=(
        b'{"type":"error","code":"outer",'
        b'"error":{"type":"invalid_request_error","code":400,"status":"INVALID_ARGUMENT","message":"bad"}}'
    )))

    assert details == HttpErrorDetails(
        http_status=400,
        code=400,
        error_type='invalid_request_error',
        provider_status='INVALID_ARGUMENT',
        message='bad',
    )


@pytest.mark.parametrize('data', [
    b'not json',
    b'[]',
    b'{"unexpected":true}',
])
def test_unrecognized_error_bodies_produce_status_only_details(data):
    assert parse_http_error_details(_response(422, data=data)) == HttpErrorDetails(http_status=422)


def test_token_rate_limit_is_not_context_overflow():
    with pytest.raises(TransientBackendError):
        raise_for_http_status(_response(429, data=b'{"error":{"message":"too many input tokens per minute"}}'))


def test_retry_after_seconds_is_carried():
    with pytest.raises(TransientBackendError) as ei:
        raise_for_http_status(_response(429, headers={'Retry-After': '12'}))

    assert ei.value.retry_after_s == 12.


def test_retry_after_date_is_carried_as_a_delay():
    when = email.utils.formatdate(time.time() + 90, usegmt=True)

    with pytest.raises(TransientBackendError) as ei:
        raise_for_http_status(_response(503, headers={'retry-after': when}))

    assert ei.value.retry_after_s is not None
    assert 60. < ei.value.retry_after_s <= 90.


@pytest.mark.parametrize(('value', 'expected'), [
    ('5', 5.),
    (' 2.5 ', 2.5),
    ('-3', 0.),
    ('', None),
    ('soon', None),
])
def test_parse_retry_after_header(value, expected):
    assert parse_retry_after_header(value) == expected


##


@pytest.mark.asyncs('asyncio')
async def test_connection_level_errors_become_transient():
    with pytest.raises(TransientBackendError) as ei:
        async with translating_http_client_errors():
            raise http.HttpClientError('connection reset')

    assert isinstance(ei.value.__cause__, http.HttpClientError)


@pytest.mark.asyncs('asyncio')
async def test_status_errors_pass_through_untranslated():
    with pytest.raises(http.StatusHttpClientError):
        async with translating_http_client_errors():
            raise http.StatusHttpClientError(_response(400))


@pytest.mark.asyncs('asyncio')
async def test_unrelated_errors_pass_through():
    with pytest.raises(ValueError):  # noqa: PT011
        async with translating_http_client_errors():
            raise ValueError('mine')
