from .....types.content import TextContent
from .....types.content import ToolCall
from .....types.context import Context
from .....types.messages import AiMessage
from .....types.messages import ToolResultMessage
from .....types.messages import UserMessage
from .....types.models import Model
from .....types.models import ModelKey
from ..requests import RequestPreparer
from ..signatures import build_tool_call_signature


##


def _function_response(is_error):
    ctx = Context(messages=[
        UserMessage('do it'),
        AiMessage([ToolCall('t1', 'act', {})], stop_reason='tool_use'),
        ToolResultMessage(tool_call_id='t1', tool_name='act', content=[TextContent('outcome')], is_error=is_error),
    ])

    raw = RequestPreparer(Model(key=ModelKey('google', 'test'), backend='google'), ctx).raw_request()

    [part] = raw['contents'][-1]['parts']
    fr = part['functionResponse']
    assert fr['name'] == 'act'
    return fr['response']


def test_tool_result_error_uses_the_error_key():
    assert _function_response(True) == {'error': 'outcome'}


def test_tool_result_success_uses_the_result_key():
    assert _function_response(False) == {'result': 'outcome'}


##


def _tool_turn(tool_call):
    ctx = Context(messages=[
        UserMessage('do it'),
        AiMessage([tool_call], stop_reason='tool_use'),
        ToolResultMessage(tool_call_id=tool_call.id, tool_name='act', content=[TextContent('ok')]),
    ])

    raw = RequestPreparer(Model(key=ModelKey('google', 'test'), backend='google'), ctx).raw_request()

    [call_part] = raw['contents'][1]['parts']
    [response_part] = raw['contents'][2]['parts']
    return call_part, response_part['functionResponse']


def test_an_id_gemini_issued_goes_back_on_the_call_and_its_response():
    call_part, response = _tool_turn(ToolCall(
        'call-1',
        'act',
        {'k': 'v'},
        backend_signature=build_tool_call_signature(thought_signature='sig', function_call_id='call-1'),
    ))

    assert call_part == {
        'functionCall': {'id': 'call-1', 'name': 'act', 'args': {'k': 'v'}},
        'thoughtSignature': 'sig',
    }
    assert response == {'id': 'call-1', 'name': 'act', 'response': {'result': 'ok'}}


def test_a_fabricated_id_stays_home_and_a_bare_signature_is_a_thought_signature():
    # A signature as this backend wrote before it recorded ids: the thought signature alone, and no id to echo.
    call_part, response = _tool_turn(ToolCall('local-uuid', 'act', {}, backend_signature='sig'))

    assert call_part == {
        'functionCall': {'name': 'act', 'args': {}},
        'thoughtSignature': 'sig',
    }
    assert response == {'name': 'act', 'response': {'result': 'ok'}}


def test_an_unsigned_call_has_nothing_to_echo():
    call_part, response = _tool_turn(ToolCall('local-uuid', 'act', {}))

    assert call_part == {'functionCall': {'name': 'act', 'args': {}}}
    assert response == {'name': 'act', 'response': {'result': 'ok'}}


def test_another_backends_signature_is_dropped():
    # The responses backend's tool call signature is json with an 'id' of its own: not gemini's, and not sent.
    call_part, response = _tool_turn(ToolCall('fc_1', 'act', {}, backend_signature='{"id":"fc_1"}'))

    assert call_part == {'functionCall': {'name': 'act', 'args': {}}}
    assert response == {'name': 'act', 'response': {'result': 'ok'}}
