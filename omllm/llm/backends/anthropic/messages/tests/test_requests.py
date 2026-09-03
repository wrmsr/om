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


def _tool_result_block(is_error):
    ctx = Context(messages=[
        UserMessage('do it'),
        AiMessage([ToolCall('t1', 'act', {})], stop_reason='tool_use'),
        ToolResultMessage(tool_call_id='t1', tool_name='act', content=[TextContent('outcome')], is_error=is_error),
    ])

    raw = RequestPreparer(Model(key=ModelKey('anthropic', 'test'), backend='anthropic'), ctx).raw_request()

    [block] = raw['messages'][-1]['content']
    assert block['type'] == 'tool_result'
    assert block['tool_use_id'] == 't1'
    assert block['content'] == 'outcome'
    return block


def test_tool_result_error_flag_is_sent():
    assert _tool_result_block(True)['is_error'] is True


def test_tool_result_success_has_no_flag():
    assert 'is_error' not in _tool_result_block(False)
