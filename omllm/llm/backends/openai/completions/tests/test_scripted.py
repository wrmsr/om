import pytest

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore.formats.json import all as json
from omcore.http import all as http
from omcore.secrets import all as sec

from .....models.default import default_model_catalog
from .....types.content import TextContent
from .....types.content import ThinkingContent
from .....types.content import ToolCall
from .....types.context import Context
from .....types.messages import UserMessage
from .....types.models import CacheCapabilities
from .....types.models import ModelKey
from .....types.options import CacheRetention
from .....types.options import Options
from ....scripted.http import ScriptedHttpError
from ....scripted.http import ScriptedHttpException
from ....scripted.http import ScriptedHttpRawResponse
from ....scripted.http import ScriptedHttpResponse
from ....scripted.http import ScriptedHttpTurn
from ....scripted.http import ScriptedUsage
from ..immediate import OpenaiCompletionsImmediateBackend
from ..scripted import OpenaiCompletionsScriptedHttpClient
from ..stream import OpenaiCompletionsStreamBackend


def _model():
    return default_model_catalog()[ModelKey('openai', 'gpt-5.4-mini')]


def _api_key():
    return sec.Secret(key=None, value='sk-scripted')


def _context():
    return Context(messages=[UserMessage('hello')])


def _response():
    return ScriptedHttpResponse(
        content=[
            ThinkingContent('thinking'),
            TextContent('answer'),
            ToolCall('call_1', 'lookup', {'key': 'value'}),
        ],
        usage=ScriptedUsage(
            uncached_input_tokens=100,
            output_tokens=50,
            reasoning_tokens=7,
            cache_read_tokens=20,
            cache_write_tokens=10,
        ),
        chunk_chars=2,
    )


@pytest.mark.parametrize('backend_cls', [
    OpenaiCompletionsImmediateBackend,
    OpenaiCompletionsStreamBackend,
])
def test_scripted_backend_round_trip(backend_cls):
    client = OpenaiCompletionsScriptedHttpClient([_response()], byte_chunk_size=3)
    backend = backend_cls(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )

    message = lang.sync_await(backend.immediate(_context()))

    assert [type(content) for content in message.content] == [ThinkingContent, TextContent, ToolCall]
    assert check.isinstance(message.content[0], ThinkingContent).text == 'thinking'
    assert check.isinstance(message.content[1], TextContent).text == 'answer'
    tool_call = check.isinstance(message.content[2], ToolCall)
    assert tool_call.id == 'call_1'
    assert tool_call.args == {'key': 'value'}
    assert message.stop_reason == 'tool_use'

    usage = check.not_none(message.token_usage)
    assert usage.input == 130
    assert usage.output == 50
    assert usage.reasoning == 7
    assert usage.cache_read == 20
    assert usage.cache_write == 10
    assert usage.total == 180

    request = check.single(client.requests)
    assert request.payload['stream'] is (backend_cls is OpenaiCompletionsStreamBackend)


@pytest.mark.parametrize(('retention', 'raw_retention'), [
    (CacheRetention.IN_MEMORY, 'in_memory'),
    (CacheRetention.ONE_DAY, '24h'),
])
def test_legacy_cache_options(retention, raw_retention):
    client = OpenaiCompletionsScriptedHttpClient([ScriptedHttpResponse()])
    backend = OpenaiCompletionsImmediateBackend(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )

    lang.sync_await(backend.immediate(_context(), Options(
        cache_key='shared-prefix',
        cache_retention=retention,
    )))

    payload = check.single(client.requests).payload
    assert payload['prompt_cache_key'] == 'shared-prefix'
    assert payload['prompt_cache_retention'] == raw_retention


def test_ttl_cache_options():
    model = dc.replace(
        _model(),
        cache=CacheCapabilities(
            control_style='openai_ttl',
            retentions=frozenset({CacheRetention.THIRTY_MINUTES}),
            key=True,
        ),
    )
    client = OpenaiCompletionsScriptedHttpClient([ScriptedHttpResponse()])
    backend = OpenaiCompletionsImmediateBackend(
        model,
        api_key=_api_key(),
        http_client=client,
    )

    lang.sync_await(backend.immediate(_context(), Options(
        cache_key='shared-prefix',
        cache_retention=CacheRetention.THIRTY_MINUTES,
    )))

    payload = check.single(client.requests).payload
    assert payload['prompt_cache_key'] == 'shared-prefix'
    assert payload['prompt_cache_options'] == {'ttl': '30m'}
    assert 'prompt_cache_retention' not in payload


def test_unsupported_cache_options():
    client = OpenaiCompletionsScriptedHttpClient([ScriptedHttpResponse()])
    backend = OpenaiCompletionsImmediateBackend(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )

    with pytest.raises(ValueError, match='does not support cache retention ONE_HOUR'):
        lang.sync_await(backend.immediate(_context(), Options(
            cache_retention=CacheRetention.ONE_HOUR,
        )))

    assert not client.requests


def test_mutable_queue_expectation_raw_response_and_errors():
    client = OpenaiCompletionsScriptedHttpClient()
    seen = []

    client.append_responses(ScriptedHttpTurn(
        result=ScriptedHttpResponse(content=[TextContent('first')]),
        expect=lambda request: seen.append(request.payload['messages'][-1]['content']),
    ))
    assert client.pending_response_count() == 1

    backend = OpenaiCompletionsImmediateBackend(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )
    assert check.isinstance(
        check.single((lang.sync_await(backend.immediate(_context()))).content),
        TextContent,
    ).text == 'first'
    assert seen == ['hello']

    client.set_responses([ScriptedHttpRawResponse(
        headers={'content-type': 'application/json'},
        body=json.dumps({
            'choices': [{
                'message': {'role': 'assistant', 'content': 'raw'},
                'finish_reason': 'stop',
            }],
        }),
    )])
    assert check.isinstance(
        check.single((lang.sync_await(backend.immediate(_context()))).content),
        TextContent,
    ).text == 'raw'

    client.set_responses([ScriptedHttpError(status=429, message='rate limited')])
    with pytest.raises(http.StatusHttpClientError) as exc_info:
        lang.sync_await(backend.immediate(_context()))
    assert exc_info.value.response.status == 429

    client.set_responses([ScriptedHttpException(error=OSError('connection failed'))])
    with pytest.raises(OSError, match='connection failed'):
        lang.sync_await(backend.immediate(_context()))


def test_strict_validation_does_not_consume_response():
    client = OpenaiCompletionsScriptedHttpClient([
        ScriptedHttpResponse(content=[TextContent('unused')]),
    ])
    response = lang.sync_await(client.request(http.HttpClientRequest(
        'https://api.openai.com/v1/chat/completions',
        headers={'content-type': 'application/json'},
        data=json.dumps({
            'model': 'gpt-test',
            'messages': [{'role': 'user', 'content': 'hi'}],
            'stream': False,
        }),
    )))

    assert response.status == 401
    assert client.pending_response_count() == 1
    assert not client.requests


def test_byte_gate_can_fail_midstream():
    points = []

    async def gate(point):
        points.append((point.invocation_index, point.chunk_index))
        if point.chunk_index == 2:
            raise RuntimeError('socket failed')

    client = OpenaiCompletionsScriptedHttpClient(
        [ScriptedHttpResponse(content=[TextContent('a fairly long response')])],
        byte_chunk_size=5,
        gate=gate,
    )
    backend = OpenaiCompletionsStreamBackend(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )

    async def run():
        async with (await backend.stream(_context())) as stream:
            async for _ in stream:
                pass

    with pytest.raises(RuntimeError, match='socket failed'):
        lang.sync_await(run())

    assert points == [(0, 0), (0, 1), (0, 2)]


def _openai_usage_from_sse(data):
    chunks = [
        json.loads(line.removeprefix('data: '))
        for line in data.decode('utf-8').splitlines()
        if line.startswith('data: {')
    ]
    return check.single([chunk['usage'] for chunk in chunks if chunk.get('usage') is not None])


def test_cache_simulation():
    client = OpenaiCompletionsScriptedHttpClient(
        [
            ScriptedHttpResponse(content=[TextContent('first')]),
            ScriptedHttpResponse(content=[TextContent('second')]),
        ],
        simulate_cache=True,
    )

    request = http.HttpClientRequest(
        'https://api.openai.com/v1/chat/completions',
        headers={
            'authorization': 'Bearer test',
            'content-type': 'application/json',
        },
        data=json.dumps({
            'model': 'gpt-test',
            'messages': [{'role': 'user', 'content': 'same prompt'}],
            'stream': True,
            'stream_options': {'include_usage': True},
            'prompt_cache_key': 'cache-key',
        }),
    )

    first = _openai_usage_from_sse(check.not_none((lang.sync_await(client.request(request))).data))
    second = _openai_usage_from_sse(check.not_none((lang.sync_await(client.request(request))).data))

    assert first['prompt_tokens_details']['cached_tokens'] == 0
    assert first['prompt_tokens_details']['cache_write_tokens'] > 0
    assert second['prompt_tokens_details']['cached_tokens'] > 0
    assert 'cache_write_tokens' not in second['prompt_tokens_details']
