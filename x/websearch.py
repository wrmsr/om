"""
Zero-dependency web-search provider demo.

Python 3.8+; standard library only.

The public surface is intentionally small:

    SearchRequest -> SearchProvider.search() -> SearchResponse

Providers that can retrieve complete readable pages additionally implement:

    ReadRequest -> DocumentReader.read() -> ReadResponse

The provider adapters in this file are deliberately thin.  They normalize the common fields while retaining the raw
provider response for debugging.  API contracts change, so production code should add contract tests and pin whatever
provider-specific behavior it relies on.

Library use:

    provider = make_provider("tinyfish")
    search = provider.search(SearchRequest(
        query="PEP 703 critical sections",
        limit=5,
        kind="developer",
    ))
    if isinstance(provider, DocumentReader) and search.hits:
        pages = provider.read(ReadRequest(
            urls=tuple(hit.url for hit in search.hits[:2]),
        ))

Command-line use:

    export BRAVE_API_KEY=...
    python web_search_demo.py --provider brave \
        --limit 5 'CPython 3.14 free threading dict atomicity'

    export TINYFISH_API_KEY=...
    python web_search_demo.py --provider tinyfish --read-first 2 \
        'PEP 703 critical sections'

    python web_search_demo.py --list-providers
    python web_search_demo.py --self-test

Environment variables are listed by --list-providers.
"""
import abc
import argparse
import dataclasses
import datetime as dt
import email.utils
import html
import html.parser
import json
import os
import random
import re
import sys
import time
import typing as ta
import urllib.error
import urllib.parse
import urllib.request


##
# Normalized public model


@dataclasses.dataclass(frozen=True)
class SearchRequest:
    query: str
    limit: int = 10

    # Optional context used by agent-oriented providers such as Parallel.
    objective: ta.Optional[str] = None
    alternate_queries: ta.Tuple[str, ...] = ()

    include_domains: ta.Tuple[str, ...] = ()
    exclude_domains: ta.Tuple[str, ...] = ()

    # Providers disagree about whether these are strict filters or ranking hints.
    country: ta.Optional[str] = None
    language: ta.Optional[str] = None
    freshness_days: ta.Optional[int] = None

    # A deliberately small portable taxonomy. Unsupported values are ignored or approximated by individual adapters.
    kind: str = 'web'  # web | news | academic | developer
    safe_search: str = 'moderate'  # off | moderate | strict

    # Providers with answer synthesis may populate SearchResponse.answer.
    want_answer: bool = False

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError('query must not be empty')
        if not 1 <= self.limit <= 100:
            raise ValueError('limit must be between 1 and 100')
        if self.freshness_days is not None and self.freshness_days < 1:
            raise ValueError('freshness_days must be positive')
        if self.kind not in ('web', 'news', 'academic', 'developer'):
            raise ValueError('kind must be web, news, academic, or developer')
        if self.safe_search not in ('off', 'moderate', 'strict'):
            raise ValueError('safe_search must be off, moderate, or strict')


@dataclasses.dataclass(frozen=True)
class SearchHit:
    title: str
    url: str
    snippet: str = ''
    published_at: ta.Optional[str] = None
    score: ta.Optional[float] = None

    # Some search APIs return extracted page text in the search response itself.
    content: ta.Optional[str] = None

    source: ta.Optional[str] = None
    metadata: ta.Mapping[str, ta.Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class SearchResponse:
    provider: str
    query: str
    hits: ta.Tuple[SearchHit, ...]
    answer: ta.Optional[str] = None
    request_id: ta.Optional[str] = None
    warnings: ta.Tuple[str, ...] = ()

    # Kept for debugging and deliberately excluded from repr/equality. Set keep_raw=False on a provider to avoid
    # retaining it.
    raw: ta.Any = dataclasses.field(default=None, repr=False, compare=False)


@dataclasses.dataclass(frozen=True)
class ReadRequest:
    urls: ta.Tuple[str, ...]
    objective: ta.Optional[str] = None
    max_chars_per_document: int = 100_000
    live: bool = False

    def __post_init__(self) -> None:
        if not self.urls:
            raise ValueError('urls must not be empty')
        if self.max_chars_per_document < 1:
            raise ValueError('max_chars_per_document must be positive')
        for url in self.urls:
            _validate_http_url(url)


@dataclasses.dataclass(frozen=True)
class ReadDocument:
    requested_url: str
    url: str
    title: str = ''
    content: str = ''
    published_at: ta.Optional[str] = None
    metadata: ta.Mapping[str, ta.Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class ReadResponse:
    provider: str
    documents: ta.Tuple[ReadDocument, ...]
    errors: ta.Tuple[str, ...] = ()
    request_id: ta.Optional[str] = None
    raw: ta.Any = dataclasses.field(default=None, repr=False, compare=False)


@dataclasses.dataclass(frozen=True)
class SearchCapabilities:
    domain_filtering: bool = False
    freshness_filtering: bool = False
    country: bool = False
    language: bool = False
    news: bool = False
    academic: bool = False
    developer: bool = False
    synthesized_answer: bool = False
    readable_documents: bool = False
    search_result_content: bool = False
    notes: ta.Tuple[str, ...] = ()


class SearchProvider(abc.ABC):
    """A provider accepting and returning the normalized dataclasses above."""

    name: ta.ClassVar[str]
    capabilities: ta.ClassVar[SearchCapabilities]

    def __init__(
            self,
            *,
            transport: ta.Optional['Transport'] = None,
            keep_raw: bool = False,
    ) -> None:
        self._transport = transport if transport is not None else UrllibTransport()
        self._keep_raw = keep_raw

    @abc.abstractmethod
    def search(self, request: SearchRequest) -> SearchResponse:
        raise NotImplementedError

    def _json(
            self,
            method: str,
            url: str,
            *,
            query: ta.Optional[ta.Mapping[str, ta.Any]] = None,
            headers: ta.Optional[ta.Mapping[str, str]] = None,
            body: ta.Any = None,
    ) -> ta.Any:
        hdrs = {'Accept': 'application/json'}
        if headers:
            hdrs.update(headers)
        raw_body: ta.Optional[bytes] = None
        if body is not None:
            raw_body = json.dumps(body, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
            hdrs.setdefault('Content-Type', 'application/json')
        response = self._transport.request(
            method,
            url,
            query=query,
            headers=hdrs,
            body=raw_body,
        )
        try:
            return json.loads(response.text())
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            preview = response.body[:500].decode('utf-8', 'replace')
            raise ResponseDecodeError(
                '{} returned non-JSON data: {!r}'.format(self.name, preview),
            ) from exc

    def _text(
            self,
            method: str,
            url: str,
            *,
            query: ta.Optional[ta.Mapping[str, ta.Any]] = None,
            headers: ta.Optional[ta.Mapping[str, str]] = None,
            body: ta.Optional[bytes] = None,
    ) -> str:
        response = self._transport.request(
            method,
            url,
            query=query,
            headers=headers,
            body=body,
        )
        return response.text()

    def _raw(self, value: ta.Any) -> ta.Any:
        return value if self._keep_raw else None


class DocumentReader(abc.ABC):
    """Optional extension implemented by providers with a URL extraction API."""

    @abc.abstractmethod
    def read(self, request: ReadRequest) -> ReadResponse:
        raise NotImplementedError


##
# HTTP transport


class SearchError(RuntimeError):
    pass


class MissingCredentialError(SearchError):
    pass


class ResponseDecodeError(SearchError):
    pass


class HttpStatusError(SearchError):
    def __init__(self, status: int, url: str, body: bytes) -> None:
        self.status = status
        self.url = url
        self.body = body
        preview = body[:1000].decode('utf-8', 'replace')
        super().__init__('HTTP {} from {}: {}'.format(status, url, preview))


@dataclasses.dataclass(frozen=True)
class HttpResponse:
    status: int
    url: str
    headers: ta.Mapping[str, str]
    body: bytes

    def text(self) -> str:
        content_type = self.headers.get('content-type', '')
        match = re.search(r'charset=([^;\s]+)', content_type, re.I)
        encoding = match.group(1).strip('"\'') if match else 'utf-8'
        try:
            return self.body.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            return self.body.decode('utf-8', 'replace')


class Transport(abc.ABC):
    @abc.abstractmethod
    def request(
            self,
            method: str,
            url: str,
            *,
            query: ta.Optional[ta.Mapping[str, ta.Any]] = None,
            headers: ta.Optional[ta.Mapping[str, str]] = None,
            body: ta.Optional[bytes] = None,
    ) -> HttpResponse:
        raise NotImplementedError


class UrllibTransport(Transport):
    """Small urllib transport with bounded responses and conservative retries."""

    def __init__(
            self,
            *,
            timeout: float = 30.0,
            max_response_bytes: int = 32 * 1024 * 1024,
            attempts: int = 3,
            user_agent: str = 'zero-dep-web-search-demo/1',
    ) -> None:
        if timeout <= 0:
            raise ValueError('timeout must be positive')
        if max_response_bytes < 1:
            raise ValueError('max_response_bytes must be positive')
        if attempts < 1:
            raise ValueError('attempts must be positive')
        self._timeout = timeout
        self._max_response_bytes = max_response_bytes
        self._attempts = attempts
        self._user_agent = user_agent

    def request(
            self,
            method: str,
            url: str,
            *,
            query: ta.Optional[ta.Mapping[str, ta.Any]] = None,
            headers: ta.Optional[ta.Mapping[str, str]] = None,
            body: ta.Optional[bytes] = None,
    ) -> HttpResponse:
        method = method.upper()
        final_url = _append_query(url, query)
        hdrs = {'User-Agent': self._user_agent}
        if headers:
            hdrs.update(headers)

        retry_statuses = {429, 500, 502, 503, 504}
        last_error: ta.Optional[BaseException] = None

        for attempt in range(self._attempts):
            request = urllib.request.Request(
                final_url,
                data=body,
                headers=hdrs,
                method=method,
            )
            try:
                with urllib.request.urlopen(request, timeout=self._timeout) as response:
                    response_body = response.read(self._max_response_bytes + 1)
                    if len(response_body) > self._max_response_bytes:
                        raise SearchError(
                            'response from {} exceeded {} bytes'.format(
                                final_url,
                                self._max_response_bytes,
                            ),
                        )
                    response_headers = {
                        key.lower(): value for key, value in response.headers.items()
                    }
                    return HttpResponse(
                        status=int(response.status),
                        url=response.geturl(),
                        headers=response_headers,
                        body=response_body,
                    )

            except urllib.error.HTTPError as exc:
                error_body = exc.read(self._max_response_bytes + 1)
                status = int(exc.code)
                if status in retry_statuses and attempt + 1 < self._attempts:
                    _sleep_before_retry(attempt, exc.headers.get('Retry-After'))
                    last_error = exc
                    continue
                raise HttpStatusError(status, final_url, error_body) from exc

            except urllib.error.URLError as exc:
                last_error = exc
                if attempt + 1 < self._attempts:
                    _sleep_before_retry(attempt, None)
                    continue
                raise SearchError('request to {} failed: {}'.format(final_url, exc)) from exc

        raise SearchError('request to {} failed: {}'.format(final_url, last_error))


@dataclasses.dataclass(frozen=True)
class RecordedRequest:
    method: str
    url: str
    query: ta.Mapping[str, ta.Any]
    headers: ta.Mapping[str, str]
    body: ta.Optional[bytes]


class FixtureTransport(Transport):
    """
    Offline transport useful for adapter contract tests.

    Fixtures are keyed by ``(METHOD, base_url_without_query)``. A value may be a Python JSON value, text, or bytes. For
    sequential calls, use a list of ``_FixtureSequence(value)`` objects; ordinary lists remain JSON arrays.
    """

    def __init__(self, fixtures: ta.Mapping[ta.Tuple[str, str], ta.Any]) -> None:
        self._fixtures: ta.Dict[ta.Tuple[str, str], ta.List[ta.Any]] = {}
        for key, value in fixtures.items():
            if isinstance(value, list) and value and isinstance(value[0], _FixtureSequence):
                sequence = [item.value for item in value]
            else:
                sequence = [value]
            self._fixtures[(key[0].upper(), key[1])] = sequence
        self.requests: ta.List[RecordedRequest] = []

    def request(
            self,
            method: str,
            url: str,
            *,
            query: ta.Optional[ta.Mapping[str, ta.Any]] = None,
            headers: ta.Optional[ta.Mapping[str, str]] = None,
            body: ta.Optional[bytes] = None,
    ) -> HttpResponse:
        method = method.upper()
        query_dict = dict(query or {})
        header_dict = dict(headers or {})
        self.requests.append(RecordedRequest(method, url, query_dict, header_dict, body))
        key = (method, url)
        values = self._fixtures.get(key)
        if not values:
            raise AssertionError('no fixture for {!r}'.format(key))
        value = values.pop(0) if len(values) > 1 else values[0]
        if isinstance(value, bytes):
            response_body = value
            content_type = 'application/octet-stream'
        elif isinstance(value, str):
            response_body = value.encode('utf-8')
            content_type = 'text/html; charset=utf-8'
        else:
            response_body = json.dumps(value).encode('utf-8')
            content_type = 'application/json; charset=utf-8'
        return HttpResponse(
            status=200,
            url=_append_query(url, query_dict),
            headers={'content-type': content_type},
            body=response_body,
        )


@dataclasses.dataclass(frozen=True)
class _FixtureSequence:
    value: ta.Any


##
# Provider helpers


def _require(value: ta.Optional[str], env_name: str) -> str:
    resolved = value or os.environ.get(env_name)
    if not resolved:
        raise MissingCredentialError('missing API credential; pass it explicitly or set {}'.format(env_name))
    return resolved


def _append_query(url: str, query: ta.Optional[ta.Mapping[str, ta.Any]]) -> str:
    if not query:
        return url
    encoded = urllib.parse.urlencode(
        [(key, item) for key, value in query.items() if value is not None
         for item in (value if isinstance(value, (list, tuple)) else (value,))],
        doseq=True,
    )
    if not encoded:
        return url
    return url + ('&' if '?' in url else '?') + encoded


def _sleep_before_retry(attempt: int, retry_after: ta.Optional[str]) -> None:
    delay: ta.Optional[float] = None
    if retry_after:
        try:
            delay = float(retry_after)
        except ValueError:
            try:
                when = email.utils.parsedate_to_datetime(retry_after)
                if when.tzinfo is None:
                    when = when.replace(tzinfo=dt.timezone.utc)
                delay = when.timestamp() - time.time()
            except (TypeError, ValueError, OverflowError):
                delay = None
    if delay is None:
        delay = (0.4 * (2 ** attempt)) + random.random() * 0.2
    time.sleep(max(0.0, min(delay, 10.0)))


def _validate_http_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        raise ValueError('not an HTTP(S) URL: {!r}'.format(url))


def _as_dict(value: ta.Any) -> ta.Dict[str, ta.Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: ta.Any) -> ta.List[ta.Any]:
    return value if isinstance(value, list) else []


def _text(value: ta.Any) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        return value
    return str(value)


def _optional_text(value: ta.Any) -> ta.Optional[str]:
    result = _text(value).strip()
    return result or None


def _optional_float(value: ta.Any) -> ta.Optional[float]:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _join_text(value: ta.Any, separator: str = '\n\n') -> str:
    if isinstance(value, list):
        return separator.join(_text(item).strip() for item in value if _text(item).strip())
    return _text(value).strip()


def _days_ago_iso(days: int) -> str:
    return (dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=days)).isoformat()


def _today_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _days_ago_iso_datetime(days: int) -> str:
    value = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)
    return value.isoformat(timespec='seconds').replace('+00:00', 'Z')


def _days_ago_us(days: int) -> str:
    value = dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=days)
    return value.strftime('%m/%d/%Y')


# Tavily's country field uses lower-case English country names rather than ISO alpha-2 codes.  This deliberately covers
# the common cases without dragging in a country database; callers may always pass a full English name directly.
_TAVILY_COUNTRY_NAMES_BY_CODE = {
    'AT': 'austria',
    'AU': 'australia',
    'BE': 'belgium',
    'BR': 'brazil',
    'CA': 'canada',
    'CH': 'switzerland',
    'CN': 'china',
    'CZ': 'czech republic',
    'DE': 'germany',
    'DK': 'denmark',
    'ES': 'spain',
    'FI': 'finland',
    'FR': 'france',
    'GB': 'united kingdom',
    'GR': 'greece',
    'HK': 'hong kong',
    'IE': 'ireland',
    'IN': 'india',
    'IT': 'italy',
    'JP': 'japan',
    'KR': 'south korea',
    'MX': 'mexico',
    'NL': 'netherlands',
    'NO': 'norway',
    'NZ': 'new zealand',
    'PL': 'poland',
    'PT': 'portugal',
    'RU': 'russia',
    'SE': 'sweden',
    'SG': 'singapore',
    'TR': 'turkey',
    'TW': 'taiwan',
    'UA': 'ukraine',
    'UK': 'united kingdom',
    'US': 'united states',
    'ZA': 'south africa',
}


def _query_with_site_operators(request: SearchRequest) -> str:
    parts = [request.query]
    if request.include_domains:
        if len(request.include_domains) == 1:
            parts.append('site:{}'.format(request.include_domains[0]))
        else:
            parts.append(
                '(' + ' OR '.join('site:{}'.format(d) for d in request.include_domains) + ')',
            )
    parts.extend('-site:{}'.format(d) for d in request.exclude_domains)
    return ' '.join(parts)


def _chunks(values: ta.Sequence[str], size: int) -> ta.Iterator[ta.Tuple[str, ...]]:
    for index in range(0, len(values), size):
        yield tuple(values[index:index + size])


def _truncate(value: str, limit: int) -> str:
    return value if len(value) <= limit else value[:limit]


def _error_string(item: ta.Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        url = _optional_text(item.get('url'))
        message = (
            _optional_text(item.get('message'))
            or _optional_text(item.get('content'))
            or _optional_text(item.get('error'))
            or _optional_text(item.get('error_type'))
            or json.dumps(item, sort_keys=True)
        )
        return '{}: {}'.format(url, message) if url else message
    return _text(item)


def _warning_strings(value: ta.Any) -> ta.Tuple[str, ...]:
    warnings: ta.List[str] = []
    for item in _as_list(value):
        if isinstance(item, dict):
            warnings.append(
                _optional_text(item.get('message'))
                or _optional_text(item.get('warning'))
                or json.dumps(item, sort_keys=True),
            )
        else:
            warnings.append(_text(item))
    return tuple(item for item in warnings if item)


##
# Concrete providers


class GoogleCseSearch(SearchProvider):
    name = 'google-cse'
    capabilities = SearchCapabilities(
        domain_filtering=True,
        freshness_filtering=True,
        country=True,
        language=True,
        notes=('Existing API only; Google has announced its retirement for 2027.',),
    )

    _URL = 'https://customsearch.googleapis.com/customsearch/v1'

    def __init__(
            self,
            api_key: ta.Optional[str] = None,
            cse_id: ta.Optional[str] = None,
            **kwargs: ta.Any,
    ) -> None:
        super().__init__(**kwargs)
        self._api_key = _require(api_key, 'GOOGLE_API_KEY')
        self._cse_id = _require(cse_id, 'GOOGLE_CSE_ID')

    def search(self, request: SearchRequest) -> SearchResponse:
        hits: ta.List[SearchHit] = []
        raw_pages: ta.List[ta.Any] = []
        start = 1
        # CSE returns at most ten items per request and at most 100 total.
        target = min(request.limit, 100)
        while len(hits) < target:
            params: ta.Dict[str, ta.Any] = {
                'key': self._api_key,
                'cx': self._cse_id,
                'q': _query_with_site_operators(request),
                'num': min(10, target - len(hits)),
                'start': start,
                'safe': 'off' if request.safe_search == 'off' else 'active',
            }
            if request.freshness_days is not None:
                params['dateRestrict'] = 'd{}'.format(request.freshness_days)
            if request.country:
                params['gl'] = request.country.lower()
            if request.language:
                language = request.language.lower().replace('-', '_')
                params['lr'] = language if language.startswith('lang_') else 'lang_' + language

            data = self._json('GET', self._URL, query=params)
            raw_pages.append(data)
            items = _as_list(_as_dict(data).get('items'))
            for item_value in items:
                item = _as_dict(item_value)
                url = _text(item.get('link')).strip()
                if not url:
                    continue
                hits.append(SearchHit(
                    title=_text(item.get('title')),
                    url=url,
                    snippet=_text(item.get('snippet')),
                    metadata={'display_link': item.get('displayLink')},
                ))
                if len(hits) >= target:
                    break
            if not items:
                break
            start += len(items)
            if start > 91:
                break

        warnings = ()
        if request.limit > 100:
            warnings = ('Google CSE exposes at most 100 results per query.',)
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            warnings=warnings,
            raw=self._raw(raw_pages),
        )


class _DuckDuckGoHtmlParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: ta.List[ta.Dict[str, str]] = []
        self._current: ta.Optional[ta.Dict[str, str]] = None
        self._capture: ta.Optional[str] = None

    def handle_starttag(self, tag: str, attrs: ta.List[ta.Tuple[str, ta.Optional[str]]]) -> None:
        attr = {key: value or '' for key, value in attrs}
        classes = set(attr.get('class', '').split())
        if tag == 'a' and 'result__a' in classes:
            self._flush()
            self._current = {'url': attr.get('href', ''), 'title': '', 'snippet': ''}
            self._capture = 'title'
        elif self._current is not None and 'result__snippet' in classes:
            self._capture = 'snippet'

    def handle_endtag(self, tag: str) -> None:
        if tag in ('a', 'div', 'span'):
            self._capture = None

    def handle_data(self, data: str) -> None:
        if self._current is not None and self._capture is not None:
            self._current[self._capture] += data

    def close(self) -> None:
        super().close()
        self._flush()

    def _flush(self) -> None:
        if self._current is not None and self._current.get('url'):
            self.rows.append(self._current)
        self._current = None
        self._capture = None


class DuckDuckGoHtmlSearch(SearchProvider):
    """Unofficial HTML adapter, not a supported DuckDuckGo API contract."""

    name = 'duckduckgo-html'
    capabilities = SearchCapabilities(
        country=True,
        language=True,
        notes=('Scrape-based and inherently less stable than a documented API.',),
    )

    _URL = 'https://html.duckduckgo.com/html/'

    def search(self, request: SearchRequest) -> SearchResponse:
        form: ta.Dict[str, str] = {'q': _query_with_site_operators(request)}
        if request.country or request.language:
            country = (request.country or 'wt').lower()
            language = (request.language or 'en').lower().split('-')[0]
            form['kl'] = '{}-{}'.format(country, language)
        body = urllib.parse.urlencode(form).encode('utf-8')
        text = self._text(
            'POST',
            self._URL,
            headers={
                'Accept': 'text/html,application/xhtml+xml',
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body=body,
        )
        parser = _DuckDuckGoHtmlParser()
        parser.feed(text)
        parser.close()
        hits: ta.List[SearchHit] = []
        for row in parser.rows[:request.limit]:
            url = _decode_duckduckgo_url(row['url'])
            hits.append(SearchHit(
                title=html.unescape(row['title']).strip(),
                url=url,
                snippet=html.unescape(row['snippet']).strip(),
            ))
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            raw=text if self._keep_raw else None,
        )


def _decode_duckduckgo_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    params = urllib.parse.parse_qs(parsed.query)
    if 'uddg' in params and params['uddg']:
        return params['uddg'][0]
    if url.startswith('//'):
        return 'https:' + url
    return url


class TavilySearch(SearchProvider, DocumentReader):
    name = 'tavily'
    capabilities = SearchCapabilities(
        domain_filtering=True,
        freshness_filtering=True,
        country=True,
        language=True,
        news=True,
        synthesized_answer=True,
        readable_documents=True,
        search_result_content=True,
    )

    _SEARCH_URL = 'https://api.tavily.com/search'
    _EXTRACT_URL = 'https://api.tavily.com/extract'

    def __init__(
            self,
            api_key: ta.Optional[str] = None,
            *,
            search_depth: str = 'basic',
            extract_depth: str = 'basic',
            **kwargs: ta.Any,
    ) -> None:
        super().__init__(**kwargs)
        if search_depth not in ('basic', 'advanced', 'fast', 'ultra-fast'):
            raise ValueError('invalid Tavily search depth')
        if extract_depth not in ('basic', 'advanced'):
            raise ValueError('invalid Tavily extract depth')
        self._api_key = _require(api_key, 'TAVILY_API_KEY')
        self._search_depth = search_depth
        self._extract_depth = extract_depth

    def _headers(self) -> ta.Dict[str, str]:
        return {'Authorization': 'Bearer ' + self._api_key}

    def search(self, request: SearchRequest) -> SearchResponse:
        warnings: ta.List[str] = []
        body: ta.Dict[str, ta.Any] = {
            'query': request.query,
            'search_depth': self._search_depth,
            'max_results': min(request.limit, 20),
            'topic': 'news' if request.kind == 'news' else 'general',
            'include_answer': request.want_answer,
            'include_raw_content': False,
            'include_published_date': True,
            'include_domains': list(request.include_domains),
            'exclude_domains': list(request.exclude_domains),
            'safe_search': request.safe_search != 'off',
        }
        if request.freshness_days is not None:
            body['start_date'] = _days_ago_iso(request.freshness_days)
            body['end_date'] = _today_iso()
            body['filter_by_published_date'] = True
        if request.country:
            country = request.country.strip()
            if len(country) == 2:
                country_name = _TAVILY_COUNTRY_NAMES_BY_CODE.get(country.upper())
                if country_name is None:
                    warnings.append(
                        'Tavily expects an English country name; unknown two-letter country code was omitted.',
                    )
                else:
                    body['country'] = country_name
            else:
                body['country'] = country.lower()
        if request.language:
            body['language'] = request.language
            body['filter_by_language'] = True

        data = _as_dict(self._json('POST', self._SEARCH_URL, headers=self._headers(), body=body))
        hits = []
        for item_value in _as_list(data.get('results')):
            item = _as_dict(item_value)
            url = _text(item.get('url')).strip()
            if not url:
                continue
            hits.append(SearchHit(
                title=_text(item.get('title')),
                url=url,
                snippet=_text(item.get('content')),
                published_at=_optional_text(item.get('published_date')),
                score=_optional_float(item.get('score')),
                content=_optional_text(item.get('raw_content')),
            ))
        if request.limit > 20:
            warnings.append('Tavily search max_results is capped at 20.')
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits[:request.limit]),
            answer=_optional_text(data.get('answer')),
            request_id=_optional_text(data.get('request_id')),
            warnings=tuple(warnings),
            raw=self._raw(data),
        )

    def read(self, request: ReadRequest) -> ReadResponse:
        documents: ta.List[ReadDocument] = []
        errors: ta.List[str] = []
        raw_pages: ta.List[ta.Any] = []
        request_id: ta.Optional[str] = None
        for chunk in _chunks(request.urls, 20):
            body: ta.Dict[str, ta.Any] = {
                'urls': list(chunk),
                'extract_depth': self._extract_depth,
                'format': 'markdown',
                'include_images': False,
            }
            if request.objective:
                body['query'] = request.objective
            data = _as_dict(self._json('POST', self._EXTRACT_URL, headers=self._headers(), body=body))
            raw_pages.append(data)
            request_id = request_id or _optional_text(data.get('request_id'))
            for item_value in _as_list(data.get('results')):
                item = _as_dict(item_value)
                url = _text(item.get('url')).strip()
                content = _text(item.get('raw_content') or item.get('content'))
                documents.append(ReadDocument(
                    requested_url=url,
                    url=url,
                    title=_text(item.get('title')),
                    content=_truncate(content, request.max_chars_per_document),
                ))
            errors.extend(_error_string(item) for item in _as_list(data.get('failed_results')))
        return ReadResponse(
            provider=self.name,
            documents=tuple(documents),
            errors=tuple(errors),
            request_id=request_id,
            raw=self._raw(raw_pages),
        )


class TinyFishSearch(SearchProvider, DocumentReader):
    name = 'tinyfish'
    capabilities = SearchCapabilities(
        domain_filtering=True,
        freshness_filtering=True,
        country=True,
        language=True,
        news=True,
        academic=True,
        readable_documents=True,
    )

    _SEARCH_URL = 'https://api.search.tinyfish.ai'
    _FETCH_URL = 'https://api.fetch.tinyfish.ai'

    def __init__(self, api_key: ta.Optional[str] = None, **kwargs: ta.Any) -> None:
        super().__init__(**kwargs)
        self._api_key = _require(api_key, 'TINYFISH_API_KEY')

    def _headers(self) -> ta.Dict[str, str]:
        return {'X-API-Key': self._api_key}

    def search(self, request: SearchRequest) -> SearchResponse:
        params: ta.Dict[str, ta.Any] = {
            'query': request.query,
            'purpose': request.objective,
            'location': request.country,
            'language': request.language,
            'include_domains': ','.join(request.include_domains) or None,
            'exclude_domains': ','.join(request.exclude_domains) or None,
        }
        if request.kind == 'news':
            params['domain_type'] = 'news'
        elif request.kind == 'academic':
            params['domain_type'] = 'research_paper'
            if request.freshness_days is not None:
                cutoff = dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(
                    days=request.freshness_days,
                )
                params['pub_year_min'] = cutoff.year
        else:
            params['domain_type'] = 'web'
        warnings: ta.List[str] = []
        if request.freshness_days is not None and request.kind != 'academic':
            recency_minutes = request.freshness_days * 24 * 60
            max_recency_minutes = 5_256_000
            if recency_minutes > max_recency_minutes:
                recency_minutes = max_recency_minutes
                warnings.append(
                    'TinyFish recency is capped at 10 years; freshness_days was clamped.',
                )
            params['recency_minutes'] = recency_minutes

        hits: ta.List[SearchHit] = []
        raw_pages: ta.List[ta.Any] = []
        for page in range(11):
            page_params = dict(params)
            page_params['page'] = page
            data = _as_dict(self._json(
                'GET',
                self._SEARCH_URL,
                query=page_params,
                headers=self._headers(),
            ))
            raw_pages.append(data)
            values = _as_list(data.get('results'))
            for item_value in values:
                item = _as_dict(item_value)
                url = _text(item.get('url')).strip()
                if not url:
                    continue
                metadata = {
                    key: value for key, value in item.items()
                    if key not in ('title', 'url', 'snippet', 'date')
                }
                hits.append(SearchHit(
                    title=_text(item.get('title')),
                    url=url,
                    snippet=_text(item.get('snippet')),
                    published_at=_optional_text(item.get('date')),
                    source=_optional_text(item.get('site_name') or item.get('publisher')),
                    metadata=metadata,
                ))
                if len(hits) >= request.limit:
                    break
            if len(hits) >= request.limit or not values:
                break

        if request.kind == 'academic' and request.freshness_days is not None:
            warnings.append(
                'TinyFish research-paper search supports publication years rather than exact recency; freshness_days '
                'was rounded to a minimum publication year.',
            )
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits[:request.limit]),
            warnings=tuple(warnings),
            raw=self._raw(raw_pages),
        )

    def read(self, request: ReadRequest) -> ReadResponse:
        documents: ta.List[ReadDocument] = []
        errors: ta.List[str] = []
        raw_pages: ta.List[ta.Any] = []
        for chunk in _chunks(request.urls, 10):
            body: ta.Dict[str, ta.Any] = {
                'urls': list(chunk),
                'format': 'markdown',
                'links': False,
                'image_links': False,
            }
            if request.objective:
                body['purpose'] = request.objective
            if request.live:
                body['ttl'] = 0
            data = _as_dict(self._json('POST', self._FETCH_URL, headers=self._headers(), body=body))
            raw_pages.append(data)
            for item_value in _as_list(data.get('results')):
                item = _as_dict(item_value)
                requested_url = _text(item.get('url'))
                final_url = _text(item.get('final_url') or requested_url)
                documents.append(ReadDocument(
                    requested_url=requested_url,
                    url=final_url,
                    title=_text(item.get('title')),
                    content=_truncate(_text(item.get('text')), request.max_chars_per_document),
                    published_at=_optional_text(item.get('published_date')),
                    metadata={
                        'description': item.get('description'),
                        'language': item.get('language'),
                        'author': item.get('author'),
                    },
                ))
            errors.extend(_error_string(item) for item in _as_list(data.get('errors')))
        return ReadResponse(
            provider=self.name,
            documents=tuple(documents),
            errors=tuple(errors),
            raw=self._raw(raw_pages),
        )


class KeenableSearch(SearchProvider, DocumentReader):
    name = 'keenable'
    capabilities = SearchCapabilities(
        domain_filtering=True,
        freshness_filtering=True,
        readable_documents=True,
        search_result_content=True,
        notes=(
            "Can use Keenable's public endpoints without a key, or authenticated endpoints with KEENABLE_API_KEY.",
        ),
    )

    _BASE_URL = 'https://api.keenable.ai'

    def __init__(
            self,
            api_key: ta.Optional[str] = None,
            *,
            client_title: str = 'zero-dep-web-search-demo',
            snippet_max_length: int = 2_000,
            **kwargs: ta.Any,
    ) -> None:
        super().__init__(**kwargs)
        self._api_key = api_key or os.environ.get('KEENABLE_API_KEY')
        if not 180 <= snippet_max_length <= 10_000:
            raise ValueError('Keenable snippet_max_length must be between 180 and 10000')
        self._client_title = client_title
        self._snippet_max_length = snippet_max_length

    def _headers(self) -> ta.Dict[str, str]:
        if self._api_key:
            return {'X-API-Key': self._api_key}
        return {'X-Keenable-Title': self._client_title}

    def _endpoint(self, operation: str) -> str:
        suffix = '' if self._api_key else '/public'
        return '{}/v1/{}{}'.format(self._BASE_URL, operation, suffix)

    def search(self, request: SearchRequest) -> SearchResponse:
        query = request.query
        site: ta.Optional[str] = None
        if len(request.include_domains) == 1:
            site = request.include_domains[0]
            if request.exclude_domains:
                query += ' ' + ' '.join(
                    '-site:{}'.format(domain) for domain in request.exclude_domains
                )
        elif request.include_domains or request.exclude_domains:
            query = _query_with_site_operators(request)

        body: ta.Dict[str, ta.Any] = {
            'query': query,
            'max_results': min(request.limit, 50),
            'snippet_max_length': self._snippet_max_length,
        }
        if site:
            body['site'] = site
        if request.freshness_days is not None:
            body['published_after'] = _days_ago_iso(request.freshness_days)

        data = _as_dict(self._json(
            'POST',
            self._endpoint('search'),
            headers=self._headers(),
            body=body,
        ))
        hits: ta.List[SearchHit] = []
        for item_value in _as_list(data.get('results'))[:request.limit]:
            item = _as_dict(item_value)
            url = _text(item.get('url')).strip()
            if not url:
                continue
            snippet = _text(item.get('snippet') or item.get('description'))
            hits.append(SearchHit(
                title=_text(item.get('title')),
                url=url,
                snippet=snippet,
                content=_optional_text(item.get('content')),
                published_at=_optional_text(item.get('published_at')),
                metadata={
                    'description': item.get('description'),
                    'acquired_at': item.get('acquired_at'),
                },
            ))
        warnings: ta.Tuple[str, ...] = ()
        if request.limit > 50:
            warnings = ('Keenable max_results is capped at 50.',)
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            request_id=_optional_text(data.get('request_id') or data.get('id')),
            warnings=warnings,
            raw=self._raw(data),
        )

    def read(self, request: ReadRequest) -> ReadResponse:
        documents: ta.List[ReadDocument] = []
        errors: ta.List[str] = []
        raw_pages: ta.List[ta.Any] = []
        for url in request.urls:
            params: ta.Dict[str, ta.Any] = {
                'url': url,
                'max_chars': request.max_chars_per_document,
                'live': 'true' if request.live else None,
                'prompt': request.objective,
            }
            try:
                data = _as_dict(self._json(
                    'GET',
                    self._endpoint('fetch'),
                    query=params,
                    headers=self._headers(),
                ))
            except SearchError as exc:
                errors.append('{}: {}'.format(url, exc))
                continue
            raw_pages.append(data)
            payload = _as_dict(data.get('data')) or data
            final_url = _text(payload.get('url') or payload.get('final_url') or url)
            content = _text(
                payload.get('content')
                or payload.get('markdown')
                or payload.get('text'),
            )
            documents.append(ReadDocument(
                requested_url=url,
                url=final_url,
                title=_text(payload.get('title')),
                content=_truncate(content, request.max_chars_per_document),
                published_at=_optional_text(payload.get('published_at')),
                metadata={
                    key: value for key, value in payload.items()
                    if key not in (
                        'url', 'final_url', 'title', 'content', 'markdown', 'text',
                        'published_at',
                    )
                },
            ))
        return ReadResponse(
            provider=self.name,
            documents=tuple(documents),
            errors=tuple(errors),
            raw=self._raw(raw_pages),
        )


class ParallelSearch(SearchProvider, DocumentReader):
    name = 'parallel'
    capabilities = SearchCapabilities(
        synthesized_answer=False,
        readable_documents=True,
        search_result_content=True,
        notes=(
            "Parallel's objective and alternate search queries map directly to the normalized request.",
            'Generic domain/country/freshness fields are approximated in the query text.',
        ),
    )

    _SEARCH_URL = 'https://api.parallel.ai/v1/search'
    _EXTRACT_URL = 'https://api.parallel.ai/v1/extract'

    def __init__(
            self,
            api_key: ta.Optional[str] = None,
            *,
            mode: str = 'fast',
            max_chars_total: int = 20_000,
            **kwargs: ta.Any,
    ) -> None:
        super().__init__(**kwargs)
        if mode not in ('turbo', 'fast', 'basic', 'advanced'):
            raise ValueError('invalid Parallel search mode')
        self._api_key = _require(api_key, 'PARALLEL_API_KEY')
        self._mode = mode
        self._max_chars_total = max_chars_total

    def _headers(self) -> ta.Dict[str, str]:
        return {'x-api-key': self._api_key}

    def search(self, request: SearchRequest) -> SearchResponse:
        primary_query = _query_with_site_operators(request)
        if request.freshness_days is not None:
            primary_query += ' published after {}'.format(
                _days_ago_iso(request.freshness_days),
            )
        if request.kind == 'news':
            primary_query += ' latest news'
        elif request.kind == 'academic':
            primary_query += ' research paper'

        queries = [primary_query]
        queries.extend(request.alternate_queries)
        body: ta.Dict[str, ta.Any] = {
            'search_queries': queries[:5],
            'mode': self._mode,
            'max_chars_total': self._max_chars_total,
        }
        if request.objective:
            body['objective'] = request.objective

        data = _as_dict(self._json(
            'POST',
            self._SEARCH_URL,
            headers=self._headers(),
            body=body,
        ))
        hits: ta.List[SearchHit] = []
        for item_value in _as_list(data.get('results'))[:request.limit]:
            item = _as_dict(item_value)
            url = _text(item.get('url')).strip()
            if not url:
                continue
            excerpts = _join_text(item.get('excerpts'))
            content = _optional_text(item.get('full_content'))
            hits.append(SearchHit(
                title=_text(item.get('title')),
                url=url,
                snippet=excerpts,
                content=content,
                published_at=_optional_text(item.get('publish_date')),
                score=_optional_float(item.get('score')),
                metadata={
                    key: value for key, value in item.items()
                    if key not in (
                        'url', 'title', 'excerpts', 'full_content', 'publish_date', 'score',
                    )
                },
            ))
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            request_id=_optional_text(data.get('search_id') or data.get('id')),
            raw=self._raw(data),
        )

    def read(self, request: ReadRequest) -> ReadResponse:
        documents: ta.List[ReadDocument] = []
        errors: ta.List[str] = []
        raw_pages: ta.List[ta.Any] = []
        request_id: ta.Optional[str] = None
        for chunk in _chunks(request.urls, 20):
            body: ta.Dict[str, ta.Any] = {
                'urls': list(chunk),
                'max_chars_total': request.max_chars_per_document * len(chunk),
            }
            if request.objective:
                body['objective'] = request.objective
            data = _as_dict(self._json(
                'POST',
                self._EXTRACT_URL,
                headers=self._headers(),
                body=body,
            ))
            raw_pages.append(data)
            request_id = request_id or _optional_text(
                data.get('extract_id') or data.get('id'),
            )
            for item_value in _as_list(data.get('results')):
                item = _as_dict(item_value)
                url = _text(item.get('url')).strip()
                content = _text(item.get('full_content'))
                if not content:
                    content = _join_text(item.get('excerpts'))
                documents.append(ReadDocument(
                    requested_url=url,
                    url=url,
                    title=_text(item.get('title')),
                    content=_truncate(content, request.max_chars_per_document),
                    published_at=_optional_text(item.get('publish_date')),
                    metadata={
                        key: value for key, value in item.items()
                        if key not in (
                            'url', 'title', 'full_content', 'excerpts', 'publish_date',
                        )
                    },
                ))
            errors.extend(_error_string(item) for item in _as_list(data.get('errors')))
        return ReadResponse(
            provider=self.name,
            documents=tuple(documents),
            errors=tuple(errors),
            request_id=request_id,
            raw=self._raw(raw_pages),
        )


class LinkupSearch(SearchProvider, DocumentReader):
    name = 'linkup'
    capabilities = SearchCapabilities(
        domain_filtering=True,
        freshness_filtering=True,
        synthesized_answer=True,
        readable_documents=True,
        search_result_content=True,
    )

    _SEARCH_URL = 'https://api.linkup.so/v1/search'
    _FETCH_URL = 'https://api.linkup.so/v1/fetch'

    def __init__(
            self,
            api_key: ta.Optional[str] = None,
            *,
            depth: str = 'fast',
            fetch_mode: str = 'standard',
            **kwargs: ta.Any,
    ) -> None:
        super().__init__(**kwargs)
        if depth not in ('flash', 'fast', 'standard', 'deep'):
            raise ValueError('invalid Linkup search depth')
        if fetch_mode not in ('standard', 'pro'):
            raise ValueError('invalid Linkup fetch mode')
        self._api_key = _require(api_key, 'LINKUP_API_KEY')
        self._depth = depth
        self._fetch_mode = fetch_mode

    def _headers(self) -> ta.Dict[str, str]:
        return {'Authorization': 'Bearer ' + self._api_key}

    def search(self, request: SearchRequest) -> SearchResponse:
        body: ta.Dict[str, ta.Any] = {
            'q': request.query,
            'depth': self._depth,
            'outputType': 'sourcedAnswer' if request.want_answer else 'searchResults',
            'maxResults': request.limit,
            'includeDomains': list(request.include_domains),
            'excludeDomains': list(request.exclude_domains),
        }
        if request.freshness_days is not None:
            body['fromDate'] = _days_ago_iso(request.freshness_days)
            body['toDate'] = _today_iso()

        data = _as_dict(self._json(
            'POST',
            self._SEARCH_URL,
            headers=self._headers(),
            body=body,
        ))
        result_values = _as_list(data.get('results'))
        if not result_values:
            result_values = _as_list(data.get('sources'))
        hits: ta.List[SearchHit] = []
        for item_value in result_values[:request.limit]:
            item = _as_dict(item_value)
            url = _text(item.get('url')).strip()
            if not url:
                continue
            hits.append(SearchHit(
                title=_text(item.get('name') or item.get('title')),
                url=url,
                snippet=_text(item.get('content') or item.get('snippet')),
                content=_optional_text(item.get('content')),
                published_at=_optional_text(
                    item.get('publishedAt') or item.get('published_at'),
                ),
                source=_optional_text(item.get('type')),
                metadata={'favicon': item.get('favicon')},
            ))
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            answer=_optional_text(data.get('answer')),
            request_id=_optional_text(data.get('requestId') or data.get('id')),
            raw=self._raw(data),
        )

    def read(self, request: ReadRequest) -> ReadResponse:
        documents: ta.List[ReadDocument] = []
        errors: ta.List[str] = []
        raw_pages: ta.List[ta.Any] = []
        for url in request.urls:
            body: ta.Dict[str, ta.Any] = {
                'url': url,
                'mode': self._fetch_mode,
                'renderJs': request.live,
                'includeRawHtml': False,
                'extractImages': False,
            }
            try:
                data = _as_dict(self._json(
                    'POST',
                    self._FETCH_URL,
                    headers=self._headers(),
                    body=body,
                ))
            except SearchError as exc:
                errors.append('{}: {}'.format(url, exc))
                continue
            raw_pages.append(data)
            payload = _as_dict(data.get('data')) or data
            final_url = _text(payload.get('url') or url)
            content = _text(payload.get('markdown') or payload.get('content'))
            documents.append(ReadDocument(
                requested_url=url,
                url=final_url,
                title=_text(payload.get('title')),
                content=_truncate(content, request.max_chars_per_document),
                metadata={
                    key: value for key, value in payload.items()
                    if key not in ('url', 'title', 'markdown', 'content')
                },
            ))
        return ReadResponse(
            provider=self.name,
            documents=tuple(documents),
            errors=tuple(errors),
            raw=self._raw(raw_pages),
        )


class YouSearch(SearchProvider, DocumentReader):
    name = 'you'
    capabilities = SearchCapabilities(
        domain_filtering=True,
        freshness_filtering=True,
        country=True,
        language=True,
        news=True,
        readable_documents=True,
        search_result_content=True,
    )

    _SEARCH_URL = 'https://ydc-index.io/v1/search'
    _CONTENTS_URL = 'https://ydc-index.io/v1/contents'

    def __init__(self, api_key: ta.Optional[str] = None, **kwargs: ta.Any) -> None:
        super().__init__(**kwargs)
        self._api_key = _require(api_key, 'YOU_API_KEY')

    def _headers(self) -> ta.Dict[str, str]:
        return {'X-API-Key': self._api_key}

    def search(self, request: SearchRequest) -> SearchResponse:
        body: ta.Dict[str, ta.Any] = {
            'query': request.query,
            'count': request.limit,
            'safesearch': request.safe_search,
        }
        if request.freshness_days is not None:
            body['freshness'] = '{}to{}'.format(
                _days_ago_iso(request.freshness_days),
                _today_iso(),
            )
        if request.country:
            body['country'] = request.country.lower()
        if request.language:
            body['language'] = request.language

        # You.com's API exposes separate include/exclude domain fields, but some
        # versions reject sending both. Query operators preserve the combined case.
        if request.include_domains and request.exclude_domains:
            body['query'] = _query_with_site_operators(request)
        elif request.include_domains:
            body['include_domains'] = list(request.include_domains)
        elif request.exclude_domains:
            body['exclude_domains'] = list(request.exclude_domains)

        data = _as_dict(self._json(
            'POST',
            self._SEARCH_URL,
            headers=self._headers(),
            body=body,
        ))
        result_groups = _as_dict(data.get('results'))
        if request.kind == 'news':
            values = _as_list(result_groups.get('news'))
        else:
            values = _as_list(result_groups.get('web'))
        if not values:
            values = _as_list(data.get('results'))

        hits: ta.List[SearchHit] = []
        for item_value in values[:request.limit]:
            item = _as_dict(item_value)
            url = _text(item.get('url')).strip()
            if not url:
                continue
            snippets = item.get('snippets')
            snippet = _join_text(snippets) if snippets is not None else _text(
                item.get('description') or item.get('snippet'),
            )
            content = _optional_text(
                item.get('markdown') or item.get('contents') or item.get('content'),
            )
            hits.append(SearchHit(
                title=_text(item.get('title')),
                url=url,
                snippet=snippet,
                content=content,
                published_at=_optional_text(
                    item.get('page_age') or item.get('published_at') or item.get('date'),
                ),
                source=_optional_text(item.get('source')),
                metadata={
                    key: value for key, value in item.items()
                    if key not in (
                        'url', 'title', 'snippets', 'description', 'snippet', 'markdown',
                        'contents', 'content', 'page_age', 'published_at', 'date', 'source',
                    )
                },
            ))
        metadata = _as_dict(data.get('metadata'))
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            request_id=_optional_text(
                metadata.get('search_uuid') or data.get('search_uuid') or data.get('id'),
            ),
            raw=self._raw(data),
        )

    def read(self, request: ReadRequest) -> ReadResponse:
        documents: ta.List[ReadDocument] = []
        errors: ta.List[str] = []
        raw_pages: ta.List[ta.Any] = []
        for chunk in _chunks(request.urls, 20):
            body: ta.Dict[str, ta.Any] = {
                'urls': list(chunk),
                'formats': ['markdown', 'metadata'],
            }
            if request.live:
                body['max_age'] = 0
            try:
                data = self._json(
                    'POST',
                    self._CONTENTS_URL,
                    headers=self._headers(),
                    body=body,
                )
            except SearchError as exc:
                errors.append('{}: {}'.format(', '.join(chunk), exc))
                continue
            raw_pages.append(data)
            values = _as_list(data)
            if not values:
                values = _as_list(_as_dict(data).get('results'))
            for item_value in values:
                item = _as_dict(item_value)
                requested_url = _text(item.get('requested_url') or item.get('url'))
                metadata = _as_dict(item.get('metadata'))
                documents.append(ReadDocument(
                    requested_url=requested_url,
                    url=_text(item.get('url') or requested_url),
                    title=_text(item.get('title') or metadata.get('title')),
                    content=_truncate(
                        _text(item.get('markdown') or item.get('content')),
                        request.max_chars_per_document,
                    ),
                    published_at=_optional_text(
                        metadata.get('published_time') or metadata.get('date'),
                    ),
                    metadata=metadata,
                ))
        return ReadResponse(
            provider=self.name,
            documents=tuple(documents),
            errors=tuple(errors),
            raw=self._raw(raw_pages),
        )


class ExaSearch(SearchProvider, DocumentReader):
    name = 'exa'
    capabilities = SearchCapabilities(
        domain_filtering=True,
        freshness_filtering=True,
        readable_documents=True,
        search_result_content=True,
        academic=True,
        notes=('Particularly useful for semantic/natural-language retrieval.',),
    )

    _SEARCH_URL = 'https://api.exa.ai/search'
    _CONTENTS_URL = 'https://api.exa.ai/contents'

    def __init__(
            self,
            api_key: ta.Optional[str] = None,
            *,
            search_type: str = 'auto',
            include_highlights: bool = True,
            **kwargs: ta.Any,
    ) -> None:
        super().__init__(**kwargs)
        if search_type not in (
                'instant', 'fast', 'auto', 'deep-lite', 'deep', 'deep-reasoning'):
            raise ValueError('invalid Exa search type')
        self._api_key = _require(api_key, 'EXA_API_KEY')
        self._search_type = search_type
        self._include_highlights = include_highlights

    def _headers(self) -> ta.Dict[str, str]:
        return {'x-api-key': self._api_key}

    def search(self, request: SearchRequest) -> SearchResponse:
        body: ta.Dict[str, ta.Any] = {
            'query': request.query,
            'numResults': request.limit,
            'type': self._search_type,
            'includeDomains': list(request.include_domains),
            'excludeDomains': list(request.exclude_domains),
        }
        if request.freshness_days is not None:
            body['startPublishedDate'] = _days_ago_iso_datetime(request.freshness_days)
        if request.country:
            body['userLocation'] = request.country
        if request.kind == 'academic':
            body['category'] = 'publication'
        elif request.kind == 'news':
            body['category'] = 'news'
        if request.alternate_queries and self._search_type.startswith('deep'):
            body['additionalQueries'] = list(request.alternate_queries[:10])
        if request.safe_search != 'off':
            body['moderation'] = True
        if self._include_highlights:
            body['contents'] = {'highlights': True}

        data = _as_dict(self._json(
            'POST',
            self._SEARCH_URL,
            headers=self._headers(),
            body=body,
        ))
        hits: ta.List[SearchHit] = []
        for item_value in _as_list(data.get('results'))[:request.limit]:
            item = _as_dict(item_value)
            url = _text(item.get('url')).strip()
            if not url:
                continue
            highlights = _join_text(item.get('highlights'))
            snippet = _text(item.get('summary')) or highlights
            content = _optional_text(item.get('text'))
            hits.append(SearchHit(
                title=_text(item.get('title')),
                url=url,
                snippet=snippet,
                content=content,
                published_at=_optional_text(item.get('publishedDate')),
                score=_optional_float(item.get('score')),
                source=_optional_text(item.get('author')),
                metadata={
                    'id': item.get('id'),
                    'highlights': item.get('highlights'),
                    'image': item.get('image'),
                    'favicon': item.get('favicon'),
                },
            ))
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            request_id=_optional_text(data.get('requestId') or data.get('id')),
            raw=self._raw(data),
        )

    def read(self, request: ReadRequest) -> ReadResponse:
        documents: ta.List[ReadDocument] = []
        errors: ta.List[str] = []
        raw_pages: ta.List[ta.Any] = []
        request_id: ta.Optional[str] = None
        for chunk in _chunks(request.urls, 100):
            body: ta.Dict[str, ta.Any] = {
                'urls': list(chunk),
                'text': True,
            }
            if request.live:
                body['maxAgeHours'] = 0
            if request.objective:
                body['highlights'] = {'query': request.objective}
            data = _as_dict(self._json(
                'POST',
                self._CONTENTS_URL,
                headers=self._headers(),
                body=body,
            ))
            raw_pages.append(data)
            request_id = request_id or _optional_text(
                data.get('requestId') or data.get('id'),
            )
            for item_value in _as_list(data.get('results')):
                item = _as_dict(item_value)
                url = _text(item.get('url')).strip()
                documents.append(ReadDocument(
                    requested_url=url,
                    url=url,
                    title=_text(item.get('title')),
                    content=_truncate(_text(item.get('text')), request.max_chars_per_document),
                    published_at=_optional_text(item.get('publishedDate')),
                    metadata={
                        'author': item.get('author'),
                        'highlights': item.get('highlights'),
                        'id': item.get('id'),
                    },
                ))
            errors.extend(_error_string(item) for item in _as_list(data.get('errors')))
        return ReadResponse(
            provider=self.name,
            documents=tuple(documents),
            errors=tuple(errors),
            request_id=request_id,
            raw=self._raw(raw_pages),
        )


class BraveSearch(SearchProvider):
    name = 'brave'
    capabilities = SearchCapabilities(
        domain_filtering=True,
        freshness_filtering=True,
        country=True,
        language=True,
        news=True,
        notes=("Backed by Brave's independent search index.",),
    )

    _WEB_URL = 'https://api.search.brave.com/res/v1/web/search'
    _NEWS_URL = 'https://api.search.brave.com/res/v1/news/search'

    def __init__(self, api_key: ta.Optional[str] = None, **kwargs: ta.Any) -> None:
        super().__init__(**kwargs)
        self._api_key = _require(api_key, 'BRAVE_API_KEY')

    def _headers(self) -> ta.Dict[str, str]:
        return {'X-Subscription-Token': self._api_key}

    def search(self, request: SearchRequest) -> SearchResponse:
        params: ta.Dict[str, ta.Any] = {
            'q': _query_with_site_operators(request),
            'count': min(request.limit, 20),
            'safesearch': request.safe_search,
        }
        if request.kind != 'news':
            params['extra_snippets'] = 'true'
        if request.country:
            params['country'] = request.country.upper()
        if request.language:
            params['search_lang'] = request.language.lower().split('-')[0]
        if request.freshness_days is not None:
            params['freshness'] = '{}to{}'.format(
                _days_ago_iso(request.freshness_days),
                _today_iso(),
            )
        endpoint = self._NEWS_URL if request.kind == 'news' else self._WEB_URL
        data = _as_dict(self._json(
            'GET',
            endpoint,
            query=params,
            headers=self._headers(),
        ))
        if request.kind == 'news':
            values = _as_list(data.get('results'))
        else:
            values = _as_list(_as_dict(data.get('web')).get('results'))
        hits: ta.List[SearchHit] = []
        for item_value in values[:request.limit]:
            item = _as_dict(item_value)
            url = _text(item.get('url')).strip()
            if not url:
                continue
            description = _text(item.get('description'))
            extra_snippets = _join_text(item.get('extra_snippets'))
            snippet = description
            if extra_snippets:
                snippet = description + ('\n\n' if description else '') + extra_snippets
            hits.append(SearchHit(
                title=_text(item.get('title')),
                url=url,
                snippet=snippet,
                published_at=_optional_text(
                    item.get('age') or item.get('page_age') or item.get('date'),
                ),
                source=_optional_text(
                    _as_dict(item.get('profile')).get('long_name')
                    or item.get('source'),
                ),
                metadata={
                    'language': item.get('language'),
                    'family_friendly': item.get('family_friendly'),
                    'type': item.get('type'),
                },
            ))
        warnings = ()
        if request.limit > 20:
            warnings = ('Brave returns at most 20 results per request in this demo.',)
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            warnings=warnings,
            raw=self._raw(data),
        )


class FirecrawlSearch(SearchProvider, DocumentReader):
    name = 'firecrawl'
    capabilities = SearchCapabilities(
        domain_filtering=True,
        freshness_filtering=True,
        country=True,
        news=True,
        academic=True,
        developer=True,
        readable_documents=True,
        search_result_content=True,
        notes=('Search can optionally scrape result pages; this demo keeps search and reading separate.',),
    )

    _SEARCH_URL = 'https://api.firecrawl.dev/v2/search'
    _SCRAPE_URL = 'https://api.firecrawl.dev/v2/scrape'

    def __init__(self, api_key: ta.Optional[str] = None, **kwargs: ta.Any) -> None:
        super().__init__(**kwargs)
        self._api_key = _require(api_key, 'FIRECRAWL_API_KEY')

    def _headers(self) -> ta.Dict[str, str]:
        return {'Authorization': 'Bearer ' + self._api_key}

    def search(self, request: SearchRequest) -> SearchResponse:
        body: ta.Dict[str, ta.Any] = {
            'query': request.query,
            'limit': request.limit,
            'safe': request.safe_search != 'off',
        }
        if request.include_domains and request.exclude_domains:
            body['query'] = _query_with_site_operators(request)
        elif request.include_domains:
            body['includeDomains'] = list(request.include_domains)
        elif request.exclude_domains:
            body['excludeDomains'] = list(request.exclude_domains)
        if request.country:
            body['country'] = request.country.upper()
        if request.freshness_days is not None:
            body['tbs'] = 'cdr:1,cd_min:{},cd_max:{}'.format(
                _days_ago_us(request.freshness_days),
                dt.datetime.now(dt.timezone.utc).date().strftime('%m/%d/%Y'),
            )
        body['sources'] = ['news' if request.kind == 'news' else 'web']
        if request.kind == 'academic':
            body['categories'] = [{'type': 'research'}]
        elif request.kind == 'developer':
            body['categories'] = [{'type': 'developer'}]

        data = _as_dict(self._json(
            'POST',
            self._SEARCH_URL,
            headers=self._headers(),
            body=body,
        ))
        payload = data.get('data')
        if isinstance(payload, list):
            values = payload
        else:
            payload_dict = _as_dict(payload)
            if request.kind == 'news':
                values = _as_list(payload_dict.get('news'))
            elif request.kind == 'academic':
                # Firecrawl has announced that research results will move from
                # data.web to data.research; accept both response shapes.
                values = _as_list(payload_dict.get('research'))
                if not values:
                    values = _as_list(payload_dict.get('web'))
            else:
                values = _as_list(payload_dict.get('web'))
            if not values:
                values = _as_list(payload_dict.get('results'))
        hits: ta.List[SearchHit] = []
        for item_value in values[:request.limit]:
            item = _as_dict(item_value)
            url = _text(item.get('url')).strip()
            if not url:
                primary_id = _text(item.get('primaryId')).strip()
                ids = _as_dict(item.get('ids'))
                if primary_id.startswith(('http://', 'https://')):
                    url = primary_id
                elif ids.get('doi'):
                    url = 'https://doi.org/{}'.format(ids['doi'])
                elif ids.get('arxiv'):
                    url = 'https://arxiv.org/abs/{}'.format(ids['arxiv'])
                elif ids.get('pubmed'):
                    url = 'https://pubmed.ncbi.nlm.nih.gov/{}/'.format(ids['pubmed'])
            if not url:
                continue
            metadata = _as_dict(item.get('metadata'))
            hits.append(SearchHit(
                title=_text(item.get('title') or metadata.get('title')),
                url=url,
                snippet=_text(
                    item.get('description')
                    or item.get('snippet')
                    or item.get('abstract')
                    or metadata.get('description'),
                ),
                score=_optional_float(item.get('score')),
                content=_optional_text(item.get('markdown')),
                published_at=_optional_text(
                    item.get('publishedDate') or metadata.get('publishedTime'),
                ),
                metadata=metadata,
            ))
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            request_id=_optional_text(data.get('id')),
            warnings=_warning_strings(data.get('warnings')),
            raw=self._raw(data),
        )

    def read(self, request: ReadRequest) -> ReadResponse:
        documents: ta.List[ReadDocument] = []
        errors: ta.List[str] = []
        raw_pages: ta.List[ta.Any] = []
        for url in request.urls:
            body: ta.Dict[str, ta.Any] = {
                'url': url,
                'formats': ['markdown'],
                'onlyMainContent': True,
            }
            if request.live:
                body['maxAge'] = 0
            try:
                data = _as_dict(self._json(
                    'POST',
                    self._SCRAPE_URL,
                    headers=self._headers(),
                    body=body,
                ))
            except SearchError as exc:
                errors.append('{}: {}'.format(url, exc))
                continue
            raw_pages.append(data)
            if data.get('success') is False:
                errors.append('{}: {}'.format(url, _text(data.get('error'))))
                continue
            payload = _as_dict(data.get('data')) or data
            metadata = _as_dict(payload.get('metadata'))
            final_url = _text(metadata.get('sourceURL') or payload.get('url') or url)
            documents.append(ReadDocument(
                requested_url=url,
                url=final_url,
                title=_text(metadata.get('title') or payload.get('title')),
                content=_truncate(
                    _text(payload.get('markdown') or payload.get('content')),
                    request.max_chars_per_document,
                ),
                published_at=_optional_text(metadata.get('publishedTime')),
                metadata=metadata,
            ))
        return ReadResponse(
            provider=self.name,
            documents=tuple(documents),
            errors=tuple(errors),
            raw=self._raw(raw_pages),
        )


class SearxngSearch(SearchProvider):
    name = 'searxng'
    capabilities = SearchCapabilities(
        freshness_filtering=True,
        language=True,
        news=True,
        academic=True,
        developer=True,
        notes=(
            'Requires a SearXNG instance with JSON output enabled.',
            'The quality and upstream engines depend entirely on that instance.',
        ),
    )

    def __init__(
            self,
            base_url: ta.Optional[str] = None,
            *,
            api_key: ta.Optional[str] = None,
            **kwargs: ta.Any,
    ) -> None:
        super().__init__(**kwargs)
        self._base_url = _require(base_url, 'SEARXNG_URL').rstrip('/')
        self._api_key = api_key or os.environ.get('SEARXNG_API_KEY')

    def search(self, request: SearchRequest) -> SearchResponse:
        category = {
            'web': 'general',
            'news': 'news',
            'academic': 'science',
            'developer': 'it',
        }[request.kind]
        params: ta.Dict[str, ta.Any] = {
            'q': _query_with_site_operators(request),
            'format': 'json',
            'language': request.language or 'auto',
            'safesearch': {'off': 0, 'moderate': 1, 'strict': 2}[request.safe_search],
            'categories': category,
        }
        if request.freshness_days is not None:
            if request.freshness_days <= 1:
                params['time_range'] = 'day'
            elif request.freshness_days <= 31:
                params['time_range'] = 'month'
            else:
                params['time_range'] = 'year'
        headers = {'X-API-Key': self._api_key} if self._api_key else None
        data = _as_dict(self._json(
            'GET',
            self._base_url + '/search',
            query=params,
            headers=headers,
        ))
        hits: ta.List[SearchHit] = []
        for item_value in _as_list(data.get('results'))[:request.limit]:
            item = _as_dict(item_value)
            url = _text(item.get('url')).strip()
            if not url:
                continue
            hits.append(SearchHit(
                title=_text(item.get('title')),
                url=url,
                snippet=_text(item.get('content')),
                published_at=_optional_text(item.get('publishedDate')),
                score=_optional_float(item.get('score')),
                source=_optional_text(item.get('engine')),
                metadata={
                    'engines': item.get('engines'),
                    'category': item.get('category'),
                },
            ))
        warnings = tuple(
            'unresponsive engine: {}'.format(_error_string(item))
            for item in _as_list(data.get('unresponsive_engines'))
        )
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            warnings=warnings,
            raw=self._raw(data),
        )


class SerperSearch(SearchProvider):
    name = 'serper'
    capabilities = SearchCapabilities(
        domain_filtering=True,
        freshness_filtering=True,
        country=True,
        language=True,
        news=True,
        notes=("Google-shaped results supplied through Serper's API.",),
    )

    _SEARCH_URL = 'https://google.serper.dev/search'
    _NEWS_URL = 'https://google.serper.dev/news'

    def __init__(self, api_key: ta.Optional[str] = None, **kwargs: ta.Any) -> None:
        super().__init__(**kwargs)
        self._api_key = _require(api_key, 'SERPER_API_KEY')

    def search(self, request: SearchRequest) -> SearchResponse:
        body: ta.Dict[str, ta.Any] = {
            'q': _query_with_site_operators(request),
            'num': request.limit,
        }
        if request.country:
            body['gl'] = request.country.lower()
        if request.language:
            body['hl'] = request.language.lower()
        if request.freshness_days is not None:
            body['tbs'] = 'qdr:d{}'.format(request.freshness_days)
        endpoint = self._NEWS_URL if request.kind == 'news' else self._SEARCH_URL
        data = _as_dict(self._json(
            'POST',
            endpoint,
            headers={'X-API-KEY': self._api_key},
            body=body,
        ))
        values = _as_list(data.get('news' if request.kind == 'news' else 'organic'))
        hits: ta.List[SearchHit] = []
        for item_value in values[:request.limit]:
            item = _as_dict(item_value)
            url = _text(item.get('link') or item.get('url')).strip()
            if not url:
                continue
            hits.append(SearchHit(
                title=_text(item.get('title')),
                url=url,
                snippet=_text(item.get('snippet')),
                published_at=_optional_text(item.get('date')),
                source=_optional_text(item.get('source')),
                metadata={'position': item.get('position')},
            ))
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            raw=self._raw(data),
        )


class JinaSearch(SearchProvider, DocumentReader):
    name = 'jina'
    capabilities = SearchCapabilities(
        readable_documents=True,
        search_result_content=True,
        notes=(
            'Uses Jina Search (s.jina.ai) and Reader (r.jina.ai).',
            'An API key is optional but raises limits.',
        ),
    )

    _SEARCH_BASE = 'https://s.jina.ai/'
    _READER_BASE = 'https://r.jina.ai/'

    def __init__(self, api_key: ta.Optional[str] = None, **kwargs: ta.Any) -> None:
        super().__init__(**kwargs)
        self._api_key = api_key or os.environ.get('JINA_API_KEY')

    def _headers(self) -> ta.Dict[str, str]:
        headers = {'Accept': 'application/json'}
        if self._api_key:
            headers['Authorization'] = 'Bearer ' + self._api_key
        return headers

    @staticmethod
    def _unwrap(data: ta.Any) -> ta.Any:
        if isinstance(data, dict) and 'data' in data:
            return data['data']
        return data

    def search(self, request: SearchRequest) -> SearchResponse:
        query = _query_with_site_operators(request)
        url = self._SEARCH_BASE + urllib.parse.quote(query, safe='')
        data = self._json('GET', url, headers=self._headers())
        payload = self._unwrap(data)
        values = _as_list(payload)
        if not values:
            values = _as_list(_as_dict(payload).get('results'))
        hits: ta.List[SearchHit] = []
        for item_value in values[:request.limit]:
            item = _as_dict(item_value)
            result_url = _text(item.get('url')).strip()
            if not result_url:
                continue
            hits.append(SearchHit(
                title=_text(item.get('title')),
                url=result_url,
                snippet=_text(item.get('description') or item.get('content')),
                content=_optional_text(item.get('content')),
                published_at=_optional_text(item.get('publishedTime') or item.get('date')),
                metadata={'usage': item.get('usage')},
            ))
        raw_dict = _as_dict(data)
        warnings: ta.Tuple[str, ...] = ()
        if request.limit > 5:
            warnings = ('Jina Search returns a fixed set of five results.',)
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            request_id=_optional_text(raw_dict.get('requestId')),
            warnings=warnings,
            raw=self._raw(data),
        )

    def read(self, request: ReadRequest) -> ReadResponse:
        documents: ta.List[ReadDocument] = []
        errors: ta.List[str] = []
        raw_pages: ta.List[ta.Any] = []
        for url in request.urls:
            try:
                data = self._json(
                    'GET',
                    self._READER_BASE + url,
                    headers=self._headers(),
                )
            except SearchError as exc:
                errors.append('{}: {}'.format(url, exc))
                continue
            raw_pages.append(data)
            payload = self._unwrap(data)
            item = _as_dict(payload)
            content = _text(item.get('content') or item.get('markdown') or item.get('text'))
            documents.append(ReadDocument(
                requested_url=url,
                url=_text(item.get('url') or url),
                title=_text(item.get('title')),
                content=_truncate(content, request.max_chars_per_document),
                published_at=_optional_text(item.get('publishedTime')),
                metadata={
                    key: value for key, value in item.items()
                    if key not in (
                        'url', 'title', 'content', 'markdown', 'text', 'publishedTime',
                    )
                },
            ))
        return ReadResponse(
            provider=self.name,
            documents=tuple(documents),
            errors=tuple(errors),
            raw=self._raw(raw_pages),
        )


class PerplexitySearch(SearchProvider):
    name = 'perplexity'
    capabilities = SearchCapabilities(
        domain_filtering=True,
        freshness_filtering=True,
        country=True,
        language=True,
        notes=(
            "This adapter uses Perplexity's raw Search API, not its answer-generation API.",
            'Academic intent is approximated in the query because the raw endpoint exposes web and people search types only.',
        ),
    )

    _URL = 'https://api.perplexity.ai/search'

    def __init__(
            self,
            api_key: ta.Optional[str] = None,
            *,
            search_context_size: str = 'medium',
            **kwargs: ta.Any,
    ) -> None:
        super().__init__(**kwargs)
        if search_context_size not in ('low', 'medium', 'high'):
            raise ValueError('invalid Perplexity search context size')
        self._api_key = _require(api_key, 'PERPLEXITY_API_KEY')
        self._search_context_size = search_context_size

    def search(self, request: SearchRequest) -> SearchResponse:
        query_parts = [request.query]
        query_parts.extend(
            '-site:{}'.format(domain) for domain in request.exclude_domains
        )
        # Perplexity's raw Search API currently exposes only web and people
        # search types; academic intent is approximated in the query text.
        if request.kind == 'academic':
            query_parts.append('scholarly research paper')

        warnings: ta.List[str] = []
        body: ta.Dict[str, ta.Any] = {
            'query': ' '.join(query_parts),
            'max_results': min(request.limit, 20),
            'search_context_size': self._search_context_size,
        }
        if request.include_domains:
            body['search_domain_filter'] = list(request.include_domains[:20])
            if len(request.include_domains) > 20:
                warnings.append(
                    'Perplexity search_domain_filter is capped at 20 domains.',
                )
        if request.country:
            body['country'] = request.country.lower()
        if request.language:
            body['search_language_filter'] = [request.language.lower().split('-')[0]]
        if request.freshness_days is not None:
            body['search_after_date_filter'] = _days_ago_us(request.freshness_days)

        data = _as_dict(self._json(
            'POST',
            self._URL,
            headers={'Authorization': 'Bearer ' + self._api_key},
            body=body,
        ))
        hits: ta.List[SearchHit] = []
        for item_value in _as_list(data.get('results'))[:request.limit]:
            item = _as_dict(item_value)
            url = _text(item.get('url')).strip()
            if not url:
                continue
            hits.append(SearchHit(
                title=_text(item.get('title')),
                url=url,
                snippet=_text(item.get('snippet')),
                published_at=_optional_text(item.get('date')),
                metadata={'last_updated': item.get('last_updated')},
            ))
        if request.limit > 20:
            warnings.append('Perplexity web search max_results is capped at 20.')
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=tuple(hits),
            request_id=_optional_text(data.get('id')),
            warnings=tuple(warnings),
            raw=self._raw(data),
        )


class MockSearch(SearchProvider, DocumentReader):
    """No-network provider used by the CLI demo and self-test."""

    name = 'mock'
    capabilities = SearchCapabilities(
        domain_filtering=True,
        freshness_filtering=True,
        country=True,
        language=True,
        news=True,
        academic=True,
        developer=True,
        synthesized_answer=True,
        readable_documents=True,
        search_result_content=True,
        notes=('Produces deterministic fake data and performs no network I/O.',),
    )

    def search(self, request: SearchRequest) -> SearchResponse:
        hits = tuple(
            SearchHit(
                title='Mock result {} for {}'.format(index + 1, request.query),
                url='https://example.com/mock/{}'.format(index + 1),
                snippet='Deterministic fixture result from the mock provider.',
                content='Readable search-result content for mock result {}.'.format(index + 1),
                score=1.0 / (index + 1),
                source='example.com',
                metadata={'rank': index + 1},
            )
            for index in range(request.limit)
        )
        answer = (
            'Mock synthesized answer for {!r}.'.format(request.query)
            if request.want_answer else None
        )
        return SearchResponse(
            provider=self.name,
            query=request.query,
            hits=hits,
            answer=answer,
            request_id='mock-search-1',
        )

    def read(self, request: ReadRequest) -> ReadResponse:
        documents = tuple(
            ReadDocument(
                requested_url=url,
                url=url,
                title='Mock document {}'.format(index + 1),
                content=(
                    'This is deterministic readable content for {}. '.format(url) * 3
                )[:request.max_chars_per_document],
                metadata={'live': request.live, 'objective': request.objective},
            )
            for index, url in enumerate(request.urls)
        )
        return ReadResponse(
            provider=self.name,
            documents=documents,
            request_id='mock-read-1',
        )


##
# Provider registry and command-line demo


@dataclasses.dataclass(frozen=True)
class ProviderInfo:
    name: str
    description: str
    environment: ta.Tuple[str, ...]
    factory: ta.Callable[..., SearchProvider] = dataclasses.field(repr=False)


_PROVIDER_INFOS: ta.Tuple[ProviderInfo, ...] = (
    ProviderInfo('mock', 'offline deterministic demo', (), MockSearch),
    ProviderInfo(
        'google',
        'Google Programmable Search / Custom Search JSON API',
        ('GOOGLE_API_KEY', 'GOOGLE_CSE_ID'),
        GoogleCseSearch,
    ),
    ProviderInfo(
        'duckduckgo',
        'unofficial DuckDuckGo HTML adapter',
        (),
        DuckDuckGoHtmlSearch,
    ),
    ProviderInfo('tavily', 'Tavily Search + Extract', ('TAVILY_API_KEY',), TavilySearch),
    ProviderInfo(
        'tinyfish',
        'TinyFish Search + Fetch',
        ('TINYFISH_API_KEY',),
        TinyFishSearch,
    ),
    ProviderInfo(
        'keenable',
        'Keenable Search + Fetch (key optional)',
        ('KEENABLE_API_KEY (optional)',),
        KeenableSearch,
    ),
    ProviderInfo(
        'parallel',
        'Parallel Search + Extract',
        ('PARALLEL_API_KEY',),
        ParallelSearch,
    ),
    ProviderInfo('linkup', 'Linkup Search + Fetch', ('LINKUP_API_KEY',), LinkupSearch),
    ProviderInfo('you', 'You.com Search + Contents', ('YOU_API_KEY',), YouSearch),
    ProviderInfo('exa', 'Exa Search + Contents', ('EXA_API_KEY',), ExaSearch),
    ProviderInfo('brave', 'Brave Web/News Search', ('BRAVE_API_KEY',), BraveSearch),
    ProviderInfo(
        'firecrawl',
        'Firecrawl Search + Scrape',
        ('FIRECRAWL_API_KEY',),
        FirecrawlSearch,
    ),
    ProviderInfo(
        'searxng',
        'self-hosted SearXNG JSON API',
        ('SEARXNG_URL', 'SEARXNG_API_KEY (optional)'),
        SearxngSearch,
    ),
    ProviderInfo('serper', 'Serper Google Search/News', ('SERPER_API_KEY',), SerperSearch),
    ProviderInfo(
        'jina',
        'Jina Search + Reader (key optional)',
        ('JINA_API_KEY (optional)',),
        JinaSearch,
    ),
    ProviderInfo(
        'perplexity',
        'Perplexity raw Search API',
        ('PERPLEXITY_API_KEY',),
        PerplexitySearch,
    ),
)

_PROVIDER_BY_NAME: ta.Dict[str, ProviderInfo] = {
    info.name: info for info in _PROVIDER_INFOS
}


def make_provider(
        name: str,
        *,
        transport: ta.Optional[Transport] = None,
        keep_raw: bool = False,
        **provider_kwargs: ta.Any,
) -> SearchProvider:
    try:
        info = _PROVIDER_BY_NAME[name]
    except KeyError as exc:
        raise ValueError(
            'unknown provider {!r}; choose one of {}'.format(
                name,
                ', '.join(sorted(_PROVIDER_BY_NAME)),
            ),
        ) from exc
    return info.factory(
        transport=transport,
        keep_raw=keep_raw,
        **provider_kwargs,
    )


def _jsonable(value: ta.Any) -> ta.Any:
    if dataclasses.is_dataclass(value):
        return {
            field.name: _jsonable(getattr(value, field.name))
            for field in dataclasses.fields(value)
            if getattr(value, field.name) is not None
        }
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _print_json(value: ta.Any) -> None:
    json.dump(_jsonable(value), sys.stdout, indent=2, ensure_ascii=False, sort_keys=False)
    sys.stdout.write('\n')


def _self_test() -> None:
    request = SearchRequest(
        query='python free threading',
        limit=2,
        objective='Find primary technical documentation',
        kind='developer',
        want_answer=True,
    )
    mock = MockSearch()
    response = mock.search(request)
    assert len(response.hits) == 2
    assert response.answer
    read_response = mock.read(ReadRequest(
        urls=tuple(hit.url for hit in response.hits),
        max_chars_per_document=80,
    ))
    assert len(read_response.documents) == 2
    assert all(len(document.content) <= 80 for document in read_response.documents)

    ddg_html = b"""
        <html><body>
          <div class='result'>
            <a class='result__a' href='//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fx'>Example title</a>
            <a class='result__snippet'>Example snippet</a>
          </div>
        </body></html>
    """
    ddg_transport = FixtureTransport({
        ('POST', DuckDuckGoHtmlSearch._URL): ddg_html,
    })
    ddg = DuckDuckGoHtmlSearch(transport=ddg_transport)
    ddg_response = ddg.search(SearchRequest('fixture', limit=1))
    assert ddg_response.hits[0].url == 'https://example.com/x'
    assert ddg_response.hits[0].title == 'Example title'

    tinyfish_transport = FixtureTransport({
        ('GET', TinyFishSearch._SEARCH_URL): {
            'results': [{
                'title': 'Tiny result',
                'url': 'https://example.com/tiny',
                'snippet': 'Tiny snippet',
            }],
        },
        ('POST', TinyFishSearch._FETCH_URL): {
            'results': [{
                'url': 'https://example.com/tiny',
                'final_url': 'https://example.com/tiny',
                'title': 'Tiny document',
                'text': 'Readable Markdown',
            }],
            'errors': [],
        },
    })
    tinyfish = TinyFishSearch(api_key='fixture-key', transport=tinyfish_transport)
    tiny_response = tinyfish.search(SearchRequest('fixture', limit=1))
    assert tiny_response.hits[0].title == 'Tiny result'
    tiny_read = tinyfish.read(ReadRequest(urls=(tiny_response.hits[0].url,)))
    assert tiny_read.documents[0].content == 'Readable Markdown'

    print('self-test passed: normalized model, mock, DuckDuckGo parser, and TinyFish fixtures')


def _build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Zero-dependency normalized web-search API demo',
    )
    parser.add_argument(
        'query',
        nargs='?',
        help='search query',
    )
    parser.add_argument(
        '--provider',
        choices=sorted(_PROVIDER_BY_NAME),
        default='mock',
        help='provider backend (default: mock)',
    )
    parser.add_argument(
        '--list-providers',
        action='store_true',
    )
    parser.add_argument(
        '--self-test',
        action='store_true',
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=5,
    )
    parser.add_argument('--objective')
    parser.add_argument(
        '--alternate-query',
        action='append',
        default=[],
    )
    parser.add_argument(
        '--include-domain',
        action='append',
        default=[],
    )
    parser.add_argument(
        '--exclude-domain',
        action='append',
        default=[],
    )
    parser.add_argument('--country')
    parser.add_argument('--language')
    parser.add_argument(
        '--freshness-days',
        type=int,
    )
    parser.add_argument(
        '--kind',
        choices=('web', 'news', 'academic', 'developer'),
        default='web',
    )
    parser.add_argument(
        '--safe-search',
        choices=('off', 'moderate', 'strict'),
        default='moderate',
    )
    parser.add_argument(
        '--answer',
        action='store_true',
        help='request synthesis when supported',
    )
    parser.add_argument(
        '--read-first',
        type=int,
        default=0,
        metavar='N',
        help='read the first N result URLs when the provider supports it',
    )
    parser.add_argument(
        '--max-document-chars',
        type=int,
        default=100_000,
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='prefer a live recrawl when supported',
    )
    parser.add_argument(
        '--keep-raw',
        action='store_true',
        help='include raw provider responses',
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=30.0,
    )
    return parser


def main(argv: ta.Optional[ta.Sequence[str]] = None) -> int:
    parser = _build_argument_parser()
    args = parser.parse_args(argv)

    if args.list_providers:
        for info in _PROVIDER_INFOS:
            environment = ', '.join(info.environment) if info.environment else 'none'
            print('{:<12} {:<48} env: {}'.format(
                info.name,
                info.description,
                environment,
            ))
        return 0

    if args.self_test:
        _self_test()
        return 0

    if not args.query:
        parser.error('query is required unless --list-providers or --self-test is used')
    if args.read_first < 0:
        parser.error('--read-first must be non-negative')

    transport = UrllibTransport(timeout=args.timeout)
    try:
        provider = make_provider(
            args.provider,
            transport=transport,
            keep_raw=args.keep_raw,
        )
        request = SearchRequest(
            query=args.query,
            limit=args.limit,
            objective=args.objective,
            alternate_queries=tuple(args.alternate_query),
            include_domains=tuple(args.include_domain),
            exclude_domains=tuple(args.exclude_domain),
            country=args.country,
            language=args.language,
            freshness_days=args.freshness_days,
            kind=args.kind,
            safe_search=args.safe_search,
            want_answer=args.answer,
        )
        search_response = provider.search(request)

        result: ta.Dict[str, ta.Any] = {'search': search_response}
        if args.read_first:
            if not isinstance(provider, DocumentReader):
                raise SearchError('provider {!r} does not implement DocumentReader'.format(provider.name))
            urls = tuple(
                hit.url for hit in search_response.hits[:args.read_first]
            )
            if urls:
                result['documents'] = provider.read(ReadRequest(
                    urls=urls,
                    objective=args.objective,
                    max_chars_per_document=args.max_document_chars,
                    live=args.live,
                ))
        _print_json(result)
        return 0

    except (SearchError, ValueError) as exc:
        print('error: {}'.format(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
