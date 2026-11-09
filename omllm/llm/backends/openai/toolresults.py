from ...types.messages import ToolResultMessage


##


TOOL_ERROR_OUTPUT_TAG = 'tool_error'


def render_tool_result_output(msg: ToolResultMessage) -> str:
    """
    A tool result as either OpenAI api takes it: text, with nowhere for the result's error flag to go. A failed call is
    marked in the text instead - wrapped rather than prefixed, so that it reads as failed whatever the text itself says.
    """

    text = '\n'.join([c.text for c in msg.content])

    if not msg.is_error:
        return text

    return f'<{TOOL_ERROR_OUTPUT_TAG}>\n{text}\n</{TOOL_ERROR_OUTPUT_TAG}>'
