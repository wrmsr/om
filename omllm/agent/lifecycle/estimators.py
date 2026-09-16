import abc
import json

from omcore import lang

from ... import llm


##


class ContextTokenEstimator(lang.Abstract):
    """Estimates provider-rendered input size for proactive context-pressure decisions."""

    @abc.abstractmethod
    def estimate_context(self, context: llm.Context) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def estimate_message(self, message: llm.Message) -> int:
        raise NotImplementedError


class CharacterContextTokenEstimator(ContextTokenEstimator):
    """Portable approximate estimator based on rendered text size plus protocol overhead."""

    def __init__(self, *, chars_per_token: int = 4) -> None:
        super().__init__()

        if chars_per_token <= 0:
            raise ValueError(chars_per_token)
        self._chars_per_token = chars_per_token

    def _text_tokens(self, text: str) -> int:
        return (len(text) + self._chars_per_token - 1) // self._chars_per_token

    def estimate_message(self, message: llm.Message) -> int:
        # Role and content framing vary by provider; the fixed allowance deliberately rounds upward.
        tokens = 8

        if isinstance(message, llm.UserMessage):
            text = message.content if isinstance(message.content, str) else message.content.text
            return tokens + self._text_tokens(text)

        if isinstance(message, llm.AiMessage):
            for content in message.content:
                if isinstance(content, (llm.TextContent, llm.ThinkingContent)):
                    tokens += self._text_tokens(content.text)
                elif isinstance(content, llm.ToolCall):
                    tokens += self._text_tokens(content.id)
                    tokens += self._text_tokens(content.name)
                    tokens += self._text_tokens(json.dumps(content.args, default=repr, sort_keys=True))
                else:
                    raise TypeError(content)
            return tokens

        if isinstance(message, llm.ToolResultMessage):
            tokens += self._text_tokens(message.tool_call_id)
            tokens += self._text_tokens(message.tool_name)
            tokens += sum(self._text_tokens(content.text) for content in message.content)
            return tokens

        raise TypeError(message)

    def estimate_context(self, context: llm.Context) -> int:
        tokens = 8

        if context.system_prompt is not None:
            tokens += self._text_tokens(context.system_prompt)

        tokens += sum(self.estimate_message(message) for message in context.messages or ())

        # repr includes every advertised name, description and parameter shape. This is only a portable estimate; the
        # safety margin absorbs provider-specific JSON-schema rendering differences.
        tokens += sum(16 + self._text_tokens(repr(tool)) for tool in context.tools or ())

        return tokens
