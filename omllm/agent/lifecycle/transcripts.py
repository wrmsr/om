"""Plain-text renderings of a transcript for a model to read, as a summarizer is given the part it is to summarize."""
import json
import typing as ta

from ... import llm


##


def _truncate(text: str, max_chars: int | None) -> str:
    if max_chars is None or len(text) <= max_chars:
        return text

    return f'{text[:max_chars]} [... {len(text) - max_chars} more characters]'


def render_transcript_tool_call(tool_call: llm.ToolCall, *, max_chars: int | None = None) -> str:
    args = json.dumps(tool_call.args, default=repr, separators=(',', ':'), sort_keys=True)
    return f'[Tool call {tool_call.name}: {_truncate(args, max_chars)}]'


def render_transcript_message(message: llm.Message, *, max_tool_call_chars: int | None = None) -> str:
    """One message as a reader would take it in. Thinking is left out: it is the model's own, and often redacted."""

    if isinstance(message, llm.UserMessage):
        text = message.content if isinstance(message.content, str) else message.content.text
        return f'## User\n\n{text}'

    if isinstance(message, llm.AiMessage):
        parts: list[str] = []
        for content in message.content:
            if isinstance(content, llm.TextContent):
                parts.append(content.text)
            elif isinstance(content, llm.ToolCall):
                parts.append(render_transcript_tool_call(content, max_chars=max_tool_call_chars))
            elif isinstance(content, llm.ThinkingContent):
                continue
            else:
                raise TypeError(content)
        return '\n\n'.join(['## Assistant', *parts])

    if isinstance(message, llm.ToolResultMessage):
        heading = f'## Tool result {message.tool_name}'
        if message.is_error:
            heading += ' (error)'
        text = '\n\n'.join(content.text for content in message.content)
        return f'{heading}\n\n{text}'

    raise TypeError(message)


def render_transcript_messages(
        messages: ta.Iterable[llm.Message],
        *,
        max_tool_call_chars: int | None = None,
) -> list[str]:
    """One block per message, kept apart so a caller fitting them to a budget can leave the oldest out."""

    return [
        render_transcript_message(message, max_tool_call_chars=max_tool_call_chars)
        for message in messages
    ]
