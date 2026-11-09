from .....types.content import TextContent
from .....types.content import ToolCall
from .....types.context import Context
from .....types.messages import AiMessage
from .....types.messages import ToolResultMessage
from .....types.messages import UserMessage
from .....types.models import Model
from .....types.models import ModelKey
from ...toolresults import TOOL_ERROR_OUTPUT_TAG
from ..requests import RequestPreparer


##


def _function_call_output(is_error):
    ctx = Context(messages=[
        UserMessage('do it'),
        AiMessage([ToolCall('t1', 'act', {})], stop_reason='tool_use'),
        ToolResultMessage(tool_call_id='t1', tool_name='act', content=[TextContent('outcome')], is_error=is_error),
    ])

    raw = RequestPreparer(Model(key=ModelKey('openai', 'test'), backend='openai-responses'), ctx).raw_request()

    item = raw['input'][-1]
    assert item['type'] == 'function_call_output'
    assert item['call_id'] == 't1'
    return item['output']


def test_tool_result_error_is_marked_in_the_output():
    # The api has no error flag on a function call's output, so the output says it.
    assert _function_call_output(True) == f'<{TOOL_ERROR_OUTPUT_TAG}>\noutcome\n</{TOOL_ERROR_OUTPUT_TAG}>'


def test_tool_result_success_is_bare():
    assert _function_call_output(False) == 'outcome'
