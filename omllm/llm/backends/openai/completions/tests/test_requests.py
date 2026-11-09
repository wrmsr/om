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


def _tool_message_content(is_error):
    ctx = Context(messages=[
        UserMessage('do it'),
        AiMessage([ToolCall('t1', 'act', {})], stop_reason='tool_use'),
        ToolResultMessage(tool_call_id='t1', tool_name='act', content=[TextContent('outcome')], is_error=is_error),
    ])

    raw = RequestPreparer(Model(key=ModelKey('openai', 'test'), backend='openai-completions'), ctx).raw_request()

    msg = raw['messages'][-1]
    assert msg['role'] == 'tool'
    assert msg['tool_call_id'] == 't1'
    return msg['content']


def test_tool_result_error_is_marked_in_the_content():
    # The api has no error flag on a tool message, so the content says it.
    assert _tool_message_content(True) == f'<{TOOL_ERROR_OUTPUT_TAG}>\noutcome\n</{TOOL_ERROR_OUTPUT_TAG}>'


def test_tool_result_success_is_bare():
    assert _tool_message_content(False) == 'outcome'
