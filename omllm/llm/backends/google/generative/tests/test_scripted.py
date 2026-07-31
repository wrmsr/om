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
from ..immediate import GoogleGenerativeImmediateBackend
from ..responses import translate_token_usage
from ..scripted import GoogleGenerativeScriptedHttpClient
from ..stream import GoogleGenerativeStreamBackend


def _model():
    return default_model_catalog()[ModelKey('google', 'gemini-3-flash-preview')]


def _api_key():
    return sec.Secret(key=None, value='goog-scripted')


def _context():
    return Context(messages=[UserMessage('hello')])


def _response():
    return ScriptedHttpResponse(
        content=[
            ThinkingContent('thinking', backend_signature='thinking-signature'),
            TextContent('answer', backend_signature='text-signature'),
            ToolCall(
                'function-call-1',
                'lookup',
                {'key': 'value'},
                backend_signature='tool-signature',
            ),
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
    GoogleGenerativeImmediateBackend,
    GoogleGenerativeStreamBackend,
])
def test_scripted_backend_round_trip(backend_cls):
    client = GoogleGenerativeScriptedHttpClient([_response()], byte_chunk_size=3)
    backend = backend_cls(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )

    message = lang.sync_await(backend.immediate(_context()))

    assert [type(content) for content in message.content] == [ThinkingContent, TextContent, ToolCall]
    thinking = check.isinstance(message.content[0], ThinkingContent)
    assert thinking.text == 'thinking'
    assert thinking.backend_signature == 'thinking-signature'
    text = check.isinstance(message.content[1], TextContent)
    assert text.text == 'answer'
    assert text.backend_signature == 'text-signature'
    tool_call = check.isinstance(message.content[2], ToolCall)
    assert tool_call.id == 'function-call-1'
    assert tool_call.args == {'key': 'value'}
    assert tool_call.backend_signature == 'tool-signature'
    assert message.stop_reason == 'tool_use'

    usage = check.not_none(message.token_usage)
    assert usage.input == 130
    assert usage.output == 50
    assert usage.reasoning == 7
    assert usage.cache_read == 20
    assert usage.cache_write is None
    assert usage.total == 180

    request = check.single(client.requests)
    assert (':streamGenerateContent' in request.url) is (backend_cls is GoogleGenerativeStreamBackend)


def test_usage_includes_tool_and_reasoning_tokens():
    usage = translate_token_usage({
        'promptTokenCount': 100,
        'toolUsePromptTokenCount': 10,
        'candidatesTokenCount': 20,
        'thoughtsTokenCount': 5,
        'cachedContentTokenCount': 40,
        'totalTokenCount': 135,
    })

    assert usage.input == 110
    assert usage.output == 25
    assert usage.reasoning == 5
    assert usage.cache_read == 40
    assert usage.total == 135


def test_cache_simulation_for_cached_content():
    client = GoogleGenerativeScriptedHttpClient(
        [
            ScriptedHttpResponse(content=[TextContent('first')]),
            ScriptedHttpResponse(content=[TextContent('second')]),
        ],
        simulate_cache=True,
    )

    request = http.HttpClientRequest(
        'https://generativelanguage.googleapis.com/v1beta/models/gemini-test:generateContent',
        headers={
            'x-goog-api-key': 'test',
            'content-type': 'application/json',
        },
        data=json.dumps({
            'cachedContent': 'cachedContents/example',
            'contents': [{
                'role': 'user',
                'parts': [{'text': 'same prompt'}],
            }],
        }),
    )

    first = json.loads(check.not_none(lang.sync_await(client.request(request)).data).decode('utf-8'))['usageMetadata']
    second = json.loads(check.not_none(lang.sync_await(client.request(request)).data).decode('utf-8'))['usageMetadata']

    assert first['cachedContentTokenCount'] == 0
    assert 'cacheWriteTokenCount' not in first
    assert second['cachedContentTokenCount'] > 0
    assert 'cacheWriteTokenCount' not in second


def test_request_scoped_explicit_cache_options_are_unsupported():
    client = GoogleGenerativeScriptedHttpClient([ScriptedHttpResponse()])
    backend = GoogleGenerativeImmediateBackend(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )

    with pytest.raises(ValueError, match='supports only implicit request-scoped caching'):
        lang.sync_await(backend.immediate(_context(), Options(
            cache_retention=CacheRetention.ONE_HOUR,
        )))

    assert not client.requests
