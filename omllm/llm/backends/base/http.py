import contextlib
import email.utils
import json
import time
import typing as ta

from omcore import check
from omcore import dataclasses as dc
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


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class HttpErrorDetails:
    """
    The small, provider-neutral part of a JSON HTTP error which is safe to use for classification.

    Providers agree only loosely on error envelopes. Most put the useful fields under a top-level ``error`` object;
    some return those fields at the top level instead, and some use an integer HTTP-like ``code`` while others use a
    symbolic string. Normalizing those mechanical differences here lets provider classifiers reason about named
    fields without searching the serialized response body.

    The fields deliberately retain their original values and spelling. A classifier should compare a symbolic value
    with ``code_is`` or normalize the particular field itself. More importantly, ``message`` is *only* the provider's
    designated error-message field. It is never the whole JSON document. This prevents an echoed request value,
    metadata field, or nested upstream diagnostic from accidentally triggering a substring heuristic.
    """

    http_status: int

    code: str | int | None = None
    error_type: str | None = None
    provider_status: str | None = None
    message: str | None = None

    def code_is(self, *values: str) -> bool:
        """Case-insensitively compares a symbolic code; numeric provider codes intentionally never match."""

        return isinstance(self.code, str) and self.code.casefold() in {value.casefold() for value in values}


type ContextOverflowHttpErrorClassifier = ta.Callable[[HttpErrorDetails], bool]


def parse_http_error_details(response: http.BaseHttpClientResponse) -> HttpErrorDetails:
    """
    Extracts the conventional fields from a JSON error response without assigning provider-specific meaning to them.

    A nested ``error`` mapping wins over the outer envelope. This matters for Anthropic, whose outer ``type`` is the
    uninformative value ``error`` while ``error.type`` is the useful ``invalid_request_error``. Top-level fields remain
    a fallback for APIs which return the error object directly. A string-valued ``error`` is treated as the message,
    but malformed, non-JSON, and structurally unfamiliar bodies simply produce status-only details: classification
    must fail closed rather than guessing from arbitrary bytes.
    """

    body: ta.Any = None
    if isinstance(response, http.HttpClientResponse) and response.data:
        try:
            body = json.loads(response.data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass

    outer = body if isinstance(body, ta.Mapping) else {}
    raw_error = outer.get('error')
    inner = raw_error if isinstance(raw_error, ta.Mapping) else outer

    def field(name: str) -> ta.Any:
        value = inner.get(name)
        if value is None and inner is not outer:
            value = outer.get(name)
        return value

    code = field('code')
    if not isinstance(code, (str, int)) or isinstance(code, bool):
        code = None

    message = field('message')
    if not isinstance(message, str):
        message = raw_error if isinstance(raw_error, str) else None

    error_type = field('type')
    provider_status = field('status')

    return HttpErrorDetails(
        http_status=response.status,
        code=code,
        error_type=error_type if isinstance(error_type, str) else None,
        provider_status=provider_status if isinstance(provider_status, str) else None,
        message=message,
    )


def raise_for_http_status(
        response: http.BaseHttpClientResponse,
        *,
        context_overflow_classifier: ContextOverflowHttpErrorClassifier | None = None,
) -> ta.NoReturn:
    """
    Raises the backend error for an unsuccessful response: a TransientBackendError for the statuses a caller should
    retry, a ContextOverflowBackendError only when the calling backend explicitly recognizes its own provider's error
    contract, and a plain BackendError otherwise. Every result is chained from the http client's status error, so the
    complete response stays reachable through the cause.

    Context overflow is intentionally not a global HTTP policy. OpenAI-compatible APIs expose useful symbolic codes,
    Google uses a broad INVALID_ARGUMENT status plus a specific message, Anthropic uses a broad invalid-request type,
    and OpenRouter may relay an upstream-specific message. A shared substring list would make every provider inherit
    every other provider's ambiguities. The backend therefore supplies a classifier which receives normalized named
    fields; without one, even an overflow-looking 400 remains an ordinary BackendError.
    """

    cause = http.StatusHttpClientError(response)
    desc = _describe_http_response(response)

    if response.status in TRANSIENT_HTTP_STATUSES:
        raise TransientBackendError(desc, retry_after_s=get_retry_after_s(response)) from cause

    if (
            context_overflow_classifier is not None and
            context_overflow_classifier(parse_http_error_details(response))
    ):
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

    def _is_context_overflow_http_error(self, error: HttpErrorDetails) -> bool:
        """
        Provider hook for the narrowly defined error which permits a context-reduction retry.

        False is the safe default. Misclassifying an authentication, schema, safety, or other validation failure as
        context overflow would discard useful model-visible history and repeat a request which cannot succeed. Each
        concrete backend family opts in using the strongest fields its provider actually promises.
        """

        return False

    def _raise_for_http_status(self, response: http.BaseHttpClientResponse) -> ta.NoReturn:
        """Applies shared status handling together with this backend family's provider-specific overflow contract."""

        raise_for_http_status(
            response,
            context_overflow_classifier=self._is_context_overflow_http_error,
        )
