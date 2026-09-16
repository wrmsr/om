import contextlib
import email.utils
import json
import time
import typing as ta

from omcore import check
from omcore import lang
from omcore.http import all as http
from omcore.secrets import all as sec

from ...types.backends import Backend
from ...types.errors import BackendError
from ...types.errors import ContextOverflowBackendError
from ...types.errors import TransientBackendError
from ...types.models import Model
from ...types.models import TokenPricing


##


# Statuses for which a provider itself asks for the request to be retried as-is: request timeouts, rate limits, server
# faults, gateway timeouts, and the non-standard overloaded status some providers use.
TRANSIENT_HTTP_STATUSES: ta.Final[ta.AbstractSet[int]] = frozenset([
    408,
    429,
    500,
    502,
    503,
    504,
    522,
    524,
    529,
])


def parse_retry_after_header(value: str) -> float | None:
    """A Retry-After value is either a delay in seconds or an HTTP date. Anything unparseable is taken as absent."""

    value = value.strip()
    if not value:
        return None

    try:
        return max(float(value), 0.)
    except ValueError:
        pass

    try:
        dt = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None

    return max(dt.timestamp() - time.time(), 0.)


def get_retry_after_s(response: http.BaseHttpClientResponse) -> float | None:
    if (headers := response.headers) is None:
        return None

    for value in headers.lower.get('retry-after') or ():
        if (secs := parse_retry_after_header(value)) is not None:
            return secs

    return None


def _describe_http_response(response: http.BaseHttpClientResponse) -> str:
    parts = [f'HTTP {response.status}']

    if isinstance(response, http.HttpClientResponse) and response.data:
        body = response.data.decode('utf-8', errors='replace').strip()
        if len(body) > 1000:
            body = body[:1000] + '...'
        if body:
            parts.append(body)

    return ': '.join(parts)


_CONTEXT_OVERFLOW_CODES: ta.Final[ta.AbstractSet[str]] = frozenset([
    'context_length_exceeded',
    'context_window_exceeded',
    'max_context_length_exceeded',
    'prompt_too_long',
])

_CONTEXT_OVERFLOW_MESSAGE_MARKERS: ta.Final[ta.Sequence[str]] = (
    'context length exceeded',
    'context window exceeded',
    'exceeds the context window',
    'exceeds the maximum context',
    'exceeds the maximum number of tokens',
    'input token count exceeds',
    'maximum context length',
    'prompt is too long',
    'prompt too long',
    'request too large for model',
    'too many tokens for model',
)


def _is_context_overflow_response(response: http.BaseHttpClientResponse) -> bool:
    if not isinstance(response, http.HttpClientResponse) or not response.data:
        return False

    try:
        body = json.loads(response.data)
    except (UnicodeDecodeError, json.JSONDecodeError):
        body = None

    codes: list[str] = []
    if isinstance(body, dict):
        error = body.get('error')
        mappings = [body, error] if isinstance(error, dict) else [body]
        for mapping in mappings:
            for key in ('code', 'type', 'status'):
                if isinstance(value := mapping.get(key), str):
                    codes.append(value.lower())

    if any(code in _CONTEXT_OVERFLOW_CODES for code in codes):
        return True

    text = response.data.decode('utf-8', errors='replace').lower()
    return any(marker in text for marker in _CONTEXT_OVERFLOW_MESSAGE_MARKERS)


def raise_for_http_status(response: http.BaseHttpClientResponse) -> ta.NoReturn:
    """
    Raises the backend error for an unsuccessful response: a TransientBackendError for the statuses a caller should
    retry, a plain BackendError otherwise. Either is chained from the http client's own status error, so the response
    itself stays reachable through the cause.
    """

    cause = http.StatusHttpClientError(response)
    desc = _describe_http_response(response)

    if response.status in TRANSIENT_HTTP_STATUSES:
        raise TransientBackendError(desc, retry_after_s=get_retry_after_s(response)) from cause

    if _is_context_overflow_response(response):
        raise ContextOverflowBackendError(desc) from cause

    raise BackendError(desc) from cause


@contextlib.asynccontextmanager
async def translating_http_client_errors() -> ta.AsyncIterator[None]:
    """
    Maps the http client's connection-level failures - a refused or dropped connection, a client-side timeout - to
    TransientBackendError. Status errors are not raised by the client under this codebase's backends: they inspect the
    status themselves and go through `raise_for_http_status`, so a StatusHttpClientError reaching here is passed on
    untouched rather than misclassified.
    """

    try:
        yield

    except http.StatusHttpClientError:
        raise

    except http.HttpClientError as e:
        raise TransientBackendError(f'HTTP client error: {e!r}') from e


##


class BaseHttpBackend(Backend, lang.Abstract):
    def __init__(
            self,
            model: Model,
            *,
            api_key: sec.Secret | None = None,
            http_client: http.AsyncHttpClient | None = None,
            base_url: str | None = None,
    ) -> None:
        super().__init__()

        self._model = model
        self._api_key = api_key
        self._http_client = http_client

        self._model_http = check.not_none(model.http)
        self._base_url = check.non_empty_str(base_url or self._model_http.base_url).rstrip('/')

        # Deferred pricing resolves here, at construction - the one point model metadata may do real work, such as a
        # first read of baked pricing data.
        pricing = model.pricing
        if callable(pricing):
            pricing = pricing()
        self._pricing = check.isinstance(pricing, (TokenPricing, None))

    @property
    def model(self) -> Model:
        return self._model
