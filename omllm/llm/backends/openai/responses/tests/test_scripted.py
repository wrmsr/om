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
from .....types.messages import AiMessage
from .....types.messages import ToolResultMessage
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
from ..immediate import OpenaiResponsesImmediateBackend
from ..requests import RequestPreparer
from ..scripted import OpenaiResponsesScriptedHttpClient
from ..stream import OpenaiResponsesStreamBackend


def _model():
    return default_model_catalog()[ModelKey('openai', 'gpt-5.6-luna')]


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
    OpenaiResponsesImmediateBackend,
    OpenaiResponsesStreamBackend,
])
def test_scripted_backend_round_trip(backend_cls):
    client = OpenaiResponsesScriptedHttpClient([_response()], byte_chunk_size=3)
    backend = backend_cls(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )

    message = lang.sync_await(backend.immediate(_context()))

    assert [type(content) for content in message.content] == [ThinkingContent, TextContent, ToolCall]

    thinking = check.isinstance(message.content[0], ThinkingContent)
    assert thinking.text == 'thinking'
    raw_thinking_item = json.loads(check.not_none(thinking.backend_signature))
    assert raw_thinking_item['type'] == 'reasoning'
    assert raw_thinking_item['encrypted_content'] == 'scripted-encrypted-1-0'

    text = check.isinstance(message.content[1], TextContent)
    assert text.text == 'answer'
    assert json.loads(check.not_none(text.backend_signature)) == {
        'id': 'msg_scripted_1_1',
        'phase': 'final_answer',
    }

    tool_call = check.isinstance(message.content[2], ToolCall)
    assert tool_call.id == 'call_1'
    assert tool_call.args == {'key': 'value'}
    assert json.loads(check.not_none(tool_call.backend_signature)) == {'id': 'fc_scripted_1_2'}

    assert message.stop_reason == 'tool_use'

    usage = check.not_none(message.token_usage)
    assert usage.input == 130
    assert usage.output == 50
    assert usage.reasoning == 7
    assert usage.cache_read == 20
    assert usage.cache_write == 10
    assert usage.total == 180

    request = check.single(client.requests)
    assert request.payload['stream'] is (backend_cls is OpenaiResponsesStreamBackend)
    assert request.payload['store'] is False
    assert request.payload['include'] == ['reasoning.encrypted_content']


def test_replay_request_translation():
    client = OpenaiResponsesScriptedHttpClient([_response()])
    backend = OpenaiResponsesImmediateBackend(
        _model(),
        api_key=_api_key(),
        http_client=client,
    )

    message = lang.sync_await(backend.immediate(_context()))

    context = Context(messages=[
        UserMessage('hello'),
        message,
        ToolResultMessage(
            tool_call_id='call_1',
            tool_name='lookup',
            content=[TextContent('result')],
        ),
    ])

    raw_input = RequestPreparer(_model(), context).raw_request()['input']

    assert raw_input[0] == {'role': 'user', 'content': [{'type': 'input_text', 'text': 'hello'}]}

    # Signed reasoning replays as the verbatim item.
    assert raw_input[1]['type'] == 'reasoning'
    assert raw_input[1]['encrypted_content'] == 'scripted-encrypted-1-0'

    # Signed text replays as its original output item, identity included.
    assert raw_input[2]['type'] == 'message'
    assert raw_input[2]['id'] == 'msg_scripted_1_1'
    assert raw_input[2]['phase'] == 'final_answer'
    assert raw_input[2]['content'] == [{'type': 'output_text', 'text': 'answer'}]

    assert raw_input[3]['type'] == 'function_call'
    assert raw_input[3]['id'] == 'fc_scripted_1_2'
    assert raw_input[3]['call_id'] == 'call_1'
    assert raw_input[3]['name'] == 'lookup'
    assert json.loads(raw_input[3]['arguments']) == {'key': 'value'}

    assert raw_input[4] == {'type': 'function_call_output', 'call_id': 'call_1', 'output': 'result'}


def test_unsigned_replay_request_translation():
    context = Context(messages=[
        UserMessage('hello'),
        AiMessage([
            ThinkingContent('private'),
            TextContent('answer'),
            ToolCall('call_9', 'lookup', {'key': 'value'}),
        ]),
        ToolResultMessage(
            tool_call_id='call_9',
            tool_name='lookup',
            content=[TextContent('result')],
        ),
    ])

    raw_input = RequestPreparer(_model(), context).raw_request()['input']

    # Unsigned thinking cannot be represented and is dropped; unsigned text downgrades to a plain assistant message;
    # an unsigned tool call replays without item identity.
    assert raw_input == [
        {'role': 'user', 'content': [{'type': 'input_text', 'text': 'hello'}]},
        {'role': 'assistant', 'content': [{'type': 'output_text', 'text': 'answer'}]},
        {'type': 'function_call', 'call_id': 'call_9', 'name': 'lookup', 'arguments': json.dumps({'key': 'value'})},
        {'type': 'function_call_output', 'call_id': 'call_9', 'output': 'result'},
    ]


def test_ttl_cache_options():
    client = OpenaiResponsesScriptedHttpClient([ScriptedHttpResponse()])
    backend = OpenaiResponsesImmediateBackend(
        _model(),
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


@pytest.mark.parametrize(('retention', 'raw_retention'), [
    (CacheRetention.IN_MEMORY, 'in_memory'),
    (CacheRetention.ONE_DAY, '24h'),
])
def test_legacy_cache_options(retention, raw_retention):
    model = dc.replace(
        _model(),
        cache=CacheCapabilities(
            control_style='openai_legacy',
            retentions=frozenset({
                CacheRetention.IN_MEMORY,
                CacheRetention.ONE_DAY,
            }),
            key=True,
        ),
    )
    client = OpenaiResponsesScriptedHttpClient([ScriptedHttpResponse()])
    backend = OpenaiResponsesImmediateBackend(
        model,
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
    assert 'prompt_cache_options' not in payload


def test_unsupported_cache_options():
    client = OpenaiResponsesScriptedHttpClient([ScriptedHttpResponse()])
    backend = OpenaiResponsesImmediateBackend(
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
    client = OpenaiResponsesScriptedHttpClient()
    seen = []

    client.append_responses(ScriptedHttpTurn(
        result=ScriptedHttpResponse(content=[TextContent('first')]),
        expect=lambda request: seen.append(request.payload['input'][-1]['content'][0]['text']),
    ))
    assert client.pending_response_count() == 1

    backend = OpenaiResponsesImmediateBackend(
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
            'status': 'completed',
            'output': [{
                'id': 'msg_raw',
                'type': 'message',
                'status': 'completed',
                'role': 'assistant',
                'content': [{'type': 'output_text', 'text': 'raw'}],
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
    client = OpenaiResponsesScriptedHttpClient([
        ScriptedHttpResponse(content=[TextContent('unused')]),
    ])
    response = lang.sync_await(client.request(http.HttpClientRequest(
        'https://api.openai.com/v1/responses',
        headers={'content-type': 'application/json'},
        data=json.dumps({
            'model': 'gpt-test',
            'input': [{'role': 'user', 'content': [{'type': 'input_text', 'text': 'hi'}]}],
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

    client = OpenaiResponsesScriptedHttpClient(
        [ScriptedHttpResponse(content=[TextContent('a fairly long response')])],
        byte_chunk_size=5,
        gate=gate,
    )
    backend = OpenaiResponsesStreamBackend(
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
    events = [
        json.loads(line.removeprefix('data: '))
        for line in data.decode('utf-8').splitlines()
        if line.startswith('data: {')
    ]
    return check.single([
        event['response']['usage']
        for event in events
        if event.get('response') is not None and event['response'].get('usage') is not None
    ])


def test_cache_simulation():
    client = OpenaiResponsesScriptedHttpClient(
        [
            ScriptedHttpResponse(content=[TextContent('first')]),
            ScriptedHttpResponse(content=[TextContent('second')]),
        ],
        simulate_cache=True,
    )

    request = http.HttpClientRequest(
        'https://api.openai.com/v1/responses',
        headers={
            'authorization': 'Bearer test',
            'content-type': 'application/json',
        },
        data=json.dumps({
            'model': 'gpt-test',
            'input': [{'role': 'user', 'content': [{'type': 'input_text', 'text': 'same prompt'}]}],
            'stream': True,
            'prompt_cache_key': 'cache-key',
        }),
    )

    first = _openai_usage_from_sse(check.not_none((lang.sync_await(client.request(request))).data))
    second = _openai_usage_from_sse(check.not_none((lang.sync_await(client.request(request))).data))

    assert first['input_tokens_details']['cached_tokens'] == 0
    assert first['input_tokens_details']['cache_write_tokens'] > 0
    assert second['input_tokens_details']['cached_tokens'] > 0
    assert second['input_tokens_details']['cache_write_tokens'] == 0
