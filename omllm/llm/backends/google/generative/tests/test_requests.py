from .....types.content import TextContent
from .....types.content import ToolCall
from .....types.context import Context
from .....types.messages import AiMessage
from .....types.messages import ToolResultMessage
from .....types.messages import UserMessage
from .....types.models import Model
from .....types.models import ModelKey
from ..requests import RequestPreparer


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
