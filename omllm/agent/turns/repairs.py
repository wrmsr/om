import typing as ta

from ... import llm
from ..types.messages import Message


##


def find_unanswered_tool_calls(messages: ta.Sequence[Message]) -> list[llm.ToolCall]:
    result_ids: set[str] = set()

    for message in reversed(messages):
        if isinstance(message, llm.ToolResultMessage):
            result_ids.add(message.tool_call_id)

        elif isinstance(message, llm.AiMessage):
            return [
                content
                for content in message.content
                if isinstance(content, llm.ToolCall) and content.id not in result_ids
            ]

        elif isinstance(message, llm.UserMessage):
            return []

        # Agent messages are transparent.

    return []


def build_unanswered_tool_call_results(
        messages: ta.Sequence[Message],
        why: str,
) -> list[llm.ToolResultMessage]:
    return [
        llm.ToolResultMessage(
            tool_call_id=tool_call.id,
            tool_name=tool_call.name,
            content=(llm.TextContent(f'Tool call was not executed: {why}.'),),
            is_error=True,
        )
        for tool_call in find_unanswered_tool_calls(messages)
    ]
