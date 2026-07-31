import pytest

from omcore import check
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
from .....types.models import ModelKey
from .....types.options import CacheRetention
from .....types.options import Options
from ....scripted.http import ScriptedHttpResponse
from ....scripted.http import ScriptedUsage
from ..immediate import AnthropicMessagesImmediateBackend
from ..scripted import AnthropicMessagesScriptedHttpClient
from ..stream import AnthropicMessagesStreamBackend


def _model():
    return default_model_catalog()[ModelKey('anthropic', 'claude-sonnet-5')]


def _api_key():
    return sec.Secret(key=None, value='sk-ant-scripted')


def _context():
    return Context(messages=[UserMessage('hello')])


def _response():
    return ScriptedHttpResponse(
        content=[
            ThinkingContent('thinking', backend_signature='thinking-signature'),
            ThinkingContent('<redacted>', backend_signature='opaque-data', redacted=True),
            TextContent('answer'),
            ToolCall('toolu_1', 'lookup', {'key': 'value'}),
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
    AnthropicMessagesImmediateBackend,
    AnthropicMessagesStreamBackend,
])
def test_scripted_backend_round_trip(backend_cls):
    client = AnthropicMessagesScriptedHttpClient([_response()], byte_chunk_size=3)
    backend = backend_cls(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )

    message = lang.sync_await(backend.immediate(_context()))

    assert [type(content) for content in message.content] == [
        ThinkingContent,
        ThinkingContent,
        TextContent,
        ToolCall,
    ]
    thinking = check.isinstance(message.content[0], ThinkingContent)
    assert thinking.text == 'thinking'
    assert thinking.backend_signature == 'thinking-signature'
    redacted = check.isinstance(message.content[1], ThinkingContent)
    assert redacted.redacted
    assert redacted.backend_signature == 'opaque-data'
    assert check.isinstance(message.content[2], TextContent).text == 'answer'
    tool_call = check.isinstance(message.content[3], ToolCall)
    assert tool_call.id == 'toolu_1'
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
    assert bool(request.payload.get('stream')) is (backend_cls is AnthropicMessagesStreamBackend)
    assert request.headers.single['anthropic-version'] == '2023-06-01'


@pytest.mark.parametrize(('retention', 'raw_retention'), [
    (CacheRetention.FIVE_MINUTES, '5m'),
    (CacheRetention.ONE_HOUR, '1h'),
])
def test_automatic_cache_options(retention, raw_retention):
    client = AnthropicMessagesScriptedHttpClient([ScriptedHttpResponse()])
    backend = AnthropicMessagesImmediateBackend(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )

    lang.sync_await(backend.immediate(_context(), Options(cache_retention=retention)))

    assert check.single(client.requests).payload['cache_control'] == {
        'type': 'ephemeral',
        'ttl': raw_retention,
    }


def test_automatic_cache_usage_is_inclusive():
    client = AnthropicMessagesScriptedHttpClient(
        [ScriptedHttpResponse(), ScriptedHttpResponse()],
        simulate_cache=True,
    )
    backend = AnthropicMessagesImmediateBackend(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )
    options = Options(cache_retention=CacheRetention.FIVE_MINUTES)

    first = check.not_none(lang.sync_await(backend.immediate(_context(), options)).token_usage)
    second = check.not_none(lang.sync_await(backend.immediate(_context(), options)).token_usage)

    assert first.input == first.cache_write
    assert first.cache_read == 0
    assert second.input == second.cache_read
    assert second.cache_write == 0
    assert first.input == second.input


def test_cache_key_is_unsupported():
    client = AnthropicMessagesScriptedHttpClient([ScriptedHttpResponse()])
    backend = AnthropicMessagesImmediateBackend(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )

    with pytest.raises(ValueError, match='does not support caller-supplied prompt cache keys'):
        lang.sync_await(backend.immediate(_context(), Options(cache_key='key')))

    assert not client.requests


def _anthropic_start_usage(data):
    events = [
        json.loads(line.removeprefix('data: '))
        for line in data.decode('utf-8').splitlines()
        if line.startswith('data: {')
    ]
    return events[0]['message']['usage']


def test_cache_simulation_normalizes_moved_markers():
    client = AnthropicMessagesScriptedHttpClient(
        [
            ScriptedHttpResponse(content=[TextContent('first')]),
            ScriptedHttpResponse(content=[TextContent('second')]),
        ],
        simulate_cache=True,
    )

    def request(*, marker_on_system):
        marker = {'cache_control': {'type': 'ephemeral'}}
        return http.HttpClientRequest(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': 'test',
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json',
            },
            data=json.dumps({
                'model': 'claude-test',
                'max_tokens': 100,
                'stream': True,
                'system': [{
                    'type': 'text',
                    'text': 'system',
                    **(marker if marker_on_system else {}),
                }],
                'messages': [{
                    'role': 'user',
                    'content': [{
                        'type': 'text',
                        'text': 'same prompt',
                        **(marker if not marker_on_system else {}),
                    }],
                }],
            }),
        )

    first = _anthropic_start_usage(check.not_none((lang.sync_await(client.request(request(marker_on_system=True))).data)))  # noqa
    second = _anthropic_start_usage(check.not_none((lang.sync_await(client.request(request(marker_on_system=False)))).data))  # noqa

    assert first['cache_read_input_tokens'] == 0
    assert first['cache_creation_input_tokens'] > 0
    assert second['cache_read_input_tokens'] > 0
    assert second['cache_creation_input_tokens'] == 0
